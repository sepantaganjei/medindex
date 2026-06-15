import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.path as mpath
import numpy as np
import os
import uuid
from skimage.measure import label, regionprops
from skimage.filters import threshold_otsu
import tkinter as tk
from tkinter import messagebox
from scipy.ndimage import generic_filter
from scipy.signal import convolve
from skimage.color import rgb2gray
from skimage import img_as_ubyte
from skimage.feature import graycomatrix, graycoprops


""" 
This code was a first implementation of the feature extraction part. 
It is now deprecated in favour of the version using pyradiomics
"""


class RoiSelector:
    def __init__(self, image_path):
        self.image_path = image_path 
        self.img = mpimg.imread(image_path)
        self.fig, self.ax = plt.subplots()
        self.ax.imshow(self.img)
        
        self.punti_x = []
        self.punti_y = []
        
        # Linea definitiva (quella che resta)
        self.linea_def, = self.ax.plot([], [], 'ro-', markersize=4)
        # Linea "elastica" (quella che segue il mouse)
        self.linea_temp, = self.ax.plot([], [], 'r--', alpha=0.5)
        
        # Connessione eventi
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_move)
        
        self.roi_done = False
        self.roi_pending = False

        plt.title("Click SX: punto | Click DX: chiudi | ESC: esci")
        plt.show()

    def on_click(self, event):
        if not self.roi_done and not self.roi_pending:
            if event.inaxes != self.ax:
                return
            if self.fig.canvas.toolbar.mode != "":
                return

            if event.button == 1:
                self.punti_x.append(event.xdata)
                self.punti_y.append(event.ydata)
                self.linea_def.set_data(self.punti_x, self.punti_y)
                self.fig.canvas.draw()

            elif event.button == 3 and len(self.punti_x) > 2:
                valid, error_msg = is_valid_polygon(self.punti_x, self.punti_y)

                if not valid:
                    root = tk.Tk()
                    root.withdraw()
                    messagebox.showerror("ROI non valida", f"Poligono non valido:\n{error_msg}\n\nRidisegna la ROI.")
                    root.destroy()
                    self.punti_x.clear()
                    self.punti_y.clear()
                    self.linea_def.set_data([], [])
                    self.linea_temp.set_data([], [])
                    self.fig.canvas.draw()
                    return

                # Chiudi il poligono visivamente
                self.punti_x.append(self.punti_x[0])
                self.punti_y.append(self.punti_y[0])
                self.linea_def.set_data(self.punti_x, self.punti_y)
                self.linea_temp.set_data([], [])
                self.roi_pending = True
                self.fig.canvas.draw()

                # Ritaglia subito la ROI
                img = mpimg.imread(self.image_path)
                points = list(zip(self.punti_x, self.punti_y))
                file_path = cut_image(points, img)

                # Dialog di conferma con anteprima
                confirmed = confirm_roi(file_path, self.fig)

                if confirmed:
                    self.roi_done = True
                    self.confirmed_path = file_path
                    print("ROI confermata!")
                else:
                    # Reset: l'utente ridisegna
                    self.roi_pending = False
                    self.punti_x.clear()
                    self.punti_y.clear()
                    self.linea_def.set_data([], [])
                    self.linea_temp.set_data([], [])
                    self.fig.canvas.draw()
                    print("ROI rifiutata, ridisegna.")

    def on_move(self, event):
        if not self.roi_done and not self.roi_pending:
            if event.inaxes != self.ax or len(self.punti_x) == 0:
                return
            
            # Aggiorna la linea elastica dall'ultimo punto alla posizione del mouse
            self.linea_temp.set_data([self.punti_x[-1], event.xdata], 
                                    [self.punti_y[-1], event.ydata])
            self.fig.canvas.draw()


def confirm_roi(image_path, selector_fig):

    img = mpimg.imread(image_path)

    # Mostra ROI
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(img)
    ax.set_title("ROI ritagliata")
    ax.axis("off")

    plt.tight_layout()
    plt.show(block=False)

    # forza refresh finestra matplotlib
    fig.canvas.draw()
    fig.canvas.flush_events()

    # finestra tkinter
    root = tk.Tk()
    root.withdraw()

    result = {"confirmed": False}

    dialog = tk.Toplevel(root)
    dialog.title("Conferma ROI")
    dialog.geometry("350x140")
    dialog.attributes("-topmost", True)

    tk.Label(
        dialog,
        text="La ROI selezionata è corretta?",
        pady=20
    ).pack()

    def on_yes():
        result["confirmed"] = True
        dialog.destroy()
        root.quit()

    def on_no():
        result["confirmed"] = False
        dialog.destroy()
        root.quit()

    frame = tk.Frame(dialog)
    frame.pack(pady=10)

    tk.Button(frame, text="Sì", width=10, command=on_yes).pack(
        side=tk.LEFT, padx=10
    )

    tk.Button(frame, text="No", width=10, command=on_no).pack(
        side=tk.LEFT, padx=10
    )

    dialog.grab_set()
    root.mainloop()
    root.destroy()

    confirmed = result["confirmed"]

    plt.close(fig)

    if confirmed:
        plt.close(selector_fig)

    return confirmed


def segments_intersect(p1, p2, p3, p4):
    """
    Controlla se il segmento p1-p2 interseca il segmento p3-p4.
    Usa il metodo delle orientazioni (cross product).
    """
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def on_segment(p, q, r):
        return (min(p[0], r[0]) <= q[0] <= max(p[0], r[0]) and
                min(p[1], r[1]) <= q[1] <= max(p[1], r[1]))

    d1 = cross(p3, p4, p1)
    d2 = cross(p3, p4, p2)
    d3 = cross(p1, p2, p3)
    d4 = cross(p1, p2, p4)

    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
       ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        return True

    # Casi collineari
    if d1 == 0 and on_segment(p3, p1, p4): return True
    if d2 == 0 and on_segment(p3, p2, p4): return True
    if d3 == 0 and on_segment(p1, p3, p2): return True
    if d4 == 0 and on_segment(p1, p4, p2): return True

    return False


def is_valid_polygon(points_x, points_y):
    """
    Controlla che nessun lato del poligono si intersechi con un altro
    (esclusi i vertici adiacenti condivisi).
    Restituisce (True, None) se valido, (False, messaggio) se no.
    """
    n = len(points_x)
    if n < 3:
        return False, "Servono almeno 3 punti per formare un poligono."

    pts = list(zip(points_x, points_y))
    segments = [(pts[i], pts[(i + 1) % n]) for i in range(n)]

    for i in range(len(segments)):
        for j in range(i + 2, len(segments)):
            # Salta il caso in cui i segmenti sono "adiacenti" (condividono un vertice)
            if i == 0 and j == len(segments) - 1:
                continue
            p1, p2 = segments[i]
            p3, p4 = segments[j]
            if segments_intersect(p1, p2, p3, p4):
                return False, f"Il poligono si auto-interseca tra il lato {i+1} e il lato {j+1}."

    return True, None


def cut_image(points, image):
    height, width = image.shape[:2]
    
    # 1. Creazione della maschera (booleana)
    x, y = np.meshgrid(np.arange(width), np.arange(height))
    pix_coords = np.column_stack((x.flatten(), y.flatten()))
    path = mpath.Path(points)
    mask = path.contains_points(pix_coords).reshape(height, width)
    
    # 2. Creazione dell'immagine RGBA (Red, Green, Blue, Alpha)
    # Inizializziamo un array di zeri (completamente trasparente)
    new_image = np.zeros((height, width, 4), dtype=np.float32)
    
    # Normalizziamo l'immagine originale in scala 0-1 se è in 0-255
    # (Matplotlib lavora meglio con i float per la trasparenza)
    img_normalized = image.astype(np.float32)
    if img_normalized.max() > 1.0:
        img_normalized /= 255.0

    if len(image.shape) == 3:
        # Immagine a colori: copiamo R, G, B
        new_image[mask, :3] = img_normalized[mask]
    else:
        # Scala di grigi: copiamo il valore su R, G e B per mantenere il grigio
        for i in range(3):
            new_image[mask, i] = img_normalized[mask]
            
    # 3. Impostiamo l'Alpha a 1.0 (opaco) solo dove la maschera è True
    new_image[mask, 3] = 1.0
    
    # 4. Ritaglio dei bordi (Crop)
    pts_array = np.array(points)
    x_min, y_min = pts_array.min(axis=0).astype(int)
    x_max, y_max = pts_array.max(axis=0).astype(int)
    
    # Padding di sicurezza per non tagliare pixel sui bordi
    cropped_image = new_image[max(0, y_min):y_max, max(0, x_min):x_max]
    
    # 5. Salvataggio
    output_dir = "."
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    file_path = os.path.join(output_dir, "cut_.png")
    
    # plt.imsave gestisce correttamente l'array RGBA
    plt.imsave(file_path, cropped_image)
    
    return file_path


def standard_deviation(image):
    
    image = np.asarray(image)
    
    # Caso RGBA → usa alpha channel come maschera
    if image.ndim == 3 and image.shape[2] == 4:
        rgb = image[:, :, :3]
        alpha = image[:, :, 3]
        
        # Maschera: pixel visibili
        mask = alpha > 0
        
        # Converti in grayscale (media semplice)
        gray = rgb.mean(axis=2)
        
        values = gray[mask]
    
    # Caso RGB (senza trasparenza)
    elif image.ndim == 3 and image.shape[2] == 3:
        gray = image.mean(axis=2)
        values = gray.flatten()
    
    # Caso grayscale
    elif image.ndim == 2:
        values = image.flatten()
    
    else:
        raise ValueError("Formato immagine non supportato")
    
    # Evita array vuoto
    if values.size == 0:
        return 0.0
    
    return float(np.std(values))


def mean(image):
    
    image = np.asarray(image)
    
    # Caso RGBA → usa alpha channel come maschera
    if image.ndim == 3 and image.shape[2] == 4:
        rgb = image[:, :, :3]
        alpha = image[:, :, 3]
        
        # Maschera: pixel visibili
        mask = alpha > 0
        
        # Converti in grayscale (media semplice)
        gray = rgb.mean(axis=2)
        
        values = gray[mask]
    
    # Caso RGB (senza trasparenza)
    elif image.ndim == 3 and image.shape[2] == 3:
        gray = image.mean(axis=2)
        values = gray.flatten()
    
    # Caso grayscale
    elif image.ndim == 2:
        values = image.flatten()
    
    else:
        raise ValueError("Formato immagine non supportato")
    
    # Evita array vuoto
    if values.size == 0:
        return 0.0
    
    return float(np.mean(values))


def eccentricity(image):
    
    image = np.asarray(image)
    
    # Se RGB → grayscale
    if image.ndim == 3:
        image = image.mean(axis=2)
    
    # Calcolo soglia automatica (Otsu)
    try:
        thresh = threshold_otsu(image)
        mask = image > thresh
    except:
        # fallback se immagine uniforme
        mask = image > image.mean()
    
    # Etichetta componenti
    labeled = label(mask)
    regions = regionprops(labeled)
    
    if len(regions) == 0:
        return 0.0
    
    # Regione principale (la ROI vera)
    largest_region = max(regions, key=lambda r: r.area)
    
    return float(largest_region.eccentricity)


def show_roi_and_histogram(image, bins=256):
    
    image = np.asarray(image)
    
    # grayscale
    if image.ndim == 3:
        image = image.mean(axis=2)
    
    # crea maschera (ROI vs background)
    mask = image > 0   # oppure threshold se serve
    
    values = image[mask]
    
    if values.size == 0:
        print("ROI vuota")
        return
    
    # immagine con trasparenza
    img_rgba = np.zeros((*image.shape, 4))
    
    img_rgba[..., 0] = image
    img_rgba[..., 1] = image
    img_rgba[..., 2] = image
    img_rgba[..., 3] = mask.astype(float)  # alpha channel
    
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    
    ax[0].imshow(img_rgba)
    ax[0].set_title("ROI")
    ax[0].axis("off")
    
    ax[1].hist(values, bins=bins)
    ax[1].set_title("Histogram")
    ax[1].set_xlabel("Intensity")
    ax[1].set_ylabel("Frequency")
    
    plt.tight_layout()
    plt.show()


def compute_glrlm(image, levels=None, direction=(0, 1)):
    """
    Calcola la Gray Level Run Length Matrix (GLRLM).

    Parameters
    ----------
    image : ndarray
        Immagine 2D della ROI già quantizzata.
    levels : int, optional
        Numero di livelli di grigio.
        Se None, viene ricavato automaticamente.
    direction : tuple
        Direzione del run:
        (0,1)=orizzontale
        (1,0)=verticale
        (1,1)=diagonale
        (-1,1)=antidiagonale

    Returns
    -------
    glrlm : ndarray
        Matrice GLRLM di shape (Ng, Nr)
    """

    image = np.asarray(image)

    # Se RGB -> grayscale
    if len(image.shape) == 3:

        # RGB/RGBA
        image = image[:, :, 0]

    if levels is None:
        levels = int(image.max()) + 1

    dx, dy = direction

    rows, cols = image.shape

    max_run = max(rows, cols)

    glrlm = np.zeros((levels, max_run), dtype=np.float64)

    visited = np.zeros_like(image, dtype=bool)

    for i in range(rows):
        for j in range(cols):

            if visited[i, j]:
                continue

            gray = image[i, j]

            run_length = 1

            x, y = i + dx, j + dy

            visited[i, j] = True

            while (
                0 <= x < rows and
                0 <= y < cols and
                image[x, y] == gray
            ):
                visited[x, y] = True
                run_length += 1
                x += dx
                y += dy

            glrlm[int(gray), run_length - 1] += 1

    return glrlm


def GLRLM_short_run_emphasis(image, levels=None, direction=(0, 1)):
    """
    Calcola la feature GLRLM Short Run Emphasis (SRE).

    Parameters
    ----------
    image : ndarray
        ROI 2D quantizzata.
    levels : int, optional
        Numero livelli di grigio.
    direction : tuple
        Direzione della GLRLM.

    Returns
    -------
    sre : float
        Short Run Emphasis
    """

    glrlm = compute_glrlm(image, levels, direction)

    Nr = np.sum(glrlm)

    if Nr == 0:
        return 0.0

    run_lengths = np.arange(1, glrlm.shape[1] + 1)

    denominator = run_lengths ** 2

    sre = np.sum(glrlm / denominator[np.newaxis, :]) / Nr

    return sre


def compute_ngtdm(image, d=1):
    # Assicuriamoci che sia un array numpy
    image = np.asanyarray(image)

    # 1. Gestione Colore e Canale Alfa
    if image.ndim == 3:
        # Se ha 4 canali (RGBA), prendiamo solo i primi 3 (RGB)
        if image.shape[-1] == 4:
            image = image[:, :, :3]
        
        # Ora che siamo sicuri di avere 3 canali, convertiamo in grigio
        if image.shape[-1] == 3:
            image = rgb2gray(image)
    
    # 2. Conversione in ubyte (0-255)
    # skimage.rgb2gray restituisce float tra 0 e 1, lo riportiamo a interi
    if image.dtype != np.uint8:
        from skimage import img_as_ubyte
        image = img_as_ubyte(image)
    
    image = image.astype(float)
    rows, cols = image.shape
    
    # 3. Calcolo Media Locale tramite Convoluzione (Molto più veloce)
    # Creiamo un kernel che somma i vicini escludendo il centro
    size = 2 * d + 1
    kernel = np.ones((size, size))
    kernel[d, d] = 0
    # Normalizziamo il kernel per ottenere la media
    kernel /= kernel.sum()
    
    # Calcoliamo la media dei vicini
    avg_neighbor = convolve(image, kernel, mode='same')
    
    # 4. Calcolo differenze
    diff_image = np.abs(image - avg_neighbor)
    
    # 5. Estrazione statistiche di base
    levels = np.unique(image.astype(int))
    total_pixels = image.size
    
    n_i = {}
    s_i = {}
    p_i = {}
    
    for i in levels:
        mask_i = (image == i)
        n_i_val = np.sum(mask_i)
        if n_i_val > 0:
            n_i[i] = n_i_val
            s_i[i] = np.sum(diff_image[mask_i])
            p_i[i] = n_i_val / total_pixels
        
    return s_i, p_i, levels


def compute_ngtdm_coarseness(image, d=1):
    s_i, p_i, levels = compute_ngtdm(image, d)
    # Formula: 1 / [sum(p_i * s_i)]
    sum_ps = sum(p_i[i] * s_i[i] for i in levels)
    return 1.0 / (sum_ps + 1e-6) # Protezione divisione per zero


def compute_ngtdm_contrast(image, d=1):
    s_i, p_i, levels = compute_ngtdm(image, d)
    # Formula legata alla differenza tra i e j pesata per p_i * p_j
    # Semplificata: [1 / (Ng*(Ng-1))] * [sum(p_i * p_j * (i-j)^2)] * [sum(s_i)]
    Ng = len(levels)
    if Ng <= 1: return 0
    
    sum_s = sum(s_i.values())
    total_sum = 0
    for i in levels:
        for j in levels:
            total_sum += p_i[i] * p_i[j] * (i - j)**2
            
    return (total_sum / (Ng * (Ng - 1))) * (sum_s / image.size)


def compute_ngtdm_busyness(image, d=1):
    s_i, p_i, levels = compute_ngtdm(image, d)
    # Formula: [sum(p_i * s_i)] / [sum(i*p_i - j*p_j)]
    numerator = sum(p_i[i] * s_i[i] for i in levels)
    denominator = 0
    for i in levels:
        for j in levels:
            if p_i[i] > 0 and p_i[j] > 0:
                denominator += abs(i * p_i[i] - j * p_i[j])
                
    return numerator / (denominator + 1e-6)


# def _preprocess_image(image):
#     """Gestisce la conversione in scala di grigi e 8-bit (RGBA/RGB -> Gray)"""
#     img = np.asanyarray(image)
    
#     # Se ha 4 canali (RGBA), scartiamo l'alfa; se ne ha 3 (RGB), convertiamo
#     if img.ndim == 3:
#         if img.shape[-1] == 4:
#             img = img[:, :, :3]
#         img = rgb2gray(img)
    
#     # Portiamo a 8-bit (0-255)
#     if img.dtype != np.uint8:
#         img = img_as_ubyte(img)
#     return img

def get_glcm(image, distances=[1], angles=[0, np.pi/4, np.pi/2, 3*np.pi/4]):
    """
    Pre-processa l'immagine e calcola la matrice GLCM.
    """
    # 1. Gestione immagine (RGBA -> RGB -> Gray -> 8-bit)
    img = np.asanyarray(image)
    if img.ndim == 3:
        if img.shape[-1] == 4: # Fix per errore (H, W, 4)
            img = img[:, :, :3]
        img = rgb2gray(img)
    
    if img.dtype != np.uint8:
        img = img_as_ubyte(img)
    
    # 2. Calcolo GLCM
    # Usiamo symmetric=True e normed=True come standard per feature radiomiche
    glcm = graycomatrix(img, 
                        distances=distances, 
                        angles=angles, 
                        levels=256, 
                        symmetric=True, 
                        normed=True)
    return glcm

def compute_glcm_correlation(glcm):
    """Calcola la correlazione media tra tutte le direzioni/distanze"""
    correlation = graycoprops(glcm, 'correlation')
    return np.mean(correlation)

def compute_glcm_homogeneity(glcm):
    """Calcola l'omogeneità media tra tutte le direzioni/distanze"""
    homogeneity = graycoprops(glcm, 'homogeneity')
    return np.mean(homogeneity)


if __name__ == "__main__":

    path_file = '../../img.jpg'
    img = plt.imread(path_file)

    selector = RoiSelector(path_file)

    img = mpimg.imread(selector.confirmed_path)

    print("La Standard Deviation è: ", standard_deviation(img))

    print("La media è: ", mean(img))

    print("L'eccentricità è: ", eccentricity(img))

    show_roi_and_histogram(img)

    sre = GLRLM_short_run_emphasis(img)
    print("Short Run Emphasis:", sre)

    print("NGTDM Coarsness: ", compute_ngtdm_coarseness(img))
    print("NGTDM Business: ", compute_ngtdm_busyness(img))
    print("NGTDM Contrast: ", compute_ngtdm_contrast(img))

    matrice_glcm = get_glcm(img)

    print("GLCM Correlation: ", compute_glcm_correlation(matrice_glcm))
    print("GLCM homogeneity: ", compute_glcm_homogeneity(matrice_glcm))

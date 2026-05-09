import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.path as mpath
import numpy as np
import os
import uuid
from skimage.measure import label, regionprops
from skimage.filters import threshold_otsu

class RoiSelector:
    def __init__(self, image_path):
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

        plt.title("Click SX: punto | Click DX: chiudi | ESC: esci")
        plt.show()

    def on_click(self, event):
        if not self.roi_done:
            # 1. Ignora se il click è fuori dagli assi
            if event.inaxes != self.ax: 
                return
            
            # 2. Ignora se lo strumento Zoom o Pan è attivo
            # Se mode è diverso da una stringa vuota, l'utente sta navigando
            if self.fig.canvas.toolbar.mode != "":
                return

            # Click sinistro: aggiungi punto
            if event.button == 1:
                self.punti_x.append(event.xdata)
                self.punti_y.append(event.ydata)
                self.linea_def.set_data(self.punti_x, self.punti_y)
                self.fig.canvas.draw()
                
            # Click destro: chiudi poligono e termina
            elif event.button == 3 and len(self.punti_x) > 2:
                self.punti_x.append(self.punti_x[0])
                self.punti_y.append(self.punti_y[0])
                self.linea_def.set_data(self.punti_x, self.punti_y)
                self.linea_temp.set_data([], []) # Rimuovi l'elastico
                self.fig.canvas.draw()
                self.roi_done = True
                print("ROI completata!")


    def on_move(self, event):
        if not self.roi_done:
            if event.inaxes != self.ax or len(self.punti_x) == 0:
                return
            
            # Aggiorna la linea elastica dall'ultimo punto alla posizione del mouse
            self.linea_temp.set_data([self.punti_x[-1], event.xdata], 
                                    [self.punti_y[-1], event.ydata])
            self.fig.canvas.draw()


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


if __name__ == "__main__":

    path_file = '../../img.jpg'

    # Esempio d'uso
    selector = RoiSelector(path_file)
    print(f"Punti selezionati: {list(zip(selector.punti_x, selector.punti_y))}")
    
    img = plt.imread(path_file)

    cut_image(list(zip(selector.punti_x, selector.punti_y)), img)

    # Caricamento immagine con matplotlib
    image_path = "cut_.png"
    img = mpimg.imread(image_path)

    print("La Standard Deviation è: ", standard_deviation(img))

    print("La media è: ", mean(img))

    print("L'eccentricità è: ", eccentricity(img))

    show_roi_and_histogram(img)

    sre = GLRLM_short_run_emphasis(img)
    print("Short Run Emphasis:", sre)

import matplotlib
matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.path as mpath

import numpy as np
import SimpleITK as sitk

from radiomics import featureextractor
from skimage.measure import label, regionprops
from skimage.filters import threshold_otsu
from skimage.color import rgb2gray
from skimage import img_as_ubyte


# ==========================================================
# ROI SELECTION
# ==========================================================

class RoiSelector:

    def __init__(self, image_path):

        self.image_path = image_path
        self.img = mpimg.imread(image_path)

        self.fig, self.ax = plt.subplots()
        self.ax.imshow(self.img)

        self.punti_x = []
        self.punti_y = []

        self.linea_def, = self.ax.plot(
            [],
            [],
            'ro-',
            markersize=4,
            linewidth=1.5
        )

        self.linea_temp, = self.ax.plot(
            [],
            [],
            'r--',
            alpha=0.5
        )

        self.roi_done = False

        self.fig.canvas.mpl_connect(
            'button_press_event',
            self.on_click
        )

        self.fig.canvas.mpl_connect(
            'motion_notify_event',
            self.on_move
        )

        plt.title(
            "Click SX = aggiungi punto | "
            "Click DX = chiudi ROI"
        )

        plt.show()

    # ======================================================
    # CLICK EVENTS
    # ======================================================

    def on_click(self, event):

        if self.roi_done:
            return

        if event.inaxes != self.ax:
            return

        # CLICK SINISTRO
        if event.button == 1:

            self.punti_x.append(event.xdata)
            self.punti_y.append(event.ydata)

            self.linea_def.set_data(
                self.punti_x,
                self.punti_y
            )

            self.fig.canvas.draw()

        # CLICK DESTRO → chiudi ROI
        elif event.button == 3 and len(self.punti_x) > 2:

            self.punti_x.append(self.punti_x[0])
            self.punti_y.append(self.punti_y[0])

            self.linea_def.set_data(
                self.punti_x,
                self.punti_y
            )

            self.linea_temp.set_data([], [])

            self.fig.canvas.draw()

            self.roi_done = True

            print("ROI completata")

    # ======================================================
    # MOUSE MOVE
    # ======================================================

    def on_move(self, event):

        if self.roi_done:
            return

        if event.inaxes != self.ax:
            return

        if len(self.punti_x) == 0:
            return

        self.linea_temp.set_data(
            [self.punti_x[-1], event.xdata],
            [self.punti_y[-1], event.ydata]
        )

        self.fig.canvas.draw()


# ==========================================================
# CREATE MASK
# ==========================================================

def create_mask(points, image_shape):

    h, w = image_shape[:2]

    x, y = np.meshgrid(
        np.arange(w),
        np.arange(h)
    )

    coords = np.vstack((
        x.flatten(),
        y.flatten()
    )).T

    path = mpath.Path(points)

    mask = path.contains_points(coords)

    mask = mask.reshape(h, w)

    return mask.astype(np.uint8)


# ==========================================================
# SAVE IMAGE + MASK
# ==========================================================

def save_for_radiomics(image, mask):

    # RGB → grayscale
    if image.ndim == 3:

        image = image[:, :, :3]

        image = np.mean(
            image,
            axis=2
        )

    # Normalizzazione uint8
    if image.max() <= 1.0:
        image = image * 255

    image = image.astype(np.uint8)

    sitk_img = sitk.GetImageFromArray(image)

    sitk_mask = sitk.GetImageFromArray(mask)

    image_path = "radiomics_image.nrrd"
    mask_path = "radiomics_mask.nrrd"

    sitk.WriteImage(sitk_img, image_path)

    sitk.WriteImage(sitk_mask, mask_path)

    return image_path, mask_path


# ==========================================================
# CROP ROI FROM POINTS
# ==========================================================

def crop_roi_from_points(points, image):
    """
    Ritaglia la ROI dall'immagine originale dato un insieme di punti
    che definiscono il poligono della ROI.

    Restituisce:
        - roi_gray  : ndarray 2D float64, solo pixel interni alla ROI
                      (pixel esterni = 0), scala [0, 255]
        - mask_2d   : ndarray 2D bool, True dove il pixel è nella ROI
        - roi_rgba  : ndarray (H, W, 4) float32 con alpha=0 fuori dalla ROI
                      (comodo per visualizzazione)
    """
    image = np.asarray(image)
    h, w = image.shape[:2]

    # ----------------------------------------------------------
    # 1. Crea la maschera booleana dal poligono
    # ----------------------------------------------------------
    x_grid, y_grid = np.meshgrid(np.arange(w), np.arange(h))
    coords = np.column_stack((x_grid.flatten(), y_grid.flatten()))
    path = mpath.Path(points)
    mask_2d = path.contains_points(coords).reshape(h, w)  # bool

    # ----------------------------------------------------------
    # 2. Converti in grayscale [0-255] float64
    # ----------------------------------------------------------
    if image.ndim == 3:
        # Gestisci sia RGB che RGBA
        rgb = image[:, :, :3].astype(np.float32)
        if rgb.max() <= 1.0:
            rgb = rgb * 255.0
        gray = rgb.mean(axis=2)          # media dei canali
    else:
        gray = image.astype(np.float64)
        if gray.max() <= 1.0:
            gray = gray * 255.0

    # ----------------------------------------------------------
    # 3. Applica la maschera: pixel fuori dalla ROI → 0
    # ----------------------------------------------------------
    roi_gray = np.where(mask_2d, gray, 0.0)

    # ----------------------------------------------------------
    # 4. Crop sul bounding-box del poligono
    # ----------------------------------------------------------
    pts_array = np.array(points)
    x_min = max(0, int(pts_array[:, 0].min()))
    x_max = min(w, int(pts_array[:, 0].max()) + 1)
    y_min = max(0, int(pts_array[:, 1].min()))
    y_max = min(h, int(pts_array[:, 1].max()) + 1)

    roi_gray   = roi_gray[y_min:y_max, x_min:x_max]
    mask_crop  = mask_2d[y_min:y_max, x_min:x_max]

    # ----------------------------------------------------------
    # 5. Versione RGBA per visualizzazione (opzionale)
    # ----------------------------------------------------------
    roi_norm = roi_gray / 255.0
    roi_rgba = np.zeros((*roi_gray.shape, 4), dtype=np.float32)
    roi_rgba[..., 0] = roi_norm
    roi_rgba[..., 1] = roi_norm
    roi_rgba[..., 2] = roi_norm
    roi_rgba[..., 3] = mask_crop.astype(np.float32)   # alpha

    return roi_gray, mask_crop, roi_rgba


# ==========================================================
# ECCENTRICITY
# ==========================================================

def compute_eccentricity(points, image):
    """
    Calcola l'eccentricità della regione principale della ROI.

    L'eccentricità è definita come il rapporto tra la distanza focale
    e l'asse maggiore dell'ellisse equivalente alla regione:
        - 0  → cerchio perfetto
        - 1  → segmento (forma degenere)

    Parameters
    ----------
    points : list of (x, y)
        Vertici del poligono ROI (coordinate pixel).
    image : ndarray
        Immagine originale (RGB, RGBA o grayscale).

    Returns
    -------
    ecc : float
        Valore di eccentricità in [0, 1).
    """
    roi_gray, mask_crop, _ = crop_roi_from_points(points, image)

    # Soglia di Otsu sulla ROI (solo pixel interni)
    roi_values = roi_gray[mask_crop]
    if roi_values.size == 0:
        return 0.0

    try:
        thresh = threshold_otsu(roi_values)
    except Exception:
        thresh = roi_values.mean()

    binary = (roi_gray > thresh) & mask_crop

    labeled  = label(binary)
    regions  = regionprops(labeled)

    if not regions:
        return 0.0

    largest = max(regions, key=lambda r: r.area)
    return float(largest.eccentricity)


# ==========================================================
# HISTOGRAM
# ==========================================================

def compute_histogram(points, image, bins=256, show=False):
    """
    Calcola l'istogramma dei livelli di grigio dei pixel interni alla ROI.

    Parameters
    ----------
    points : list of (x, y)
        Vertici del poligono ROI.
    image : ndarray
        Immagine originale (RGB, RGBA o grayscale).
    bins : int
        Numero di bin dell'istogramma (default 256).
    show : bool
        Se True, mostra a schermo ROI + istogramma.

    Returns
    -------
    hist   : ndarray (bins,)   conteggio per ogni bin
    edges  : ndarray (bins+1,) bordi dei bin in [0, 255]
    """
    roi_gray, mask_crop, roi_rgba = crop_roi_from_points(points, image)

    pixel_values = roi_gray[mask_crop]

    if pixel_values.size == 0:
        print("ROI vuota: nessun pixel interno al poligono.")
        return np.zeros(bins), np.linspace(0, 255, bins + 1)

    hist, edges = np.histogram(pixel_values, bins=bins, range=(0, 255))

    if show:
        fig, axes = plt.subplots(1, 2, figsize=(11, 4))

        axes[0].imshow(roi_rgba)
        axes[0].set_title("ROI selezionata")
        axes[0].axis("off")

        axes[1].bar(
            edges[:-1], hist,
            width=(edges[1] - edges[0]),
            color="steelblue",
            edgecolor="none"
        )
        axes[1].set_title(f"Istogramma ROI  (bins={bins})")
        axes[1].set_xlabel("Intensità [0-255]")
        axes[1].set_ylabel("Frequenza")

        plt.tight_layout()
        plt.show()

    return hist, edges


# ==========================================================
# HISTOGRAM AS FRONTEND DATA
# ==========================================================

def histogram_as_frontend_data(points, image, bins=256):
    """
    Calcola l'istogramma della ROI e lo restituisce come dizionario
    JSON-serializzabile, pronto per essere consumato da un frontend.

    Parameters
    ----------
    points : list of (x, y)
        Vertici del poligono ROI (coordinate pixel).
    image : ndarray
        Immagine originale (RGB, RGBA o grayscale).
    bins : int
        Numero di bin dell'istogramma (default 256).

    Returns
    -------
    dict con le chiavi:
        bins        : int   - numero di bin usati
        labels      : list[float] - centro di ogni bin (asse X, intensità)
        counts      : list[int]   - conteggio pixel per ogni bin (asse Y)
        total_pixels: int   - pixel totali nella ROI
        min_val     : float - intensità minima nella ROI
        max_val     : float - intensità massima nella ROI
        mean_val    : float - intensità media nella ROI
        std_val     : float - deviazione standard nella ROI

    Esempio di output
    -----------------
    {
        "bins": 256,
        "labels": [0.5, 1.5, ..., 254.5],
        "counts": [0, 3, 17, ...],
        "total_pixels": 4821,
        "min_val": 12.0,
        "max_val": 241.0,
        "mean_val": 127.4,
        "std_val": 38.2
    }
    """
    roi_gray, mask_crop, _ = crop_roi_from_points(points, image)

    pixel_values = roi_gray[mask_crop]

    if pixel_values.size == 0:
        return {
            "bins": bins,
            "labels": [],
            "counts": [],
            "total_pixels": 0,
            "min_val": None,
            "max_val": None,
            "mean_val": None,
            "std_val": None,
        }

    hist, edges = np.histogram(pixel_values, bins=bins, range=(0, 255))

    # Centro di ogni bin come label sull'asse X
    centers = ((edges[:-1] + edges[1:]) / 2).tolist()

    return {
        "bins":         bins,
        "labels":       [round(c, 4) for c in centers],
        "counts":       hist.tolist(),
        "total_pixels": int(pixel_values.size),
        "min_val":      round(float(pixel_values.min()), 4),
        "max_val":      round(float(pixel_values.max()), 4),
        "mean_val":     round(float(pixel_values.mean()), 4),
        "std_val":      round(float(pixel_values.std()), 4),
    }


# ==========================================================
# PYRADIOMICS EXTRACTION
# ==========================================================

def extract_radiomics_features(image_path, mask_path):

    extractor = featureextractor.RadiomicsFeatureExtractor()

    # ======================================================
    # SETTINGS
    # ======================================================

    extractor.settings['binWidth'] = 25

    # ======================================================
    # DISABILITA TUTTO
    # ======================================================

    extractor.disableAllFeatures()

    # ======================================================
    # ABILITA SOLO LE FEATURE DESIDERATE
    # ======================================================

    extractor.enableFeaturesByName(

        ngtdm=[
            'Busyness',
            'Contrast',
            'Coarseness'
        ],

        glszm=[
            'ZoneEntropy'
        ],

        glrlm=[
            'ShortRunEmphasis'
        ],

        glcm=[
            'Correlation',
            'Idm'
        ],

        firstorder=[
            'Mean',
            'StandardDeviation'
        ]
    )

    result = extractor.execute(
        image_path,
        mask_path
    )

    return result


# ==========================================================
# PRINT SELECTED FEATURES
# ==========================================================

def print_selected_features(features):

    wanted = [

        "original_ngtdm_Busyness",
        "original_ngtdm_Contrast",
        "original_ngtdm_Coarseness",

        "original_glszm_ZoneEntropy",

        "original_glrlm_ShortRunEmphasis",

        "original_glcm_Correlation",
        "original_glcm_Idm",

        "original_firstorder_Mean",
        "original_firstorder_StandardDeviation"
    ]

    print("\n========== SELECTED FEATURES ==========\n")

    for key in wanted:

        if key in features:

            print(f"{key}: {features[key]}")


def filter_features(features, desired_features):
    result = {}
    for i in desired_features:
        result[i] = features[i]
    return result


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    image_path = "../../img.jpg"

    image = mpimg.imread(image_path)

    # ======================================================
    # ROI SELECTION
    # ======================================================

    selector = RoiSelector(image_path)

    points = list(zip(
        selector.punti_x,
        selector.punti_y
    ))

    # ======================================================
    # CREATE MASK
    # ======================================================

    mask = create_mask(
        points,
        image.shape
    )

    # ======================================================
    # SAVE IMAGE + MASK
    # ======================================================

    img_path, mask_path = save_for_radiomics(
        image,
        mask
    )

    # ======================================================
    # FEATURE EXTRACTION (pyradiomics)
    # ======================================================

    features = extract_radiomics_features(
        img_path,
        mask_path
    )

    res = filter_features(features, desired_features=[
        "original_ngtdm_Busyness",
        "original_ngtdm_Contrast",
        "original_ngtdm_Coarseness",
        "original_glszm_ZoneEntropy",
        "original_glrlm_ShortRunEmphasis",
        "original_glcm_Correlation",
        "original_glcm_Idm",
        "original_firstorder_Mean",
        "original_firstorder_StandardDeviation"
    ])

    print("\n========== PYRADIOMICS FEATURES ==========\n")
    for k, v in res.items():
        print(f"{k}: {v}")

    # ======================================================
    # ECCENTRICITY
    # ======================================================

    ecc = compute_eccentricity(points, image)
    print(f"eccentricity: {ecc:.6f}")

    # ======================================================
    # HISTOGRAM
    # ======================================================

    import json

    hist_data = histogram_as_frontend_data(points, image, bins=256)
    json_payload = json.dumps(hist_data)   # pronto per HTTP response

    print(json_payload)

    hist, edges = compute_histogram(points, image, bins=256, show=True)
    print(f"\nHistogram computed: {hist.sum():.0f} pixel nella ROI")
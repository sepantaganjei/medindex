from __future__ import annotations

from io import BytesIO
from typing import Iterable

import numpy as np
import SimpleITK as sitk
from PIL import Image, UnidentifiedImageError
from matplotlib.path import Path
from radiomics import featureextractor

DESIRED_FEATURES = [
    "original_ngtdm_Busyness",
    "original_ngtdm_Contrast",
    "original_ngtdm_Coarseness",
    "original_glszm_ZoneEntropy",
    "original_glrlm_ShortRunEmphasis",
    "original_glcm_Correlation",
    "original_glcm_Idm",
    "original_firstorder_Mean",
    "original_firstorder_StandardDeviation",
]


def decode_image_bytes(image_bytes: bytes) -> np.ndarray:
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            grayscale = image.convert("L")
            return np.asarray(grayscale, dtype=np.float32)
    except UnidentifiedImageError as exc:
        raise ValueError("Unsupported image format") from exc


def create_mask(points: Iterable[tuple[float, float]], image_shape: tuple[int, int]) -> np.ndarray:
    height, width = image_shape

    x, y = np.meshgrid(np.arange(width), np.arange(height))
    coords = np.vstack((x.flatten(), y.flatten())).T

    path = Path(list(points))
    mask = path.contains_points(coords).reshape(height, width)

    return mask.astype(np.uint8)


def extract_pyradiomics_features(image: np.ndarray, mask: np.ndarray) -> dict[str, float | None]:
    if image.ndim != 2:
        raise ValueError("Radiomics extraction expects a 2D grayscale image.")
    if image.shape != mask.shape:
        raise ValueError("Mask size does not match image size.")
    if np.count_nonzero(mask) == 0:
        raise ValueError("ROI does not cover any pixels.")

    sitk_img = sitk.GetImageFromArray(image.astype(np.float32))
    sitk_mask = sitk.GetImageFromArray(mask.astype(np.uint8))

    extractor = featureextractor.RadiomicsFeatureExtractor()
    extractor.settings["binWidth"] = 25
    extractor.disableAllFeatures()
    extractor.enableFeaturesByName(
        ngtdm=["Busyness", "Contrast", "Coarseness"],
        glszm=["ZoneEntropy"],
        glrlm=["ShortRunEmphasis"],
        glcm=["Correlation", "Idm"],
        firstorder=["Mean", "StandardDeviation"],
    )

    result = extractor.execute(sitk_img, sitk_mask)

    features: dict[str, float | None] = {}
    for key in DESIRED_FEATURES:
        value = result.get(key)
        features[key] = float(value) if value is not None else None
    return features

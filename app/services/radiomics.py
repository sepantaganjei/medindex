from __future__ import annotations

from io import BytesIO
from typing import Iterable

import numpy as np
import SimpleITK as sitk
from PIL import Image, UnidentifiedImageError
from matplotlib.path import Path
from radiomics import featureextractor

SUPPORTED_FEATURES = {
    "mean": {
        "key": "original_firstorder_Mean",
        "class": "firstorder",
        "name": "Mean",
    },
    "std": {
        "key": "original_firstorder_StandardDeviation",
        "class": "firstorder",
        "name": "StandardDeviation",
    },
    "glcm_homogeneity": {
        "key": "original_glcm_Idm",
        "class": "glcm",
        "name": "Idm",
    },
    "glcm_correlation": {
        "key": "original_glcm_Correlation",
        "class": "glcm",
        "name": "Correlation",
    },
    "glrlm_sre": {
        "key": "original_glrlm_ShortRunEmphasis",
        "class": "glrlm",
        "name": "ShortRunEmphasis",
    },
    "glszm_ze": {
        "key": "original_glszm_ZoneEntropy",
        "class": "glszm",
        "name": "ZoneEntropy",
    },
    "ngtdm_coarseness": {
        "key": "original_ngtdm_Coarseness",
        "class": "ngtdm",
        "name": "Coarseness",
    },
    "ngtdm_contrast": {
        "key": "original_ngtdm_Contrast",
        "class": "ngtdm",
        "name": "Contrast",
    },
    "ngtdm_busyness": {
        "key": "original_ngtdm_Busyness",
        "class": "ngtdm",
        "name": "Busyness",
    },
}

SUPPORTED_FEATURE_KEYS = [feature["key"] for feature in SUPPORTED_FEATURES.values()]
FEATURE_ALIASES = {
    alias: feature["key"]
    for alias, feature in SUPPORTED_FEATURES.items()
}
FEATURE_ALIASES.update({key: key for key in SUPPORTED_FEATURE_KEYS})


def normalize_feature_keys(selected_features: Iterable[str] | None = None) -> list[str]:
    """Resolve feature aliases to canonical keys, returning all supported keys if none are specified."""
    if selected_features is None:
        return list(SUPPORTED_FEATURE_KEYS)

    feature_keys: list[str] = []
    invalid_features: list[str] = []
    for feature in selected_features:
        feature_key = FEATURE_ALIASES.get(feature)
        if not feature_key:
            invalid_features.append(feature)
            continue
        if feature_key not in feature_keys:
            feature_keys.append(feature_key)

    if invalid_features:
        supported_features = ", ".join(SUPPORTED_FEATURES)
        raise ValueError(
            f"Unsupported feature(s): {', '.join(invalid_features)}. "
            f"Supported features: {supported_features}"
        )
    if not feature_keys:
        raise ValueError("Select at least one feature.")

    return feature_keys


def decode_image_bytes(image_bytes: bytes) -> np.ndarray:
    """Decode raw image bytes into a 2D float32 grayscale NumPy array."""
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            grayscale = image.convert("L")
            return np.asarray(grayscale, dtype=np.float32)
    except UnidentifiedImageError as exc:
        raise ValueError("Unsupported image format") from exc


def create_mask(points: Iterable[tuple[float, float]], image_shape: tuple[int, int]) -> np.ndarray:
    """Build a binary uint8 mask where pixels inside the polygon defined by points are set to 1."""
    height, width = image_shape

    x, y = np.meshgrid(np.arange(width), np.arange(height))
    coords = np.vstack((x.flatten(), y.flatten())).T

    path = Path(list(points))
    mask = path.contains_points(coords).reshape(height, width)

    return mask.astype(np.uint8)


def extract_pyradiomics_features(
    image: np.ndarray,
    mask: np.ndarray,
    selected_features: Iterable[str] | None = None,
) -> dict[str, float | None]:
    """Run PyRadiomics on the masked region of the image and return the requested feature values."""
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
    feature_keys = normalize_feature_keys(selected_features)
    enabled_features: dict[str, list[str]] = {}
    for feature in SUPPORTED_FEATURES.values():
        if feature["key"] in feature_keys:
            enabled_features.setdefault(feature["class"], []).append(feature["name"])

    extractor.enableFeaturesByName(**enabled_features)

    result = extractor.execute(sitk_img, sitk_mask)

    features: dict[str, float | None] = {}
    for key in feature_keys:
        value = result.get(key)
        features[key] = float(value) if value is not None else None
    return features

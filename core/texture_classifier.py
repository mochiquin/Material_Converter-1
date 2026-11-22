"""Pure Python texture filename classification and color-space rules."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

TEXTURE_CATEGORY_PATTERNS: dict[str, tuple[str, ...]] = {
    "Diffuse": ("Albedo", "Diffuse", "BaseColor", "diff", r"(?<![a-z])col(?![a-z])"),
    "Reflection": ("Reflection", "Specular", "reflect", "refl", "spec"),
    "Roughness": ("Glossiness", "Roughness", "RGH", "gloss", "rough"),
    "Metal": ("Gold", "Chrome", "Metal", "alum", "brass", "steel", "metallic"),
    "Normal": ("Normal", "nrm", "nor", "NRM"),
    "Bump": ("Bump", "bump"),
    "Glass": ("glass", "water", "milk", "juice"),
    "Transmission": ("Transmission", "Translucency", "trans", "SubsurfaceColor"),
    "Opacity": ("Opacity", "alpha"),
    "Displacement": ("Displacement", "disp", "Height"),
    "Fabrics": ("wool", "fabric"),
    "IOR": ("IOR", "ior"),
    "AO": ("AO", "ambient"),
    "Cavity": ("Cavity", "CAVITY"),
}

SRGB_CATEGORIES: frozenset[str] = frozenset({"Diffuse", "Glass", "Fabrics", "Transmission"})

LABEL_REMAP: dict[str, str] = {
    "ALPHA": "Opacity",
    "COLOR": "Diffuse",
    "ROUGHNESS": "Roughness",
    "TRANSLUCENCY": "Transmission",
    "NORMAL": "Normal",
    "METALNESS": "Metallic",
    "DISPLACEMENT": "Displacement",
}

LINEAR_GAMMA_KEYWORDS: tuple[str, ...] = (
    "normal",
    "gloss",
    "reflec",
    "rough",
    "opacity",
    "height",
    "nrm",
    "bump",
    "displacement",
)

AUTO_CONNECT_KEYWORD_MAPPING: dict[str, tuple[str, int]] = {
    "diffuse": ("Diffuse", 5),
    "albedo": ("Diffuse", 5),
    "basecolor": ("Diffuse", 5),
    "base": ("Diffuse", 5),
    "color": ("Diffuse", 5),
    "normal": ("Normal", 24),
    "nrm": ("Normal", 24),
    "norm": ("Normal", 24),
    "rough": ("Roughness", 13),
    "roughness": ("Roughness", 13),
    "metal": ("Metallic", 7),
    "metallic": ("Metallic", 7),
    "metalness": ("Metallic", 7),
    "bump": ("Bump", 25),
    "height": ("Bump", 25),
    "opacity": ("Opacity", 43),
    "alpha": ("Opacity", 43),
    "spec": ("Specular", 10),
    "specular": ("Specular", 10),
}


@dataclass(frozen=True, slots=True)
class TextureClassification:
    """Result of classifying an image filename for PBR material wiring."""

    category: str | None
    is_srgb: bool
    invert_gloss: bool


def classify_texture_filename(filename: str) -> TextureClassification:
    """Classify a texture filename or path using regex keyword rules.

    Empty or whitespace-only names return ``category=None`` and ``is_srgb=True``.
    """
    cleaned = filename.strip()
    if not cleaned:
        return TextureClassification(category=None, is_srgb=True, invert_gloss=False)

    stem = Path(cleaned).name
    invert_gloss = "gloss" in stem.lower()

    for category, patterns in TEXTURE_CATEGORY_PATTERNS.items():
        if any(re.search(pattern, stem, re.IGNORECASE) for pattern in patterns):
            return TextureClassification(
                category=category,
                is_srgb=category in SRGB_CATEGORIES,
                invert_gloss=invert_gloss,
            )

    return TextureClassification(category=None, is_srgb=True, invert_gloss=invert_gloss)


def detect_auto_connect_target(filename: str) -> tuple[str, int] | None:
    """Detect target Octane Universal Material input ``(name, index)`` from filename."""
    cleaned = filename.strip()
    if not cleaned:
        return None

    name_lower = Path(cleaned).name.lower()
    for keyword, target in AUTO_CONNECT_KEYWORD_MAPPING.items():
        if keyword in name_lower:
            return target
    return None


def infer_octane_gamma(
    colorspace_name: str,
    filename: str = "",
    *,
    check_filename_keywords: bool = False,
) -> float:
    """Infer Octane image gamma (1.0 for linear/non-color data, 2.2 for sRGB)."""
    if not colorspace_name or "srgb" not in colorspace_name.lower():
        return 1.0
    if check_filename_keywords and filename:
        name_lower = Path(filename).name.lower()
        if any(keyword in name_lower for keyword in LINEAR_GAMMA_KEYWORDS):
            return 1.0
    return 2.2


def remap_label(label: str) -> str:
    """Remap legacy uppercase texture labels to canonical PBR labels."""
    return LABEL_REMAP.get(label, label)

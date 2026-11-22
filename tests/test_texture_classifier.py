"""Unit tests for texture filename classification and gamma inference."""

from __future__ import annotations

import pytest

from core.texture_classifier import (
    classify_texture_filename,
    detect_auto_connect_target,
    infer_octane_gamma,
    remap_label,
)


@pytest.mark.parametrize(
    ("filename", "expected_category", "expected_srgb", "expected_invert_gloss"),
    [
        ("Wood_Oak_Albedo_4K.png", "Diffuse", True, False),
        ("/assets/textures/Wall_NRM.exr", "Normal", False, False),
        ("C:\\textures\\Metal_RGH.tif", "Roughness", False, False),
        ("Floor_Glossiness_2k.png", "Roughness", False, True),
        ("Fence_Alpha_Mask.png", "Opacity", False, False),
        ("Brick_Height_16bit.exr", "Displacement", False, False),
        ("Steel_Metallic.png", "Metal", False, False),
        ("Leaf_SubsurfaceColor.jpg", "Transmission", True, False),
    ],
)
def test_classify_common_and_cross_platform_filenames(
    filename: str,
    expected_category: str,
    expected_srgb: bool,
    expected_invert_gloss: bool,
) -> None:
    result = classify_texture_filename(filename)
    assert result.category == expected_category
    assert result.is_srgb is expected_srgb
    assert result.invert_gloss is expected_invert_gloss


def test_classify_empty_and_unknown_filenames() -> None:
    empty_res = classify_texture_filename("   ")
    assert empty_res.category is None
    assert empty_res.is_srgb is True
    assert empty_res.invert_gloss is False

    unknown_res = classify_texture_filename("random_scan_0042.png")
    assert unknown_res.category is None
    assert unknown_res.is_srgb is True


def test_classify_priority_when_multiple_keywords_present() -> None:
    # Diffuse patterns are checked before Roughness / AO
    result = classify_texture_filename("Concrete_BaseColor_Roughness_AO.png")
    assert result.category == "Diffuse"
    assert result.is_srgb is True


def test_infer_octane_gamma_edge_cases() -> None:
    assert infer_octane_gamma("Non-Color", "anything.png") == 1.0
    assert infer_octane_gamma("", "diffuse.png") == 1.0
    assert infer_octane_gamma("sRGB", "Wood_Albedo.png") == 2.2
    # Filename override for auto-convert when colorspace was left as sRGB
    assert infer_octane_gamma("sRGB", "Wall_Normal.png", check_filename_keywords=True) == 1.0
    assert infer_octane_gamma("sRGB", "Wall_Normal.png", check_filename_keywords=False) == 2.2


def test_detect_auto_connect_target_and_remap_label() -> None:
    assert detect_auto_connect_target("plaster_basecolor_2k.png") == ("Diffuse", 5)
    assert detect_auto_connect_target("plaster_nrm.png") == ("Normal", 24)
    assert detect_auto_connect_target("") is None
    assert detect_auto_connect_target("unrecognized_map.png") is None

    assert remap_label("ALPHA") == "Opacity"
    assert remap_label("METALNESS") == "Metallic"
    assert remap_label("CustomLabel") == "CustomLabel"

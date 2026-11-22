"""Unit tests for pure Python preferences codec."""

from __future__ import annotations

from pathlib import Path

from core.preferences_codec import (
    normalize_preferences_path,
    parse_color_repr,
    prepare_preferences_updates,
)


def test_parse_color_repr_valid_and_invalid() -> None:
    assert parse_color_repr("<Color (r=0.8000, g=0.5, b=0.125)>") == (0.8, 0.5, 0.125)
    assert parse_color_repr("<Color (r=1.0, g=0.0)>") is None
    assert parse_color_repr("0.8, 0.8, 0.8") is None


def test_normalize_preferences_path_uses_pathlib() -> None:
    path = normalize_preferences_path("~/mc_settings.json")
    assert isinstance(path, Path)
    assert path.name == "mc_settings.json"


def test_prepare_preferences_updates_tracks_malformed_colors() -> None:
    data = {
        "auto_convert_images": True,
        "unknown_field": "ignored",
        "octane_preferences": {
            "octane_albedo_color_addon": "<Color (r=0.2, g=0.4, b=0.6)>",
            "broken_color": "<Color malformed>",
        },
    }
    updates, errors = prepare_preferences_updates(
        data,
        known_attrs={"auto_convert_images", "octane_preferences"},
    )
    assert errors == 1
    assert len(updates) == 2
    assert updates[0].key == "auto_convert_images"
    assert updates[0].value is True
    assert updates[1].sub_key == "octane_albedo_color_addon"
    assert updates[1].is_color is True
    assert updates[1].value == (0.2, 0.4, 0.6)

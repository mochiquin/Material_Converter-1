"""Pure Python preferences serialization/deserialization helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_COLOR_RE = re.compile(
    r"r=([-+]?\d+(?:\.\d+)?),\s*g=([-+]?\d+(?:\.\d+)?),\s*b=([-+]?\d+(?:\.\d+)?)"
)


@dataclass(frozen=True, slots=True)
class PreferenceUpdate:
    """Validated preference update extracted from JSON configuration."""

    key: str
    sub_key: str | None
    value: Any
    is_color: bool = False


def parse_color_repr(value: str) -> tuple[float, float, float] | None:
    """Parse Blender ``<Color (r=..., g=..., b=...)>`` string into an RGB tuple."""
    if "<Color" not in value:
        return None
    match = _COLOR_RE.search(value)
    if not match:
        return None
    return (float(match.group(1)), float(match.group(2)), float(match.group(3)))


def normalize_preferences_path(filepath: str | Path) -> Path:
    """Normalize a preferences JSON path using ``pathlib.Path``."""
    return Path(filepath).expanduser()


def prepare_preferences_updates(
    data: dict[str, Any],
    known_attrs: set[str],
) -> tuple[list[PreferenceUpdate], int]:
    """Prepare preference updates from JSON dict, returning ``(updates, error_count)``."""
    updates: list[PreferenceUpdate] = []
    errors = 0

    for key, value in data.items():
        if key not in known_attrs:
            continue
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, str) and "<Color" in sub_value:
                    parsed = parse_color_repr(sub_value)
                    if parsed is None:
                        errors += 1
                    else:
                        updates.append(PreferenceUpdate(key=key, sub_key=sub_key, value=parsed, is_color=True))
                else:
                    updates.append(PreferenceUpdate(key=key, sub_key=sub_key, value=sub_value))
        elif isinstance(value, str) and "<Color" in value:
            parsed = parse_color_repr(value)
            if parsed is None:
                errors += 1
            else:
                updates.append(PreferenceUpdate(key=key, sub_key=None, value=parsed, is_color=True))
        else:
            updates.append(PreferenceUpdate(key=key, sub_key=None, value=value))

    return updates, errors

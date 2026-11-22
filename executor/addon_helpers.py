"""Blender addon preferences lookup and JSON import/export helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import bpy

from ..core.preferences_codec import normalize_preferences_path, prepare_preferences_updates


def get_addon_package_name() -> str:
    """Return the root Python package name of this addon."""
    if __package__:
        return __package__.split(".")[0]
    return Path(__file__).resolve().parent.parent.name


def get_addon_preferences(addon_name: str | None = None, context: Any = None) -> Any:
    """Resolve addon preferences without hardcoding the folder name."""
    ctx = context if context is not None else bpy.context
    addons = ctx.preferences.addons
    candidates: list[str] = []
    if addon_name:
        candidates.append(addon_name)
    pkg = get_addon_package_name()
    if pkg not in candidates:
        candidates.append(pkg)
    if "Material_Converter" not in candidates:
        candidates.append("Material_Converter")

    for key in candidates:
        addon = addons.get(key)
        if addon and addon.preferences:
            return addon.preferences

    for key in addons.keys():
        addon = addons.get(key)
        if addon and addon.preferences and hasattr(addon.preferences, "octane_preferences"):
            return addon.preferences
    return None


def serialize_preferences(prefs: Any) -> dict[str, Any]:
    """Convert addon preferences to a JSON-serializable dictionary."""
    result: dict[str, Any] = {}
    for attr_name in dir(prefs):
        if attr_name.startswith("__") or attr_name.startswith("bl_"):
            continue
        try:
            attr_value = getattr(prefs, attr_name)
            if callable(attr_value):
                continue
            if isinstance(attr_value, (bool, int, float, str)) or attr_value is None:
                result[attr_name] = attr_value
            elif hasattr(attr_value, "to_list"):
                result[attr_name] = attr_value.to_list()
            elif isinstance(attr_value, set):
                result[attr_name] = list(attr_value)
            elif isinstance(attr_value, bpy.types.bpy_struct):
                nested_dict: dict[str, Any] = {}
                for sub_attr_name in dir(attr_value):
                    if sub_attr_name.startswith("__") or sub_attr_name.startswith("bl_"):
                        continue
                    try:
                        sub_attr_value = getattr(attr_value, sub_attr_name)
                        if callable(sub_attr_value):
                            continue
                        if isinstance(sub_attr_value, (bool, int, float, str)) or sub_attr_value is None:
                            nested_dict[sub_attr_name] = sub_attr_value
                        elif hasattr(sub_attr_value, "to_list"):
                            nested_dict[sub_attr_name] = sub_attr_value.to_list()
                        else:
                            nested_dict[sub_attr_name] = str(sub_attr_value)
                    except Exception:
                        continue
                result[attr_name] = nested_dict
            else:
                result[attr_name] = str(attr_value)
        except Exception:
            continue
    return result


def save_addon_preferences_to_json(
    filepath: str | Path,
    addon_name: str | None = None,
) -> tuple[set[str], str]:
    """Save addon preferences to a JSON file using ``pathlib.Path``."""
    resolved_name = addon_name or get_addon_package_name()
    prefs = get_addon_preferences(resolved_name)
    if not prefs:
        return {"WARNING"}, f"Preferences not found for addon: {resolved_name}"

    data = serialize_preferences(prefs)
    target_path = normalize_preferences_path(filepath)
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(json.dumps(data, indent=4), encoding="utf-8")
        return {"INFO"}, f"Saved preferences for '{resolved_name}' to: {target_path}"
    except Exception as exc:
        return {"ERROR"}, f"Failed saving preferences: {exc}"


def load_addon_preferences_from_json(
    filepath: str | Path,
    addon_name: str | None = None,
) -> tuple[set[str], str]:
    """Load addon preferences from a JSON file via ``core.preferences_codec``."""
    resolved_name = addon_name or get_addon_package_name()
    prefs = get_addon_preferences(resolved_name)
    if not prefs:
        return {"WARNING"}, f"Preferences not found for addon: {resolved_name}"

    source_path = normalize_preferences_path(filepath)
    try:
        data = json.loads(source_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ERROR"}, f"Failed reading preferences: {exc}"

    if not isinstance(data, dict):
        return {"ERROR"}, "Preferences JSON root must be an object."

    known_attrs = {name for name in dir(prefs) if hasattr(prefs, name)}
    updates, error_count = prepare_preferences_updates(data, known_attrs)
    applied_count = 0

    for upd in updates:
        try:
            if upd.sub_key is None:
                if upd.is_color:
                    current_value = getattr(prefs, upd.key)
                    if len(current_value) >= 3:
                        current_value[0], current_value[1], current_value[2] = upd.value
                        applied_count += 1
                    else:
                        error_count += 1
                else:
                    setattr(prefs, upd.key, upd.value)
                    applied_count += 1
            else:
                container = getattr(prefs, upd.key)
                if not isinstance(container, bpy.types.bpy_struct) or not hasattr(container, upd.sub_key):
                    error_count += 1
                    continue
                if upd.is_color:
                    sub_current = getattr(container, upd.sub_key)
                    if len(sub_current) >= 3:
                        sub_current[0], sub_current[1], sub_current[2] = upd.value
                        applied_count += 1
                    else:
                        error_count += 1
                else:
                    setattr(container, upd.sub_key, upd.value)
                    applied_count += 1
        except Exception:
            error_count += 1

    return (
        {"INFO"},
        f"Loaded {applied_count} preferences for '{resolved_name}' from {source_path} ({error_count} errors).",
    )

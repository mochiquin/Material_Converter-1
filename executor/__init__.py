"""Host execution layer bridging Blender API and pure core/ planners."""

from .addon_helpers import (
    get_addon_package_name,
    get_addon_preferences,
    load_addon_preferences_from_json,
    save_addon_preferences_to_json,
    serialize_preferences,
)
from .graph_serializer import serialize_material_graph
from .octane_executor import (
    apply_octane_alpha_clip_bypass,
    apply_octane_mapping_nodes,
    apply_octane_math_nodes,
    apply_octane_separate_color,
    log_material_audit_warnings,
)

__all__ = [
    "apply_octane_alpha_clip_bypass",
    "apply_octane_mapping_nodes",
    "apply_octane_math_nodes",
    "apply_octane_separate_color",
    "get_addon_package_name",
    "get_addon_preferences",
    "load_addon_preferences_from_json",
    "log_material_audit_warnings",
    "save_addon_preferences_to_json",
    "serialize_material_graph",
    "serialize_preferences",
]

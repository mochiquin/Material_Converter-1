"""Entry point for incremental bulk conversion of scene materials to Octane."""

from __future__ import annotations

import bpy

from .convert_core import convert_material_to_octane, is_octane_converted

__all__ = ["convert_material_to_octane", "get_materials_to_convert"]


def get_materials_to_convert() -> list:
    """Return non-Octane materials eligible for bulk conversion."""
    if bpy.context.scene.render.engine != "octane":
        bpy.context.scene.view_settings.view_transform = "Raw"
        bpy.context.scene.view_settings.look = "None"
        bpy.context.scene.render.engine = "octane"

    for screen in bpy.context.workspace.screens:
        for area in screen.areas:
            if area.type == "NODE_EDITOR" and area.ui_type not in ("GeometryNodeTree", "CompositorNodeTree"):
                area.ui_type = "ShaderNodeTree"

    materials = []
    for mat in bpy.data.materials:
        if "Dot Stroke" in mat.name:
            continue
        if not mat or not hasattr(mat, "node_tree") or not mat.node_tree:
            continue
        if is_octane_converted(mat):
            continue
        materials.append(mat)
    return materials

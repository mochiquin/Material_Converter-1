"""Entry point for converting the active material to Octane."""

from __future__ import annotations

import bpy

from .convert_core import convert_material_to_octane


def convert_active(context=None) -> None:
    """Switch scene to Octane if needed and convert the active material."""
    ctx = context if context is not None else bpy.context
    if ctx.scene.render.engine != "octane":
        ctx.scene.view_settings.view_transform = "Raw"
        ctx.scene.view_settings.look = "None"
        ctx.scene.render.engine = "octane"

    for screen in ctx.workspace.screens:
        for area in screen.areas:
            if area.type == "NODE_EDITOR" and area.ui_type not in ("GeometryNodeTree", "CompositorNodeTree"):
                area.ui_type = "ShaderNodeTree"

    mat = ctx.object.active_material
    convert_material_to_octane(mat)

"""Entry point for converting selected objects' materials to Octane."""

from __future__ import annotations

import traceback

import bpy

from .convert_core import convert_material_to_octane, is_octane_converted


def convert_selected(context=None) -> None:
    """Convert non-Octane materials on selected/active objects to Octane."""
    ctx = context if context is not None else bpy.context
    if ctx.scene.render.engine != "octane":
        ctx.scene.view_settings.view_transform = "Raw"
        ctx.scene.view_settings.look = "None"
        ctx.scene.render.engine = "octane"

    for screen in ctx.workspace.screens:
        for area in screen.areas:
            if area.type == "NODE_EDITOR" and area.ui_type not in ("GeometryNodeTree", "CompositorNodeTree"):
                area.ui_type = "ShaderNodeTree"

    objects = list(ctx.selected_objects)
    active = ctx.active_object
    if active and active not in objects:
        objects.append(active)

    seen: set[str] = set()
    for obj in objects:
        for slot in obj.material_slots:
            mat = slot.material
            if not mat or mat.name in seen:
                continue
            seen.add(mat.name)
            if not hasattr(mat, "node_tree") or not mat.node_tree:
                continue
            if is_octane_converted(mat):
                continue

            try:
                convert_material_to_octane(mat)
            except Exception:
                print(f"[Material Converter] Failed to convert '{mat.name}':")
                traceback.print_exc()

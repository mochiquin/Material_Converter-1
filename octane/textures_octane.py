"""Import image textures for Octane materials."""

from __future__ import annotations

import bpy


def import_textures(context=None) -> None:
    """Entry point for ``material.import_textures`` operator."""
    ctx = context if context is not None else bpy.context
    if ctx.scene.render.engine != "octane":
        ctx.scene.view_settings.view_transform = "Raw"
        ctx.scene.view_settings.look = "None"
        ctx.scene.render.engine = "octane"

    for screen in ctx.workspace.screens:
        for area in screen.areas:
            if area.type == "NODE_EDITOR" and area.ui_type not in ("GeometryNodeTree", "CompositorNodeTree"):
                area.ui_type = "ShaderNodeTree"

    obj = getattr(ctx, "object", None) or getattr(ctx, "active_object", None)
    mat = obj.active_material if obj else None
    if not mat:
        raise RuntimeError("No active material found.")
    if not mat.use_nodes:
        mat.use_nodes = True
    nodetree = mat.node_tree
    if not nodetree:
        raise RuntimeError("Active material has no node tree.")

    texture = next((n for n in nodetree.nodes if n.bl_idname == "OctaneRGBImage"), None)
    if not nodetree.nodes:
        m = nodetree.nodes.new("ShaderNodeOutputMaterial")
        m.label = "Octane Output"

    if not texture:
        bpy.ops.shader.import_images_to_shadernodes("INVOKE_DEFAULT")

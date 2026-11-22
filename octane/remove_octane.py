"""Remove non-Octane shader nodes from scene materials."""

from __future__ import annotations

import bpy


def remove_nodes(context=None) -> None:
    """Entry point for ``material.remove_nodes_confirm`` operator."""
    for mat in bpy.data.materials:
        if "Dot Stroke" in mat.name or "Dots Stroke" in mat.name or not mat.node_tree:
            continue
        nodes = mat.node_tree.nodes
        for node in list(nodes):
            if node.bl_idname == "ShaderNodeOutputMaterial":
                if not node.inputs or node.target != "ALL":
                    nodes.remove(node)
                elif not any(inp.is_linked for inp in node.inputs):
                    nodes.remove(node)
            elif not node.bl_idname.startswith("Octane"):
                nodes.remove(node)

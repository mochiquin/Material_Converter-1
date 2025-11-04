import bpy

for mat in bpy.data.materials:
    if "Dots Stroke" not in mat.name and mat.node_tree:
        for node in mat.node_tree.nodes:
            if node.bl_idname.startswith("VRay"):
                pass
            else:
                mat.node_tree.nodes.remove(node)
            
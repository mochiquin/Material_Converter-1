import bpy

materials = bpy.data.materials

for mat in materials:
    if "Dots Stroke" not in mat.name and mat.node_tree:
        for node in mat.node_tree.nodes:
                           
            mat.node_tree.nodes.remove(node)
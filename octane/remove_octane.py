import bpy

for mat in bpy.data.materials:
    if "Dots Stroke" not in mat.name and mat.node_tree:
        for node in mat.node_tree.nodes:
            if node.bl_idname == 'ShaderNodeOutputMaterial':
                if not node.inputs: 
                    mat.node_tree.nodes.remove(node)
                elif node.target != "ALL":
                   mat.node_tree.nodes.remove(node) 
                else:
                    all_inputs_disconnected = True
                    for input in node.inputs:
                        if input.is_linked:
                            all_inputs_disconnected = False
                            break
                    if all_inputs_disconnected:
                        mat.node_tree.nodes.remove(node)
            elif not node.bl_idname.startswith("Octane"):
                mat.node_tree.nodes.remove(node)
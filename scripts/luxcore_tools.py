import bpy


preferences = bpy.context.preferences.addons["Material_Converter 1"].preferences
Render_Engine = bpy.context.scene.render.engine

mat = bpy.context.object.active_material


def process_luxcore_nodes(mat):
    Normal_names = ("Normal", "nrm", "nor", "NRM")
    for luxcore_node in mat.luxcore.node_tree.nodes:
        if luxcore_node.bl_idname == "LuxCoreNodeTexImagemap":
            if luxcore_node.image and any(nrm in luxcore_node.image.name for nrm in Normal_names):
                luxcore_node.is_normal_map = True
            if "nor" in luxcore_node.label.lower():
                luxcore_node.is_normal_map = True

            for output in luxcore_node.outputs:
                for link in output.links:
                    invert_node = link.to_node
                    if invert_node and invert_node.bl_idname == "LuxCoreNodeTexInvert":
                       
                        for invert_output in invert_node.outputs:
                            for invert_link in invert_output.links:
                                next_node = invert_link.to_node
                                target_input = invert_link.to_socket
                                
                                # Find the index of the target input socket
                                target_input_index = None
                                for i, input_socket in enumerate(next_node.inputs):
                                    if input_socket == target_input:
                                        target_input_index = i
                                        break
                                
                                if target_input_index is not None:
                                    print(f"Found target input index: {target_input_index}")
                                    print(f"Target socket: {next_node.inputs[target_input_index]}")
                                    
                                    # Create new color mix node
                                    mix_color_node = mat.luxcore.node_tree.nodes.new("LuxCoreNodeTexColorMix")
                                    mix_color_node.inputs[0].default_value = invert_node.inputs[1].default_value
                                    invert_node.inputs[1].default_value = 1
                                    # Position the node
                                    mix_color_node.location = (
                                        (invert_node.location[0] + 150) ,
                                        (invert_node.location[1] ) 
                                    )
                                    mix_color_node.label = invert_node.label

                                    # First, connect the invert node to the mix node's input
                                    
                                    mat.luxcore.node_tree.links.new(invert_node.outputs[0], mix_color_node.inputs[2])
                                    mat.luxcore.node_tree.links.new(luxcore_node.outputs[0], mix_color_node.inputs[1])
                                    mat.luxcore.node_tree.links.new(mix_color_node.outputs["Color"], next_node.inputs[target_input_index])
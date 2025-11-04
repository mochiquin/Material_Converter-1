import bpy


def Convert_Color_ramp_node(val_to_rgb_node,mat):
    Render_engine = bpy.context.scene.render.engine
    
    node_c = val_to_rgb_node.color_ramp
    Color_ramp_location = val_to_rgb_node.location
    cycles_interpolation = node_c.interpolation
    num_elements = len(node_c.elements)
    interpolation_map = {'CONSTANT': 'none', 'B_SPLINE': 'linear', 'LINEAR': 'linear', 'EASE': 'cubic'}

    if Render_engine == "octane":
        Colorramp_blidname = "NodeReroute"
        nodes = mat.node_tree.nodes
        Converted_Colorramp_base_name = "Reroute"
        input_name = "Texture"
        output_name = "Texture out"
        offset_x = 1650
        offset_y = 0
    elif Render_engine == "VRAY_RENDER_RT":
        Colorramp_blidname = "VRayNodeTexGradRamp"
        Converted_Colorramp_base_name = "V-Ray Gradient Ramp"
        nodes = mat.node_tree.nodes
        offset_x = 0
        offset_y = -1650
    elif Render_engine == "LUXCORE":
        Colorramp_blidname = "LuxCoreNodeTexBand"
        Converted_Colorramp_base_name = "ColorRamp"
        nodes = mat.luxcore.node_tree.nodes
        offset_x = 0
        offset_y = 0 
       
    Converted_Colorramp_node = None
    Converted_Colorramp_node_name = val_to_rgb_node.name.replace("Color Ramp",Converted_Colorramp_base_name)
            
    for n in nodes:
        if n.bl_idname == Colorramp_blidname and n.name == Converted_Colorramp_node_name:
            Converted_Colorramp_node = n
            continue
    if not Converted_Colorramp_node:
        Converted_Colorramp_node = nodes.new(Colorramp_blidname)
        Converted_Colorramp_node.name = Converted_Colorramp_node_name
        
    Converted_Colorramp_node.label = val_to_rgb_node.label
    Converted_Colorramp_node.location = (val_to_rgb_node.location[0] + offset_x, val_to_rgb_node.location[1] + offset_y)
    
    if Render_engine == "VRAY_RENDER_RT":
        
         # Check if texture is assigned to the gradient ramp node
        if hasattr(Converted_Colorramp_node, 'texture') and Converted_Colorramp_node.texture:
            # Retrieve texture name and assign it to the V-Ray node
            texture_name = Converted_Colorramp_node.texture.name
            texture = bpy.data.textures.get(texture_name)

            if texture:
                # If texture exists, update its color ramp
                #print(f"Texture '{texture_name}' found and assigned to the V-Ray Gradient Ramp.")
                Converted_Colorramp_node.texture = texture

                # Set interpolation and color mode
                texture.color_ramp.interpolation = val_to_rgb_node.color_ramp.interpolation
                texture.color_ramp.color_mode = val_to_rgb_node.color_ramp.color_mode

                # Ensure the correct number of elements in the color ramp
                while len(texture.color_ramp.elements) < num_elements:
                    texture.color_ramp.elements.new(position=0.5)

                while len(texture.color_ramp.elements) > num_elements:
                    texture.color_ramp.elements.remove(texture.color_ramp.elements[-1])

                # Update the color and position of each ramp element
                for i, element in enumerate(node_c.elements):
                    texture_element = texture.color_ramp.elements[i]
                    texture_element.color = element.color
                    texture_element.position = element.position
    elif Render_engine == 'LUXCORE':
        
        pos_1 = node_c.elements[0].position
        color_1 = node_c.elements[0].color
        pos_2 = node_c.elements[1].position
        color_2 = node_c.elements[1].color
        num_elements = len(node_c.elements)
        # Check if ColorRamp has more than two color stops
        if num_elements >= 2:
            """
            # Check if LuxCore ColorRamp node already exists
            Converted_Colorramp_node = False
            if hasattr(node_tree, 'nodes'):
                for node1 in node_tree.nodes:
                    if "Converted_Colorramp_node" in node1.name and node1.name.endswith(val_to_rgb_node.name.split(".")[-1]):
                        Converted_Colorramp_node = node1
                        Converted_Colorramp_node = True
                        break
            # If LuxCore ColorRamp node doesn't exist, create one
            if not Converted_Colorramp_node:
                bpy.context.object.active_material.luxcore.use_cycles_nodes = False
                Converted_Colorramp_node = lux_obj['lux_nodes'].new("LuxCoreNodeTexBand")
                Converted_Colorramp_node.name = "Converted_Colorramp_node." + val_to_rgb_node.name.split(".")[-1]
                Converted_Colorramp_node.location = Color_ramp_location
                Converted_Colorramp_node.interpolation = interpolation_map.get(cycles_interpolation, 'none')
                #counter += 1
                
            """

            Converted_Colorramp_node.ramp_items[0].offset = pos_1
            Converted_Colorramp_node.ramp_items[0].value = (color_1[0], color_1[1], color_1[2])

            Converted_Colorramp_node.ramp_items[1].offset = pos_2
            Converted_Colorramp_node.ramp_items[1].value = (color_2[0], color_2[1], color_2[2])

            # Add input nodes to LuxCore ColorRamp node for each additional color stop
            for i in range(2, num_elements):
                element = node_c.elements[i]
                Converted_Colorramp_node.add_item = False
                ramp_item = Converted_Colorramp_node.ramp_items[-1]
                ramp_item.offset = element.position
                ramp_item.value = (element.color[0], element.color[1], element.color[2])

           
        
        
        
    else:
        pass    
    
"""   
mat = bpy.context.object.active_material
c_nodes = mat.node_tree.nodes
val_to_rgb_nodes = [node for node in c_nodes if node.bl_idname.startswith("ShaderNodeValToRGB")]
for val_to_rgb_node in val_to_rgb_nodes:
                                     
    Convert_Color_ramp_node(val_to_rgb_node,mat)
"""
    

                    


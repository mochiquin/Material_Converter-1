import bpy


def Convert_ColorMix_node(Cycles_mix_color_node,mat):
    Render_engine = bpy.context.scene.render.engine
    
    if Render_engine == "octane":
        ColorMix_blidname = "NodeReroute"
        nodes = mat.node_tree.nodes
        Converted_ColorMix_base_name = "Reroute"
        input_name = "Texture"
        output_name = "Texture out"
        offset_x = 1650
        offset_y = 0
    elif Render_engine == "VRAY_RENDER_RT":
        ColorMix_blidname = "VRayNodeTexMix"
        Converted_ColorMix_base_name = "V-Ray Mix"
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        offset_x = 0
        offset_y = -1650
        blend_type_map = {
            'MULTIPLY': 'scale',
            'ADD': 'add',
            'SUBTRACT': 'subtract'
        }
    elif Render_engine == "LUXCORE":
        blend_type_map = {
            'MULTIPLY': 'scale',
            'ADD': 'add',
            'SUBTRACT': 'subtract'
        }
        ColorMix_blidname = "LuxCoreNodeTexColorMix"
        Converted_ColorMix_base_name = "Color Math"
        nodes = mat.luxcore.node_tree.nodes
        offset_x = 0
        offset_y = 0 
       
    Converted_ColorMix_node = None
    Converted_ColorMix_node_name = Cycles_mix_color_node.name.replace("Mix",Converted_ColorMix_base_name)
            
    for n in nodes:
        if n.bl_idname == ColorMix_blidname and n.name == Converted_ColorMix_node_name:
            Converted_ColorMix_node = n
            continue
    if not Converted_ColorMix_node:
        Converted_ColorMix_node = nodes.new(ColorMix_blidname)
        Converted_ColorMix_node.name = Converted_ColorMix_node_name
        
    Converted_ColorMix_node.label = Cycles_mix_color_node.label
    Converted_ColorMix_node.location = (Cycles_mix_color_node.location[0] + offset_x, Cycles_mix_color_node.location[1] + offset_y)
    
    if Render_engine == "VRAY_RENDER_RT":
        Converted_ColorMix_node.inputs["Color1"].value = Cycles_mix_color_node.inputs[6].default_value[:3]
        Converted_ColorMix_node.inputs["Color2"].value = Cycles_mix_color_node.inputs[7].default_value[:3]
        #Converted_ColorMix_node.inputs[3].value = (Cycles_mix_color_node.inputs[6].default_value[0],Cycles_mix_color_node.inputs[6].default_value[1],Cycles_mix_color_node.inputs[6].default_value[2])
        #Converted_ColorMix_node.inputs[4].value = (Cycles_mix_color_node.inputs[7].default_value[0],Cycles_mix_color_node.inputs[7].default_value[1],Cycles_mix_color_node.inputs[7].default_value[2])
                        
        #Factor:
        Converted_ColorMix_node.inputs["Mix Map"].value = (Cycles_mix_color_node.inputs[0].default_value,Cycles_mix_color_node.inputs[0].default_value,Cycles_mix_color_node.inputs[0].default_value)
        
        """if not Cycles_mix_color_node.inputs[0].is_linked:
            # Jeśli port 'Factor' nie jest podpięty, tworzysz nowy węzeł 'VRayNodeTexUserColor'
            vray_user_color = None
            for n in nodes:
                if n.bl_idname == "VRayNodeTexUserColor" and n.label == Converted_ColorMix_node.label:
                    vray_user_color = n
                    continue
            if not vray_user_color:
                                            
                vray_user_color = nodes.new("VRayNodeTexUserColor")
                vray_user_color.location = (Converted_ColorMix_node.location[0] - 300, Converted_ColorMix_node.location[1] - 150) 
                vray_user_color.label = Converted_ColorMix_node.label
            
            # Ustawienie wartości koloru na podstawie wartości z Factor
            factor_value = Cycles_mix_color_node.inputs[0].default_value
            vray_user_color.inputs[2].value[0] = factor_value  # R, G, B, A
            vray_user_color.inputs[2].value[1] = factor_value  # R, G, B, A
            vray_user_color.inputs[2].value[2] = factor_value  # R, G, B, A
            links.new(vray_user_color.outputs[0], Converted_ColorMix_node.inputs[5])""" 
    elif Render_engine == 'LUXCORE':
        
                
        Converted_ColorMix_node.clamp_output = Cycles_mix_color_node.clamp_result
        Converted_ColorMix_node.mode = blend_type_map.get(Cycles_mix_color_node.blend_type, 'mix')
        #Factor:
        Converted_ColorMix_node.inputs[0].default_value = Cycles_mix_color_node.inputs[0].default_value
        #Colors:
        Converted_ColorMix_node.inputs[1].default_value = (Cycles_mix_color_node.inputs[6].default_value[0],Cycles_mix_color_node.inputs[6].default_value[1],Cycles_mix_color_node.inputs[6].default_value[2])
        Converted_ColorMix_node.inputs[2].default_value = (Cycles_mix_color_node.inputs[7].default_value[0],Cycles_mix_color_node.inputs[7].default_value[1],Cycles_mix_color_node.inputs[7].default_value[2])
        
    elif Render_engine == 'octane':
 
        pass    
    
"""   
mat = bpy.context.object.active_material
c_nodes = mat.node_tree.nodes
Cycles_mix_color_nodes = [node for node in c_nodes if node.bl_idname.startswith("ShaderNodeMix")]
for Cycles_mix_color_node in Cycles_mix_color_nodes:
                                     
    Convert_ColorMix_node(Cycles_mix_color_node,mat)
#"""
    

                    


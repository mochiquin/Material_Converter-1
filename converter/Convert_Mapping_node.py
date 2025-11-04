import bpy


def Convert_Mapping_node(Cycles_mapping,mat):
    Render_engine = bpy.context.scene.render.engine
    c_nodes = mat.node_tree.nodes
    if Render_engine == "octane":
        Mapping_bl_idname = "NodeReroute"
        nodes = mat.node_tree.nodes
        Converted_mapping_base_name = "Reroute"
        input_name = "Texture"
        output_name = "Texture out"
        offset_x = 1650
        offset_y = 0
        
    elif Render_engine == "VRAY_RENDER_RT":
        Mapping_bl_idname = "VRayNodeUVWMapping"
        Converted_mapping_base_name = "V-Ray UWV Mapping"
        nodes = mat.node_tree.nodes
        offset_x = 0
        offset_y = -1650
        rotation = 17
        scale_x = 13
        scale_y = 14
        offset_mapping_x = 15
        offset_mapping_y = 16
    elif Render_engine == "LUXCORE":
        Mapping_bl_idname = "LuxCoreNodeTexMapping2D"
        Converted_mapping_base_name = "2D Mapping"
        nodes = mat.luxcore.node_tree.nodes
        offset_x = 0
        offset_y = 0 
       
    Converted_mapping_node = None
    Converted_mapping_node_name = Cycles_mapping.name.replace("Mapping",Converted_mapping_base_name)
            
    for n in nodes:
        if n.bl_idname == "VRayNodeUVWMapping" and n.name == Converted_mapping_node_name:
            Converted_mapping_node = n
            continue
    if not Converted_mapping_node:
        Converted_mapping_node = nodes.new(Mapping_bl_idname)
        Converted_mapping_node.name = Converted_mapping_node_name
        
    Converted_mapping_node.label = Cycles_mapping.label
    Converted_mapping_node.location = (Cycles_mapping.location[0] + offset_x, Cycles_mapping.location[1] + offset_y)
    
    uv_name = False
    for uv in c_nodes:
        if "ShaderNodeUVMap" in uv.bl_idname:
            for output in uv.outputs:
           
                for link in output.links:
                    
                    if link.to_node == Cycles_mapping:
                        
                        Nazwa_UV = uv.uv_map
                        uv_name = True
    
    if Render_engine == "VRAY_RENDER_RT":
        Converted_mapping_node.inputs[rotation].value = Cycles_mapping.inputs[2].default_value[1]
        Converted_mapping_node.inputs[scale_x].value = Cycles_mapping.inputs[3].default_value[0]
        Converted_mapping_node.inputs[scale_y].value = Cycles_mapping.inputs[3].default_value[1]
        Converted_mapping_node.inputs[offset_mapping_x].value = Cycles_mapping.inputs[1].default_value[0]
        Converted_mapping_node.inputs[offset_mapping_y].value = Cycles_mapping.inputs[1].default_value[1]
                            
        if uv_name:
            Converted_mapping_node.inputs[20].value = Nazwa_UV
            
    elif Render_engine == "LUXCORE":
        if Cycles_mapping.inputs[3].default_value[0] == Cycles_mapping.inputs[3].default_value[1]:
            Converted_mapping_node.use_uniform_scale = True
            Converted_mapping_node.uniform_scale = Cycles_mapping.inputs[3].default_value[0]
        else:
            Converted_mapping_node.use_uniform_scale = False
            Converted_mapping_node.uscale = Cycles_mapping.inputs[3].default_value[0]
            Converted_mapping_node.vscale = Cycles_mapping.inputs[3].default_value[1]
        if uv_name:
            Converted_mapping_node.uvmap = Nazwa_UV
        Converted_mapping_node.rotation = Cycles_mapping.inputs[2].default_value[0]
        Converted_mapping_node.udelta = Cycles_mapping.inputs[1].default_value[0]
        Converted_mapping_node.vdelta = Cycles_mapping.inputs[1].default_value[1]
    elif Render_engine == "octane":
        pass    
    
"""   
mat = bpy.context.object.active_material
c_nodes = mat.node_tree.nodes
Cycles_mappings = [node for node in c_nodes if node.bl_idname.startswith("ShaderNodeMapping")]
for Cycles_mapping in Cycles_mappings:
                                     
    Convert_Mapping_node(Cycles_mapping,mat)
    
        
#"""
                    


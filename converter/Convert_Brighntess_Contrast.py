import bpy


def Convert_brs_cst_node(Cycles_Brightness_Contrast,mat):
    Render_engine = bpy.context.scene.render.engine
    
    if Render_engine == "octane":
        br_ctr_blidname = "NodeReroute"
        nodes = mat.node_tree.nodes
        Converted_Bright_ctrs_base_name = "Reroute"
        input_name = "Texture"
        output_name = "Texture out"
        offset_x = 1650
        offset_y = 0
    elif Render_engine == "VRAY_RENDER_RT":
        br_ctr_blidname = "VRayNodeColorCorrection"
        Converted_Bright_ctrs_base_name = "V-Ray Color Correction"
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        offset_x = 0
        offset_y = -1650
        
    elif Render_engine == "LUXCORE":
        br_ctr_blidname = "LuxCoreNodeTexBrightContrast"
        Converted_Bright_ctrs_base_name = "Brightness/Contrast"
        nodes = mat.luxcore.node_tree.nodes
        offset_x = 0
        offset_y = 0 
       
    Converted_Brg_cnst_node = None
    Converted_Brg_cnst_node_name = Cycles_Brightness_Contrast.name.replace("Brightness/Contrast",Converted_Bright_ctrs_base_name)
    Brightness_Contrast_value = Cycles_Brightness_Contrast.inputs["Color"].default_value[:3]
    Brightness_value = Cycles_Brightness_Contrast.inputs["Bright"].default_value
    Contrast_Value = Cycles_Brightness_Contrast.inputs["Contrast"].default_value     
    for n in nodes:
        if n.bl_idname == br_ctr_blidname and n.name == Converted_Brg_cnst_node_name:
            Converted_Brg_cnst_node = n
            continue
    if not Converted_Brg_cnst_node:
        Converted_Brg_cnst_node = nodes.new(br_ctr_blidname)
        Converted_Brg_cnst_node.name = Converted_Brg_cnst_node_name
        
    Converted_Brg_cnst_node.label = Cycles_Brightness_Contrast.label
    Converted_Brg_cnst_node.location = (Cycles_Brightness_Contrast.location[0] + offset_x, Cycles_Brightness_Contrast.location[1] + offset_y)
    
    if Render_engine == "VRAY_RENDER_RT":
        Converted_Brg_cnst_node.inputs["Source Color"].value = Brightness_Contrast_value
        Converted_Brg_cnst_node.inputs[16].value = Brightness_value
        Converted_Brg_cnst_node.inputs[17].value = Contrast_Value
       
    elif Render_engine == 'LUXCORE':
        
                
        Converted_Brg_cnst_node.inputs["Brightness"].default_value = Brightness_value
        Converted_Brg_cnst_node.inputs["Contrast"].default_value = Contrast_Value
        Converted_Brg_cnst_node.inputs["Color"].default_value = Brightness_Contrast_value
    elif Render_engine == 'octane':
 
        pass    
    
"""   
mat = bpy.context.object.active_material
c_nodes = mat.node_tree.nodes
Cycles_Brightness_Contrasts = [node for node in c_nodes if node.bl_idname.startswith("ShaderNodeBrightContrast")]
for Cycles_Brightness_Contrast in Cycles_Brightness_Contrasts:
                                     
    Convert_brs_cst_node(Cycles_Brightness_Contrast,mat)
#"""
    

 

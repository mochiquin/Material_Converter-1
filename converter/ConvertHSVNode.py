import bpy


def Convert_HSV_node(node_HSV,mat):
    Render_engine = bpy.context.scene.render.engine
    
    if Render_engine == "octane":
        Colorramp_blidname = "NodeReroute"
        nodes = mat.node_tree.nodes
        Converted_Colorramp_base_name = "Reroute"
        input_name = "Texture"
        output_name = "Texture out"
        offset_x = 1650
        offset_y = 0
    elif Render_engine == "VRAY_RENDER_RT":
        Colorramp_blidname = "VRayNodeColorCorrection"
        Converted_Colorramp_base_name = "V-Ray Color Correction"
        nodes = mat.node_tree.nodes
        offset_x = 0
        offset_y = -1650
    elif Render_engine == "LUXCORE":
        Colorramp_blidname = "LuxCoreNodeTexHSV"
        Converted_Colorramp_base_name = "Hue Saturation Value"
        nodes = mat.luxcore.node_tree.nodes
        offset_x = 0
        offset_y = 0 
       
    Converted_HSV_node = None
    Converted_HSV_node_name = node_HSV.name.replace("Hue/Saturation/Value",Converted_Colorramp_base_name).replace("Hue Saturation Value",Converted_Colorramp_base_name)
            
    for n in nodes:
        if n.bl_idname == Colorramp_blidname and n.name == Converted_HSV_node_name:
            Converted_HSV_node = n
            continue
    if not Converted_HSV_node:
        Converted_HSV_node = nodes.new(Colorramp_blidname)
        Converted_HSV_node.name = Converted_HSV_node_name
        
    Converted_HSV_node.label = node_HSV.label
    Converted_HSV_node.location = (node_HSV.location[0] + offset_x, node_HSV.location[1] + offset_y)
    
    if Render_engine == "VRAY_RENDER_RT":
        
        
        Converted_HSV_node.inputs[12].value = (node_HSV.inputs[0].default_value * 360 - 180)
        Converted_HSV_node.inputs[13].value = node_HSV.inputs[1].default_value
        Converted_HSV_node.inputs[16].value = (node_HSV.inputs[2].default_value - 1)
    elif Render_engine == 'LUXCORE':
        
        #if len(node_HSV.inputs) >= 3 and len(existing_lux_hsv.inputs) >= 4:
        Converted_HSV_node.inputs[1].default_value = node_HSV.inputs[0].default_value
        Converted_HSV_node.inputs[2].default_value = node_HSV.inputs[1].default_value
        Converted_HSV_node.inputs[3].default_value = node_HSV.inputs[2].default_value
    elif Render_engine == 'octane':
 
        pass    
    
"""   
mat = bpy.context.object.active_material
c_nodes = mat.node_tree.nodes
node_HSVs = [node for node in c_nodes if node.bl_idname.startswith("ShaderNodeHueSaturation")]
for node_HSV in node_HSVs:
                                     
    Convert_HSV_node(node_HSV,mat)
#"""
    

                    


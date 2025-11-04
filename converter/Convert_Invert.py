import bpy


def Convert_Invert_node(Cycles_invert,mat):
    Render_engine = bpy.context.scene.render.engine
    
    if Render_engine == "octane":
        Invert_blidname = "NodeReroute"
        nodes = mat.node_tree.nodes
        Converted_invert_base_name = "Reroute"
        input_name = "Texture"
        output_name = "Texture out"
        offset_x = 1650
        offset_y = 0
    elif Render_engine == "VRAY_RENDER_RT":
        Invert_blidname = "VRayNodeTexInvert"
        Converted_invert_base_name = "V-Ray Invert"
        nodes = mat.node_tree.nodes
        offset_x = 0
        offset_y = -1650
    elif Render_engine == "LUXCORE":
        Invert_blidname = "LuxCoreNodeTexInvert"
        Converted_invert_base_name = "Invert"
        nodes = mat.luxcore.node_tree.nodes
        offset_x = 0
        offset_y = 0 
       
    Converted_invert_node = None
    Converted_invert_node_name = Cycles_invert.name.replace("Invert Color",Converted_invert_base_name)
            
    for n in nodes:
        if n.bl_idname == Invert_blidname and n.name == Converted_invert_node_name:
            Converted_invert_node = n
            continue
    if not Converted_invert_node:
        Converted_invert_node = nodes.new(Invert_blidname)
        Converted_invert_node.name = Converted_invert_node_name
        
    Converted_invert_node.label = Cycles_invert.label
    Converted_invert_node.location = (Cycles_invert.location[0] + offset_x, Cycles_invert.location[1] + offset_y)
    
    if Render_engine == "VRAY_RENDER_RT":
        
        Converted_invert_node.inputs[0].value = tuple(Cycles_invert.inputs[1].default_value[:3])
        Converted_invert_node.inputs[0].multiplier = (Cycles_invert.inputs[0].default_value * 100)
        Converted_invert_node.location = (Cycles_invert.location[0], Cycles_invert.location[1] - 1650) 
        Converted_invert_node.label = Cycles_invert.label
        
    elif Render_engine == 'LUXCORE':
        
        Converted_invert_node.inputs[1].default_value = Cycles_invert.inputs[0].default_value
        Converted_invert_node.location = Cycles_invert.location
        Converted_invert_node.inputs["Color"].default_value = Cycles_invert.inputs["Color"].default_value[:3]
        Converted_invert_node.label = Cycles_invert.label
    elif Render_engine == 'octane':
 
        pass    
    
"""   
mat = bpy.context.object.active_material
c_nodes = mat.node_tree.nodes
Cycles_inverts = [node for node in c_nodes if node.bl_idname.startswith("ShaderNodeInvert")]
for Cycles_invert in Cycles_inverts:
                                     
    Convert_Invert_node(Cycles_invert,mat)
#"""
    

                    


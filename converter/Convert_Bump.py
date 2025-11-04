import bpy


def Convert_bump_node(Cycles_Bump,mat):
    Render_engine = bpy.context.scene.render.engine
    
    if Render_engine == "octane":
        Bump_blidname = "NodeReroute"
        nodes = mat.node_tree.nodes
        Converted_Bump_base_name = "Reroute"
        input_name = "Texture"
        output_name = "Texture out"
        offset_x = 1650
        offset_y = 0
    elif Render_engine == "VRAY_RENDER_RT":
        Bump_blidname = "VRayNodeTexMix"
        Converted_Bump_base_name = "V-Ray Mix"
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        offset_x = 0
        offset_y = -1650
        
    elif Render_engine == "LUXCORE":
        Bump_blidname = "LuxCoreNodeTexBump"
        Converted_Bump_base_name = "Bump"
        nodes = mat.luxcore.node_tree.nodes
        offset_x = 0
        offset_y = 0 
       
    Converted_Bump_node = None
    Converted_Bump_node_name = Cycles_Bump.name.replace("Bump",Converted_Bump_base_name)
    Bump_Strength = Cycles_Bump.inputs["Strength"].default_value
    Bump_Distance = Cycles_Bump.inputs["Distance"].default_value     
    for n in nodes:
        if n.bl_idname == Bump_blidname and n.name == Converted_Bump_node_name:
            Converted_Bump_node = n
            continue
    if not Converted_Bump_node:
        Converted_Bump_node = nodes.new(Bump_blidname)
        Converted_Bump_node.name = Converted_Bump_node_name
        
    Converted_Bump_node.label = Cycles_Bump.label
    Converted_Bump_node.location = (Cycles_Bump.location[0] + offset_x, Cycles_Bump.location[1] + offset_y)
    
    if Render_engine == "VRAY_RENDER_RT":
        Converted_Bump_node.inputs["Color1"].value = Cycles_Bump.inputs[6].default_value[:3]
        Converted_Bump_node.inputs["Color2"].value = Cycles_Bump.inputs[7].default_value[:3]
        #Converted_Bump_node.inputs[3].value = (Cycles_Bump.inputs[6].default_value[0],Cycles_Bump.inputs[6].default_value[1],Cycles_Bump.inputs[6].default_value[2])
        #Converted_Bump_node.inputs[4].value = (Cycles_Bump.inputs[7].default_value[0],Cycles_Bump.inputs[7].default_value[1],Cycles_Bump.inputs[7].default_value[2])
                        
        #Factor:
        Converted_Bump_node.inputs["Mix Map"].value = (Cycles_Bump.inputs[0].default_value,Cycles_Bump.inputs[0].default_value,Cycles_Bump.inputs[0].default_value)
        
       
    elif Render_engine == 'LUXCORE':
        
                
        Converted_Bump_node.label = Cycles_Bump.label
        Converted_Bump_node.location = Cycles_Bump.location
        Converted_Bump_node.inputs[1].default_value = min(Bump_Strength, Bump_Distance)
    elif Render_engine == 'octane':
 
        pass    
    
"""   
mat = bpy.context.object.active_material
c_nodes = mat.node_tree.nodes
Cycles_Bumps = [node for node in c_nodes if node.bl_idname.startswith("ShaderNodeBump")]
for Cycles_Bump in Cycles_Bumps:
                                     
    Convert_bump_node(Cycles_Bump,mat)
#"""
    

                    


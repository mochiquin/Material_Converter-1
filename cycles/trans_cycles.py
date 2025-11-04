import bpy
import math
import sys
import os

## Import ##
script_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if script_folder not in sys.path:
    sys.path.append(script_folder)


Render_Engine = bpy.context.scene.render.engine
if Render_Engine not in ("CYCLES", "BLENDER_EEVEE_NEXT"):
    bpy.context.scene.view_settings.view_transform = 'AgX'
    bpy.context.scene.view_settings.look = 'None'

    # Ustaw silnik renderujący na Octane dla bieżącej aktywnej sceny
    bpy.context.scene.render.engine = "CYCLES"


current_workspace = bpy.context.workspace
for screen in current_workspace.screens:
    for area in screen.areas:
        if area.type == 'NODE_EDITOR'and not area.ui_type in ["GeometryNodeTree", "CompositorNodeTree"]:
            area.ui_type = 'ShaderNodeTree'

def create_basic_material():
    


    material_names_to_remove = [
        "ShaderNodeAddShader",
        "ShaderNodeBsdfDiffuse",
        "ShaderNodeEmission",
        "ShaderNodeBsdfGlass",
        "ShaderNodeBsdfGlossy",
        "ShaderNodeBsdfHair",
        "ShaderNodeHoldout",
        "ShaderNodeMixShader",
        "ShaderNodeBsdfHairPrincipled",
        "ShaderNodeVolumePrincipled",
        "ShaderNodeBsdfRayPortal",
        "ShaderNodeBsdfRefraction",
        "ShaderNodeBsdfSheen",
        "ShaderNodeSubsurfaceScattering",
        "ShaderNodeBsdfToon",
        "ShaderNodeBsdfTranslucent",
        "ShaderNodeBsdfTransparent",
        "ShaderNodeVolumeAbsorption",
        "ShaderNodeVolumeScatter"
    
        
    ]
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    Diffuse_color =[]
    Roughness_value = []
    IOR_Value = []
    
    for n in nodes:
        if n.bl_idname in material_names_to_remove:
            if 'Color' in n.inputs:
                # Get the diffuse color value
                diffuse_input = n.inputs['Color']
                Diffuse_color.append(diffuse_input.default_value[0])
                Diffuse_color.append(diffuse_input.default_value[1])
                Diffuse_color.append(diffuse_input.default_value[2])
                Diffuse_color.append(diffuse_input.default_value[3])
            if 'Roughness' in n.inputs:
                roughness_input = n.inputs['Roughness']
                Roughness_value.append(roughness_input.default_value)
                
            if 'IOR' in n.inputs:
                IOR_input = n.inputs['IOR']
                IOR_Value.append(IOR_input.default_value)
                
                
            nodes.remove(n)
    
    texture_node = None 
    for n in nodes:
        if n.bl_idname == ("ShaderNodeTexImage"):
            texture_node = n
            break

    Material_output = None
    for n in nodes:
        if n.bl_idname == ("ShaderNodeOutputMaterial"):
            if links:
                for link in links:
                    if link.to_node == n and link.from_node.bl_idname.startswith ("Shader"):
                        Material_output = n
                        Material_output.label = "Cycles Output"
                        continue
            if not links:
                Material_output = n
                Material_output.label = "Cycles Output"
                Material_output.target = "CYCLES"
                continue
            if n.target == "CYCLES":
                Material_output = n
                Material_output.label = "Cycles Output"
                Material_output.target = "CYCLES"
                break
                
    if not Material_output:
        Material_output = nodetree.nodes.new("ShaderNodeOutputMaterial")
        Material_output.label = "Cycles Output"
    Material_output.target = "CYCLES"
    
    EEVEE_output = None
    for n in nodes:
        
        if n.bl_idname == ("ShaderNodeOutputMaterial"):
            if n.target == "EEVEE":
                EEVEE_output = n
                EEVEE_output.label = "EEVEE Output"
                continue
    if not EEVEE_output:
        EEVEE_output = nodetree.nodes.new("ShaderNodeOutputMaterial")
        EEVEE_output.label = "EEVEE Output"
        EEVEE_output.target  = "EEVEE"
        
    Mis_Shader = None
    Mix_Shader_Nodes = []
    
    for n in nodetree.nodes:
        if n.bl_idname == "ShaderNodeMixShader":
            Mix_Shader_Nodes.append(n)

    if len(Mix_Shader_Nodes) > 0:
        Mis_Shader = Mix_Shader_Nodes[0]  
        Mis_Shader.label = "Material" 

        # Remove any other Principled BSDFs
        for node in Mix_Shader_Nodes[1:]:
            nodetree.nodes.remove(node) 

    if not Mis_Shader:  # If no Principled BSDF was found
        Mis_Shader = nodetree.nodes.new("ShaderNodeMixShader")
        Mis_Shader.label = "Material"
        
    Transmission = None
    Transmission_nodes = []
    
    for n in nodetree.nodes:
        if n.bl_idname == "ShaderNodeBsdfTranslucent":
            Transmission_nodes.append(n)

    if len(Transmission_nodes) > 0:
        Transmission = Transmission_nodes[0]  
        Transmission.label = "Material" 

        # Remove any other Principled BSDFs
        for node in Transmission_nodes[1:]:
            nodetree.nodes.remove(node) 

    if not Transmission:  # If no Principled BSDF was found
        Transmission = nodetree.nodes.new("ShaderNodeBsdfTranslucent")
        Transmission.label = "Material"
        
    
    
    Universal = None
    principled_nodes = []

    for n in nodetree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            principled_nodes.append(n)

    if len(principled_nodes) > 0:
        Universal = principled_nodes[0]  
        Universal.label = "Material" 

        # Remove any other Principled BSDFs
        for node in principled_nodes[1:]:
            nodetree.nodes.remove(node) 

    if not Universal:  # If no Principled BSDF was found
        Universal = nodetree.nodes.new("ShaderNodeBsdfPrincipled")
        Universal.label = "Material"
                          
        
    
    if texture_node:    
        Universal.location = (texture_node.location[0] + 600, texture_node.location[1])
    #Diffuse Color:    
    Universal.inputs[0].default_value = Diffuse_color[:4] if Diffuse_color else (0.5,0.5,0.5,1) 
     
    if Roughness_value:
        
        Universal.inputs['Roughness'].default_value = Roughness_value[0]
    mat.node_tree.links.new(Mis_Shader.outputs[0],Material_output.inputs[0])
    mat.node_tree.links.new(Mis_Shader.outputs[0],EEVEE_output.inputs[0])
    mat.node_tree.links.new(Universal.outputs[0],Mis_Shader.inputs[2])   
    mat.node_tree.links.new(Transmission.outputs[0],Mis_Shader.inputs[1])
    
    Transmission.location = (Universal.location[0], Universal.location[1] + 300 )
    Mis_Shader.location = (Universal.location[0] + 300, Universal.location[1] )
    Material_output.location = (Mis_Shader.location[0] + 300, Mis_Shader.location[1] )
    EEVEE_output.location = (Material_output.location[0], Material_output.location[1] - 150 )         
    
mat = bpy.context.object.active_material

nodetree = mat.node_tree
        
    
create_basic_material()


def Connect_Cycles_Transmission():
    # Dictionary mapping prefixes to input names
    prefix_to_input_name = {
        "Diffuse": "Base Color",
        "Normal": "Normal",
        "Roughness": "Roughness",
        "IOR": "IOR",
        "Bump": "Normal",
        
        
    }
    active_mat = bpy.context.object.active_material
    
    node_tree = active_mat.node_tree
    
    if node_tree:
        nodes = node_tree.nodes
        links = node_tree.links
        
        Cycles_output = next((node for node in nodes if node.bl_idname == ("ShaderNodeOutputMaterial") and "Cycles Output" in node.label), None)
        Eevee_output = next((node for node in nodes if node.bl_idname == ("ShaderNodeOutputMaterial") and "EEVEE Output" in node.label), None)
        Cycles_trans = next((node for node in nodes if node.bl_idname == ("ShaderNodeBsdfTranslucent") and "Material" in node.label), None)
        Cycles_mat = next((node for node in nodes if node.bl_idname == ("ShaderNodeBsdfPrincipled") and "Material" in node.label), None)
        Mix_Shader = next((node for node in nodes if node.bl_idname == ("ShaderNodeMixShader") and "Material" in node.label), None)
        Cycles_Images_nodes = [node for node in node_tree.nodes if node.bl_idname.startswith("ShaderNodeTexImage")]
        Opacity_texture =[node for node in Cycles_Images_nodes if "Opacity" in node.label] 
        Diffuse_texture = [node for node in Cycles_Images_nodes if "Diffuse" in node.label]
        AO_texture = [node for node in Cycles_Images_nodes if "AO" in node.label]
        AO_node = [node for node in node_tree.nodes if node.bl_idname.startswith("ShaderNodeMix") and "Diffuse" in node.label]
        Transmission_texture = [node for node in Cycles_Images_nodes if "Transmission" in node.label]
        Normal_texture = [node for node in Cycles_Images_nodes if "Normal" in node.label]
        Normal_node = [node for node in node_tree.nodes if node.bl_idname.startswith("ShaderNodeNormalMap")]
        Bump_texture = [node for node in Cycles_Images_nodes if "Bump" in node.label]
        Bump_node = [node for node in node_tree.nodes if node.bl_idname.startswith("ShaderNodeBump")]
        Displacement_texture = [node for node in Cycles_Images_nodes if "Displacement" in node.label]
        Displacement_node = [node for node in node_tree.nodes if node.bl_idname.startswith("ShaderNodeDisplacement") and "Displacement" in node.label]
        
        if not Cycles_mat:
            print(f"No Cycles group node found in material '{active_mat.name}'.")
            return
        
        # Create a dictionary to store inputs of the group node
        group_node_inputs = {input.name: input for input in Cycles_mat.inputs}
                
        
       
        for n in nodes:
            if n.label == "Normal" and n.bl_idname == "ShaderNodeNormalMap":
                use_normal = n
                
        if Bump_texture:
            Bump_texture = Bump_texture[0]
            if Bump_node:
                Bump_node = Bump_node[0]
            if not Bump_node:
                Bump_node = nodes.new("ShaderNodeBump")
                Bump_node.label = "Bump"
            links.new(Bump_texture.outputs[0],Bump_node.inputs[2])
            links.new(Bump_node.outputs[0],Cycles_trans.inputs[1])
            Bump_node.location = (Bump_texture.location[0] + 300, Bump_texture.location[1] )
                
            
            
        if Normal_texture:
            Normal_texture = Normal_texture[0]
            if Normal_node:
                Normal_node = Normal_node[0]
            if not Normal_node:
                Normal_node = nodes.new("ShaderNodeNormalMap")
                Normal_node.location = (Normal_texture.location[0] + 200,Normal_texture.location[1])
                Normal_node.label = "Normal"
            if not Bump_texture:
                links.new(Normal_texture.outputs[0],Normal_node.inputs[1])
                links.new(Normal_node.outputs[0],Cycles_trans.inputs[1])
            else:
                links.new(Normal_texture.outputs[0],Normal_node.inputs[1])
                links.new(Normal_node.outputs[0],Bump_node.inputs[3])
                Bump_node.location = (Normal_node.location[0] + 300, Normal_node.location[1] )
            
        if Opacity_texture:
            Opacity_texture = Opacity_texture[0]
            Opacity_mix = None
            Transparent = None
            for n in nodes:
                if n.bl_idname == "ShaderNodeMixShader" and n.label == "Material Help":
                    Opacity_mix = n
                if n.bl_idname == "ShaderNodeBsdfTransparent" and n.label == "Material Help":
                    Transparent = n
                
            if not Transparent:
                Transparent = nodes.new("ShaderNodeBsdfTransparent")
                Transparent.label = "Material Help"
            if not Opacity_mix:
                Opacity_mix = nodes.new("ShaderNodeMixShader")
                Opacity_mix.label = "Material Help"
            
            Opacity_mix.location = (Mix_Shader.location[0]+ 200, Mix_Shader.location[1] )
            Cycles_output.location = (Opacity_mix.location [0] + 200, Opacity_mix.location[1]  )
            Eevee_output.location = (Cycles_output.location [0], Cycles_output.location[1] + 150)
            Transparent.location = (Opacity_mix.location [0] - 200, Opacity_mix.location[1] -100 )
            links.new(Opacity_mix.outputs[0],Eevee_output.inputs[0])
            links.new(Opacity_mix.outputs[0],Cycles_output.inputs[0])
            links.new(Mix_Shader.outputs[0],Opacity_mix.inputs[2])
            links.new(Transparent.outputs[0],Opacity_mix.inputs[1])
            links.new(Opacity_texture.outputs[0],Opacity_mix.inputs[0])
            
        if Displacement_texture:
            Displacement_texture = Displacement_texture[0]
            if Displacement_node:
                Displacement_node = Displacement_node[0]
            if not Displacement_node:
            
                Displacement_node = nodes.new("ShaderNodeDisplacement")
                Displacement_node.label = "Displacement"
            
            links.new(Displacement_texture.outputs[0],Displacement_node.inputs[0])
            links.new(Displacement_node.outputs[0],Cycles_output.inputs[2])
            links.new(Displacement_node.outputs[0],Eevee_output.inputs[2])
            Displacement_node.location = (Displacement_texture.location[0] + 600 ,Displacement_texture.location[1])
                
        for d in nodes:
            if "Diffuse" in d.label and d.bl_idname !="ShaderNodeMix":
                Diffuse_node = d
        
        if not Transmission_texture:
            if Diffuse_texture:
                Diffuse_texture = Diffuse_texture[0]
                Transmission_HSV = None
                #Diffuse_Texture = None
                for T_hsv in nodes:
                    if "Transmission help" in T_hsv.label and T_hsv.bl_idname == "ShaderNodeHueSaturation":
                        Transmission_HSV = T_hsv
                    
                if not Transmission_HSV:
                                
                    Transmission_HSV = nodes.new("ShaderNodeHueSaturation")
                    Transmission_HSV.label = "Transmission help"
                Transmission_HSV.location = (Diffuse_texture.location[0] + 350, Diffuse_texture.location[1] + 150)
                Transmission_HSV.inputs[1].default_value  = 1.5
                Transmission_HSV.inputs[2].default_value  = 2
                links.new(Diffuse_texture.outputs[0],Transmission_HSV.inputs[4])
                links.new(Transmission_HSV.outputs[0],Cycles_trans.inputs[0])
        if Transmission_texture:
            Transmission_texture = Transmission_texture[0]
            links.new(Transmission_texture.outputs[0],Cycles_trans.inputs[0])
                
            
        if AO_texture:
            AO_texture = AO_texture[0]
            if AO_node:
                AO_node = AO_node[0]
            else:
                AO_node = nodes.new("ShaderNodeMix")
                AO_node.label = "Diffuse"
                AO_node.blend_type = "MULTIPLY"
                AO_node.data_type = "RGBA"
            AO_node.location = (Diffuse_node.location[0] + 300, Diffuse_node.location[1])    
            links.new(AO_texture.outputs[0],AO_node.inputs[7])
            links.new(Diffuse_node.outputs[0],AO_node.inputs[6])
            links.new(AO_node.outputs[1],Cycles_mat.inputs[0])
                   
        
            
            
        other_nodes = [node for node in nodes if node.bl_idname.startswith('Shader') and node.bl_idname != "ShaderNodeOutputMaterial"]
        # Distance calculation function   
        def distance(node):
            return math.sqrt((Cycles_mat.location.x + node.location.x)**2)
        
        # Sort nodes by distance
        sorted_nodes = sorted(other_nodes, key=distance)
        
        # Debug print node locations and distances
        print(f"Cycles  Material node({Cycles_mat.name}) location: ({Cycles_mat.location.x}, {Cycles_mat.location.y})")
        for node in sorted_nodes:
            dist = distance(node)
            print(f"Node {node.name} at ({node.location.x}, {node.location.y}) is {dist:.2f} units away")
        
        # Connect nodes to group node inputs
        for node in sorted_nodes:
            if node.label:
               
                # Find the appropriate input name in the group node based on the node's label prefix
                for prefix, input_name in prefix_to_input_name.items():
                    if prefix in node.label:
                        if input_name in group_node_inputs:
                            input_socket = group_node_inputs[input_name]
                            
                            # Remove existing links to this input socket
                            while input_socket.is_linked:
                                link_to_remove = input_socket.links[0]
                                links.remove(link_to_remove)
                            
                            # Connect the node's output to the input of the group node
                            if node.outputs:
                                if node.label == "Diffuse" and node.bl_idname == "ShaderNodeMix":
                                    current_output = node.outputs[2]
                                else:
                                    current_output = node.outputs[0]
                                links.new(current_output, input_socket)
                                print(f"Connecting '{node.label}' output to '{Cycles_mat.name}' group's '{input_name}' input")
                                if node.label == "AO Multiply":
                                   links.new(node.outputs[2],Cycles_mat.inputs[0])
                                #break  # Stop once connected to an available input




Connect_Cycles_Transmission()
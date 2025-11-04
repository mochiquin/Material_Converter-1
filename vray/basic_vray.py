import bpy
import math
import sys
import os

## Import ##
script_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if script_folder not in sys.path:
    sys.path.append(script_folder)


from connect_nodes import connect_to_closest_Vray_mat
from nodes import (setup_disp_nodes,setup_ao_nodes,setup_disp_nodes)
from premade import Add_Mapping_Node
from vray_tools import Change_Vray_outputs

preferences = bpy.context.preferences.addons["Material_Converter 1"].preferences
Render_Engine = bpy.context.scene.render.engine

#Vray_Sahder_Ui:
current_workspace = bpy.context.workspace
for screen in current_workspace.screens:
    for area in screen.areas:
        if area.type == 'NODE_EDITOR'and not area.ui_type in ["GeometryNodeTree", "CompositorNodeTree"]:
            area.ui_type = 'VRayNodeTreeEditor'

# Ustaw View Transform na 'Raw' i Look na 'None'
bpy.context.scene.view_settings.view_transform = 'AgX'
bpy.context.scene.view_settings.look = 'None'


def create_basic_material():
    

    material_names_to_remove = [
        "VRayNodeBRDFAlSurface",
        "VRayNodeBRDFSSS2Complex",
        "VRayNodeBRDFLayered",
        "OctaneGlossyMaterial",
        "OctaneHairMaterial",
        "OctaneLayeredMaterial",
        "OctaneMetallicMaterial",
        "OctaneMixMaterial",
        "OctaneNullMaterial",
        "OctanePortalMaterial",
        "OctaneShadowCatcherMaterial",
        "OctaneSpecularMaterial",
        "OctaneStandardSurfaceMaterial",
        "OctaneToonMaterial"
    ]
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    vray_preferences = preferences.vray_preferences
    
    
    
    diffuse_texture = [node for node in nodes if node.bl_idname.startswith("VRayNodeMetaImageTexture") and node.label == "Diffuse"]
    ao_texture = [node for node in nodes if node.bl_idname.startswith("VRayNodeMetaImageTexture") and node.label == "AO"]
    material_node = [node for node in nodes if node.bl_idname.startswith("VRayNodeBRDFVRayMtl") and node.label == "Material"]
    Output_node = [node for node in nodes if node.bl_idname.startswith("VRayNodeOutputMaterial") and node.label == "V-ray Output"]
    ao_node = [node for node in nodes if node.bl_idname.startswith("VRayNodeTexMix") and node.label == "Diffuse AO"]
    Displacement_texture = [node for node in nodes if node.bl_idname.startswith("VRayNodeMetaImageTexture") and node.label == "Displacement"]
    Displacement_node = [node for node in nodes if ("OctaneTextureDisplacement" in node.bl_idname or "OctaneVertexDisplacement" in node.bl_idname) and ("Displacement" in node.label or "COLOR * AO" in node.label)]
    
    Diffuse_color =[]
    Roughness_value = []
    Specualar_value = []
    
    
    
    for n in nodes:
        if n.bl_idname in material_names_to_remove:
            if not 'Viewport' in n.label:
                if 'Diffuse Color' in n.inputs:
                    # Get the diffuse color value
                    diffuse_input = n.inputs['Diffuse Color']
                    Diffuse_color.append(diffuse_input.value[0])
                    Diffuse_color.append(diffuse_input.value[1])
                    Diffuse_color.append(diffuse_input.value[2])
                elif 'Reflection Glossiness' in n.inputs:
                    roughness_input = n.inputs['Reflection Glossiness']
                    Roughness_value.append(roughness_input.value)
                elif 'Reflection Color' in n.inputs:
                    specular_input = n.inputs["Reflection Color"]
                    Specualar_value.append[specular_input]
            
                nodes.remove(n)
    
    for n in nodes:
       if any(z in n.label for z in ["Viewport", "help"]):
           nodes.remove(n)
    
    texture_node = None 
    for n in nodes:
        if n.bl_idname == ("VRayNodeMetaImageTexture"):
            texture_node = n
            break
    if Output_node:
        Output_node = Output_node[0]
    else:
        Output_node = nodes.new("VRayNodeOutputMaterial")
    Output_node.label = "V-ray Output" 
    
    #Material_Creation:    
    if material_node:
        material_node = material_node[0]
    else:
        material_node = nodes.new("VRayNodeBRDFVRayMtl")
        material_node.inputs["Diffuse Color"].value = vray_preferences.vray_albedo_color_addon
        material_node.inputs["Reflection Color"].value = vray_preferences.vray_reflection_color_addon
        material_node.inputs["Reflection Glossiness"].value = vray_preferences.vray_glossiness_amount
        material_node.inputs["Fresnel IOR"].value = vray_preferences.vray_Fresnel_amount
    
            
    material_node.inputs["Metalness"].value = 0.0
    material_node.inputs["Refraction Color"].value = (0,0,0)
    material_node.inputs["Self-Illumination Color"].value = (0,0,0)
    material_node.inputs["Translucency Amount"].value = 0.0
    material_node.inputs["Coat Amount"].value = 0.0
    material_node.inputs["Sheen Amount"].value = 0.0
    if material_node.inputs["Diffuse Color"].value[:3] == (0,0,0):
        material_node.inputs["Diffuse Color"].value = vray_preferences.vray_albedo_color_addon       
    material_node.label = "Material"
                          
        
    
    if texture_node:    
        material_node.location = (texture_node.location[0] + 600, texture_node.location[1])
    if Diffuse_color:
        print("Diffuse color to: ", Diffuse_color )
        #material_node.inputs["Diffuse Color"].value = Diffuse_color 
        if Diffuse_color[3] == (0,0,0):
            material_node.inputs["Diffuse Color"].value = vray_preferences.vray_albedo_color_addon
            
            
    if Roughness_value:
        
        material_node.inputs['Reflection Glossiness'].value = Roughness_value 
    if ao_texture:
        ao_texture = ao_texture[0]
        if ao_node:
            ao_node = ao_node[0]
        else:
            ao_node = setup_ao_nodes(Render_Engine, nodes, links, diffuse_texture, ao_texture, diffuse_color=None)
        links.new(ao_node.outputs[0], material_node.inputs["Diffuse Color"])
        
    mat.node_tree.links.new(material_node.outputs[0],Output_node.inputs[0])
    Output_node.location = (material_node.location[0] + 300, material_node.location[1] )
    
    if Displacement_texture:
        Displacement_texture = Displacement_texture[0]
        setup_disp_nodes(preferences, Render_Engine, nodes, links, Displacement_texture, Displacement_node)
        
def connect_to_basic_Vray_mat(mat):
   
    # Dictionary mapping prefixes to input names
    prefix_to_input_name = {
        "Diffuse": "Diffuse Color",
        "Specular": "Reflection Color",
        "Normal": "Bump Map",
        "Roughness": "Reflection Glossiness",
        "Displacement": "Displacement",
        "Bump": "Bump",
        "Opacity": "Opacity"
    }
    active_mat = mat
    
    node_tree = active_mat.node_tree
    
    if node_tree:
        nodes = node_tree.nodes
        links = node_tree.links
        
        # Find the Vray Material node
        Vray_mat = next((node for node in nodes if node.bl_idname.startswith("VRay") and "Material" in node.label), None)
        Unlinking_dictionary = [
            "Metalness",
            "Refraction Color",
            "Translucency Color",
            "Translucency Amount",
            "Sheen Amount",
            "Coat Amount",
            "Sheen Color",
            "Coat Color",
            "Fog Color"
        ]
        for input_name in Unlinking_dictionary:
                input_socket = Vray_mat.inputs.get(input_name)
                if input_socket:
                    links_to_remove = list(input_socket.links)
                    for link in links_to_remove:
                        active_mat.node_tree.links.remove(link)
        
        if not Vray_mat:
            print(f"No Vray group node found in material '{active_mat.name}'.")
            return
        
        # Create a dictionary to store inputs of the group node
        group_node_inputs = {input.name: input for input in Vray_mat.inputs}
        
                    
        
        use_normal = None
        normal_texture = None
        for n in nodes:
            if n.label == "Normal" and n.bl_idname == "VRayNodeTexNormalMapFlip":
                use_normal = n
                use_normal.label = "Normal"
                continue
            elif n.label == "Normal" and n.bl_idname == "VRayNodeMetaImageTexture":
                normal_texture = n
        if not use_normal and normal_texture:
            use_normal = nodes.new("VRayNodeTexNormalMapFlip")
            use_normal.location = (normal_texture.location[0] + 200,normal_texture.location[1])
            use_normal.label = "Normal" 
            links.new(normal_texture.outputs[0],use_normal.inputs[4])
            
        other_nodes = [node for node in nodes if node.bl_idname.startswith('VRay')] 
        
        def distance(node):
            return math.sqrt((Vray_mat.location.x - node.location.x)**2)
        
        # Sort nodes by distance
        sorted_nodes = sorted(other_nodes, key=distance)
        
        # Debug print node locations and distances
        #print(f"LuxCore group node({Vray_mat.name}) location: ({Vray_mat.location.x}, {Vray_mat.location.y})")
        for node in sorted_nodes:
            dist = distance(node)
            #print(f"Node {node.name} with label {node.label} at ({node.location.x}, {node.location.y}) is {dist:.2f} units away")
        
        # Connect nodes to group node inputs
        for prefix, input_name in prefix_to_input_name.items():
            # Check if the input exists in the group node
            if input_name in group_node_inputs:
                input_socket = group_node_inputs[input_name]
                
                # Skip if the input is already connected
                if input_socket.is_linked:
                    continue
                
                # Find the nearest node with a matching prefix
                for node in sorted_nodes:
                    if node.label and prefix in node.label:
                        # Connect the nearest node's output to the input
                        if node.outputs:
                            current_output = node.outputs[0]
                            links.new(current_output, input_socket)
                            print(f"Connecting '{node.bl_idname}' with label '{node.label}' output to '{Vray_mat.name}' group's '{input_name}' input")
                        break  
        
             
    
mat = bpy.context.object.active_material

nodetree = mat.node_tree
        
    
create_basic_material()
connect_to_basic_Vray_mat(mat)
Change_Vray_outputs(mat)











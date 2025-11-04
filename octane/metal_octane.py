import bpy
import math
import sys
import os

#Import
script_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if script_folder not in sys.path:
    sys.path.append(script_folder)

from connect_nodes import (connect_to_closest_octane_group_node,Connect_To_Material)
from nodes import (setup_disp_nodes,setup_ao_nodes)

preferences = bpy.context.preferences.addons["Material_Converter 1"].preferences
Render_Engine = bpy.context.scene.render.engine



current_workspace = bpy.context.workspace
for screen in current_workspace.screens:
    for area in screen.areas:
        if area.type == 'NODE_EDITOR'and not area.ui_type in ["GeometryNodeTree", "CompositorNodeTree"]:
            area.ui_type = 'ShaderNodeTree'

def create_Metallic_material(mat, preferences):
    
    
    
    material_names_to_remove = [
        "OctaneClippingMaterial",
        "OctaneCompositeMaterial",
        "OctaneDiffuseMaterial",
        "OctaneGlossyMaterial",
        "OctaneHairMaterial",
        "OctaneLayeredMaterial",
        
        "OctaneMixMaterial",
        "OctaneNullMaterial",
        "OctanePortalMaterial",
        "OctaneShadowCatcherMaterial",
        "OctaneSpecularMaterial",
        
        "OctaneToonMaterial"
    ]
    Metall = preferences.octane_preferences.use_metallic_material
    if not Metall:
        Chosen_material = preferences.octane_preferences.octane_base_material
        if Chosen_material == "UNIVERSAL":
             material_names_to_remove.append("OctaneStandardSurfaceMaterial")
             material_names_to_remove.append("OctaneMetallicMaterial")
             Material_type = "OctaneUniversalMaterial"
             Albedo_name = "Albedo"
             Old_Albedo = "Base color"
             Roughness_name = "Roughness"
             Roughness_old = "Specular Roughness"
             Old_Specular = "Specular"
             Metallic_input = "Metallic"
             
        else:
             material_names_to_remove.append("OctaneUniversalMaterial")
             material_names_to_remove.append("OctaneMetallicMaterial")
             Material_type = "OctaneStandardSurfaceMaterial"
             Albedo_name = "Base color"
             Old_Albedo = "Albedo"
             Metallic_input = "Metalness"
             
             Roughness_name = "Specular roughness"
             Roughness_old = "Roughness"
             Old_Specular = "Specular weight"
    if Metall == True:
         material_names_to_remove.append("OctaneUniversalMaterial")
         material_names_to_remove.append("OctaneStandardSurfaceMaterial")
         Material_type = "OctaneMetallicMaterial"
         Old_Albedo = "Albedo"
         Roughness_name = "Roughness"
         Old_Specular = "Specular map"
    print(material_names_to_remove)
         
     
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    diffuse_texture = [node for node in nodes if node.bl_idname.startswith("OctaneRGBImage") and node.label == "Diffuse"]
    ao_texture = [node for node in nodes if node.bl_idname.startswith("OctaneRGBImage") and node.label == "AO"]
    material_node = [node for node in nodes if node.bl_idname.startswith(Material_type) and node.label == "Material"]
    Material_output = [node for node in nodes if node.bl_idname.startswith("ShaderNodeOutputMaterial") and node.label == "Octane Output"]
    ao_node = [node for node in nodes if node.bl_idname.startswith("OctaneCyclesMixColorNodeWrapper") and node.label == "Diffuse AO"]
    Displacement_texture = [node for node in nodes if node.bl_idname.startswith("OctaneRGBImage") and node.label == "Displacement"]
    Displacement_node = [node for node in nodes if ("OctaneTextureDisplacement" in node.bl_idname or "OctaneVertexDisplacement" in node.bl_idname) and ("Displacement" in node.label or "COLOR * AO" in node.label)]
    Transmission_Color_node = [node for node in nodes if node.bl_idname.startswith("OctaneRGBColor") and node.label == "Transmisison help"]

    
    
    Diffuse_color =[]
    Roughness_value = []
    Specular_value = [] 
    
    for n in nodes:
                
            
        if n.bl_idname in material_names_to_remove:
            # Iterate through the inputs of the node
            for input in n.inputs:
                # Check for Albedo or Base Color
                if input.name == "Albedo" or input.name == "Base Color":
                    # Get the diffuse color value
                    Diffuse_color.append(input.default_value[0])  # R
                    Diffuse_color.append(input.default_value[1])  # G
                    Diffuse_color.append(input.default_value[2])  # B
                    
                # Check for Roughness or Specular Roughness
                elif input.name == "Roughness" or input.name == "Specular Roughness":
                    roughness_value = input.default_value
                    Roughness_value.append(roughness_value)
                
                # Check for Specular
                elif input.name == "Specular" or input.name == "Specular map" or input.name == "Specular weight":
                    specular_value = input.default_value
                    Specular_value.append(specular_value)
                 
                
            nodes.remove(n)
    Delete_nodes = [node for node in nodes if node.bl_idname.startswith("Octane") and any(z in node.label for z in ("help", "Viewport"))]
    
    for nd in Delete_nodes:
        
        nodes.remove(nd)
    texture_node = None 
    for n in nodes:
        if n.bl_idname == ("OctaneRGBImage"):
            texture_node = n
            break
        
    #Material output:
    if Material_output:
        Material_output = Material_output[0]
    else:
        Material_output = nodetree.nodes.new("ShaderNodeOutputMaterial")
        Material_output.label = "Octane Output"

        
    #Material Creation
    
    if material_node:
        Material = material_node[0]
        Material.label = "Material"
    else:
        Material = nodetree.nodes.new(Material_type)
        Material.inputs[Roughness_name].default_value = 0
        Material.label = "Material"
        if Metall == True:
            Material.inputs[Roughness_name].default_value = preferences.octane_preferences.octane_metallic_roughness
            Material.inputs["Specular map"].default_value = preferences.octane_preferences.octane_metallic_specular_color
            Material.inputs["BRDF model"].default_value = preferences.octane_preferences.octane_metallic_BRDF
            Material.inputs["Metallic reflection mode"].default_value = preferences.octane_preferences.octane_metallic_reflection
        else:
            Material.inputs[Albedo_name].default_value = preferences.octane_preferences.octane_albedo_color_addon
            Material.inputs[Roughness_name].default_value = preferences.octane_preferences.octane_base_roughness
            Material.inputs[Old_Specular].default_value = preferences.octane_preferences.octane_base_specular
            Material.inputs[Metallic_input].default_value = 1
    if Metall == False:
        Material.inputs[Metallic_input].default_value = 1
        if Chosen_material != "UNIVERSAL":
            Material.inputs["Transmission weight"].default_value = 0
            Material.inputs["Subsurface weight"].default_value = 0
            Material.inputs["Coating weight"].default_value = 0
            Material.inputs["Sheen weight"].default_value = 0
            Material.inputs["Emission weight"].default_value = 0
            Material.inputs["Film thickness (nm)"].default_value = 0
        else:
            Material.inputs["Coating"].default_value = (0,0,0)
            Material.inputs["Sheen"].default_value = (0,0,0)
        
            
        
    
    
        
    
    if texture_node:    
        Material.location = (texture_node.location[0] + 600, texture_node.location[1])
    
    if Roughness_value:
        
        Material.inputs[Roughness_name].default_value = Roughness_value[0]
    if Specular_value:
        Material.inputs[Old_Specular].default_value = Specular_value[0]
    if Material.bl_idname!="OctaneMetallicMaterial":
        Material.inputs["Diffuse BRDF model"].default_value = preferences.octane_preferences.octane_BRDF
        if Chosen_material == "UNIVERSAL":
            Material.inputs["[OctaneGroupTitle]Transmission Layer"].default_value = preferences.octane_preferences.octane_transmission
        
            Material.inputs["BSDF model"].default_value = preferences.octane_preferences.octane_BSDF
            Material.inputs["Metallic reflection mode"].default_value = preferences.octane_preferences.octane_metallic_type
            
        else:
            Material.inputs["Dispersion mode"].default_value = preferences.octane_preferences.octane_Dispersion_mode
        
    if ao_texture:
        ao_texture = ao_texture[0]
        if ao_node:
            ao_node = ao_node[0]
        else:
            ao_node = setup_ao_nodes(Render_Engine, nodes, links, diffuse_texture, ao_texture, diffuse_color=None)
        links.new(ao_node.outputs[0], Material.inputs[Albedo_name])
    if Displacement_texture:
        Displacement_texture = Displacement_texture[0]
        if Displacement_node:
            Displacement_node = Displacement_node[0]
        else:
            Displacement_node = setup_disp_nodes(preferences, Render_Engine, nodes, links, Displacement_texture, Displacement_node)
        links.new(Displacement_node.outputs["Displacement out"], Material.inputs["Displacement"])
    #Transmission_Color_node.location = (Material.location[0] - 300, Material.location[1] )
    if Material.bl_idname == "OctaneStandardSurfaceMaterial":
        Material.inputs["Transmission weight"].default_value = 0
    mat.node_tree.links.new(Material.outputs[0],Material_output.inputs[0])
    Material_output.location = (Material.location[0] + 300, Material.location[1] )
    
    
def Connect_To_Metal(mat):
    active_mat = mat
    engine = bpy.context.scene.render.engine
    
    node_tree = active_mat.node_tree
    
    if node_tree:
        nodes = node_tree.nodes
        links = node_tree.links
        
                
            
        if engine == "octane":
            Material_node = next((node for node in nodes if node.bl_idname.startswith("Octane") and "Material" in node.label), None)
            engine_name = "Octane"
            other_nodes = [node for node in nodes if node != Material_node and node.bl_idname.startswith("Octane")]
            
            prefix_to_input_name = {
                
                
                ("Metallic", "METALNESS", "METAL"): "Metalness",
                ("NRM", "NORMAL", "Normal Map"): "Normal",
                ("SSS", "Subsurface"): "Subsurface color",
                ("Displacement", "DISP", "HEIGHT", "displacement"): "Displacement",
                ("BUMP",): "Bump",
                ("Opacity", "OPACITY"): "Opacity",
                ("Transmission", "TRANS"): "Transmission",
                ("Coat", "COATING"): "Coating"
            }
            if bpy.context.preferences.addons["Material_Converter 1"].preferences.octane_preferences.use_metallic_material == False:
                
                if bpy.context.preferences.addons["Material_Converter 1"].preferences.octane_preferences.octane_base_material == "UNIVERSAL":
                    prefix_to_input_name[("Diffuse", "COL", "COLOR", "COLOR * AO")] = "Albedo"
                    prefix_to_input_name[("GLOSS", "ROUGHNESS", "Roughness")] =  "Roughness"
                    prefix_to_input_name[("Specular", "REFL", "REFLECTION")] = "Specular"
                else:
                    prefix_to_input_name[("Diffuse", "COL", "COLOR", "COLOR * AO")] = "Base color"
                    prefix_to_input_name[("GLOSS", "ROUGHNESS", "Roughness")] =  "Specular roughness"
                    prefix_to_input_name[("Specular", "REFL", "REFLECTION")] = "Specular"
            else:
                prefix_to_input_name[("Diffuse", "COL", "COLOR", "COLOR * AO")] = "Diffuse color"
                prefix_to_input_name[("GLOSS", "ROUGHNESS", "Roughness")] =  "Roughness"
                prefix_to_input_name[("Specular", "REFL", "REFLECTION")] = "Specular map"
            
        
            
        if not Material_node:
            print(f"No {engine_name} group node found in material '{active_mat.name}'.")
            return

        print("Active Nodetree: ", node_tree)
        
        # Create a dictionary to store inputs of the group node
        group_node_inputs = {input.name: input for input in Material_node.inputs}
        
        # Distance calculation function
        def distance(node):
            return math.sqrt(
                (Material_node.location.x - node.location.x)**2 + 
                (Material_node.location.y - node.location.y)**2
            )
        
        # Sort nodes by distance
        sorted_nodes = sorted(other_nodes, key=distance)
        
        # Debug print
        print(f"Material node for {engine_name} : ({Material_node.name}) location: ({Material_node.location.x}, {Material_node.location.y})")
        for node in sorted_nodes:
            dist = distance(node)
            print(f"Node {node.name} at ({node.location.x}, {node.location.y}) is {dist:.2f} units away")
        
        # Connect nodes to group node inputs
        for node in sorted_nodes:
            
            if node.label:
                node_label_upper = node.label.upper()
                
                # Try to match the node label with our prefix groups
                for prefixes, input_name in prefix_to_input_name.items():
                    if any(prefix.upper() in node_label_upper for prefix in prefixes):
                        if input_name in group_node_inputs:
                            input_socket = group_node_inputs[input_name]
                            
                            if not input_socket.is_linked:
                                if node.outputs:
                                    #current_output = node.outputs[0]
                                    if node.bl_idname == "LuxCoreNodeTexImagemap" and any(x in node.label for x in ["NRM", "NORMAL", "Normal Map"]):
                                        current_output = node.outputs[2]
                                    
                                    elif node.bl_idname == "VRayNodeMetaImageTexture" and any(l in node.label for l in ["GLOSS", "ROUGHNESS", "Metallic", "METALNESS", "METAL"]):
                                        current_output = node.outputs[3]
                                    else:
                                        current_output = node.outputs[0]
                                    if node.bl_idname == "VRayNodeMetaImageTexture" and any(z in node.label for z in ["SSS", "Subsurface"]):
                                        
                                        links.new(node.outputs[0], Material_node.inputs["Fog Color"])
                                        #links.new(node.outputs[0], Material_node.inputs["Refraction Color"])
                                        Material_node.inputs["Refraction Color"].value = (0.248867, 0.248867, 0.248867)
                                        if Material_node.bl_idname == "VRayNodeBRDFVRayMtl":
                                            Material_node.inputs[49].value ="6"
                                    
                                        
                                    links.new(current_output, input_socket)
                                    print(f"Connecting '{node.label}' output to '{Material_node.name}' group's '{input_name}' input")
                                    break
                                    

       
    
mat = bpy.context.object.active_material

nodetree = mat.node_tree
        
if not nodetree.nodes:
    m = nodetree.nodes.new("ShaderNodeOutputMaterial")
    m.label = "Octane Output"

   
create_Metallic_material(mat, preferences)

Connect_To_Metal(mat)











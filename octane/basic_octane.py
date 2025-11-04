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

def create_basic_material(mat, preferences):
    
    
    
    material_names_to_remove = [
        "OctaneClippingMaterial",
        "OctaneCompositeMaterial",
        "OctaneDiffuseMaterial",
        "OctaneGlossyMaterial",
        "OctaneHairMaterial",
        "OctaneLayeredMaterial",
        "OctaneMetallicMaterial",
        "OctaneMixMaterial",
        "OctaneNullMaterial",
        "OctanePortalMaterial",
        "OctaneShadowCatcherMaterial",
        "OctaneSpecularMaterial",
        
        "OctaneToonMaterial"
    ]
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
         
     
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    diffuse_texture = [node for node in nodes if node.bl_idname.startswith("OctaneRGBImage") and node.label == "Diffuse"]
    
    ao_texture = [node for node in nodes if node.bl_idname.startswith("OctaneRGBImage") and node.label == "AO"]
    material_node = [node for node in nodes if node.bl_idname.startswith(Material_type) and node.label == "Material"]
    Material_output = [node for node in nodes if node.bl_idname.startswith("ShaderNodeOutputMaterial") and node.label == "Octane Output"]
    ao_node = [node for node in nodes if node.bl_idname.startswith("OctaneCyclesMixColorNodeWrapper") and node.label == "Diffuse AO"]
    Displacement_texture = [node for node in nodes if node.bl_idname.startswith("OctaneRGBImage") and node.label == "Displacement"]
    Displacement_node = [node for node in nodes if ("OctaneTextureDisplacement" in node.bl_idname or "OctaneVertexDisplacement" in node.bl_idname) and ("Displacement" in node.label or "COLOR * AO" in node.label)]

    
    
    Diffuse_color =[]
    Roughness_value = []
    
    for n in nodes:
        if n.bl_idname in material_names_to_remove:
            if Old_Albedo in n.inputs:
                # Get the diffuse color value
                diffuse_input = n.inputs[Old_Albedo]
                Diffuse_color.append(diffuse_input.default_value[0])
                Diffuse_color.append(diffuse_input.default_value[1])
                Diffuse_color.append(diffuse_input.default_value[2])
            elif Roughness_old in n.inputs:
                roughness_input = n.inputs[Roughness_old]
                Roughness_value.append(roughness_input.default_value)  
                
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
        Material.label = "Material"
    Material.inputs[Metallic_input].default_value = 0
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
    if Diffuse_color:
        Material.inputs[Albedo_name].default_value = Diffuse_color[:3] 
    if Roughness_value:
        
        Material.inputs[Roughness_name].default_value = Roughness_value
    
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
        
    mat.node_tree.links.new(Material.outputs[0],Material_output.inputs[0])
    Material_output.location = (Material.location[0] + 300, Material.location[1] )

       
    
mat = bpy.context.object.active_material

nodetree = mat.node_tree
        
if not nodetree.nodes:
    m = nodetree.nodes.new("ShaderNodeOutputMaterial")
    m.label = "Octane Output"

   
create_basic_material(mat, preferences)

Connect_To_Material(mat)











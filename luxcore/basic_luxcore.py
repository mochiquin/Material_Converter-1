import bpy
import math
import sys
import os
import re

# Import
script_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if script_folder not in sys.path:
    sys.path.append(script_folder)


from connect_nodes import (connect_to_closest_luxcore_group_node, label_texture_nodes,Connect_To_Material)
from nodes import (setup_disp_nodes,setup_ao_nodes,setup_disp_nodes)
from premade import Add_Mapping_Node

preferences = bpy.context.preferences.addons["Material_Converter 1"].preferences
Render_Engine = bpy.context.scene.render.engine

if Render_Engine != "LUXCORE":
    bpy.context.scene.view_settings.view_transform = 'AgX'
    bpy.context.scene.view_settings.look = 'None'
    bpy.context.scene.render.engine = "LUXCORE"

current_workspace = bpy.context.workspace
for screen in current_workspace.screens:
    for area in screen.areas:
        if area.type == 'NODE_EDITOR' and not area.ui_type in ["GeometryNodeTree", "CompositorNodeTree"]:
            area.ui_type = 'luxcore_material_nodes'


def create_basic_material():
    
    material_names_to_remove = [
        "LuxCoreNodeMatMatte",
        "LuxCoreNodeMatMix",
        "LuxCoreNodeMatMatteTranslucent",
        "LuxCoreNodeMatMetal",
        "LuxCoreNodeMatMirror",
        "LuxCoreNodeMatGlossy2",
        "LuxCoreNodeMatGlossyTranslucent",
        "LuxCoreNodeMatGlossyCoating",
        "LuxCoreNodeMatGlass",
        "LuxCoreNodeMatNull",
        "LuxCoreNodeMatCarpaint",
        "LuxCoreNodeMatCloth",
        "LuxCoreNodeMatVelvet",
        "LuxCoreNodeMatTwoSided",
        "LuxCoreNodeMatFrontBackOpacity",
    ]
    
    nodes = mat.luxcore.node_tree.nodes
    links = mat.luxcore.node_tree.links
    
    help_nodes = [node for node in nodes if  "help" in node.label]
    
    diffuse_texture = [node for node in nodes if node.bl_idname.startswith("LuxCoreNodeTexImagemap") and any (z in node.label for z in ["Diffuse", "COL"])]
    ao_texture = [node for node in nodes if node.bl_idname.startswith("LuxCoreNodeTexImagemap") and node.label == "AO"]
    Material_node = [node for node in nodes if node.bl_idname.startswith("LuxCoreNodeMatDisney") and node.label == "Material"]
    Material_output = [node for node in nodes if node.bl_idname.startswith("LuxCoreNodeMatOutput") ]
    #Diffuse_texture = [node for node in Luxcore_Images_nodes if any (z in node.label for z in ["Diffuse", "COL"])]
    ao_node = [node for node in nodes if node.bl_idname.startswith("LuxCoreNodeTexColorMix") and "AO" in node.label]
    Displacement_texture = [node for node in nodes if node.bl_idname.startswith("LuxCoreNodeTexImagemap") and node.label == "Displacement"]
    Displacement_node = [node for node in nodes if ("LuxCoreNodeShapeHeightDisplacement" in node.bl_idname or "LuxCoreNodeShapeVectorDisplacement" in node.bl_idname) and ("Displacement" in node.label or "COLOR * AO" in node.label)]

    
    Diffuse_color =[]
    Roughness_value = []
    Specular_value = []
    
    Diffues_names = {"Diffuse Color", "Color", "Base Color"}
    Specular_mapping = {"Specular Color", "Wrap Specular Color"}
    for n in nodes:
        if n.bl_idname in material_names_to_remove:
            for input in n.inputs:
                if input.name in Diffues_names: 
            
                    Diffuse_color.append(input.default_value[0])  # R
                    Diffuse_color.append(input.default_value[1])  # G
                    Diffuse_color.append(input.default_value[2])  # B
                elif input.name == 'Roughness':
                    roughness_value = input.default_value
                    Roughness_value.append(roughness_value)
                elif input.name == "Specular":
                    specular_value = input.default_value
                    Specular_value.append(specular_value)
                elif input.name in Specular_mapping:
                    specular_value = input.default_value[0]
                    Specular_value.append(specular_value) 
                
            nodes.remove(n)
    for node in help_nodes:
        nodes.remove(node)
        
    texture_node = None 
    for n in nodes:
        if n.bl_idname == ("LuxCoreNodeTexImagemap"):

            texture_node = n
            break
    #Material output creation:       
    if Material_output:
        Material_output = Material_output[0]
    else:
        Material_output = nodes.new("LuxCoreNodeMatOutput")
   
    Material_output.label = "LuxCore Output"
        
    if Material_node:
        Material_node = Material_node[0]
    else:
        Material_node = nodes.new("LuxCoreNodeMatDisney")
        Material_node.label = "Material"
        Material_node.inputs["Base Color"].default_value = preferences.luxcore_preferences.luxcore_albedo_color_addon
        Material_node.inputs["Specular"].default_value = preferences.luxcore_preferences.luxcore_base_specular
        Material_node.inputs["Roughness"].default_value = preferences.luxcore_preferences.luxcore_base_roughness
    Material_node.inputs["Metallic"].default_value = 0
    Material_node.inputs["Sheen"].default_value = 0 
    Material_node.inputs["Clearcoat"].default_value = 0  
    Material_node.inputs["Anisotropic"].default_value = 0
    Material_node.use_thinfilmcoating = False                
    
    if texture_node:    
        Material_node.location = (texture_node.location[0] + 600, texture_node.location[1])
    if Diffuse_color:
        Material_node.inputs[0].default_value = Diffuse_color 
    if Roughness_value:
        
        Material_node.inputs[5].default_value = Roughness_value
        
    links.new(Material_node.outputs[0],Material_output.inputs[0])
    Material_output.location = (Material_node.location[0] + 300, Material_node.location[1] )
    
    if ao_texture:
        ao_texture = ao_texture[0]
        if ao_node:
            ao_node = ao_node[0]
        else:
            ao_node = setup_ao_nodes(Render_Engine, nodes, links, diffuse_texture, ao_texture, diffuse_color=None)
        links.new(ao_node.outputs[0], Material_node.inputs["Base Color"])
    if Displacement_texture:
        Displacement_texture = Displacement_texture[0]
        if preferences.luxcore_preferences.luxcore_displacement == "Modifier":
            if Displacement_node:
                for nodes in Displacement_node:
                    nodes.remove(nodes)
            setup_disp_modifier(preferences, Render_Engine, nodes, Displacement_texture, Displacement_node)
        else:
            Displacement_node = setup_disp_nodes(preferences, Render_Engine, nodes, links, Displacement_texture, Displacement_node)
            links.new(Displacement_node.outputs[0], Material_output.inputs[3])
            
            
             
    
mat = bpy.context.object.active_material


nodetree = mat.luxcore.node_tree

material_name = mat.name
   
if not mat.luxcore.node_tree:
    color = []
    color.append(mat.diffuse_color[0])
    color.append(mat.diffuse_color[1])
    color.append(mat.diffuse_color[2])
    color.append(mat.diffuse_color[3])
    mat.luxcore.node_tree = bpy.data.node_groups.new(name=material_name, type="luxcore_material_nodes") 
    mat.luxcore.use_cycles_nodes = False
    mat.luxcore.auto_vp_color = False
    mat.diffuse_color = (color[0],color[1],color[2],color[3])
    m = mat.luxcore.node_tree.nodes.new("LuxCoreNodeMatOutput")

    m.label = "LuxCore Output"
    nodes = mat.luxcore.node_tree.nodes
        
if mat:
    label_texture_nodes(mat)
else:
    print("No active material found")
    

create_basic_material()
#connect_to_closest_luxcore_group_node()
Add_Mapping_Node(mat)
Connect_To_Material(mat)











import bpy
import os
import math
import sys
from bpy.props import StringProperty



## Import ##
script_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if script_folder not in sys.path:
    sys.path.append(script_folder)
    
convert_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "converter"))
if convert_folder not in sys.path:
    sys.path.append(convert_folder)

Normal_names = ("Normal", "nrm", "nor", "NRM")

from connect_nodes import (connect_to_closest_luxcore_group_node, label_texture_nodes,Connect_To_Material)
from rebuild import rebuild_Luxcore_connections
from premade import (label_nodes_from_base_color,set_labels_recursive,remove_reroutes_from_material)
from nodes import (setup_disp_nodes,setup_ao_nodes,setup_disp_modifier)
from luxcore_tools import process_luxcore_nodes

#Import Node Conversion 
from convert_curve import Convert_Curve_node
from convert_images import Convert_image_node
from ConvertHSVNode import Convert_HSV_node
from ConvertColorRampNode import Convert_Color_ramp_node
from Convert_Mapping_node import Convert_Mapping_node
from Convert_Invert import Convert_Invert_node
from Convert_Color_Mix_node import Convert_ColorMix_node
from Convert_Bump import Convert_bump_node
from Convert_Brighntess_Contrast import Convert_brs_cst_node
from Convert_BDSF import Convert_BDSF_node
from Shader_node_group import Unpack_Shader_node_group

preferences = bpy.context.preferences.addons["Material_Converter 1"].preferences

current_workspace = bpy.context.workspace
for screen in current_workspace.screens:
    for area in screen.areas:
        if area.type == 'NODE_EDITOR' and not area.ui_type in ["GeometryNodeTree", "CompositorNodeTree"]:
            area.ui_type = 'luxcore_material_nodes'

mat = bpy.context.object.active_material
#Premade:
label_nodes_from_base_color(mat)
remove_reroutes_from_material(mat)

current_workspace = bpy.context.workspace
Render_Engine = bpy.context.scene.render.engine
if Render_Engine != "LUXCORE":
    bpy.context.scene.view_settings.view_transform = 'AgX'
    bpy.context.scene.view_settings.look = 'None'
    bpy.context.scene.render.engine = "LUXCORE"

    
for screen in current_workspace.screens:
    for area in screen.areas:
        if area.type == 'NODE_EDITOR' and not area.ui_type in ["GeometryNodeTree", "CompositorNodeTree"]:
            area.ui_type = 'luxcore_material_nodes'


if hasattr(mat, 'node_tree'):
    active_material = mat
    c_nodes_tree = active_material.node_tree
    if hasattr(c_nodes_tree, 'nodes'):
        c_nodes = c_nodes_tree.nodes
        color = []
        color.append(mat.diffuse_color[0])
        color.append(mat.diffuse_color[1])
        color.append(mat.diffuse_color[2])
        color.append(mat.diffuse_color[3])

        
        map_colorspace = {"Filmic Log": 1, "Linear": 1,  "LinearAces": 1, "Non-Color": 1, "Raw": 1, "sRGB": 2.2, "Generic Data": 1}
        
        # LuxCore Material node tree creation
        tree_name = "Nodes_" + active_material.name

        if active_material.luxcore.node_tree:
            print("------- Luxcore Material Exists Already !!! --------")
            node_tree = active_material.luxcore.node_tree
            lux_nodes = node_tree.nodes
        else:
            node_tree = bpy.data.node_groups.new(name=tree_name, type="luxcore_material_nodes")
            active_material.luxcore.node_tree = node_tree
            node_tree.use_fake_user = True
            lux_nodes = node_tree.nodes
        active_material.luxcore.auto_vp_color = False
        mat.diffuse_color = (color[0],color[1],color[2],color[3])
        lux_obj = {'lux_nodes': lux_nodes, 'node_tree': node_tree}
        nodes = active_material.luxcore.node_tree.nodes
        links = active_material.luxcore.node_tree.links

        counter = 0

        
                
        #Images:
        Cycles_Images_nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeTexImage")]
        for Cycles_Images in Cycles_Images_nodes:
            Convert_image_node(Cycles_Images,mat)
        Cycles_Node_Group = [node for node in c_nodes_tree.nodes if node.bl_idname == "ShaderNodeGroup"]
        Cycles_metallic_nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeBsdfMetallic")]
        Cycles_Output_nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeMaterialOutput")]
        Cycles_Translusency_nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeBsdfTranslucent")]
        Cycles_principled_nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeBsdfPrincipled")]
        Cycles_Color_Mix = [node for node in c_nodes_tree.nodes if node.bl_idname == "ShaderNodeMix"]
        Cycles_Glass_nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeBsdfGlass")]
        Cycles_ShaderMix_nodes = [node for node in c_nodes_tree.nodes if node.bl_idname == "ShaderNodeMixShader"]
        Cycles_HSV_nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeHueSaturation")]
        val_to_rgb_nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeValToRGB")]
        Cycles_Bump_nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeBump")]
        Cycles_Mapping_Nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeMapping")]
        Cycles_Invert_Nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeInvert")]
        Cycles_Displacement = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeDisplacement")]
        Cycles_Brightness_Contrast_nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeBrightContrast")]
        Displacement_texture = [node for node in nodes if node.bl_idname.startswith("LuxCoreNodeTexImagemap") and node.label == "Displacement"]
        Displacement_node = [node for node in nodes if ("LuxCoreNodeShapeHeightDisplacement" in node.bl_idname or "LuxCoreNodeShapeVectorDisplacement" in node.bl_idname) and ("Displacement" in node.label or "COLOR * AO" in node.label)]
        Luxcore_output = [node for node in nodes if node.bl_idname.startswith("LuxCoreNodeMatOutput")]
        
        Cycles_curves = [node for node in c_nodes_tree.nodes if node.bl_idname == "ShaderNodeRGBCurve"]
        #groups
        for Cycles_Groups in Cycles_Node_Group:
            Unpack_Shader_node_group(Cycles_Groups,mat)
        
        # Curves Conversion:
        for cycles_curve in Cycles_curves:
                                             
            Convert_Curve_node(cycles_curve,mat)

        ao_texture = [node for node in nodes if node.bl_idname.startswith("LuxCoreNodeTexImagemap") and node.label == "AO"]
        ao_node = [node for node in nodes if node.bl_idname.startswith("LuxCoreNodeTexColorMix") and node.label == "Diffuse AO"]
        
        for Cycles_invert in Cycles_Invert_Nodes:
            Convert_Invert_node(Cycles_invert,mat)
            
        blend_type_map = {
            'MULTIPLY': 'scale',
            'ADD': 'add',
            'SUBTRACT': 'subtract'
        }
        for Cycles_mix_color_node in Cycles_Color_Mix:
            Convert_ColorMix_node(Cycles_mix_color_node,mat)
                    
        for Cycles_mapping in Cycles_Mapping_Nodes:
            Convert_Mapping_node(Cycles_mapping,mat)
            
        for Cycles_Brightness_Contrast in Cycles_Brightness_Contrast_nodes:
            Convert_brs_cst_node(Cycles_Brightness_Contrast,mat)
            
            
        
        if Luxcore_output:
            Luxcore_output = Luxcore_output[0]
        else:
            Luxcore_output = nodes.new("LuxCoreNodeMatOutput")
            Luxcore_output.label = "Luxcore Output"
            


        counter = 0
        for Cycles_Bump in Cycles_Bump_nodes:
            Convert_bump_node(Cycles_Bump,mat)
            
        #Dispalcement:
        for Cycles_Disp_node in Cycles_Displacement:
            if preferences.luxcore_preferences.luxcore_displacement == "Modifier":
                if Displacement_texture:
                    Displacement_texture = Displacement_texture[0]
                    Displacement = setup_disp_modifier(preferences, Render_Engine, nodes, Displacement_texture, Displacement_node)
            else:
                if Displacement_texture:
                    if not Displacement_node:
                        Displacement_texture = Displacement_texture[0]
                        Displacement_node = setup_disp_nodes(preferences, Render_Engine, nodes, links, Displacement_texture, Displacement_node)
                        links.new(Displacement_node.outputs[0], Luxcore_output.inputs[3])
                
            
        for val_to_rgb_node in val_to_rgb_nodes:
            Convert_Color_ramp_node(val_to_rgb_node,mat)
        
       
        for node_HSV in Cycles_HSV_nodes:
            Convert_HSV_node(node_HSV,mat)
        
        
        #Metall BSDF     
        #for Cycles_metallic in Cycles_metallic_nodes:

               

        
        
        
                
        

        
        Cycles_Translucent = False
        
        for Cycles_Translusency in Cycles_Translusency_nodes:
            BSDF_help = None
            for node_BSDF_help in Cycles_principled_nodes:
                if node_BSDF_help in Cycles_principled_nodes:
                   
                    BSDF_help = node_BSDF_help
                    
                    break
            
                
            node_name_parts = Cycles_Translusency.name.split('.')
            if len(node_name_parts) > 1:
                    
                    numeracja_trans = "."+ node_name_parts[1]
            else:
                # Handle the case where there's no dot in the name
                numeracja_trans = ""
                print("Node name does not contain a dot.")
                                    
                
            Luxcore_trans = False
            if hasattr(node_tree, 'nodes'):
                for node1 in node_tree.nodes:
                    if "Glossy Translucent Material" in node1.name and numeracja_trans in node1.name:
                        Luxcore_translucent = node1
                        Luxcore_trans = True
                        Cycles_Translucent = True
                        break
                if not Luxcore_trans:
                    bpy.context.object.active_material.luxcore.use_cycles_nodes = False 
                    Luxcore_translucent = lux_obj['lux_nodes'].new("LuxCoreNodeMatGlossyTranslucent")
                    Luxcore_translucent.label = "Material"

                    Luxcore_translucent.inputs[1].default_value = (Cycles_Translusency.inputs[0].default_value[0],Cycles_Translusency.inputs[0].default_value[1],Cycles_Translusency.inputs[0].default_value[2])
                                        
                    Luxcore_translucent.location = Cycles_Translusency.location
                    Luxcore_trans = True
                    Cycles_Translucent = True
                
                Luxcore_translucent.use_ior = True
                if BSDF_help:
                    Luxcore_translucent.inputs[0].default_value = (BSDF_help.inputs[0].default_value[0],BSDF_help.inputs[0].default_value[1],BSDF_help.inputs[0].default_value[2])
                    Luxcore_translucent.inputs[6].deafult_value = BSDF_help.inputs[2].default_value
                    Luxcore_translucent.inputs[14].default_value =  BSDF_help.inputs[4].default_value
                    Luxcore_translucent.inputs[3].default_value =  BSDF_help.inputs[3].default_value
                
                node_tree.links.new(Luxcore_translucent.outputs[0], Luxcore_output.inputs[0])
                Luxcore_output.location = (Luxcore_translucent.location[0]+300,Luxcore_translucent.location[1])

        Cycles_Glass = False  
        for Cycles_Glass_node in Cycles_Glass_nodes:
            BSDF_help = None
            for node_BSDF_help in Cycles_principled_nodes:
                if node_BSDF_help in Cycles_principled_nodes:
                   
                    BSDF_help = node_BSDF_help
                    break
            #print(BSDF_help.inputs[0].default_value)
                
            node_name_parts = Cycles_Glass_node.name.split('.')
            if len(node_name_parts) > 1:
                    
                    numeracja_glass = "."+ node_name_parts[1]
            else:
                # Handle the case where there's no dot in the name
                numeracja_glass = ""
                print("Node name does not contain a dot.")
                                    
                
            Luxcore_Glass = False
            if hasattr(node_tree, 'nodes'):
                for node1 in node_tree.nodes:
                    if "Glass Material" in node1.name and numeracja_glass in node1.name:
                        Luxcore_glass = node1
                        Luxcore_Glass = True
                        Cycles_Glass = True
                        break
                if not Luxcore_Glass:
                    bpy.context.object.active_material.luxcore.use_cycles_nodes = False 
                    Luxcore_glass = lux_obj['lux_nodes'].new("LuxCoreNodeMatGlass")


                   
                    Luxcore_glass.label = "Material"                    
                    Luxcore_glass.location = Cycles_Glass_node.location
                    Luxcore_Glass = True
                    Cycles_Glass = True
                
                #Luxcore_translucent.use_ior = True
                
                Luxcore_glass.inputs[0].default_value = (Cycles_Glass_node.inputs[0].default_value[0],Cycles_Glass_node.inputs[0].default_value[1],Cycles_Glass_node.inputs[0].default_value[2])
                if Cycles_Glass_node.inputs[1].default_value != 0:
                    
                    Luxcore_glass.inputs[6].default_value = Cycles_Glass_node.inputs[1].default_value
                    Luxcore_glass.rough = True
                else:
                    Luxcore_glass.rough = False
                Luxcore_glass.inputs[2].default_value = Cycles_Glass_node.inputs[2].default_value
                
                node_tree.links.new(Luxcore_glass.outputs[0], Luxcore_output.inputs[0])
                Luxcore_output.location = (Luxcore_glass.location[0]+300,Luxcore_glass.location[1])
        
                
        
        if not Cycles_Translucent and not Cycles_Glass:
            existing_mix_node_luxcore = None
            node_connection_done = False
            for Cycles_mix_shader in Cycles_ShaderMix_nodes:
                luxcore_name = Cycles_mix_shader.name.replace("Mix Shader", "Mix Material")
                
                existing_mix_node_luxcore = None
                if hasattr(node_tree, 'nodes'):
                    for n in node_tree.nodes:
                        if (n.bl_idname == "LuxCoreNodeMatMix" and luxcore_name in n.name and luxcore_name == n.name):
                            existing_mix_node_luxcore = n
                            node_connection_done = True
                            continue
                    if not existing_mix_node_luxcore:
                        existing_mix_node_luxcore = lux_obj['lux_nodes'].new("LuxCoreNodeMatMix")
                        existing_mix_node_luxcore.name = luxcore_name
                       
                        
                    # Sprawdź, czy oryginalny node Cycles jest podłączony do Material Output
                    is_connected_to_output = any(link.to_node.bl_idname == 'ShaderNodeOutputMaterial' for link in Cycles_mix_shader.outputs[0].links )    
                      
                    
                                        
                    existing_mix_node_luxcore.location = Cycles_mix_shader.location
                    
                    existing_mix_node_luxcore.inputs[2].default_value = Cycles_mix_shader.inputs[0].default_value
                    if not node_connection_done:
                       
                        if is_connected_to_output:
                            # Jeśli jest podłączony, użyj tego węzła do połączenia
                            if existing_mix_node_luxcore:
                                node_tree.links.new(existing_mix_node_luxcore.outputs[0], Luxcore_output.inputs[0])
                                Luxcore_output.location = (existing_mix_node_luxcore.location[0]+300, existing_mix_node_luxcore.location[1])
                               
                                node_connection_done = True
                                continue
                        else:
                            node_tree.links.new(existing_mix_node_luxcore.outputs[0], Luxcore_output.inputs[0])
                            Luxcore_output.location = (existing_mix_node_luxcore.location[0]+300,existing_mix_node_luxcore.location[1])
                           
                            node_connection_done = True
                    
            for Cycles_principled in Cycles_principled_nodes:
                Converted_Base_Material = Convert_BDSF_node(Cycles_principled,mat)
                
                node_c = Cycles_principled
                new_shader_Transmission = Cycles_principled.inputs["Transmission Weight"].default_value
                """
                node_c = Cycles_principled
                new_shader = Cycles_principled.location
                new_shader_Base_color = Cycles_principled.inputs["Base Color"].default_value
                new_shader_Metallic = Cycles_principled.inputs["Metallic"].default_value
                new_shader_Roughness = Cycles_principled.inputs["Roughness"].default_value
                new_shader_IOR = Cycles_principled.inputs["IOR"].default_value
                new_shader_opacity = Cycles_principled.inputs["Alpha"].default_value
                
                #Subsurface    
                new_shader_Base_Subsurface = Cycles_principled.inputs["Subsurface Weight"].default_value
                #Specular:
                new_shader_Specualar = Cycles_principled.inputs["Specular IOR Level"].default_value
                new_shader_Specualar_Tilt = Cycles_principled.inputs["Specular Tint"].default_value[0]
                #Anisotropic
                new_shader_Anisotropic = Cycles_principled.inputs["Anisotropic"].default_value
                new_shader_Anisotropic_rotation = Cycles_principled.inputs["Anisotropic Rotation"].default_value
                #Sheen
                new_shader_Sheen = Cycles_principled.inputs["Sheen Weight"].default_value
                new_shader_Sheen_tilt = Cycles_principled.inputs["Sheen Tint"].default_value[0]
                #Clearcoat
                new_shader_Clearcoat = Cycles_principled.inputs["Coat Weight"].default_value
                new_shader_clearcoat_Rougness = Cycles_principled.inputs["Coat Roughness"].default_value
                
                new_shader_Transmission = Cycles_principled.inputs["Transmission Weight"].default_value
                
                
                
                
                
                Luxcore_Converted_Base_Material = Cycles_principled.name.replace("Principled BSDF","Converted_Base_Material Material") 
                            
                if new_shader_Transmission == 0:
                                
                    Converted_Base_Material_shader = False
                    if hasattr(node_tree, 'nodes'):
                        for node1 in node_tree.nodes:
                            if "Converted_Base_Material Material" in node1.name and Luxcore_Converted_Base_Material in node1.name:
                                Converted_Base_Material = node1
                                Converted_Base_Material_shader = True
                                node_connection_done = True
                                
                                continue
                        if not Converted_Base_Material_shader:
                            bpy.context.object.active_material.luxcore.use_cycles_nodes = False 
                            Converted_Base_Material = lux_obj['lux_nodes'].new("LuxCoreNodeMatConverted_Base_Material")
                            Converted_Base_Material.name = Luxcore_Converted_Base_Material
                            Converted_Base_Material.label = Cycles_principled.label                    
                            Converted_Base_Material.location = new_shader
                            Converted_Base_Material_shader = True
                            Converted_Base_Material.inputs[0].default_value = (new_shader_Base_color[0], new_shader_Base_color[1], new_shader_Base_color[2]) 
                           
                            
                            
                    Converted_Base_Material.inputs[0].default_value = (new_shader_Base_color[0], new_shader_Base_color[1], new_shader_Base_color[2]) 
                    Converted_Base_Material.inputs[1].default_value = new_shader_Base_Subsurface
                    Converted_Base_Material.inputs[2].default_value = new_shader_Metallic  
                    Converted_Base_Material.inputs[3].default_value = new_shader_Specualar
                    Converted_Base_Material.inputs[4].default_value = new_shader_Specualar_Tilt
                    Converted_Base_Material.inputs[5].default_value = new_shader_Roughness
                    Converted_Base_Material.inputs[6].default_value = new_shader_Anisotropic
                    Converted_Base_Material.inputs[7].default_value = new_shader_Sheen
                    Converted_Base_Material.inputs[8].default_value = new_shader_Sheen_tilt
                    Converted_Base_Material.inputs[9].default_value = new_shader_Clearcoat
                    Converted_Base_Material.inputs[10].default_value = 1 - new_shader_clearcoat_Rougness
                    Converted_Base_Material.inputs[14].default_value = new_shader_opacity
                        
                        
                            
                        #node_tree.linksnew """
                       
                if new_shader_Transmission != 0:
                    Glass_Shader = False
                    if hasattr(node_tree, 'nodes'):
                        for node_g in node_tree.nodes:
                            if "LuxCoreNodeMatGlass" in node_g.bl_idname:
                                Converted_Base_Material = node_g
                                Glass_Shader = True
                                break
                        if not Glass_Shader:
                            bpy.context.object.active_material.luxcore.use_cycles_nodes = False 
                            Converted_Base_Material = lux_obj['lux_nodes'].new("LuxCoreNodeMatGlass")
                            Converted_Base_Material.location = new_shader
                            Converted_Base_Material.label = Cycles_principled.label
                            Glass_Shader = True
                            #break
                            
                        Converted_Base_Material.inputs[0].default_value = (new_shader_Base_color[0], new_shader_Base_color[1], new_shader_Base_color[2]) 
                        Converted_Base_Material.inputs[1].default_value = (new_shader_Base_color[0], new_shader_Base_color[1], new_shader_Base_color[2])
                        Converted_Base_Material.inputs[2].default_value = new_shader_IOR
                        if new_shader_Roughness != 0:
                            Converted_Base_Material.rough = True
                            Converted_Base_Material.inputs[6].default_value = new_shader_Roughness
                if Luxcore_output.inputs[0].links:
                    node_connection_done = True
                if not node_connection_done:
                           
                    node_tree.links.new(Converted_Base_Material.outputs[0], Luxcore_output.inputs[0])   
                    Luxcore_output.location = (Converted_Base_Material.location[0]+300,Converted_Base_Material.location[1])  
                    node_connection_done = True
                    
                           
        rebuild_Luxcore_connections(mat) 
        Connect_To_Material(mat)
        process_luxcore_nodes(mat)
                        
                


                                        
                                    
                                    

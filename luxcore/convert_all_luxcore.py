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



for material in bpy.data.materials:
    if not "Dot Stroke" in material.name:
        mat = material
        
        

        if hasattr(mat, 'node_tree'):
            active_material = mat
            c_nodes_tree = active_material.node_tree
            if hasattr(c_nodes_tree, 'nodes'):
                label_nodes_from_base_color(mat)
                remove_reroutes_from_material(mat)
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
                    continue
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
                Displacement_texture = [node for node in nodes if node.bl_idname.startswith("LuxCoreNodeTexImagemap") and node.label == "Displacement"]
                Displacement_node = [node for node in nodes if ("LuxCoreNodeShapeHeightDisplacement" in node.bl_idname or "LuxCoreNodeShapeVectorDisplacement" in node.bl_idname) and ("Displacement" in node.label or "COLOR * AO" in node.label)]
                Luxcore_output = [node for node in nodes if node.bl_idname.startswith("LuxCoreNodeMatOutput")]

                ao_texture = [node for node in nodes if node.bl_idname.startswith("LuxCoreNodeTexImagemap") and node.label == "AO"]
                ao_node = [node for node in nodes if node.bl_idname.startswith("LuxCoreNodeTexColorMix") and node.label == "Diffuse AO"]
                
                #Groups        
                for Cycles_Groups in Cycles_Node_Group:
                    Unpack_Shader_node_group(Cycles_Groups,mat) 
        
                # Curves Conversion:
                Cycles_curves = [node for node in c_nodes_tree.nodes if node.bl_idname == "ShaderNodeRGBCurve"]
                for cycles_curve in Cycles_curves:
                                             
                    Convert_Curve_node(cycles_curve,mat)
                
                for Cycles_invert in Cycles_Invert_Nodes:
                    #Luxcore_Invert_Name = Cycles_invert.name.replace("Invert Color","Invert")
                    existing_LuxCore_invert = None
                    for n in node_tree.nodes:
                        if n.bl_idname == "LuxCoreNodeTexInvert" and n.label == Cycles_invert.label:
                            existing_LuxCore_invert = n
                            break
                    if not existing_LuxCore_invert:
                        existing_LuxCore_invert = lux_obj['lux_nodes'].new("LuxCoreNodeTexInvert")
                        #existing_LuxCore_invert.name = Luxcore_Invert_Name
                    existing_LuxCore_invert.inputs[1].default_value = Cycles_invert.inputs[0].default_value
                    existing_LuxCore_invert.location = Cycles_invert.location
                    existing_LuxCore_invert.label = Cycles_invert.label
                blend_type_map = {
                    'MULTIPLY': 'scale',
                    'ADD': 'add',
                    'SUBTRACT': 'subtract'
                }
                for Cycles_mix_color_node in Cycles_Color_Mix:
                    if Cycles_mix_color_node.data_type == 'RGBA':
                        luxcore_mix_color_name = Cycles_mix_color_node.name.replace("Mix", "Color Math")
                        existing_luxcore_mix_color = None
                        for n in node_tree.nodes:
                            if n.bl_idname == "LuxCoreNodeTexColorMix" and n.name == luxcore_mix_color_name:
                                existing_luxcore_mix_color = n
                                break
                        if not existing_luxcore_mix_color:
                            existing_luxcore_mix_color = lux_obj['lux_nodes'].new("LuxCoreNodeTexColorMix")
                            existing_luxcore_mix_color.name = luxcore_mix_color_name
                        existing_luxcore_mix_color.location = Cycles_mix_color_node.location
                        existing_luxcore_mix_color.label = Cycles_mix_color_node.label
                        
                        existing_luxcore_mix_color.clamp_output = Cycles_mix_color_node.clamp_result
                        existing_luxcore_mix_color.mode = blend_type_map.get(Cycles_mix_color_node.blend_type, 'mix')
                        #Factor:
                        existing_luxcore_mix_color.inputs[0].default_value = Cycles_mix_color_node.inputs[0].default_value
                        #Colors:
                        existing_luxcore_mix_color.inputs[1].default_value = (Cycles_mix_color_node.inputs[6].default_value[0],Cycles_mix_color_node.inputs[6].default_value[1],Cycles_mix_color_node.inputs[6].default_value[2])
                        existing_luxcore_mix_color.inputs[2].default_value = (Cycles_mix_color_node.inputs[7].default_value[0],Cycles_mix_color_node.inputs[7].default_value[1],Cycles_mix_color_node.inputs[7].default_value[2])
                        
                        
                
                for Cycles_mapping in Cycles_Mapping_Nodes:
                    
                    luxcore_mapping_name = Cycles_mapping.name.replace("Mapping","2D Mapping")
                    existing_Luxcore_mapping = None
                    for n in node_tree.nodes:
                        if n.bl_idname == "LuxCoreNodeTexMapping2D" and n.name == luxcore_mapping_name:
                            existing_Luxcore_mapping = n
                            break
                    if not existing_Luxcore_mapping:
                        existing_Luxcore_mapping = lux_obj['lux_nodes'].new("LuxCoreNodeTexMapping2D")
                        existing_Luxcore_mapping.name = luxcore_mapping_name
                    existing_Luxcore_mapping.location = Cycles_mapping.location
                    existing_Luxcore_mapping.label = Cycles_mapping.label
                    unifrom_scale = False
                    
                    uv_name = False
                    for uv in c_nodes_tree.nodes:
                        print(uv.bl_idname)
                        if "ShaderNodeUVMap" in uv.bl_idname:
                            print("UVMap siema")
                            for output in uv.outputs:
                           # Iteruj przez wszystkie linki tego wyjścia
                                for link in output.links:
                                    # Sprawdź, czy link prowadzi do noda Cycles_mapping
                                    if link.to_node == Cycles_mapping:
                                        print("eee")
                                        Nazwa_UV = uv.uv_map
                                        uv_name = True
                    
                    if Cycles_mapping.inputs[3].default_value[0] == Cycles_mapping.inputs[3].default_value[1]:
                        existing_Luxcore_mapping.use_uniform_scale = True
                        existing_Luxcore_mapping.uniform_scale = Cycles_mapping.inputs[3].default_value[0]
                    else:
                        existing_Luxcore_mapping.use_uniform_scale = False
                        existing_Luxcore_mapping.uscale = Cycles_mapping.inputs[3].default_value[0]
                        existing_Luxcore_mapping.vscale = Cycles_mapping.inputs[3].default_value[1]
                    if uv_name:
                        existing_Luxcore_mapping.uvmap = Nazwa_UV
                    existing_Luxcore_mapping.rotation = Cycles_mapping.inputs[2].default_value[0]
                    existing_Luxcore_mapping.udelta = Cycles_mapping.inputs[1].default_value[0]
                    existing_Luxcore_mapping.vdelta = Cycles_mapping.inputs[1].default_value[1]
                
                if Luxcore_output:
                    Luxcore_output = Luxcore_output[0]
                else:
                    Luxcore_output = nodes.new("LuxCoreNodeMatOutput")
                    Luxcore_output.label = "Luxcore Output"
                    


                counter = 0
                for Cycles_Bump in Cycles_Bump_nodes:
                    luxcore_bump_name = Cycles_Bump.name
                    existing_lux_bump = None
                    for n in node_tree.nodes:
                        print(f"Checking LuxCore node: {n.name}")
                        if n.bl_idname == "LuxCoreNodeTexBump" and n.name == luxcore_bump_name:
                            print(f"Found matching LuxCore node: {n.name}")
                            existing_lux_bump = n
                            break
                    
                    # Jeśli nie znaleziono, utwórz nowy węzeł
                    if not existing_lux_bump:
                        print(f"Creating new LuxCore node: {luxcore_bump_name}")
                        existing_lux_bump = lux_obj['lux_nodes'].new("LuxCoreNodeTexBump")
                        existing_lux_bump.name = luxcore_bump_name
                        print(f"Created LuxCore node with name: {existing_lux_bump.name}")
                    
                    # Ustawienia węzła
                    existing_lux_bump.label = Cycles_Bump.label
                    existing_lux_bump.location = Cycles_Bump.location
                    existing_lux_bump.inputs[1].default_value = Cycles_Bump.inputs[1].default_value
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
                        
                    
                counter = 0
                print(val_to_rgb_nodes)
                for val_to_rgb_node in val_to_rgb_nodes:
                    interpolation_map = {'CONSTANT': 'none', 'B_SPLINE': 'linear', 'LINEAR': 'linear', 'EASE': 'cubic'}
                    node_c = val_to_rgb_node.color_ramp
                    Color_ramp_location = val_to_rgb_node.location
                    cycles_interpolation = node_c.interpolation
                    pos_1 = node_c.elements[0].position
                    color_1 = node_c.elements[0].color
                    pos_2 = node_c.elements[1].position
                    color_2 = node_c.elements[1].color
                    num_elements = len(node_c.elements)
                    # Check if ColorRamp has more than two color stops
                    if num_elements >= 2:
                        # Check if LuxCore ColorRamp node already exists
                        Luxcore_colorramp_exists = False
                        if hasattr(node_tree, 'nodes'):
                            for node1 in node_tree.nodes:
                                if "ColorRampLux" in node1.name and node1.name.endswith(val_to_rgb_node.name.split(".")[-1]):
                                    ColorRampLux = node1
                                    Luxcore_colorramp_exists = True
                                    break
                        # If LuxCore ColorRamp node doesn't exist, create one
                        if not Luxcore_colorramp_exists:
                            bpy.context.object.active_material.luxcore.use_cycles_nodes = False
                            ColorRampLux = lux_obj['lux_nodes'].new("LuxCoreNodeTexBand")
                            ColorRampLux.name = "ColorRampLux." + val_to_rgb_node.name.split(".")[-1]
                            ColorRampLux.location = Color_ramp_location
                            ColorRampLux.interpolation = interpolation_map.get(cycles_interpolation, 'none')
                            #counter += 1
                            
                        ColorRampLux.label = val_to_rgb_node.label

                        ColorRampLux.ramp_items[0].offset = pos_1
                        ColorRampLux.ramp_items[0].value = (color_1[0], color_1[1], color_1[2])

                        ColorRampLux.ramp_items[1].offset = pos_2
                        ColorRampLux.ramp_items[1].value = (color_2[0], color_2[1], color_2[2])

                        # Add input nodes to LuxCore ColorRamp node for each additional color stop
                        for i in range(2, num_elements):
                            element = node_c.elements[i]
                            ColorRampLux.add_item = False
                            ramp_item = ColorRampLux.ramp_items[-1]
                            ramp_item.offset = element.position
                            ramp_item.value = (element.color[0], element.color[1], element.color[2])
                
                existing_lux_hsv = None
                for node_HSV in Cycles_HSV_nodes:
                    print(f"Processing Cycles node: {node_HSV.name}, label: {node_HSV.label}")
                    luxcore_hsv_name = node_HSV.name.replace("Hue/Saturation/Value", "Hue Saturation Value")
                    print(f"Generated LuxCore name: {luxcore_hsv_name}")
                    
                    # Sprawdź, czy istnieje węzeł LuxCore o takiej nazwie
                    existing_lux_hsv = None
                    for n in node_tree.nodes:
                        print(f"Checking LuxCore node: {n.name}")
                        if n.bl_idname == "LuxCoreNodeTexHSV" and n.name == luxcore_hsv_name:
                            print(f"Found matching LuxCore node: {n.name}")
                            existing_lux_hsv = n
                            break
                    
                    # Jeśli nie znaleziono, utwórz nowy węzeł
                    if not existing_lux_hsv:
                        print(f"Creating new LuxCore node: {luxcore_hsv_name}")
                        existing_lux_hsv = lux_obj['lux_nodes'].new("LuxCoreNodeTexHSV")
                        existing_lux_hsv.name = luxcore_hsv_name
                        print(f"Created LuxCore node with name: {existing_lux_hsv.name}")
                    
                    # Ustawienia węzła
                    existing_lux_hsv.label = node_HSV.label
                    existing_lux_hsv.location = node_HSV.location
                    if len(node_HSV.inputs) >= 3 and len(existing_lux_hsv.inputs) >= 4:
                        existing_lux_hsv.inputs[1].default_value = node_HSV.inputs[0].default_value
                        existing_lux_hsv.inputs[2].default_value = node_HSV.inputs[1].default_value
                        existing_lux_hsv.inputs[3].default_value = node_HSV.inputs[2].default_value

                       

                
                
                
                        
                

                
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
                        
                        
                        
                        
                        
                        Luxcore_Disney = Cycles_principled.name.replace("Principled BSDF","Disney Material") 
                                    
                        if new_shader_Transmission == 0:
                                        
                            Disney_shader = False
                            if hasattr(node_tree, 'nodes'):
                                for node1 in node_tree.nodes:
                                    if "Disney Material" in node1.name and Luxcore_Disney in node1.name:
                                        Disney = node1
                                        Disney_shader = True
                                        node_connection_done = True
                                        
                                        continue
                                if not Disney_shader:
                                    bpy.context.object.active_material.luxcore.use_cycles_nodes = False 
                                    Disney = lux_obj['lux_nodes'].new("LuxCoreNodeMatDisney")
                                    Disney.name = Luxcore_Disney
                                    Disney.label = Cycles_principled.label                    
                                    Disney.location = new_shader
                                    Disney_shader = True
                                    Disney.inputs[0].default_value = (new_shader_Base_color[0], new_shader_Base_color[1], new_shader_Base_color[2]) 
                                   
                                    
                                    
                            Disney.inputs[0].default_value = (new_shader_Base_color[0], new_shader_Base_color[1], new_shader_Base_color[2]) 
                            Disney.inputs[1].default_value = new_shader_Base_Subsurface
                            Disney.inputs[2].default_value = new_shader_Metallic  
                            Disney.inputs[3].default_value = new_shader_Specualar
                            Disney.inputs[4].default_value = new_shader_Specualar_Tilt
                            Disney.inputs[5].default_value = new_shader_Roughness
                            Disney.inputs[6].default_value = new_shader_Anisotropic
                            Disney.inputs[7].default_value = new_shader_Sheen
                            Disney.inputs[8].default_value = new_shader_Sheen_tilt
                            Disney.inputs[9].default_value = new_shader_Clearcoat
                            Disney.inputs[10].default_value = 1 - new_shader_clearcoat_Rougness
                            Disney.inputs[14].default_value = new_shader_opacity
                                
                                
                                    
                                #node_tree.linksnew 
                               
                        if new_shader_Transmission != 0:
                            Glass_Shader = False
                            if hasattr(node_tree, 'nodes'):
                                for node_g in node_tree.nodes:
                                    if "LuxCoreNodeMatGlass" in node_g.bl_idname:
                                        Disney = node_g
                                        Glass_Shader = True
                                        break
                                if not Glass_Shader:
                                    bpy.context.object.active_material.luxcore.use_cycles_nodes = False 
                                    Disney = lux_obj['lux_nodes'].new("LuxCoreNodeMatGlass")
                                    Disney.location = new_shader
                                    Disney.label = Cycles_principled.label
                                    Glass_Shader = True
                                    #break
                                    
                                Disney.inputs[0].default_value = (new_shader_Base_color[0], new_shader_Base_color[1], new_shader_Base_color[2]) 
                                Disney.inputs[1].default_value = (new_shader_Base_color[0], new_shader_Base_color[1], new_shader_Base_color[2])
                                Disney.inputs[2].default_value = new_shader_IOR
                                if new_shader_Roughness != 0:
                                    Disney.rough = True
                                    Disney.inputs[6].default_value = new_shader_Roughness
                        if Luxcore_output.inputs[0].links:
                            node_connection_done = True
                        if not node_connection_done:
                                   
                            node_tree.links.new(Disney.outputs[0], Luxcore_output.inputs[0])   
                            Luxcore_output.location = (Disney.location[0]+300,Disney.location[1])  
                            node_connection_done = True
                            
                                   
                rebuild_Luxcore_connections(mat) 
                Connect_To_Material(mat)
                process_luxcore_nodes(mat)
                    

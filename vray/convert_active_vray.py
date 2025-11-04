import bpy
import os
import math
import sys


## Import ##
script_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if script_folder not in sys.path:
    sys.path.append(script_folder)
convert_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "converter"))
if convert_folder not in sys.path:
    sys.path.append(convert_folder)
    
preferences = bpy.context.preferences.addons["Material_Converter 1"].preferences

from rebuild import rebuild_vray_connections
from connect_nodes import (connect_to_closest_Vray_mat,Connect_Vray_Mapping_Node,Connect_To_Material,reorganize_material_nodes)
from premade import (label_nodes_from_base_color,set_labels_recursive)
from nodes import (setup_disp_nodes,setup_ao_nodes,setup_disp_nodes)
from vray_tools import (Change_Vray_outputs,split_object_by_material)

#Import Node Conversion 
from convert_curve import Convert_Curve_node
from convert_images import Convert_image_node
from ConvertHSVNode import Convert_HSV_node
from ConvertColorRampNode import Convert_Color_ramp_node
from Convert_Mapping_node import Convert_Mapping_node
from Convert_Invert import Convert_Invert_node
from Convert_Color_Mix_node import Convert_ColorMix_node
from Convert_Brighntess_Contrast import Convert_brs_cst_node
from Convert_BDSF import Convert_BDSF_node
from Shader_node_group import Unpack_Shader_node_group


#bpy.context.scene.render.engine = 'VRAY_RENDER_RT'
Render_Engine = bpy.context.scene.render.engine
current_workspace = bpy.context.workspace
for screen in current_workspace.screens:
    for area in screen.areas:
        if area.type == 'NODE_EDITOR'and not area.ui_type in ["GeometryNodeTree", "CompositorNodeTree"]:
            area.ui_type = 'VRayNodeTreeEditor'
            

mat = bpy.context.object.active_material
obj = bpy.context.object

label_nodes_from_base_color(mat)
def get_object_with_material(objects, target_material):
    """Find an object that has the target_material assigned."""
    if not objects:  # Check if the objects list is empty
        print("No objects to check.")
        return None
    
    for obj in objects:
        for mat in obj.data.materials:
            if mat and mat.name == target_material:  # Added check if mat exists
                return obj
    return None




if hasattr(mat, 'node_tree'):
    active_material_name = mat.name
    active_material = mat
    active_material.vray.is_vray_class = True
    c_nodes_tree = active_material.node_tree
    if hasattr(c_nodes_tree, 'nodes'):
        c_nodes = c_nodes_tree.nodes
        nodes = c_nodes_tree.nodes
        links = c_nodes_tree.links
        color = []
        color.append(mat.diffuse_color[0])
        color.append(mat.diffuse_color[1])
        color.append(mat.diffuse_color[2])
        color.append(mat.diffuse_color[3])
        Cycles_Node_Group = [node for node in c_nodes if node.bl_idname == "ShaderNodeGroup"]
        Cycles_Images_nodes = [node for node in nodes if node.bl_idname.startswith("ShaderNodeTexImage")]
        Cycles_Output_nodes = [node for node in nodes if node.bl_idname.startswith("ShaderNodeMaterialOutput")]
        Cycles_Translusency_nodes = [node for node in nodes if node.bl_idname.startswith("ShaderNodeBsdfTranslucent")]
        Cycles_principled_nodes = [node for node in nodes if node.bl_idname.startswith("ShaderNodeBsdfPrincipled")]
        Cycles_Color_Mix = [node for node in nodes if node.bl_idname == "ShaderNodeMix"]
        Cycles_Glass_nodes = [node for node in nodes if node.bl_idname.startswith("ShaderNodeBsdfGlass")]
        Cycles_ShaderMix_nodes = [node for node in nodes if node.bl_idname == "ShaderNodeMixShader"]
        Cycles_HSV_nodes = [node for node in nodes if node.bl_idname.startswith("ShaderNodeHueSaturation")]
        val_to_rgb_nodes = [node for node in nodes if node.bl_idname.startswith("ShaderNodeValToRGB")]
        Cycles_Bump_nodes = [node for node in nodes if node.bl_idname.startswith("ShaderNodeBump")]
        Cycles_Mapping_Nodes = [node for node in nodes if node.bl_idname.startswith("ShaderNodeMapping")]
        Cycles_Invert_Nodes = [node for node in nodes if node.bl_idname.startswith("ShaderNodeInvert")]
        Cycles_Normal_Nodes = [node for node in nodes if node.bl_idname.startswith("ShaderNodeNormalMap")]
        Cycles_Displacement = [node for node in nodes if node.bl_idname.startswith("ShaderNodeDisplacement")]
        Cycles_curves = [node for node in nodes if node.bl_idname == "ShaderNodeRGBCurve"]
        Cycles_Brightness_Contrast_nodes = [node for node in nodes if node.bl_idname.startswith("ShaderNodeBrightContrast")]
        for cycles_curve in Cycles_curves:
                                             
            Convert_Curve_node(cycles_curve,mat)
        Cycles_gloss = next(
            (node for node in Cycles_Images_nodes if "gloss" in node.image.name.lower()),
            None
        )
        
        Vray_output = None
        
        #Groups        
        for Cycles_Groups in Cycles_Node_Group:
            Unpack_Shader_node_group(Cycles_Groups,mat)    
            
        for Vray_output_node in nodes:
            if Vray_output_node.bl_idname == "VRayNodeOutputMaterial":
                Vray_output = Vray_output_node
        if not Vray_output:
            Vray_output = nodes.new("VRayNodeOutputMaterial")
        
        for Cycles_Image in Cycles_Images_nodes:
            Convert_image_node(Cycles_Image,mat)
            
        for Cycles_Brightness_Contrast in Cycles_Brightness_Contrast_nodes:
            Convert_brs_cst_node(Cycles_Brightness_Contrast,mat)
            
        
        Displacement_node = None
        Displacement_texture = [
            node for node in nodes 
            if node.bl_idname.startswith("VRayNodeMetaImageTexture") and 
            any(z in node.label for z in ("Displacement", "DISP")) 
        ]
        # Główny kod
        if Displacement_texture:
            Displacement_texture = Displacement_texture[0]
            
            if len(obj.data.materials) > 1:
                new_objects = split_object_by_material(obj)
                # Znajdź obiekt o nazwie zawierającej nazwę aktywnego materiału
                target_object = next((o for o in new_objects if active_material_name in o.name), None)
                
                if target_object:
                    bpy.context.view_layer.objects.active = target_object
                    target_object.select_set(True)
                    Disp_node = setup_disp_nodes(preferences, Render_Engine, nodes, links, Displacement_texture, Displacement_node)
            else:
                Disp_node = setup_disp_nodes(preferences, Render_Engine, nodes, links, Displacement_texture, Displacement_node)
                print("Nasz Dispalcement: ",Displacement_node)
            if Cycles_Displacement:
                Cycles_Displacement = Cycles_Displacement[0]
                # Pobranie inputów Scale i Height
                scale_input = Cycles_Displacement.inputs.get("Scale")
                height_input = Cycles_Displacement.inputs.get("Height")
                
                # Pobranie wartości z niepodłączonego inputu (jeśli istnieje)
                displacement_amount_value = None
                if scale_input and not scale_input.is_linked:
                    Disp_node.inputs["Displacement Amount"].value = scale_input.default_value
                elif height_input and not height_input.is_linked:
                   Disp_node.inputs["Displacement Amount"].value = height_input.default_value
                
                Disp_node.inputs["Displacement Shift"].value = Cycles_Displacement.inputs["Midlevel"].default_value
            
        for Cycles_invert in Cycles_Invert_Nodes:
            # Sprawdź połączenia z glossem lub Roughness
            is_gloss_connected = (
                Cycles_gloss and 
                any(link.from_node == Cycles_invert for link in Cycles_gloss.outputs[0].links)
            )
            
            is_roughness_connected = any(
                link.from_node == Cycles_invert and 
                link.to_socket.name == "Roughness" 
                for node in Cycles_principled_nodes 
                for link in node.inputs["Roughness"].links
            )
            
            # Jeśli node nie jest połączony z glossem lub Roughness
            if not (is_gloss_connected or is_roughness_connected):
                          
                Convert_Invert_node(Cycles_invert,mat)
        blend_type_map = {
            'MULTIPLY': 'scale',
            'ADD': 'add',
            'SUBTRACT': 'subtract'
        }
        for Cycles_mix_color_node in Cycles_Color_Mix:
            if Cycles_mix_color_node.data_type == 'RGBA':
                Convert_ColorMix_node(Cycles_mix_color_node,mat)
              
                    
                    
                    
               
        
        for Cycles_mapping in Cycles_Mapping_Nodes:
            Convert_Mapping_node(Cycles_mapping,mat)
                
        for Cycles_Normal in Cycles_Normal_Nodes:
            Vray_normal = None
            Vray_normal_name = Cycles_Normal.name.replace("Normal Map","V-Ray Normal Map")
            for n in nodes:
                if n.bl_idname == "VRayNodeTexNormalMapFlip" and Vray_normal_name == n.name:
                    Vray_normal = n
                    continue
            if not Vray_normal:
                Vray_normal = nodes.new("VRayNodeTexNormalMapFlip")
                Vray_normal.label = Cycles_Normal.label
                Vray_normal.location = (Cycles_Normal.location[0], Cycles_Normal.location[1] - 1650)
                Vray_normal.name = Vray_normal_name
            
                
            
            


        
        
        
        for val_to_rgb_node in val_to_rgb_nodes:
            Convert_Color_ramp_node(val_to_rgb_node,mat)
        for node_HSV in Cycles_HSV_nodes:
            Convert_HSV_node(node_HSV,mat)
       
        Cycles_Translucent = False
        
        for Cycles_Translusency in Cycles_Translusency_nodes:
            Cycles_Translucent = True
            BSDF_help = None
            for node_BSDF_help in Cycles_principled_nodes:
                if node_BSDF_help in Cycles_principled_nodes:
                   
                    BSDF_help = node_BSDF_help
                    
                    break
            Mix_Node_Translusency = None 
            for output in Cycles_Translusency.outputs:
                for link in output.links:
                    # Sprawdź, czy link prowadzi do ShaderNodeMixShader
                    if link.to_node.bl_idname == "ShaderNodeMixShader":
                        Mix_Node_Translusency = link.to_node
                        break
              
            
                
            Vray_Translusency_Name = Cycles_Translusency.name.replace("Translucent BSDF","V-Ray Mtl")
            Vray_Translusency = None
            
            
            for n in nodes:
                if n.bl_idname == "VRayNodeBRDFVRayMtl" and n.name == Vray_Translusency_Name:
                    Vray_Translusency = n
                    continue
            if not Vray_Translusency:
                Vray_Translusency = nodes.new("VRayNodeBRDFVRayMtl")
                Vray_Translusency.location = (Cycles_Translusency.location[0] - 200 , Cycles_Translusency.location[1] - 1650) 
                Vray_Translusency.label = Cycles_Translusency.label
                Vray_Translusency.name = Vray_Translusency_Name
                
            Vray_Translusency.inputs[49].value = Cycles_Translusency.inputs[0].default_value[:3]
            
            #Vray_output
            c_nodes_tree.links.new(Vray_Translusency.outputs[0],Vray_output.inputs[0])
            Vray_output.location = (Vray_Translusency.location[0] + 300, Vray_Translusency.location[1])
            
            if Mix_Node_Translusency:
                
                Vray_Translusency.inputs[51].value = Mix_Node_Translusency.inputs[0].default_value
            
            if BSDF_help:
                #Alpha    
                Vray_Translusency.inputs[1].value = (BSDF_help.inputs[4].default_value,)*3 
                #Diffuse
                Vray_Translusency.inputs[3].value = BSDF_help.inputs[0].default_value[:3]
                #Ilumination
                Vray_Translusency.inputs[6].value = BSDF_help.inputs[26].default_value[:3] if BSDF_help.inputs[27].default_value != 0 else (0,0,0)
            
                #Glossiness
                Vray_Translusency.inputs[11].value = 1 - BSDF_help.inputs[2].default_value
                
                #Fresnel IOR
                Vray_Translusency.inputs[14].value =  BSDF_help.inputs[3].default_value
                
                #Metalness
                Vray_Translusency.inputs[16].value =  BSDF_help.inputs[1].default_value
                
                if BSDF_help.inputs[5].is_linked:
                    linked_node = BSDF_help.inputs[5].links[0].from_node
                    if linked_node.bl_idname == 'ShaderNodeNormalMap':
                        # Użyj wartości z Normal Map node
                        normal_value = linked_node.inputs[0].default_value
                       
                        Vray_Translusency.inputs[69].value = normal_value 
                    elif linked_node.bl_idname == "ShaderNodeBump":
                        normal_value = linked_node.inputs[0].default_value
                        Vray_Translusency.inputs[69].value = normal_value 
            
            
        Cycles_Glass = False  
        for Cycles_Glass_node in Cycles_Glass_nodes:
            Cycles_Glass = True
            BSDF_help = None
            for node_BSDF_help in Cycles_principled_nodes:
                if node_BSDF_help in Cycles_principled_nodes:
                   
                    BSDF_help = node_BSDF_help
                    break
            Glass_Vray_Name = Cycles_Glass_node.name.replace("Glass BSDF","V-Ray Mtl")
            Vray_Glass = None
            for n in nodes:
                if n.bl_idname == "VRayNodeBRDFVRayMtl" and n.name == Glass_Vray_Name:
                    Vray_Glass = n
                    continue
            if not Vray_Glass:
                
                Vray_Glass = nodes.new("VRayNodeBRDFVRayMtl")
                Vray_Glass.location = (Cycles_Glass_node.location[0] - 200 , Cycles_Glass_node.location[1] - 1650) 
                Vray_Glass.label = Cycles_Glass_node.label
                Vray_Glass.name = Glass_Vray_Name
                
            Vray_Glass.inputs[36].value = Cycles_Glass_node.inputs[0].default_value[:3]
            
            #Glossiness
            Vray_Glass.inputs[38].value = 1 - Cycles_Glass_node.inputs[1].default_value
            
            #Refraction IOR
            Vray_Glass.inputs[37].value = 1 - Cycles_Glass_node.inputs[2].default_value
            
            c_nodes_tree.links.new(Vray_Glass.outputs[0],Vray_output.inputs[0])
            Vray_output.location = (Vray_Glass.location[0] + 300, Vray_Glass.location[1])
                    
            
            
            if BSDF_help:
                
            
                #Alpha    
                Vray_Glass.inputs[1].value = (BSDF_help.inputs[4].default_value,)*3    
            
                
            
                #Ilumination
                Vray_Glass.inputs[6].value = BSDF_help.inputs[26].default_value[:3] if BSDF_help.inputs[27].default_value != 0 else (0,0,0)
            
                                
                #Metalness
                Vray_Glass.inputs[16].value =  BSDF_help.inputs[1].default_value
                
                if BSDF_help.inputs[5].is_linked:
                    linked_node = BSDF_help.inputs[5].links[0].from_node
                    Vray_Glass.inputs[69].value = linked_node.inputs[0].default_value if linked_node.bl_idname in ["ShaderNodeNormalMap", "ShaderNodeBump"] else 1
                    
            if Cycles_Glass_node.inputs[3].is_linked:
                linked_normal = Cycles_Glass_node.inputs[3].links[0].from_node
                Vray_Glass.inputs[72].value = linked_normal.inputs[0].default_value if linked_normal.bl_idname in ["ShaderNodeNormalMap", "ShaderNodeBump"] else 1
                
            
        if not Cycles_Translucent and not Cycles_Glass:
            
            Layered_Material = None
            for Mix_Shader_Node in Cycles_ShaderMix_nodes:
                                
                Layered_Material = Mix_Shader_Node
                break
                
            if Layered_Material:
                Layered_Vray_Mtl = None
                
               
                for n in nodes:
                    if n.bl_idname == "VRayNodeBRDFLayered":
                        Layered_Vray_Mtl = n
                if not Layered_Vray_Mtl:
                    Layered_Vray_Mtl = nodes.new("VRayNodeBRDFLayered")
                    Layered_Vray_Mtl.location = (Layered_Material.location[0] - 200 , Layered_Material.location[1] - 1650) 
                    
                c_nodes_tree.links.new(Layered_Vray_Mtl.outputs[0],Vray_output.inputs[0])
                Vray_output.location = (Layered_Vray_Mtl.location[0] + 300, Layered_Vray_Mtl.location[1])
                
                for Cycles_principled in Cycles_principled_nodes:
                    Converted_Base_Material = Convert_BDSF_node(Cycles_principled, c_nodes_tree)
                    if Cycles_Normal_Nodes:
                        if Cycles_Normal_Nodes[0].space == "TANGENT":
                            Converted_Base_Material.inputs[70].value = '1'
                        if Cycles_Normal_Nodes[0].space == "OBJECT":
                            Converted_Base_Material.inputs[70].value = '2'
                        if Cycles_Normal_Nodes[0].space == "WORLD":
                            Converted_Base_Material.inputs[70].value = '4'
                            
                            
                    if Converted_Base_Material.label == "Material":
                        # Connect Material to BRDF 1
                        for input_name in Layered_Vray_Mtl.inputs:
                            if input_name.name == "Base Material":
                                c_nodes_tree.links.new(Converted_Base_Material.outputs[0], input_name)
                                break
                    elif Converted_Base_Material.label == "Material 1":
                        # Connect Material 1 to BRDF 2
                        for input_name in Layered_Vray_Mtl.inputs:
                            if input_name.name == "Coat Material 1":
                                c_nodes_tree.links.new(Converted_Base_Material.outputs[0], input_name)
                                break

                    elif Converted_Base_Material.label in ("Material 2", "Material 3", "Material 4", "Material 5"):
                        # Extract the number from Material X
                        material_num = int(Converted_Base_Material.label.split()[-1])
                        brdf_name = f"Coat Material {material_num + 1}"
                        
                        # Check if BRDF exists
                        brdf_exists = False
                        for input_name in Layered_Vray_Mtl.inputs:
                            if input_name.name == brdf_name:
                                brdf_exists = True
                                c_nodes_tree.links.new(Converted_Base_Material.outputs[0], input_name)
                                break
                        
                        if not brdf_exists:
                            
                            # Create and connect BRDF socket
                            brdf_socket = Layered_Vray_Mtl.inputs.new('VRaySocketBRDF', brdf_name)
                            c_nodes_tree.links.new(Converted_Base_Material.outputs[0], brdf_socket)
                            # Create Weight socket first (wymagane przez V-Ray, ale bez połączenia)
                            Layered_Vray_Mtl.inputs.new('VRaySocketWeight', f'Weight {material_num + 1}')
                                
            
            
                
                
            if not Layered_Material:
                for Cycles_principled in Cycles_principled_nodes:
                    node_c = Cycles_principled
                            
                    #if Cycles_principled.inputs[7].default_value == 0:
                    Converted_Base_Material = Convert_BDSF_node(Cycles_principled, mat)
                    c_nodes_tree.links.new(Converted_Base_Material.outputs[0],Vray_output.inputs[0])
                    Vray_output.location = (Converted_Base_Material.location[0] + 300, Converted_Base_Material.location[1])
                    if Cycles_Normal_Nodes:
                        if Cycles_Normal_Nodes[0].space == "TANGENT":
                            Converted_Base_Material.inputs[70].value = '1'
                        if Cycles_Normal_Nodes[0].space == "OBJECT":
                            Converted_Base_Material.inputs[70].value = '2'
                        if Cycles_Normal_Nodes[0].space == "WORLD":
                            Converted_Base_Material.inputs[70].value = '4'
                            
                    
                        
                   
        rebuild_vray_connections(mat)
        Connect_To_Material(mat)
        Change_Vray_outputs(mat)
        Connect_Vray_Mapping_Node(mat)
        reorganize_material_nodes(mat, Render_Engine)

                
                    
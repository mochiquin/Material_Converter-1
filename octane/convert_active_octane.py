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
Chosen_material = preferences.octane_preferences.octane_base_material
displacement_type = preferences.octane_preferences.octane_displacement_mode 

from rebuild import rebuild_octane_connections
from connect_nodes import (connect_to_closest_octane_group_node,Connect_To_Material,Connect_Vray_Mapping_Node)
from premade import (label_nodes_from_base_color,set_labels_recursive,remove_reroutes_from_material)

#Import Node Conversion 
from convert_curve import Convert_Curve_node
from convert_images import Convert_image_node
from Shader_node_group import Unpack_Shader_node_group



Render_engine = bpy.context.scene.render.engine
if Render_engine != 'octane':
    bpy.context.scene.view_settings.view_transform = 'Raw'
    bpy.context.scene.view_settings.look = 'None'
    bpy.context.scene.render.engine = "octane"

current_workspace = bpy.context.workspace
for screen in current_workspace.screens:
    for area in screen.areas:
        if area.type == 'NODE_EDITOR'and not area.ui_type in ["GeometryNodeTree", "CompositorNodeTree"]:
            area.ui_type = 'ShaderNodeTree'


def Convert_Universal_Material(cycles_principled, c_nodes_tree):
     
        Octane_material_name = cycles_principled.name.replace("Principled BSDF", "Universal material")

        Universal_node = None
        for n in c_nodes_tree.nodes:
            if n.bl_idname == "OctaneUniversalMaterial" and n.name == Octane_material_name:
                Universal_node = n
                break  # Dodano break, aby przerwać pętlę po znalezieniu noda

        if not Universal_node:
            Universal_node = c_nodes_tree.nodes.new("OctaneUniversalMaterial")
            Universal_node.location = (cycles_principled.location[0] +1650, cycles_principled.location[1] - 0)
            Universal_node.label = cycles_principled.label
            Universal_node.name = Octane_material_name

        
        new_shader_Base_color = cycles_principled.inputs["Base Color"].default_value
        new_shader_Metallic = cycles_principled.inputs["Metallic"].default_value
        new_shader_Roughness = cycles_principled.inputs["Roughness"].default_value
        new_shader_IOR = cycles_principled.inputs["IOR"].default_value
        new_shader_opacity = cycles_principled.inputs["Alpha"].default_value
                
        #Subsurface    
        new_shader_Base_Subsurface = cycles_principled.inputs["Subsurface Weight"].default_value
        #Specular:
        new_shader_Specualar = cycles_principled.inputs["Specular IOR Level"].default_value
        new_shader_Specualar_Tilt = cycles_principled.inputs["Specular Tint"].default_value[0]
        #Anisotropic
        new_shader_Anisotropic = cycles_principled.inputs["Anisotropic"].default_value
        new_shader_Anisotropic_rotation = cycles_principled.inputs["Anisotropic Rotation"].default_value
        #Sheen
        new_shader_Sheen = cycles_principled.inputs["Sheen Weight"].default_value
        new_shader_Sheen_tilt = cycles_principled.inputs["Sheen Tint"].default_value[:3]
        new_shader_Sheen_Roughness = cycles_principled.inputs["Sheen Roughness"].default_value
        #Clearcoat
        new_shader_Clearcoat = cycles_principled.inputs["Coat Weight"].default_value
        new_shader_Clearcoat_Tilt = cycles_principled.inputs["Coat Tint"].default_value[:3]
        new_shader_clearcoat_Rougness = cycles_principled.inputs["Coat Roughness"].default_value
        new_shader_clearcoat_IOR = cycles_principled.inputs["Coat IOR"].default_value
        #Transmission
        new_shader_Transmission = cycles_principled.inputs["Transmission Weight"].default_value
        #Thin Film:
        new_shader_Thin_Film_Thickness = cycles_principled.inputs["Thin Film Thickness"].default_value
        new_shader_Thin_Film_IOR = cycles_principled.inputs["Thin Film IOR"].default_value

        # Diffuse:
        Universal_node.inputs[5].default_value = new_shader_Base_color[:3]
        #Metallic:
        Universal_node.inputs[7].default_value = new_shader_Metallic
        #Specular:
        Universal_node.inputs[10].default_value = min(new_shader_Specualar*preferences.octane_preferences.octane_specular_multipler,1)
        #Roughness
        Universal_node.inputs[13].default_value = new_shader_Roughness
        #Anisotropy:
        Universal_node.inputs[14].default_value = new_shader_Anisotropic
        #Anisotropy Rotation:
        Universal_node.inputs[15].default_value = new_shader_Anisotropic_rotation
        #IOR
        Universal_node.inputs[18].default_value = new_shader_IOR
        #Coat
        if new_shader_Clearcoat != 0:
            Universal_node.inputs[26].default_value = new_shader_Clearcoat_Tilt
            Universal_node.inputs[28].default_value = new_shader_clearcoat_IOR
            Universal_node.inputs[27].default_value = new_shader_clearcoat_Rougness
        #Thin Film
        Universal_node.inputs[32].default_value = new_shader_Thin_Film_Thickness
        Universal_node.inputs[33].default_value = new_shader_Thin_Film_IOR
        
        #Sheen
        if new_shader_Sheen != 0:
            Universal_node.inputs[35].default_value = new_shader_Sheen_tilt
            Universal_node.inputs[36].default_value = new_shader_Sheen_Roughness
        #Opacity
        Universal_node.inputs[43].default_value = new_shader_opacity
        
        #models:
        Universal_node.inputs["[OctaneGroupTitle]Transmission Layer"].default_value = preferences.octane_preferences.octane_transmission
        Universal_node.inputs["Diffuse BRDF model"].default_value = preferences.octane_preferences.octane_BRDF
        Universal_node.inputs["BSDF model"].default_value = preferences.octane_preferences.octane_BSDF
        Universal_node.inputs["Metallic reflection mode"].default_value = preferences.octane_preferences.octane_metallic_type
        Universal_node.inputs["Dispersion mode"].default_value = preferences.octane_preferences.octane_Dispersion_mode
                
            
        return Universal_node
def Convert_Standard_Material(cycles_principled, c_nodes_tree):
     
        Octane_material_name = cycles_principled.name.replace("Principled BSDF", "Universal material")


        Universal_node = None
        for n in c_nodes_tree.nodes:
            if n.bl_idname == "OctaneStandardSurfaceMaterial" and n.name == Octane_material_name:
                Universal_node = n
                break  # Dodano break, aby przerwać pętlę po znalezieniu noda

        if not Universal_node:
            Universal_node = c_nodes_tree.nodes.new("OctaneStandardSurfaceMaterial")
            Universal_node.location = (cycles_principled.location[0] +1650, cycles_principled.location[1] - 0)
            Universal_node.label = cycles_principled.label
            Universal_node.name = Octane_material_name

        #Diffuse:
        Universal_node.inputs["Base color"].default_value = cycles_principled.inputs["Base Color"].default_value[:3]
        Universal_node.inputs["Diffuse roughness"].default_value = cycles_principled.inputs["Diffuse Roughness"].default_value if cycles_principled and "Diffuse Roughness" in cycles_principled.inputs else Universal_node.inputs["Diffuse roughness"].default_value
        #Metalness:
        Universal_node.inputs["Metalness"].default_value = cycles_principled.inputs["Metallic"].default_value
        
        Universal_node.inputs["Opacity"].default_value = cycles_principled.inputs["Alpha"].default_value
                
        #Subsurface    
        Universal_node.inputs["Subsurface weight"].default_value = (cycles_principled.inputs["Subsurface Weight"].default_value /2)
        Universal_node.inputs["Subsurface color"].default_value = cycles_principled.inputs["Base Color"].default_value[:3]
        Universal_node.inputs["Subsurface radius"].default_value = cycles_principled.inputs["Subsurface Radius"].default_value
        Universal_node.inputs["Subsurface scale"].default_value = cycles_principled.inputs["Subsurface Scale"].default_value
        Universal_node.inputs["Subsurface anisotropy"].default_value = cycles_principled.inputs["Subsurface Anisotropy"].default_value if cycles_principled and "Subsurface Anisotropy" in cycles_principled.inputs else Universal_node.inputs["Subsurface anisotropy"].default_value
        #Specular:
        Universal_node.inputs["Specular roughness"].default_value = cycles_principled.inputs["Roughness"].default_value
        Universal_node.inputs["Specular IOR"].default_value = cycles_principled.inputs["IOR"].default_value
        Universal_node.inputs["Specular roughness"].default_value = cycles_principled.inputs["Roughness"].default_value
        Universal_node.inputs["Specular weight"].default_value = min(cycles_principled.inputs["Specular IOR Level"].default_value*preferences.octane_preferences.octane_specular_multipler,1)
        Universal_node.inputs["Specular color"].default_value = cycles_principled.inputs["Specular Tint"].default_value[:3]
        
        #Anisotropic
        Universal_node.inputs["Specular anisotropy"].default_value = cycles_principled.inputs["Anisotropic"].default_value
        Universal_node.inputs["Specular rotation"].default_value = cycles_principled.inputs["Anisotropic Rotation"].default_value
        
        #Sheen
        Universal_node.inputs["Sheen weight"].default_value = cycles_principled.inputs["Sheen Weight"].default_value
        Universal_node.inputs["Sheen color"].default_value = cycles_principled.inputs["Sheen Tint"].default_value[:3]
        Universal_node.inputs["Sheen roughness"].default_value = cycles_principled.inputs["Sheen Roughness"].default_value
        
        #Clearcoat
        Universal_node.inputs["Coating weight"].default_value = cycles_principled.inputs["Coat Weight"].default_value
        Universal_node.inputs["Coating color"].default_value = cycles_principled.inputs["Coat Tint"].default_value[:3]
        Universal_node.inputs["Coating roughness"].default_value = cycles_principled.inputs["Coat Roughness"].default_value
        Universal_node.inputs["Coating IOR"].default_value = cycles_principled.inputs["Coat IOR"].default_value
        #Transmission
        Universal_node.inputs["Transmission weight"].default_value = cycles_principled.inputs["Transmission Weight"].default_value
        Universal_node.inputs["Transmission color"].default_value = cycles_principled.inputs["Base Color"].default_value[:3]
        
        #Thin Film:
        Universal_node.inputs["Film thickness (nm)"].default_value = cycles_principled.inputs["Thin Film Thickness"].default_value
        Universal_node.inputs["Film IOR"].default_value = cycles_principled.inputs["Thin Film IOR"].default_value
        
        
        #models:
        Universal_node.inputs["[OctaneGroupTitle]Transmission Layer"].default_value = preferences.octane_preferences.octane_transmission
        Universal_node.inputs["Diffuse BRDF model"].default_value = preferences.octane_preferences.octane_BRDF
        
        Universal_node.inputs["Dispersion mode"].default_value = preferences.octane_preferences.octane_Dispersion_mode
                
            
        return Universal_node


mat = bpy.context.object.active_material
remove_reroutes_from_material(mat)

# Ungroup all node groups before conversion (simplified approach)
# This flattens the entire node tree so all nodes are in the main material tree
print("=" * 60)
print("UNGROUPING ALL NODE GROUPS BEFORE CONVERSION")
print("=" * 60)
from Shader_node_group import ungroup_all_recursively
ungroup_all_recursively(mat)

# Label nodes AFTER ungrouping so all nodes are accessible
print("=" * 60)
print("LABELING NODES BASED ON CONNECTIONS")
print("=" * 60)
label_nodes_from_base_color(mat)

if hasattr(mat, 'node_tree'):
    active_material = mat
    c_nodes_tree = active_material.node_tree
    if hasattr(c_nodes_tree, 'nodes'):
        c_nodes = c_nodes_tree.nodes
        nodes = c_nodes
        links = c_nodes_tree.links
        
        Cycles_Node_Group = [node for node in c_nodes if node.bl_idname == "ShaderNodeGroup"]
        print(f"=== DEBUG: Found {len(Cycles_Node_Group)} node groups in material ===")
        Cycles_Images_nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeTexImage")]
        Cycles_Output_nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeOutputMaterial")]
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
        Cycles_Normal_Nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeNormalMap")]
        Cycles_Displacement = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeDisplacement")]
        Displacement_texture = [node for node in nodes if node.bl_idname.startswith("OctaneRGBImage") and node.label == "Displacement"]
        Displacement_node = [node for node in nodes if ("OctaneTextureDisplacement" in node.bl_idname or "OctaneVertexDisplacement" in node.bl_idname) and ("Displacement" in node.label or "COLOR * AO" in node.label)]
        Cycles_curves = [node for node in nodes if node.bl_idname == "ShaderNodeRGBCurve"]

        # Curves Conversion:
        for cycles_curve in Cycles_curves:

            Convert_Curve_node(cycles_curve,mat)

        # Normal Map Node Processing:
        # Tag Image Texture nodes connected to Normal Map's Color input
        # Normal textures are just image textures, not Combine RGB
        print(f"=== Processing {len(Cycles_Normal_Nodes)} Normal Map nodes ===")

        for normal_map_node in Cycles_Normal_Nodes:
            print(f"  Processing Normal Map node: {normal_map_node.name}")

            # Tag Image Texture connected to the Color input
            if normal_map_node.inputs[1].is_linked:  # Color input
                for link in normal_map_node.inputs[1].links:
                    input_node = link.from_node

                    # Only tag Image Texture nodes - normal textures are just images
                    if input_node.bl_idname == "ShaderNodeTexImage":
                        if not input_node.label or "Normal" not in input_node.label:
                            input_node.label = "Normal"
                            print(f"    ✓ Tagged Image Texture as 'Normal': {input_node.name}")
                    else:
                        print(f"    ! Skipped non-image node: {input_node.name} ({input_node.bl_idname})")

            print(f"    → Processed Normal Map node")

        #Octane_Output:
        
        for Octane_output_node in Cycles_Output_nodes:
            # Inicjalizacja zmiennych do przechowywania znalezionych nodów
            Octane_Output = None
            Cycles_EEVEE_Output = None
            Eevee_Output = None
            Cycles_Output = None

            # Pierwszy przebieg - szukanie istniejących nodów
            for output_node in Cycles_Output_nodes:
                if output_node.inputs[0].is_linked:
                    linked_node = output_node.inputs[0].links[0].from_node
                    if linked_node.bl_idname.startswith("Octane"):
                        Octane_Output = output_node
                        Octane_Output.label = "Octane Output"
                    else:
                        Cycles_EEVEE_Output = output_node
                elif not output_node.inputs[0].is_linked:
                    
                    Octane_Output = output_node
                    Octane_Output.target = "ALL"
                    Octane_Output.label = "Octane Output"
                else: 
                    pass
                    
            if Cycles_EEVEE_Output:
                if Cycles_EEVEE_Output.target == "ALL":
                    Cycles_output = Cycles_EEVEE_Output
                    Cycles_output.target = "CYCLES"
                    EEVEE_output = c_nodes_tree.nodes.new('ShaderNodeOutputMaterial')
                    EEVEE_output.location = (Cycles_output.location [0], Cycles_output.location[1] - 300)
                    EEVEE_output.target = "EEVEE"
                    # Przeniesienie połączeń wejściowych
                    for i, input_socket in enumerate(Cycles_EEVEE_Output.inputs):
                        if input_socket.is_linked:
                            for link in input_socket.links:
                                c_nodes_tree.links.new(link.from_socket, EEVEE_output.inputs[i])

                    # Przeniesienie połączeń wyjściowych
                    for i, output_socket in enumerate(Cycles_EEVEE_Output.outputs):
                        if output_socket.is_linked:
                            for link in output_socket.links:
                                c_nodes_tree.links.new(EEVEE_output.outputs[i], link.to_socket)
                else:
                    pass
            if not Octane_Output:
                Octane_Output = c_nodes_tree.nodes.new('ShaderNodeOutputMaterial')
                Octane_Output.label = "Octane Output"
                Octane_Output.target = "ALL"
                
                
            
                                    
                   
        # Process node groups and collect Principled BSDF nodes found inside them
        principled_nodes_in_groups = []
        print(f"=== DEBUG: Starting to process {len(Cycles_Node_Group)} node groups ===")
        for Cycles_Groups in Cycles_Node_Group:
            print(f"=== DEBUG: Processing node group: {Cycles_Groups.name} ===")
            group_principled = Unpack_Shader_node_group(Cycles_Groups, mat)
            if group_principled:
                print(f"=== DEBUG: Found {len(group_principled)} Principled BSDF nodes in this group ===")
                principled_nodes_in_groups.extend(group_principled)
            else:
                print(f"=== DEBUG: No Principled BSDF found in group: {Cycles_Groups.name} ===")

        print(f"=== DEBUG: Total Principled BSDF nodes found in all groups: {len(principled_nodes_in_groups)} ===")

        # Convert Principled BSDF nodes found inside node groups
        for principled_info in principled_nodes_in_groups:
            cycles_principled = principled_info['node']
            source_node_tree = principled_info['node_tree']

            print(f"Converting Principled BSDF from node group: {principled_info['group_name']}")

            # Create Octane material in the main material node tree
            if Chosen_material == "UNIVERSAL":
                Universal_node = Convert_Universal_Material(cycles_principled, c_nodes_tree)
                if cycles_principled.distribution == "GGX":
                    Universal_node.inputs["BSDF model"].default_value = "GGX"
                if cycles_principled.distribution == "MULTI_GGX":
                    Universal_node.inputs["BSDF model"].default_value = "GGX (energy preserving)"
            else:
                Universal_node = Convert_Standard_Material(cycles_principled, c_nodes_tree)

            # Helper function to find the node group instance in main material tree
            def find_group_node_in_main_tree(group_tree_name):
                """Find the ShaderNodeGroup node in main material tree that uses this node group"""
                for node in c_nodes_tree.nodes:
                    if node.bl_idname == "ShaderNodeGroup":
                        if hasattr(node, 'node_tree') and node.node_tree and node.node_tree.name == group_tree_name:
                            return node
                return None

            # Helper function to trace back to image texture nodes
            def trace_to_image_textures(node, from_socket=None, visited=None, depth=0, current_group_name=None):
                """Recursively trace back through node connections to find image textures
                Can traverse through node group boundaries in both directions

                Args:
                    node: Current node being traced
                    from_socket: The OUTPUT socket we came from (to match with group inputs)
                    visited: Set of visited node IDs
                    depth: Current recursion depth
                    current_group_name: Name of current node group (if inside one)
                """
                if visited is None:
                    visited = set()

                if not node or id(node) in visited or depth > 20:
                    return []

                visited.add(id(node))
                image_textures = []
                indent = "        " + "  " * depth

                print(f"{indent}Tracing: {node.name} ({node.bl_idname})")

                # If this is an image texture, return it
                if node.bl_idname == "ShaderNodeTexImage":
                    print(f"{indent}  → Found image texture!")
                    return [node]

                # If this is a Group Input node, jump back to the main material tree
                if node.bl_idname == "NodeGroupInput" and current_group_name:
                    print(f"{indent}  → Group Input detected, jumping to main material tree...")
                    # Find the node in main tree that uses this group
                    group_node = find_group_node_in_main_tree(current_group_name)
                    if group_node:
                        print(f"{indent}    → Found group node in main tree: {group_node.name}")

                        # If we know which output socket we came from on the Group Input node,
                        # match it to the corresponding input socket on the group node in main tree
                        if from_socket and hasattr(from_socket, 'name'):
                            socket_name = from_socket.name
                            print(f"{indent}      → Looking for input matching Group Input output: '{socket_name}'")

                            # Find the matching input on the group node
                            if socket_name in group_node.inputs:
                                group_input = group_node.inputs[socket_name]
                                if group_input.is_linked:
                                    for link in group_input.links:
                                        connected_node = link.from_node
                                        print(f"{indent}      ✓ Tracing from matched group input: {socket_name}")
                                        image_textures.extend(trace_to_image_textures(connected_node, link.from_socket, visited, depth + 1, None))
                                else:
                                    print(f"{indent}      ! Input '{socket_name}' is not linked")
                            else:
                                print(f"{indent}      ! Could not find input socket '{socket_name}' on group node")
                        else:
                            # Fallback: trace all inputs (old behavior)
                            print(f"{indent}      → No specific socket info, tracing all inputs...")
                            for group_input in group_node.inputs:
                                if group_input.is_linked:
                                    for link in group_input.links:
                                        connected_node = link.from_node
                                        print(f"{indent}      → Tracing from group input: {group_input.name}")
                                        image_textures.extend(trace_to_image_textures(connected_node, link.from_socket, visited, depth + 1, None))
                    else:
                        print(f"{indent}    ! Could not find group node in main tree")
                    return image_textures

                # If this is a node group, enter it and trace from its outputs
                if node.bl_idname == "ShaderNodeGroup" and hasattr(node, 'node_tree') and node.node_tree:
                    print(f"{indent}  → Entering node group: {node.node_tree.name}")
                    group_tree = node.node_tree
                    group_name = group_tree.name

                    # Find Group Output nodes in the node group
                    for group_node in group_tree.nodes:
                        if group_node.bl_idname == "NodeGroupOutput":
                            print(f"{indent}    → Found Group Output")
                            # Trace from all inputs of the Group Output
                            for group_output_input in group_node.inputs:
                                if group_output_input.is_linked:
                                    for link in group_output_input.links:
                                        connected_node = link.from_node
                                        image_textures.extend(trace_to_image_textures(connected_node, link.from_socket, visited, depth + 1, group_name))

                # Otherwise, trace through all input connections
                for input_socket in node.inputs:
                    if input_socket.is_linked:
                        for link in input_socket.links:
                            connected_node = link.from_node
                            # Pass the FROM socket (output socket) for proper matching
                            image_textures.extend(trace_to_image_textures(connected_node, link.from_socket, visited, depth + 1, current_group_name))

                return image_textures

            # Process input connections from the node group
            print(f"  Processing input connections for Principled BSDF from node group...")
            for input_socket in cycles_principled.inputs:
                if input_socket.is_linked:
                    for link in input_socket.links:
                        source_node = link.from_node
                        source_socket = link.from_socket

                        print(f"    Found connection: {source_node.name} ({source_node.bl_idname}) -> {input_socket.name}")

                        # Trace back to find image texture nodes
                        # Pass the current group name and the from_socket for proper matching
                        image_textures = trace_to_image_textures(source_node, source_socket, None, 0, principled_info['group_name'])
                        if image_textures:
                            print(f"      Traced back to {len(image_textures)} image texture(s): {[img.name for img in image_textures]}")
                            # Use the first image texture found for this connection
                            source_node = image_textures[0]
                            print(f"      Using image texture: {source_node.name}")

                        # Try to find the corresponding Octane node in the main material tree
                        octane_source_node = None

                        # Method 1: Match by label (if label is not empty)
                        if source_node.label != "":
                            for n in c_nodes_tree.nodes:
                                if n.label == source_node.label and n.bl_idname.startswith("Octane"):
                                    octane_source_node = n
                                    print(f"      Found matching Octane node by label: {n.name} ({n.bl_idname})")
                                    break

                        # Method 2: Match by image name (for image texture nodes)
                        if not octane_source_node and source_node.bl_idname == "ShaderNodeTexImage":
                            if hasattr(source_node, 'image') and source_node.image:
                                image_name = source_node.image.name
                                for n in c_nodes_tree.nodes:
                                    if n.bl_idname == "OctaneRGBImage" and hasattr(n, 'image') and n.image:
                                        if n.image.name == image_name:
                                            octane_source_node = n
                                            print(f"      Found matching Octane node by image name: {n.name} (image: {image_name})")
                                            break

                        # Method 3: Match by node name pattern
                        if not octane_source_node:
                            # Convert node name pattern (e.g., "Image Texture" -> "RGB image")
                            expected_octane_name = source_node.name.replace("Image Texture", "RGB image")
                            for n in c_nodes_tree.nodes:
                                if n.name == expected_octane_name and n.bl_idname.startswith("Octane"):
                                    octane_source_node = n
                                    print(f"      Found matching Octane node by name: {n.name} ({n.bl_idname})")
                                    break

                        if octane_source_node:
                            # Map input socket names from Cycles to Octane Universal Material
                            # Based on the Convert_Universal_Material function indices
                            input_mapping = {
                                'Base Color': 5,      # Diffuse
                                'Metallic': 7,        # Metallic
                                'Roughness': 13,      # Roughness
                                'Normal': None,       # Need to find the correct index
                                'Alpha': 43,          # Opacity
                                'Specular IOR Level': 10,  # Specular
                                'IOR': 18,            # IOR
                                'Anisotropic': 14,    # Anisotropy
                                'Anisotropic Rotation': 15,  # Anisotropy Rotation
                            }

                            # Try to connect by socket index (more reliable for Universal Material)
                            if input_socket.name in input_mapping:
                                socket_index = input_mapping[input_socket.name]
                                if socket_index is not None:
                                    try:
                                        # Find appropriate output socket (usually "Texture out" or first output)
                                        output_socket_name = "Texture out" if "Texture out" in octane_source_node.outputs else octane_source_node.outputs[0].name

                                        links.new(octane_source_node.outputs[output_socket_name], Universal_node.inputs[socket_index])
                                        print(f"      ✓ Connected: {octane_source_node.name}.{output_socket_name} -> {Universal_node.name}.inputs[{socket_index}] ({input_socket.name})")
                                    except Exception as e:
                                        print(f"      ✗ Failed to connect: {e}")
                                else:
                                    print(f"      ! Socket index not defined for '{input_socket.name}'")
                            else:
                                # Try by name as fallback
                                try:
                                    if input_socket.name in Universal_node.inputs:
                                        output_socket_name = "Texture out" if "Texture out" in octane_source_node.outputs else octane_source_node.outputs[0].name
                                        links.new(octane_source_node.outputs[output_socket_name], Universal_node.inputs[input_socket.name])
                                        print(f"      ✓ Connected by name: {octane_source_node.name}.{output_socket_name} -> {Universal_node.name}.{input_socket.name}")
                                except:
                                    print(f"      ! No mapping found for input '{input_socket.name}'")
                        else:
                            print(f"      ! No matching Octane node found for '{source_node.name}'")

        #Images:
        for Cycles_Images in Cycles_Images_nodes:
            Convert_image_node(Cycles_Images,mat)
           
        # Invert Node       
        for Cycles_invert in Cycles_Invert_Nodes:
            existing_Octane_Invert = None
            for n in c_nodes_tree.nodes:
                if n.bl_idname == "OctaneInvertTexture" and n.label == Cycles_invert.label:
                    existing_Octane_Invert
                    break
            if not existing_Octane_Invert:
                existing_Octane_Invert = c_nodes_tree.nodes.new("OctaneInvertTexture")
                
            existing_Octane_Invert.location = (Cycles_invert.location[0] + 1650, Cycles_invert.location[1])
            existing_Octane_Invert.label = Cycles_invert.label
            
        #Mix color Node
        for Cycles_mix_color_node in Cycles_Color_Mix:
            
        
            blend_type_mapping = {
                'DARKEN': 'Darken',
                'MULTIPLY': 'Multiply',
                'COLOR_BURN': 'Color Burn',
                'LINEAR_BURN': 'Linear Burn',
                'LIGHTEN': 'Lighten',
                'SCREEN': 'Screen',
                'COLOR_DODGE': 'Color Dodge',
                'ADD': 'Add',
                'OVERLAY': 'Overlay',
                'SOFT_LIGHT': 'Soft Light',
                'HARD_LIGHT': 'Hard Light',
                'VIVID_LIGHT': 'Vivid Light',
                'LINEAR_LIGHT': 'Linear Light',
                'PIN_LIGHT': 'Pin Light',
                'HARD_MIX': 'Hard Mix',
                'DIFFERENCE': 'Difference',
                'EXCLUSION': 'Exclusion',
                'SUBTRACT': 'Subtract',
                'DIVIDE': 'Divide',
                'HUE': 'Hue',
                'SATURATION': 'Saturation',
                'COLOR': 'Color',
                'LUMINOSITY': 'Luminosity'
            }
                
            if Cycles_mix_color_node.data_type == 'RGBA':
                Octane_mix_name = Cycles_mix_color_node.name.replace("Mix","Octane CyclesMixColorNode Wrapper")
                Octane_mix_color = None
                for n in c_nodes_tree.nodes:
                    if n.bl_idname == "OctaneCyclesMixColorNodeWrapper" and Octane_mix_name in Cycles_mix_color_node.name:
                        Octane_mix_color = n
                        break
                if not Octane_mix_color: 
                    Octane_mix_color = c_nodes_tree.nodes.new("OctaneCyclesMixColorNodeWrapper")
            
                Octane_mix_color.name = Octane_mix_name
                Octane_mix_color.label = Cycles_mix_color_node.label 
                Octane_mix_color.inputs[0].default_value = blend_type_mapping.get(Cycles_mix_color_node.blend_type.upper(), 'Mix')  # Default to 'Mix' if not found
                
                Octane_mix_color.location = (Cycles_mix_color_node.location[0] + 1650, Cycles_mix_color_node.location[1])
                Octane_mix_color.inputs[6].default_value = Cycles_mix_color_node.inputs[6].default_value[:3]
                Octane_mix_color.inputs[7].default_value = Cycles_mix_color_node.inputs[7].default_value[:3]
                Octane_mix_color.inputs[4].default_value = Cycles_mix_color_node.clamp_result
                Octane_mix_color.inputs[2].default_value = Cycles_mix_color_node.clamp_factor
                
            elif Cycles_mix_color_node.data_type == 'FLOAT':
                Octane_mix_name_float = Cycles_mix_color_node.name.replace("Mix","Octane CyclesMixFloatNode Wrapper")
                Octane_Mix_Float = None
                for n in c_nodes_tree.nodes:
                    if n.bl_idname == "OctaneCyclesMixFloatNodeWrapper" and Octane_mix_name_float in n.name:
                        Octane_Mix_Float = n
                        break
                if not Octane_Mix_Float:
                    Octane_Mix_Float = c_nodes_tree.nodes.new("OctaneCyclesMixFloatNodeWrapper")
                Octane_Mix_Float.label = Cycles_mix_color_node.label
                Octane_Mix_Float.location = (Cycles_mix_color_node.location[0] + 1650, Cycles_mix_color_node.location[1])
                Octane_Mix_Float.name = Octane_mix_name_float
                Octane_Mix_Float.inputs[1].default_value = Cycles_mix_color_node.clamp_factor
                Octane_Mix_Float.inputs[2].default_value = Cycles_mix_color_node.inputs[0].default_value
                Octane_Mix_Float.inputs[3].default_value = Cycles_mix_color_node.inputs[2].default_value
                Octane_Mix_Float.inputs[4].default_value = Cycles_mix_color_node.inputs[3].default_value
                
            elif Cycles_mix_color_node.data_type == 'VECTOR':
                Octane_Mix_Name_Vector = Cycles_mix_color_node.name.replace("Mix","Octane CyclesMixFloat3Node Wrapper")
                Octane_Mix_Vector = None
                for n in c_nodes_tree.nodes:
                    if n.bl_idname == "OctaneCyclesMixFloat3NodeWrapper" and n.name == Octane_Mix_Name_Vector:
                        Octane_Mix_Vector = n
                        break
                if not Octane_Mix_Vector:
                    Octane_Mix_Vector = c_nodes_tree.nodes.new("OctaneCyclesMixFloat3NodeWrapper")
                    Octane_Mix_Vector.label = Cycles_mix_color_node.label
                    Octane_Mix_Vector.location = (Cycles_mix_color_node.location[0] + 1650, Cycles_mix_color_node.location[1])
                Octane_Mix_Vector.name = Octane_Mix_Name_Vector
                mode_mapping = {
                  "UNIFORM": "Uniform",
                  "NON_UNIFORM": "Non-Uniform",
                  
                }

                Octane_Mix_Vector.inputs[0].default_value = mode_mapping.get(Cycles_mix_color_node.factor_mode, Cycles_mix_color_node.factor_mode)
                
                Octane_Mix_Vector.inputs[2].default_value = Cycles_mix_color_node.clamp_factor
                Octane_Mix_Vector.inputs[3].default_value = Cycles_mix_color_node.inputs[0].default_value
                Octane_Mix_Vector.inputs[4].default_value = Cycles_mix_color_node.inputs[1].default_value
                Octane_Mix_Vector.inputs[5].default_value = Cycles_mix_color_node.inputs[4].default_value
                Octane_Mix_Vector.inputs[6].default_value = Cycles_mix_color_node.inputs[5].default_value
        #Displacement
        Displacement_texture = [node for node in nodes if node.bl_idname.startswith("OctaneRGBImage") and node.label.lower() == "displacement"]
        Displacement_node = [node for node in nodes if ("OctaneTextureDisplacement" in node.bl_idname or "OctaneVertexDisplacement" in node.bl_idname) and ("displacement" in node.label.lower() or "COLOR * AO" in node.label)]

        
        for Node_Disp in Cycles_Displacement:
            Octane_Displacement = None
            if displacement_type == "TEXTURE":
                
                Octane_Displacement_Name = Node_Disp.name.replace("Displacement","Texture displacement")
                for n in c_nodes_tree.nodes:
                    if n.bl_idname == "OctaneTextureDisplacement" and n.name == Octane_Displacement_Name:
                       Octane_Displacement = n
                       break
                    if n.bl_idname == "OctaneVertexDisplacement":
                        c_nodes_tree.nodes.remove(n) 
               
                if not Octane_Displacement:
                    Octane_Displacement = c_nodes_tree.nodes.new("OctaneTextureDisplacement")
                    Octane_Displacement.label = Node_Disp.label
                    Octane_Displacement.location = (Node_Disp.location[0] + 1650, Node_Disp.location[1])
                    Octane_Displacement.name = Octane_Displacement_Name
                Octane_Displacement.inputs[1].default_value = Node_Disp.inputs[1].default_value
                Octane_Displacement.inputs[3].default_value = Node_Disp.inputs[0].default_value
                if Displacement_texture:
                    links.new(Displacement_texture[0].outputs[0],Octane_Displacement.inputs["Texture"])
            else:
                Octane_Displacement_Name = Node_Disp.name.replace("Displacement","Vertex displacement")
                for n in c_nodes_tree.nodes:
                    if n.bl_idname == "OctaneVertexDisplacement" and n.name == Octane_Displacement_Name:
                       Octane_Displacement = n
                       break
                    if n.bl_idname == "OctaneTextureDisplacement":
                        c_nodes_tree.nodes.remove(n) 
                if not Octane_Displacement:
                    Octane_Displacement = c_nodes_tree.nodes.new("OctaneVertexDisplacement")
                    Octane_Displacement.label = Node_Disp.label
                    Octane_Displacement.location = (Node_Disp.location[0] + 1650, Node_Disp.location[1])
                    Octane_Displacement.name = Octane_Displacement_Name
                
                Octane_Displacement.inputs[1].default_value = Node_Disp.inputs[0].default_value
                Octane_Displacement.inputs[2].default_value = Node_Disp.inputs[1].default_value
                if Displacement_texture:
                    links.new(Displacement_texture[0].outputs[0],Octane_Displacement.inputs["Texture"])
                   

            
        
        
        # Color Correction
        for Node_HSV in Cycles_HSV_nodes:
            Octane_HSV = None
            Octane_HSV_Name = Node_HSV.name.replace("Hue/Saturation/Value","Color correction")
            for n in c_nodes_tree.nodes:
                if n.bl_idname == "OctaneColorCorrection" and n.name == Octane_HSV_Name:
                    Octane_HSV = n
                    break
            if not Octane_HSV:
                Octane_HSV = c_nodes_tree.nodes.new("OctaneColorCorrection")
                Octane_HSV.label = Node_HSV.label
                Octane_HSV.location = (Node_HSV.location[0] + 1650, Node_HSV.location[1])
                Octane_HSV.name = Octane_HSV_Name
             
            Octane_HSV.inputs[3].default_value = (Node_HSV.inputs[0].default_value *2 -1)
            Octane_HSV.inputs[4].default_value = (Node_HSV.inputs[1].default_value *100)
            
            Octane_HSV.inputs[1].default_value = (Node_HSV.inputs[2].default_value *100)
            Octane_HSV.inputs[9].default_value = Node_HSV.inputs[3].default_value
            
        #Color Ramp Node
        for val_to_rgb in val_to_rgb_nodes:
            node_c = val_to_rgb.color_ramp
            num_elements = len(node_c.elements)
            
            Octane_Gradient_map = None
            Octane_Gradient_name = val_to_rgb.name.replace("Color Ramp","Gradient map")
            for n in c_nodes_tree.nodes:
                if n.bl_idname == "OctaneGradientMap" and n.name == Octane_Gradient_name:
                    Octane_Gradient_map = n
                    break
            if not Octane_Gradient_map:
                Octane_Gradient_map = c_nodes_tree.nodes.new("OctaneGradientMap")
                Octane_Gradient_map.location = (val_to_rgb.location[0] + 1650, val_to_rgb.location[1])
                Octane_Gradient_map.name = Octane_Gradient_name
                Octane_Gradient_map.label = val_to_rgb.label
            octane_helper = bpy.data.node_groups.get(".[OCTANE_HELPER_NODE_GROUP]")
                #if octane_helper:
                   # node_gradient = "OctaneGradientMap"
            #octane_elements = True
           
            octane_name = Octane_Gradient_map.color_ramp_name
            ramp_items = octane_helper.nodes[octane_name].color_ramp.elements
            
            for i in range(num_elements):
                elements = node_c.elements[i]
                if i >= len(ramp_items):
                    ramp_items.new(elements.position)
                ramp_items[i].position = elements.position
                ramp_items[i].color = elements.color
                ramp_items[i].position = elements.position
                ramp_items[i].color = elements.color
        # Mapping:
        
        for Cycles_Mapping_Node in Cycles_Mapping_Nodes:
            Octane_Mapping_Name = Cycles_Mapping_Node.name.replace("Mapping","3D transformation")
            Octane_Mapping = None
            for n in c_nodes_tree.nodes:
                if n.bl_idname == "Octane3DTransformation" and n.name == Octane_Mapping_Name:
                    Octane_Mapping = n
                    continue
            if not Octane_Mapping:
                Octane_Mapping = c_nodes_tree.nodes.new("Octane3DTransformation")
                Octane_Mapping.location = (Cycles_Mapping_Node.location[0] + 1650, Cycles_Mapping_Node.location[1])
                Octane_Mapping.name = Octane_Mapping_Name
                
            Octane_Mapping.label = Cycles_Mapping_Node.label
            radians_to_degrees = lambda x: x * 180.0 / math.pi
                
            #Rotation
            Octane_Mapping.inputs[1].default_value[0] = radians_to_degrees(Cycles_Mapping_Node.inputs[2].default_value[0])
            Octane_Mapping.inputs[1].default_value[1] = radians_to_degrees(Cycles_Mapping_Node.inputs[2].default_value[1])
            Octane_Mapping.inputs[1].default_value[2] = radians_to_degrees(Cycles_Mapping_Node.inputs[2].default_value[2])
            
            #Scale
            Octane_Mapping.inputs[2].default_value[0] = 1 / (Cycles_Mapping_Node.inputs[3].default_value[0])
            Octane_Mapping.inputs[2].default_value[1] = 1 / (Cycles_Mapping_Node.inputs[3].default_value[1])
            Octane_Mapping.inputs[2].default_value[2] = 1 / (Cycles_Mapping_Node.inputs[3].default_value[2])
            
            #Location
            Octane_Mapping.inputs[3].default_value[0] = Cycles_Mapping_Node.inputs[1].default_value[0]
            Octane_Mapping.inputs[3].default_value[1] = Cycles_Mapping_Node.inputs[1].default_value[1]
            Octane_Mapping.inputs[3].default_value[2] = Cycles_Mapping_Node.inputs[1].default_value[2]
        
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
                  
                
                    
                Octane_Translusency_Name = Cycles_Translusency.name.replace("Translucent BSDF","Universal material")
                Octane_Translusency = None
                
                
                for n in c_nodes_tree.nodes:
                    if n.bl_idname == "OctaneUniversalMaterial" and n.name == Octane_Translusency_Name:
                        Octane_Translusency = n
                        continue
                if not Octane_Translusency:
                    Octane_Translusency = c_nodes_tree.nodes.new("OctaneUniversalMaterial")
                    Octane_Translusency.location = (Cycles_Translusency.location[0] +1650 , Cycles_Translusency.location[1]) 
                    Octane_Translusency.label = Cycles_Translusency.label
                    Octane_Translusency.name = Octane_Translusency_Name
                 
                Octane_Translusency.inputs[2].default_value = "Diffuse"
                    
                
                #Transmission Color:
                if not Cycles_Translusency.inputs[0].is_linked:
                    Octane_Trans_Color = None
                    for nodes in c_nodes_tree.nodes:
                        if n.bl_idname == "OctaneRGBColor" and  n.label == "Octane Color Transmision":
                            Octane_Trans_Color = n
                            continue
                    if not Octane_Trans_Color:
                        Octane_Trans_Color = c_nodes_tree.nodes.new("OctaneRGBColor")
                        Octane_Trans_Color.label = "Octane Color Transmission"
                    Octane_Trans_Color.location = (Octane_Translusency.location[0] -300 , Octane_Translusency.location[1] -75) 
                    Octane_Trans_Color.a_value = Cycles_Translusency.inputs[0].default_value[:3]
                    c_nodes_tree.links.new(Octane_Trans_Color.outputs[0], Octane_Translusency.inputs[1])
                    
                
                #Octane_output
                c_nodes_tree.links.new(Octane_Translusency.outputs[0],Octane_Output.inputs[0])
                
                Octane_Output.location = (Octane_Translusency.location[0] + 300, Octane_Translusency.location[1])
                                       
                if BSDF_help:
                    #Alpha    
                    Octane_Translusency.inputs[43].value = BSDF_help.inputs[4].default_value
                    #Diffuse
                    Octane_Translusency.inputs[5].value = BSDF_help.inputs[0].default_value[:3]
                                
                    #Glossiness
                    Octane_Translusency.inputs[13].value = BSDF_help.inputs[2].default_value
                    
                    #Fresnel IOR
                    Octane_Translusency.inputs[18].value =  BSDF_help.inputs[3].default_value
                    
                    #Metalness
                    Octane_Translusency.inputs[7].value =  BSDF_help.inputs[1].default_value
                    
        Cycles_Glass = False
        for Cycles_Glass_node in Cycles_Glass_nodes:
            Cycles_Glass = True
            BSDF_help = None
            for node_BSDF_help in Cycles_principled_nodes:
                if node_BSDF_help in Cycles_principled_nodes:
                   
                    BSDF_help = node_BSDF_help
                    break
                                
                    
            Octane_Glass_Name = Cycles_Glass_node.name.replace("Glass BSDF","Universal material")
            Octane_Glass = None
            
            
            for n in c_nodes_tree.nodes:
                if n.bl_idname == "OctaneUniversalMaterial" and n.name == Octane_Glass_Name:
                    Octane_Glass = n
                    continue
            if not Octane_Glass:
                Octane_Glass = c_nodes_tree.nodes.new("OctaneUniversalMaterial")
                Octane_Glass.location = (Cycles_Glass_node.location[0] +1650 , Cycles_Glass_node.location[1]) 
                Octane_Glass.label = Cycles_Glass_node.label
                Octane_Glass.name = Octane_Glass_Name
             
                    
            Octane_Glass.inputs[2].default_value = "Specular"
            #Diffuse
            Octane_Glass.inputs[5].value = (0,0,0)   
            
            #Transmission Color:
            if not Cycles_Glass_node.inputs[0].is_linked:
                Octane_Trans_Color = None
                for nodes in c_nodes_tree.nodes:
                    if n.bl_idname == "OctaneRGBColor" and  n.label == "Octane Color Transmision":
                        Octane_Trans_Color = n
                        continue
                if not Octane_Trans_Color:
                    Octane_Trans_Color = c_nodes_tree.nodes.new("OctaneRGBColor")
                    Octane_Trans_Color.label = "Octane Color Transmission"
                Octane_Trans_Color.location = (Octane_Glass.location[0] -300 , Octane_Glass.location[1] -75) 
                Octane_Trans_Color.a_value = Cycles_Glass_node.inputs[0].default_value[:3]
                c_nodes_tree.links.new(Octane_Trans_Color.outputs[0], Octane_Glass.inputs[1])
            #Glossiness
            Octane_Glass.inputs[13].value = Cycles_Glass_node.inputs[1].default_value    
            
            #Octane_output
            c_nodes_tree.links.new(Octane_Glass.outputs[0],Octane_Output.inputs[0])
            
            Octane_Output.location = (Octane_Glass.location[0] + 300, Octane_Glass.location[1])
            
            #Fresnel IOR
            Octane_Glass.inputs[18].value =  Cycles_Glass_node.inputs[2].default_value
        if not Cycles_Glass and not Cycles_Translucent:
            Layered_Material = None
           
            for Mix_Shader_Node in Cycles_ShaderMix_nodes:
                Layered_octane = None
                Mix_Octane_Name = Mix_Shader_Node.name.replace("Mix Shader","Mix material")
                for n in c_nodes_tree.nodes:
                    if n.bl_idname == "OctaneMixMaterial" and n.name == Mix_Octane_Name:
                        Layered_octane = n
                        continue
                if not Layered_octane:
                    Layered_octane = c_nodes_tree.nodes.new("OctaneMixMaterial")
                    Layered_octane.location = (Mix_Shader_Node.location[0] +1650 , Mix_Shader_Node.location[1]) 
                    Layered_octane.label = Mix_Shader_Node.label
                    Layered_octane.name = Mix_Octane_Name
                    
                Layered_octane.inputs[0].default_value = Mix_Shader_Node.inputs[0].default_value
                for cycles_principled in Cycles_principled_nodes:
                    if Chosen_material == "UNIVERSAL":
                        Universal_node = Convert_Universal_Material(cycles_principled, c_nodes_tree)
                        if cycles_principled.distribution == "GGX":
                            Universal_node.inputs["BSDF model"].default_value = "GGX"
                        if cycles_principled.distribution == "MULTI_GGX":
                            Universal_node.inputs["BSDF model"].default_value = "GGX (energy preserving)"
                            
                    else:
                        Universal_node = Convert_Standard_Material(cycles_principled, c_nodes_tree) 
                   
            if not Layered_Material:
                for cycles_principled in Cycles_principled_nodes:
                    if Chosen_material == "UNIVERSAL":
                        Universal_node = Convert_Universal_Material(cycles_principled, c_nodes_tree)
                        if cycles_principled.distribution == "GGX":
                            Universal_node.inputs["BSDF model"].default_value = "GGX"
                        if cycles_principled.distribution == "MULTI_GGX":
                            Universal_node.inputs["BSDF model"].default_value = "GGX (energy preserving)"
                    else:
                        Universal_node = Convert_Standard_Material(cycles_principled, c_nodes_tree) 
                   
                    c_nodes_tree.links.new(Universal_node.outputs[0],Octane_Output.inputs[0])
                    
                    Octane_Output.location = (Universal_node.location[0] + 300, Universal_node.location[1])
                    
        # Znalezienie wszystkich węzłów typu ShaderNodeOutputMaterial
        Cycles_Output_nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeOutputMaterial")]

        # Iteracja przez węzły i usunięcie niepodłączonych
        for node in Cycles_Output_nodes:
            has_connections = any(link.is_linked for link in node.inputs) or any(link.is_linked for link in node.outputs)
            if not has_connections:
                print(f"Usuwanie węzła: {node.name}")
                c_nodes_tree.nodes.remove(node)
                    
        Connect_To_Material(mat)
        rebuild_octane_connections(mat)
        Connect_Vray_Mapping_Node(mat)
               
               
        
                
                            
                        
                                
            
                    
                
        
                 
                     
                
                    
                
                
                
                
                
                    
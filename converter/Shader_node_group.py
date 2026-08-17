import bpy
import os
import math
import sys
import importlib

convert_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "converter"))
if convert_folder not in sys.path:
    sys.path.append(convert_folder)

from convert_images import Convert_image_node

# Force reload this module to ensure latest code is used
print("=" * 60)
print("SHADER NODE GROUP MODULE LOADED - Version 6.0 MANUAL")
print("  - Ungroup all node groups before conversion")
print("  - Manual node copying (no operator dependency)")
print("  - More reliable and context-independent")
print("=" * 60)


def ungroup_all_recursively(mat):
    """
    Recursively ungroup all node groups in the material
    This flattens the node tree so all nodes are in the main material tree
    Uses manual node copying instead of operators (more reliable)
    """
    if not hasattr(mat, 'node_tree') or not mat.node_tree:
        return

    node_tree = mat.node_tree
    max_iterations = 50  # Prevent infinite loops
    iteration = 0

    while iteration < max_iterations:
        # Find all node groups
        node_groups = [node for node in node_tree.nodes if node.bl_idname == "ShaderNodeGroup"]

        if not node_groups:
            print("  ✓ All node groups have been ungrouped")
            break

        print(f"  Iteration {iteration + 1}: Found {len(node_groups)} node groups to ungroup")

        # Show all node group names for debugging
        for ng in node_groups:
            ng_tree_name = ng.node_tree.name if ng.node_tree else "No node_tree"
            print(f"    → Node group: {ng.name} (tree: {ng_tree_name})")

        # Ungroup each node group manually
        for group_node in node_groups:
            if not group_node.node_tree:
                print(f"    ! Skipping {group_node.name}: No node_tree attached")
                continue

            print(f"    - Ungrouping: {group_node.name} ({group_node.node_tree.name})")

            try:
                ungroup_node_manually(node_tree, group_node)
                print(f"      ✓ Ungrouped successfully")
            except Exception as e:
                print(f"      ! Failed to ungroup: {e}")
                import traceback
                traceback.print_exc()

        iteration += 1

    if iteration >= max_iterations:
        print(f"  ⚠ WARNING: Reached maximum iterations ({max_iterations})")


def ungroup_node_manually(parent_tree, group_node):
    """
    Manually ungroup a single node group by copying its internal nodes to parent tree
    and rewiring connections
    """
    if not group_node.node_tree:
        return

    group_tree = group_node.node_tree

    # Store the group node's location for positioning copied nodes
    group_location = group_node.location

    # Dictionary to map internal nodes to their copies in parent tree
    node_mapping = {}

    # Step 1: Copy all internal nodes (except Group Input/Output) to parent tree
    internal_nodes_count = 0
    for internal_node in group_tree.nodes:
        # Skip Group Input and Group Output nodes
        if internal_node.bl_idname in ("NodeGroupInput", "NodeGroupOutput"):
            continue

        internal_nodes_count += 1

        # Create a copy of the node in parent tree
        new_node = parent_tree.nodes.new(internal_node.bl_idname)

        # Copy basic properties
        new_node.name = internal_node.name
        new_node.label = internal_node.label
        new_node.location = (
            group_location[0] + internal_node.location[0],
            group_location[1] + internal_node.location[1]
        )
        new_node.hide = internal_node.hide
        new_node.mute = internal_node.mute

        # Copy node-specific properties
        copy_node_properties(internal_node, new_node)

        # Store the mapping
        node_mapping[internal_node] = new_node

    print(f"      → Copied {internal_nodes_count} internal nodes")

    # Step 2: Recreate internal connections in parent tree
    for internal_link in group_tree.links:
        from_node = internal_link.from_node
        to_node = internal_link.to_node

        # Skip links involving Group Input/Output
        if from_node.bl_idname in ("NodeGroupInput", "NodeGroupOutput"):
            continue
        if to_node.bl_idname in ("NodeGroupInput", "NodeGroupOutput"):
            continue

        # Get the copied nodes
        if from_node in node_mapping and to_node in node_mapping:
            new_from_node = node_mapping[from_node]
            new_to_node = node_mapping[to_node]

            # Create the link
            try:
                parent_tree.links.new(
                    new_from_node.outputs[internal_link.from_socket.name],
                    new_to_node.inputs[internal_link.to_socket.name]
                )
            except:
                # If socket name doesn't match, try by index
                try:
                    from_index = list(from_node.outputs).index(internal_link.from_socket)
                    to_index = list(to_node.inputs).index(internal_link.to_socket)
                    parent_tree.links.new(
                        new_from_node.outputs[from_index],
                        new_to_node.inputs[to_index]
                    )
                except:
                    pass

    # Step 3: Reconnect external connections
    # Map Group Input connections to the copied nodes
    group_input_node = None
    for node in group_tree.nodes:
        if node.bl_idname == "NodeGroupInput":
            group_input_node = node
            break

    if group_input_node:
        print(f"      → Reconnecting Group Input connections...")
        # For each output of Group Input node
        for output_socket in group_input_node.outputs:
            if not output_socket.is_linked:
                continue

            print(f"        Group Input output: '{output_socket.name}' → {len(output_socket.links)} internal connection(s)")

            # Find the corresponding input on the group node
            if output_socket.name in group_node.inputs:
                group_input_socket = group_node.inputs[output_socket.name]
                print(f"          Found matching group node input: '{group_input_socket.name}'")
                print(f"          External connections: {len(group_input_socket.links)}")

                # For each internal connection from Group Input
                for internal_link in output_socket.links:
                    internal_to_node = internal_link.to_node
                    internal_to_socket = internal_link.to_socket

                    print(f"          Internal: Group Input.{output_socket.name} → {internal_to_node.name}.{internal_to_socket.name}")

                    # If this internal node was copied
                    if internal_to_node in node_mapping:
                        copied_node = node_mapping[internal_to_node]
                        print(f"            Copied node: {copied_node.name}")

                        # Connect external input to copied node
                        if group_input_socket.is_linked:
                            for external_link in group_input_socket.links:
                                print(f"            External: {external_link.from_node.name}.{external_link.from_socket.name}")

                                connection_made = False
                                # Try by socket name first
                                try:
                                    parent_tree.links.new(
                                        external_link.from_socket,
                                        copied_node.inputs[internal_to_socket.name]
                                    )
                                    print(f"            ✓ Connected by name: {external_link.from_node.name}.{external_link.from_socket.name} → {copied_node.name}.{internal_to_socket.name}")
                                    connection_made = True
                                except Exception as e:
                                    print(f"            ! Failed to connect by name: {e}")
                                    # Try by index if name doesn't match
                                    try:
                                        to_index = list(internal_to_node.inputs).index(internal_to_socket)
                                        parent_tree.links.new(
                                            external_link.from_socket,
                                            copied_node.inputs[to_index]
                                        )
                                        print(f"            ✓ Connected by index [{to_index}]: {external_link.from_node.name} → {copied_node.name}")
                                        connection_made = True
                                    except Exception as e2:
                                        print(f"            ✗ Failed to connect by index: {e2}")

                                if not connection_made:
                                    print(f"            ✗ Failed to reconnect Group Input connection!")
                        else:
                            print(f"            ! Group input socket '{group_input_socket.name}' is not linked externally")
                    else:
                        print(f"            ! Internal node {internal_to_node.name} was not copied (not in mapping)")
            else:
                print(f"          ! Could not find matching input '{output_socket.name}' on group node")

    # Step 4: Reconnect Group Output connections
    group_output_node = None
    for node in group_tree.nodes:
        if node.bl_idname == "NodeGroupOutput":
            group_output_node = node
            break

    if group_output_node:
        print(f"      → Reconnecting Group Output connections...")
        # For each input of Group Output node (these are the outputs of the group)
        for input_socket in group_output_node.inputs:
            if not input_socket.is_linked:
                continue

            print(f"        Group Output input: '{input_socket.name}' → {len(input_socket.links)} internal connection(s)")

            # Find what's connected to this Group Output input internally
            for internal_link in input_socket.links:
                internal_from_node = internal_link.from_node
                internal_from_socket = internal_link.from_socket

                print(f"          Internal: {internal_from_node.name}.{internal_from_socket.name} → Group Output.{input_socket.name}")

                # If this internal node was copied
                if internal_from_node in node_mapping:
                    copied_node = node_mapping[internal_from_node]
                    print(f"            Copied node: {copied_node.name}")

                    # Find the corresponding output on the group node
                    if input_socket.name in group_node.outputs:
                        group_output_socket = group_node.outputs[input_socket.name]
                        print(f"            Found matching group node output: '{group_output_socket.name}'")
                        print(f"            External connections: {len(group_output_socket.links)}")

                        # Connect copied node to external outputs
                        if group_output_socket.is_linked:
                            for external_link in group_output_socket.links:
                                print(f"            External: → {external_link.to_node.name}.{external_link.to_socket.name}")

                                connection_made = False
                                # Try by socket name first
                                try:
                                    parent_tree.links.new(
                                        copied_node.outputs[internal_from_socket.name],
                                        external_link.to_socket
                                    )
                                    print(f"            ✓ Connected by name: {copied_node.name}.{internal_from_socket.name} → {external_link.to_node.name}.{external_link.to_socket.name}")
                                    connection_made = True
                                except Exception as e:
                                    print(f"            ! Failed to connect by name: {e}")
                                    # Try by index if name doesn't match
                                    try:
                                        from_index = list(internal_from_node.outputs).index(internal_from_socket)
                                        parent_tree.links.new(
                                            copied_node.outputs[from_index],
                                            external_link.to_socket
                                        )
                                        print(f"            ✓ Connected by index [{from_index}]: {copied_node.name} → {external_link.to_node.name}.{external_link.to_socket.name}")
                                        connection_made = True
                                    except Exception as e2:
                                        print(f"            ✗ Failed to connect by index: {e2}")

                                if not connection_made:
                                    print(f"            ✗ Failed to reconnect Group Output connection!")
                        else:
                            print(f"            ! Group output socket '{group_output_socket.name}' is not linked externally")
                    else:
                        print(f"            ! Could not find matching output '{input_socket.name}' on group node")
                else:
                    print(f"            ! Internal node {internal_from_node.name} was not copied (not in mapping)")

    # Step 5: Remove the group node
    parent_tree.nodes.remove(group_node)


def copy_node_properties(src_node, dst_node):
    """
    Copy properties from source node to destination node
    """
    # Copy input default values
    for i, input_socket in enumerate(src_node.inputs):
        if i < len(dst_node.inputs):
            try:
                if hasattr(input_socket, 'default_value'):
                    dst_node.inputs[i].default_value = input_socket.default_value
            except:
                pass

    # Copy specific node type properties
    try:
        # Node Group - IMPORTANT: Copy the node_tree reference for nested groups
        if src_node.bl_idname == "ShaderNodeGroup":
            if hasattr(src_node, 'node_tree') and src_node.node_tree:
                dst_node.node_tree = src_node.node_tree
                print(f"          → Copied node_tree reference: {src_node.node_tree.name}")
                print(f"             Inputs: {[inp.name for inp in dst_node.inputs]}")
                print(f"             Outputs: {[out.name for out in dst_node.outputs]}")

        # Image texture nodes
        elif src_node.bl_idname == "ShaderNodeTexImage":
            if hasattr(src_node, 'image'):
                dst_node.image = src_node.image
            if hasattr(src_node, 'interpolation'):
                dst_node.interpolation = src_node.interpolation
            if hasattr(src_node, 'projection'):
                dst_node.projection = src_node.projection
            if hasattr(src_node, 'extension'):
                dst_node.extension = src_node.extension

        # RGB node
        elif src_node.bl_idname == "ShaderNodeRGB":
            if hasattr(src_node.outputs[0], 'default_value'):
                dst_node.outputs[0].default_value = src_node.outputs[0].default_value

        # Value node
        elif src_node.bl_idname == "ShaderNodeValue":
            if hasattr(src_node.outputs[0], 'default_value'):
                dst_node.outputs[0].default_value = src_node.outputs[0].default_value

        # ColorRamp node
        elif src_node.bl_idname == "ShaderNodeValToRGB":
            if hasattr(src_node, 'color_ramp'):
                dst_ramp = dst_node.color_ramp
                src_ramp = src_node.color_ramp
                # Copy color ramp elements
                while len(dst_ramp.elements) < len(src_ramp.elements):
                    dst_ramp.elements.new(0.5)
                while len(dst_ramp.elements) > len(src_ramp.elements):
                    dst_ramp.elements.remove(dst_ramp.elements[-1])
                for i, elem in enumerate(src_ramp.elements):
                    dst_ramp.elements[i].position = elem.position
                    dst_ramp.elements[i].color = elem.color

        # Math node
        elif src_node.bl_idname == "ShaderNodeMath":
            if hasattr(src_node, 'operation'):
                dst_node.operation = src_node.operation
            if hasattr(src_node, 'use_clamp'):
                dst_node.use_clamp = src_node.use_clamp

        # Vector Math node
        elif src_node.bl_idname == "ShaderNodeVectorMath":
            if hasattr(src_node, 'operation'):
                dst_node.operation = src_node.operation

        # Mix node
        elif src_node.bl_idname in ("ShaderNodeMix", "ShaderNodeMixRGB"):
            if hasattr(src_node, 'blend_type'):
                dst_node.blend_type = src_node.blend_type
            if hasattr(src_node, 'data_type'):
                dst_node.data_type = src_node.data_type

        # Mapping node
        elif src_node.bl_idname == "ShaderNodeMapping":
            if hasattr(src_node, 'vector_type'):
                dst_node.vector_type = src_node.vector_type

        # Normal Map node
        elif src_node.bl_idname == "ShaderNodeNormalMap":
            if hasattr(src_node, 'space'):
                dst_node.space = src_node.space
            if hasattr(src_node, 'uv_map'):
                dst_node.uv_map = src_node.uv_map

        # Bump node
        elif src_node.bl_idname == "ShaderNodeBump":
            if hasattr(src_node, 'invert'):
                dst_node.invert = src_node.invert

        # Separate RGB node (Blender 3.x and earlier)
        elif src_node.bl_idname == "ShaderNodeSeparateRGB":
            pass  # No special properties to copy

        # Separate Color node (Blender 4.x)
        elif src_node.bl_idname == "ShaderNodeSeparateColor":
            if hasattr(src_node, 'mode'):
                dst_node.mode = src_node.mode

        # Combine RGB node
        elif src_node.bl_idname == "ShaderNodeCombineRGB":
            pass  # No special properties to copy

        # Combine Color node (Blender 4.x)
        elif src_node.bl_idname == "ShaderNodeCombineColor":
            if hasattr(src_node, 'mode'):
                dst_node.mode = src_node.mode

    except Exception as e:
        # If copying specific properties fails, just continue
        print(f"        ! Warning: Failed to copy properties for {src_node.bl_idname}: {e}")
        pass


def Unpack_Shader_node_group(Cycles_Groups, mat):
    """
    This function is now just a placeholder since we ungroup everything before conversion
    """
    # No longer needed - ungrouping is done before this is called
    return []
    
    
    

"""    
    
def Convert_image_node(Cycles_Images,mat):
    Render_engine = bpy.context.scene.render.engine
    
    if Render_engine == "octane":
        node_image = "OctaneRGBImage"
        nodes = mat.node_tree.nodes
        engine_image_name = "RGB image"
        gamma_input = "Legacy gamma"
        offset_x = 1650
        offset_y = 0
        
    elif Render_engine == "VRAY_RENDER_RT":
        node_image = "VRayNodeMetaImageTexture"
        engine_image_name = "V-Ray Bitmap"
        nodes = mat.node_tree.nodes
        offset_x = 0
        offset_y = -1650
    elif Render_engine == "LUXCORE":
        engine_image_name = "Imagemap"
        node_image = "LuxCoreNodeTexImagemap"
        
        nodes = mat.luxcore.node_tree.nodes
        offset_x = 0
        offset_y = 0 
      
    Engine_image_node = None
    Engine_image_node_name = Cycles_Images.name.replace("Image Texture", engine_image_name)
    print(Engine_image_node_name)
    for n in nodes:
        if n.bl_idname == node_image and n.name == Engine_image_node_name:
            Engine_image_node = n
            break
    if not Engine_image_node:
        
        
        Engine_image_node = nodes.new(node_image)
        Engine_image_node.name = Engine_image_node_name
    Engine_image_node.label = Cycles_Images.label
    Engine_image_node.location = (Cycles_Images.location[0] + offset_x, Cycles_Images.location[1] + offset_y)
    Engine_image_node.hide = Cycles_Images.hide
        
    new_texture_name = Cycles_Images.image.name
    new_texture = bpy.data.images.get(new_texture_name) 
    
    if Render_engine == "LUXCORE":
        Engine_image_node.image = Cycles_Images.image
        
        if not "sRGB" in Cycles_Images.image.colorspace_settings.name:
            Engine_image_node.gamma = 1
        else:
            Engine_image_node.gamma = 2.2
    if Render_engine == "octane":
        Engine_image_node.image = Cycles_Images.image
        if not "sRGB" in Cycles_Images.image.colorspace_settings.name:
            Engine_image_node.inputs[gamma_input].default_value = 1.0
            
        else:
            Engine_image_node.inputs[gamma_input].default_value = 2.2
            
    else:
       if new_texture:
           if hasattr(Engine_image_node, 'texture') and Engine_image_node.texture:
               Engine_image_node.texture.image = new_texture
               if not "sRGB" in Cycles_Images.image.colorspace_settings.name:
                   Engine_image_node.BitmapBuffer.transfer_function = '1'
                   Engine_image_node.BitmapBuffer.gamma = 1
               else:
                   Engine_image_node.BitmapBuffer.transfer_function = '1'
                   Engine_image_node.BitmapBuffer.gamma = 2.2  
                   
"""
                   
   
"""
mat = bpy.context.object.active_material
c_nodes = mat.node_tree.nodes
Cycles_Node_Group = [node for node in c_nodes if node.bl_idname == "ShaderNodeGroup" and not node.name.startswith('.')]
for Cycles_Groups in Cycles_Node_Group:
    print(Cycles_Groups.name)
                                     
    Unpack_Shader_node_group(Cycles_Groups,mat)#"""   
"""mat = bpy.context.object.active_material
c_nodes = mat.node_tree.nodes
Cycles_Images_nodes = [node for node in c_nodes if node.bl_idname == "ShaderNodeTexImage"]
for Cycles_Images in Cycles_Images_nodes:
                                     
   Convert_image_node(Cycles_Images,mat)#"""
    
        

                    


import contextlib
import io
import time
from typing import Any

import bpy

from ..converter.convert_curve import Convert_Curve_node
from ..converter.convert_images import Convert_image_node
from ..converter.Shader_node_group import Unpack_Shader_node_group, ungroup_all_recursively
from ..core.node_mappings import (
    BLEND_TYPE_MAPPING,
    UNIVERSAL_MATERIAL_INPUT_INDICES,
    VECTOR_MODE_MAPPING,
)
from ..executor.addon_helpers import get_addon_preferences
from ..executor.octane_executor import (
    apply_octane_mapping_nodes,
    apply_octane_math_nodes,
    apply_octane_separate_color,
    log_material_audit_warnings,
    prune_unconnected_octane_nodes,
    set_octane_float_value,
)
from ..scripts.connect_nodes import (
    Connect_Alpha_Clip_Texture,
    Connect_To_Material,
    Connect_Vray_Mapping_Node,
)
from ..scripts.premade import label_nodes_from_base_color, remove_reroutes_from_material
from ..scripts.rebuild import (
    rebuild_octane_connections,
    rebuild_octane_separate_color_connections,
)


def _set_input_val(node, names: str | tuple[str, ...], fallback_idx: int, val: Any) -> None:
    """Set node input default_value by socket name(s), with fallback to index."""
    name_tuple = (names,) if isinstance(names, str) else names
    for name in name_tuple:
        if name in node.inputs:
            node.inputs[name].default_value = val
            return
    if 0 <= fallback_idx < len(node.inputs):
        node.inputs[fallback_idx].default_value = val


def Convert_Universal_Material(cycles_principled, c_nodes_tree, preferences):

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
    #Specular:
    new_shader_Specualar = cycles_principled.inputs["Specular IOR Level"].default_value
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
    #Thin Film:
    new_shader_Thin_Film_Thickness = cycles_principled.inputs["Thin Film Thickness"].default_value
    new_shader_Thin_Film_IOR = cycles_principled.inputs["Thin Film IOR"].default_value

    # Diffuse:
    _set_input_val(Universal_node, ("Albedo", "Diffuse"), 5, new_shader_Base_color[:3])
    # Metallic:
    _set_input_val(Universal_node, "Metallic", 7, new_shader_Metallic)
    # Specular:
    specular_val = min(new_shader_Specualar * preferences.octane_preferences.octane_specular_multipler, 1)
    _set_input_val(Universal_node, "Specular", 10, specular_val)
    # Roughness:
    _set_input_val(Universal_node, "Roughness", 13, new_shader_Roughness)
    # Anisotropy:
    _set_input_val(Universal_node, "Anisotropy", 14, new_shader_Anisotropic)
    # Anisotropy Rotation:
    _set_input_val(Universal_node, ("Anisotropy Rotation", "Anisotropy rotation"), 15, new_shader_Anisotropic_rotation)
    # IOR:
    _set_input_val(Universal_node, ("Dielectric IOR", "IOR"), 18, new_shader_IOR)
    # Coat:
    if new_shader_Clearcoat != 0:
        _set_input_val(Universal_node, ("Coat Color", "Coat Tint"), 26, new_shader_Clearcoat_Tilt)
        _set_input_val(Universal_node, "Coat Roughness", 27, new_shader_clearcoat_Rougness)
        _set_input_val(Universal_node, "Coat IOR", 28, new_shader_clearcoat_IOR)
    # Thin Film:
    _set_input_val(Universal_node, ("Film Thickness", "Thin Film Thickness"), 32, new_shader_Thin_Film_Thickness)
    _set_input_val(Universal_node, ("Film IOR", "Thin Film IOR"), 33, new_shader_Thin_Film_IOR)

    # Sheen:
    if new_shader_Sheen != 0:
        _set_input_val(Universal_node, ("Sheen Color", "Sheen Tint"), 35, new_shader_Sheen_tilt)
        _set_input_val(Universal_node, "Sheen Roughness", 36, new_shader_Sheen_Roughness)
    # Opacity:
    _set_input_val(Universal_node, "Opacity", 43, new_shader_opacity)

    #models:
    Universal_node.inputs["[OctaneGroupTitle]Transmission Layer"].default_value = preferences.octane_preferences.octane_transmission
    Universal_node.inputs["Diffuse BRDF model"].default_value = preferences.octane_preferences.octane_BRDF
    Universal_node.inputs["BSDF model"].default_value = preferences.octane_preferences.octane_BSDF
    Universal_node.inputs["Metallic reflection mode"].default_value = preferences.octane_preferences.octane_metallic_type
    Universal_node.inputs["Dispersion mode"].default_value = preferences.octane_preferences.octane_Dispersion_mode


    return Universal_node


def Convert_Standard_Material(cycles_principled, c_nodes_tree, preferences):

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


def is_octane_converted(mat):
    """True only if the material already has an Octane *material* node (e.g.
    OctaneUniversalMaterial). Octane texture/helper nodes alone (left by the
    drag-in auto-convert or a half-finished earlier run) don't count - such
    materials still need converting, otherwise they end up with no main material."""
    return any(
        n.bl_idname.startswith("Octane") and n.bl_idname.endswith("Material")
        for n in mat.node_tree.nodes
    )


def _is_octane_material_node(node):
    return node.bl_idname.startswith("Octane") and node.bl_idname.endswith("Material")


def ensure_main_material(mat, preferences, chosen_material):
    """Last-resort safety net: guarantee the material ends up with an Octane main
    material node wired to a Material Output. The normal passes only build one from
    a Principled BSDF, so materials made of Diffuse/Emission/Glossy BSDFs only (or
    ones where an earlier pass bailed out) would otherwise convert to nothing."""
    tree = mat.node_tree
    nodes, links = tree.nodes, tree.links

    outputs = [n for n in nodes if n.bl_idname == "ShaderNodeOutputMaterial"]
    output = next((n for n in outputs if n.label == "Octane Output"), None)
    if output is None:
        output = next((n for n in outputs if not n.inputs[0].is_linked), None)
    if output is None:
        output = nodes.new("ShaderNodeOutputMaterial")
        output.label = "Octane Output"
        output.target = "ALL"
        if outputs:
            output.location = (outputs[0].location[0], outputs[0].location[1] - 300)

    if output.inputs[0].is_linked and _is_octane_material_node(output.inputs[0].links[0].from_node):
        return

    # An Octane material exists but isn't hooked up: just wire it in.
    existing = next((n for n in nodes if _is_octane_material_node(n)), None)
    if existing is not None:
        links.new(existing.outputs[0], output.inputs[0])
        return

    # Nothing at all: build one from the colour of whatever simple BSDF is there.
    color = None
    for n in nodes:
        if n.bl_idname in ("ShaderNodeBsdfDiffuse", "ShaderNodeEmission", "ShaderNodeBsdfGlossy",
                           "ShaderNodeBsdfTranslucent", "ShaderNodeBsdfGlass") and "Color" in n.inputs:
            color = n.inputs["Color"].default_value[:]
            break

    temp = nodes.new("ShaderNodeBsdfPrincipled")
    temp.location = (output.location[0] - 1950, output.location[1])
    if color is not None:
        temp.inputs["Base Color"].default_value = color
    try:
        if chosen_material == "UNIVERSAL":
            new_node = Convert_Universal_Material(temp, tree, preferences)
        else:
            new_node = Convert_Standard_Material(temp, tree, preferences)
    finally:
        nodes.remove(temp)
    links.new(new_node.outputs[0], output.inputs[0])
    output.location = (new_node.location[0] + 300, new_node.location[1])


# Set True to get the full per-node debug output while converting. Left off
# because ~150 prints per material is slow on Blender's Windows console.
VERBOSE = False


def convert_material_to_octane(mat):
    """Wrapper around _convert_material_to_octane(): silences the debug prints,
    pauses the auto-convert-image depsgraph handler (it rescans every material on
    each node created here) and reports how long the material took."""
    start = time.perf_counter()
    ns = bpy.app.driver_namespace
    ns["mc_converting"] = True
    try:
        if VERBOSE:
            _convert_material_to_octane(mat)
        else:
            with contextlib.redirect_stdout(io.StringIO()):
                _convert_material_to_octane(mat)
    finally:
        ns["mc_converting"] = False
        name = mat.name if mat else "<none>"
        print(f"[Material Converter] '{name}' converted in {time.perf_counter() - start:.2f}s")


def _convert_material_to_octane(mat):
    """
    Single source of truth for "Cycles material -> Octane material" node-graph
    conversion for ONE material. convert_active_octane.py / convert_selected_octane.py
    / convert_all_octane.py are thin wrappers that only differ in which materials
    they gather - they all call this function to do the actual work.

    This used to be ~900 lines copy-pasted three times, which is exactly how
    features (Separate Color, node-group ungrouping, RGB/Value nodes, Math nodes...)
    kept ending up working in one entry point and silently missing from the other
    two. Fix bugs/add features HERE, once - do not re-duplicate this function.
    """
    preferences = get_addon_preferences()
    if preferences is None:
        raise RuntimeError("Material Converter preferences not found.")
    Chosen_material = preferences.octane_preferences.octane_base_material
    displacement_type = preferences.octane_preferences.octane_displacement_mode

    if not mat or not hasattr(mat, 'node_tree') or not mat.node_tree:
        return
    if not hasattr(mat.node_tree, 'nodes'):
        return

    remove_reroutes_from_material(mat)
    ungroup_all_recursively(mat)
    log_material_audit_warnings(mat)
    label_nodes_from_base_color(mat)

    active_material = mat
    c_nodes_tree = active_material.node_tree
    c_nodes = c_nodes_tree.nodes
    nodes = c_nodes
    links = c_nodes_tree.links

    Cycles_Node_Group = [node for node in c_nodes if node.bl_idname == "ShaderNodeGroup"]
    print(f"=== DEBUG: Found {len(Cycles_Node_Group)} node groups in material ===")
    Cycles_Images_nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeTexImage")]
    # A material with no Material Output node would leave Octane_Output undefined below.
    if not any(node.bl_idname == "ShaderNodeOutputMaterial" for node in c_nodes_tree.nodes):
        c_nodes_tree.nodes.new("ShaderNodeOutputMaterial")
    Cycles_Output_nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeOutputMaterial")]
    Cycles_Translusency_nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeBsdfTranslucent")]
    Cycles_principled_nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeBsdfPrincipled")]
    Cycles_Color_Mix = [node for node in c_nodes_tree.nodes if node.bl_idname == "ShaderNodeMix"]
    Cycles_Glass_nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeBsdfGlass")]
    Cycles_HSV_nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeHueSaturation")]
    val_to_rgb_nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeValToRGB")]
    Cycles_Mapping_Nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeMapping")]
    Cycles_Invert_Nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeInvert")]
    Cycles_Normal_Nodes = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeNormalMap")]
    Cycles_Displacement = [node for node in c_nodes_tree.nodes if node.bl_idname.startswith("ShaderNodeDisplacement")]
    Cycles_Separate_Color = [node for node in c_nodes_tree.nodes if node.bl_idname in ("ShaderNodeSeparateColor", "ShaderNodeSeparateRGB")]
    Cycles_Math_Nodes = [node for node in c_nodes_tree.nodes if node.bl_idname == "ShaderNodeMath"]
    Cycles_RGB_Nodes = [node for node in c_nodes_tree.nodes if node.bl_idname == "ShaderNodeRGB"]
    Cycles_Value_Nodes = [node for node in c_nodes_tree.nodes if node.bl_idname == "ShaderNodeValue"]
    Displacement_texture = [node for node in nodes if node.bl_idname.startswith("OctaneRGBImage") and node.label == "Displacement"]
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

        print("    → Processed Normal Map node")

    #Octane_Output:
    Octane_Output = None
    Cycles_EEVEE_Output = None

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

    if Cycles_EEVEE_Output and Cycles_EEVEE_Output.target == "ALL":
        Cycles_output = Cycles_EEVEE_Output
        Cycles_output.target = "CYCLES"
        EEVEE_output = c_nodes_tree.nodes.new("ShaderNodeOutputMaterial")
        EEVEE_output.location = (Cycles_output.location[0], Cycles_output.location[1] - 300)
        EEVEE_output.target = "EEVEE"
        for i, input_socket in enumerate(Cycles_EEVEE_Output.inputs):
            if input_socket.is_linked:
                for link in input_socket.links:
                    c_nodes_tree.links.new(link.from_socket, EEVEE_output.inputs[i])

        for i, output_socket in enumerate(Cycles_EEVEE_Output.outputs):
            if output_socket.is_linked:
                for link in output_socket.links:
                    c_nodes_tree.links.new(EEVEE_output.outputs[i], link.to_socket)

    if not Octane_Output:
        Octane_Output = c_nodes_tree.nodes.new("ShaderNodeOutputMaterial")
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

        print(f"Converting Principled BSDF from node group: {principled_info['group_name']}")

        # Create Octane material in the main material node tree
        if Chosen_material == "UNIVERSAL":
            Universal_node = Convert_Universal_Material(cycles_principled, c_nodes_tree, preferences)
            if cycles_principled.distribution == "GGX":
                Universal_node.inputs["BSDF model"].default_value = "GGX"
            if cycles_principled.distribution == "MULTI_GGX":
                Universal_node.inputs["BSDF model"].default_value = "GGX (energy preserving)"
        else:
            Universal_node = Convert_Standard_Material(cycles_principled, c_nodes_tree, preferences)

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
        print("  Processing input connections for Principled BSDF from node group...")
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
                        input_mapping = UNIVERSAL_MATERIAL_INPUT_INDICES

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
                            except Exception:
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
                existing_Octane_Invert = n
                break
        if not existing_Octane_Invert:
            existing_Octane_Invert = c_nodes_tree.nodes.new("OctaneInvertTexture")

        existing_Octane_Invert.location = (Cycles_invert.location[0] + 1650, Cycles_invert.location[1])
        existing_Octane_Invert.label = Cycles_invert.label

    apply_octane_separate_color(mat, Cycles_Separate_Color)
    apply_octane_math_nodes(mat, Cycles_Math_Nodes)

    # RGB Node (constant color source)
    for Cycles_rgb in Cycles_RGB_Nodes:
        Octane_RGB_Name = Cycles_rgb.name.replace("RGB", "Octane RGB Color")
        Octane_RGB = None
        for n in c_nodes_tree.nodes:
            if n.bl_idname == "OctaneRGBColor" and n.name == Octane_RGB_Name:
                Octane_RGB = n
                break
        if not Octane_RGB:
            Octane_RGB = c_nodes_tree.nodes.new("OctaneRGBColor")
            Octane_RGB.name = Octane_RGB_Name
            Octane_RGB.location = (Cycles_rgb.location[0] + 1650, Cycles_rgb.location[1])

        Octane_RGB.label = Cycles_rgb.label
        Octane_RGB.a_value = Cycles_rgb.outputs[0].default_value[:3]

    # Value Node (constant float source)
    for Cycles_value in Cycles_Value_Nodes:
        Octane_Value_Name = Cycles_value.name.replace("Value", "Octane Float Value")
        Octane_Value = None
        for n in c_nodes_tree.nodes:
            if n.bl_idname == "OctaneFloatValue" and n.name == Octane_Value_Name:
                Octane_Value = n
                break
        if not Octane_Value:
            Octane_Value = c_nodes_tree.nodes.new("OctaneFloatValue")
            Octane_Value.name = Octane_Value_Name
            Octane_Value.location = (Cycles_value.location[0] + 1650, Cycles_value.location[1])

        Octane_Value.label = Cycles_value.label
        # a_value is FLOAT4 on Blender 5.2 / Octane 2026 and FLOAT3 on older
        # builds; set_octane_float_value matches whatever width is installed.
        set_octane_float_value(Octane_Value, Cycles_value.outputs[0].default_value)

    #Mix color Node
    for Cycles_mix_color_node in Cycles_Color_Mix:
        if Cycles_mix_color_node.data_type == 'RGBA':
            Octane_mix_name = Cycles_mix_color_node.name.replace("Mix","Octane CyclesMixColorNode Wrapper")
            Octane_mix_color = None
            for n in c_nodes_tree.nodes:
                if n.bl_idname == "OctaneCyclesMixColorNodeWrapper" and n.name == Octane_mix_name:
                    Octane_mix_color = n
                    break
            if not Octane_mix_color:
                Octane_mix_color = c_nodes_tree.nodes.new("OctaneCyclesMixColorNodeWrapper")

            Octane_mix_color.name = Octane_mix_name
            Octane_mix_color.label = Cycles_mix_color_node.label
            Octane_mix_color.inputs[0].default_value = BLEND_TYPE_MAPPING.get(Cycles_mix_color_node.blend_type.upper(), 'Mix')

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
            Octane_Mix_Vector.inputs[0].default_value = VECTOR_MODE_MAPPING.get(Cycles_mix_color_node.factor_mode, Cycles_mix_color_node.factor_mode)

            Octane_Mix_Vector.inputs[2].default_value = Cycles_mix_color_node.clamp_factor
            Octane_Mix_Vector.inputs[3].default_value = Cycles_mix_color_node.inputs[0].default_value
            Octane_Mix_Vector.inputs[4].default_value = Cycles_mix_color_node.inputs[1].default_value
            Octane_Mix_Vector.inputs[5].default_value = Cycles_mix_color_node.inputs[4].default_value
            Octane_Mix_Vector.inputs[6].default_value = Cycles_mix_color_node.inputs[5].default_value

    #Displacement
    Displacement_texture = [node for node in nodes if node.bl_idname.startswith("OctaneRGBImage") and node.label.lower() == "displacement"]

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
        octane_name = getattr(Octane_Gradient_map, "color_ramp_name", "")
        if octane_helper and octane_name and octane_name in octane_helper.nodes:
            helper_node = octane_helper.nodes[octane_name]
            if hasattr(helper_node, "color_ramp"):
                ramp_items = helper_node.color_ramp.elements
                for i in range(num_elements):
                    elements = node_c.elements[i]
                    if i >= len(ramp_items):
                        ramp_items.new(elements.position)
                    ramp_items[i].position = elements.position
                    ramp_items[i].color = elements.color

    # Mapping:
    apply_octane_mapping_nodes(mat, Cycles_Mapping_Nodes)

    # ------------------------------------------------------------------
    # Shader conversion + Mix Shader reconstruction.
    #
    # Every shader that is actually reachable from the surface output is
    # converted exactly once (so no unused duplicates end up in the tree),
    # and every Mix Shader becomes an Octane Mix material with BOTH branches
    # wired in - the old code converted glass/translucent OR principled and
    # silently dropped the rest of the graph.
    # ------------------------------------------------------------------
    def _reachable_shaders(root, depth=0, seen=None, found=None):
        if seen is None:
            seen, found = set(), []
        if root is None or depth > 32 or root.name in seen:
            return found
        seen.add(root.name)
        found.append(root)
        if root.bl_idname == "ShaderNodeMixShader":
            for socket_index in (1, 2):
                socket = root.inputs[socket_index]
                if socket.is_linked:
                    _reachable_shaders(socket.links[0].from_node, depth + 1, seen, found)
        return found

    cycles_root_shader = None
    for output_node in Cycles_Output_nodes:
        if getattr(output_node, "label", "") == "Octane Output":
            continue
        if output_node.inputs and output_node.inputs[0].is_linked:
            cycles_root_shader = output_node.inputs[0].links[0].from_node
            break

    reachable_shaders = _reachable_shaders(cycles_root_shader)
    reachable_names = {node.name for node in reachable_shaders}

    def _is_reachable(node):
        # If the surface output is unlinked (or feeds something exotic), fall
        # back to converting everything, which matches the previous behaviour.
        return not reachable_names or node.name in reachable_names

    octane_material_by_cycles: dict[str, object] = {}

    def _register_octane_material(cycles_node, octane_node):
        octane_material_by_cycles[cycles_node.name] = octane_node
        return octane_node

    def _unique_transmission_color(octane_material, cycles_node, replace_token):
        """One transmission-colour node per glass/translucent shader.

        The old code reused a single node matching the shared label, so a
        material combining glass + translucent ended up with both materials
        driven by one RGB node.
        """
        name = f"{cycles_node.name} [Transmission color]"
        color_node = next(
            (n for n in c_nodes_tree.nodes if n.bl_idname == "OctaneRGBColor" and n.name == name),
            None,
        )
        if color_node is None:
            color_node = c_nodes_tree.nodes.new("OctaneRGBColor")
            color_node.name = name
            color_node.label = "Octane Color Transmission"
        color_node.location = (octane_material.location[0] - 300, octane_material.location[1] - 75)
        color_node.a_value = cycles_node.inputs[0].default_value[:3]
        c_nodes_tree.links.new(color_node.outputs[0], octane_material.inputs[1])
        return color_node

    # ---- Principled BSDF -------------------------------------------------
    # Converted FIRST so its Octane material is the first "Material"-labelled
    # node in the tree; Connect_To_Material() then wires textures into the
    # Principled branch rather than into whichever glass/translucent material
    # happened to be created first.
    last_universal_node = None
    for cycles_principled in Cycles_principled_nodes:
        if not _is_reachable(cycles_principled):
            continue
        if Chosen_material == "UNIVERSAL":
            Universal_node = Convert_Universal_Material(cycles_principled, c_nodes_tree, preferences)
            if cycles_principled.distribution == "GGX":
                Universal_node.inputs["BSDF model"].default_value = "GGX"
            elif cycles_principled.distribution == "MULTI_GGX":
                Universal_node.inputs["BSDF model"].default_value = "GGX (energy preserving)"
        else:
            Universal_node = Convert_Standard_Material(cycles_principled, c_nodes_tree, preferences)
        _register_octane_material(cycles_principled, Universal_node)
        last_universal_node = Universal_node

    # ---- Translucent BSDF ------------------------------------------------
    for Cycles_Translusency in Cycles_Translusency_nodes:
        if not _is_reachable(Cycles_Translusency):
            continue
        BSDF_help = next(
            (node for node in Cycles_principled_nodes if _is_reachable(node)),
            None,
        )

        # Must not be "Universal material": a Principled BSDF in the same graph
        # already owns that name, and reusing it silently merged the glass and
        # diffuse branches into one material node.
        Octane_Translusency_Name = Cycles_Translusency.name.replace("Translucent BSDF", "Translucent material")
        Octane_Translusency = next(
            (
                n
                for n in c_nodes_tree.nodes
                if n.bl_idname == "OctaneUniversalMaterial" and n.name == Octane_Translusency_Name
            ),
            None,
        )
        if not Octane_Translusency:
            Octane_Translusency = c_nodes_tree.nodes.new("OctaneUniversalMaterial")
            Octane_Translusency.location = (Cycles_Translusency.location[0] + 1650, Cycles_Translusency.location[1])
            Octane_Translusency.label = Cycles_Translusency.label
            Octane_Translusency.name = Octane_Translusency_Name

        Octane_Translusency.inputs[2].default_value = "Diffuse"
        _register_octane_material(Cycles_Translusency, Octane_Translusency)

        if not Cycles_Translusency.inputs[0].is_linked:
            _unique_transmission_color(Octane_Translusency, Cycles_Translusency, "Translucent BSDF")

        if BSDF_help:
            # Alpha
            _set_input_val(Octane_Translusency, "Opacity", 43, BSDF_help.inputs["Alpha"].default_value if "Alpha" in BSDF_help.inputs else BSDF_help.inputs[4].default_value)
            # Diffuse
            _set_input_val(Octane_Translusency, ("Albedo", "Diffuse"), 5, BSDF_help.inputs["Base Color"].default_value[:3] if "Base Color" in BSDF_help.inputs else BSDF_help.inputs[0].default_value[:3])
            # Glossiness / Roughness
            _set_input_val(Octane_Translusency, "Roughness", 13, BSDF_help.inputs["Roughness"].default_value if "Roughness" in BSDF_help.inputs else BSDF_help.inputs[2].default_value)
            # Fresnel IOR
            _set_input_val(Octane_Translusency, ("Dielectric IOR", "IOR"), 18, BSDF_help.inputs["IOR"].default_value if "IOR" in BSDF_help.inputs else BSDF_help.inputs[3].default_value)
            # Metalness
            _set_input_val(Octane_Translusency, "Metallic", 7, BSDF_help.inputs["Metallic"].default_value if "Metallic" in BSDF_help.inputs else BSDF_help.inputs[1].default_value)

    # ---- Glass BSDF ------------------------------------------------------
    for Cycles_Glass_node in Cycles_Glass_nodes:
        if not _is_reachable(Cycles_Glass_node):
            continue
        BSDF_help = next(
            (node for node in Cycles_principled_nodes if _is_reachable(node)),
            None,
        )

        # See the translucent branch above: "Universal material" is the name the
        # Principled conversion uses, so glass must get its own base name.
        Octane_Glass_Name = Cycles_Glass_node.name.replace("Glass BSDF", "Glass material")
        Octane_Glass = next(
            (
                n
                for n in c_nodes_tree.nodes
                if n.bl_idname == "OctaneUniversalMaterial" and n.name == Octane_Glass_Name
            ),
            None,
        )
        if not Octane_Glass:
            Octane_Glass = c_nodes_tree.nodes.new("OctaneUniversalMaterial")
            Octane_Glass.location = (Cycles_Glass_node.location[0] + 1650, Cycles_Glass_node.location[1])
            Octane_Glass.label = Cycles_Glass_node.label
            Octane_Glass.name = Octane_Glass_Name

        _set_input_val(Octane_Glass, ("Transmission Layer", "[OctaneGroupTitle]Transmission Layer"), 2, "Specular")
        # Diffuse
        _set_input_val(Octane_Glass, ("Albedo", "Diffuse"), 5, (0.0, 0.0, 0.0))
        _register_octane_material(Cycles_Glass_node, Octane_Glass)

        if not Cycles_Glass_node.inputs[0].is_linked:
            _unique_transmission_color(Octane_Glass, Cycles_Glass_node, "Glass BSDF")

        # Roughness / Glossiness
        _set_input_val(Octane_Glass, "Roughness", 13, Cycles_Glass_node.inputs[1].default_value)
        # Fresnel IOR
        _set_input_val(Octane_Glass, ("Dielectric IOR", "IOR"), 18, Cycles_Glass_node.inputs[2].default_value)

    # ---- Mix Shader -> Octane Mix material -------------------------------
    def _octane_for_cycles_shader(cycles_node, depth=0):
        if cycles_node is None or depth > 32:
            return None
        cached = octane_material_by_cycles.get(cycles_node.name)
        if cached is not None:
            return cached
        if cycles_node.bl_idname != "ShaderNodeMixShader":
            return None

        mix_name = cycles_node.name.replace("Mix Shader", "Mix material")
        mix_node = next(
            (n for n in c_nodes_tree.nodes if n.bl_idname == "OctaneMixMaterial" and n.name == mix_name),
            None,
        )
        if mix_node is None:
            mix_node = c_nodes_tree.nodes.new("OctaneMixMaterial")
            mix_node.name = mix_name
            mix_node.label = cycles_node.label
            mix_node.location = (cycles_node.location[0] + 1650, cycles_node.location[1])

        # Cache before recursing so a malformed cyclic graph terminates.
        octane_material_by_cycles[cycles_node.name] = mix_node
        mix_node.inputs[0].default_value = cycles_node.inputs[0].default_value

        for socket_index in (1, 2):
            source_socket = cycles_node.inputs[socket_index]
            if not source_socket.is_linked:
                continue
            branch = _octane_for_cycles_shader(source_socket.links[0].from_node, depth + 1)
            if branch is None:
                continue
            for existing_link in list(mix_node.inputs[socket_index].links):
                c_nodes_tree.links.remove(existing_link)
            c_nodes_tree.links.new(branch.outputs[0], mix_node.inputs[socket_index])
        return mix_node

    root_octane_node = _octane_for_cycles_shader(cycles_root_shader)
    if root_octane_node is None:
        # Fall back to the outermost mix material, then the last converted
        # Principled material (matches the old behaviour).
        root_octane_node = next(
            (n for n in octane_material_by_cycles.values() if n.bl_idname == "OctaneMixMaterial"),
            None,
        )
    if root_octane_node is None:
        root_octane_node = last_universal_node
    if root_octane_node is not None:
        for existing_link in list(Octane_Output.inputs[0].links):
            c_nodes_tree.links.remove(existing_link)
        c_nodes_tree.links.new(root_octane_node.outputs[0], Octane_Output.inputs[0])
        Octane_Output.location = (root_octane_node.location[0] + 300, root_octane_node.location[1])

    ensure_main_material(mat, preferences, Chosen_material)

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
    rebuild_octane_separate_color_connections(mat)
    # Must run before Connect_Vray_Mapping_Node() so the OctaneAlphaImage node it
    # may create gets its "UV transform" input wired up by that pass too.
    Connect_Alpha_Clip_Texture(mat)
    Connect_Vray_Mapping_Node(mat)

    # "Ignore Alpha/Opacity Channel" final override. Several of the passes above
    # (Connect_To_Material's label matching, rebuild_octane_connections' generic
    # Alpha -> Opacity mapping, the node-group Principled unpacking code) can all
    # independently land a link on Opacity - rather than gate every one of them,
    # just strip whatever ended up on Opacity here and force it fully opaque.
    if preferences.octane_preferences.octane_ignore_alpha_clip:
        for n in c_nodes_tree.nodes:
            if n.bl_idname.startswith("Octane") and "Opacity" in n.inputs:
                opacity_input = n.inputs["Opacity"]
                while opacity_input.is_linked:
                    links.remove(opacity_input.links[0])
                try:
                    opacity_input.default_value = 1.0
                except Exception:
                    pass

    # Final cleanup: drop Octane helpers that never got wired to anything
    # (unsupported procedural/math inputs leave their partial nodes behind).
    prune_unconnected_octane_nodes(mat)

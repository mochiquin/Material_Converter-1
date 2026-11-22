"""Label-matched connection rebuilding across target render engines."""

from __future__ import annotations

from ..core.node_mappings import (
    OCTANE_NODE_MAPPING,
    resolve_octane_socket_names,
)


def rebuild_octane_connections(mat) -> None:
    """Rebuild node connections in an Octane material from Cycles node labels."""
    active_mat = mat
    cycles_nodes = active_mat.node_tree.nodes
    octane_node_tree = active_mat.node_tree
    octane_nodes = octane_node_tree.nodes
    octane_links = octane_node_tree.links

    for key, value_list in OCTANE_NODE_MAPPING.items():
        cycles_type_nodes = [n for n in cycles_nodes if n.bl_idname == key]

        for cycles_node in cycles_type_nodes:
            for value in value_list:
                octane_type_nodes = [n for n in octane_nodes if n.bl_idname == value]
                octane_node = next((n for n in octane_type_nodes if n.label == cycles_node.label), None)

                if not octane_node:
                    continue

                for output in cycles_node.outputs:
                    for link in output.links:
                        target_node = link.to_node
                        if target_node.bl_idname not in OCTANE_NODE_MAPPING:
                            continue

                        octane_target_nodes = [
                            n
                            for n in octane_nodes
                            if n.bl_idname in OCTANE_NODE_MAPPING[target_node.bl_idname]
                        ]
                        octane_target_node = next(
                            (n for n in octane_target_nodes if n.label == target_node.label),
                            None,
                        )
                        if not octane_target_node:
                            continue

                        to_socket = link.to_socket
                        output_name, input_name = resolve_octane_socket_names(
                            from_node_type=cycles_node.bl_idname,
                            from_socket_name=output.name,
                            to_node_type=target_node.bl_idname,
                            to_socket_name=to_socket.name,
                            to_socket_identifier=getattr(to_socket, "identifier", to_socket.name),
                            octane_target_type=octane_target_node.bl_idname,
                        )

                        output_socket = next((s for s in octane_node.outputs if s.name == output_name), None)
                        input_socket = next((s for s in octane_target_node.inputs if s.name == input_name), None)
                        if output_socket and input_socket and octane_target_node.name != octane_node.name:
                            octane_links.new(input_socket, output_socket)


def rebuild_octane_separate_color_connections(mat) -> None:
    """Wire up OctaneChannelPicker nodes created for Separate Color/RGB nodes."""
    node_tree = mat.node_tree
    nodes = node_tree.nodes
    links = node_tree.links

    separate_nodes = [
        n for n in nodes if n.bl_idname in ("ShaderNodeSeparateColor", "ShaderNodeSeparateRGB")
    ]

    for sep_node in separate_nodes:
        octane_source_node = None
        octane_source_output_name = None
        if sep_node.inputs[0].is_linked:
            source_node = sep_node.inputs[0].links[0].from_node
            for n in nodes:
                if n.label == source_node.label and n.bl_idname.startswith("Octane"):
                    octane_source_node = n
                    break
            if octane_source_node:
                octane_source_output_name = (
                    "Texture out"
                    if "Texture out" in octane_source_node.outputs
                    else octane_source_node.outputs[0].name
                )

        for i in range(min(3, len(sep_node.outputs))):
            out_socket = sep_node.outputs[i]
            if not out_socket.is_linked:
                continue

            picker = nodes.get(f"{sep_node.name}__ch{i}")
            if not picker:
                continue

            if octane_source_node:
                links.new(octane_source_node.outputs[octane_source_output_name], picker.inputs["Input"])

            for link in out_socket.links:
                target_node = link.to_node
                input_socket = link.to_socket

                octane_target_node = None
                for n in nodes:
                    if n.label == target_node.label and n.bl_idname.startswith("Octane"):
                        octane_target_node = n
                        break
                if not octane_target_node:
                    continue

                _, input_name = resolve_octane_socket_names(
                    from_node_type=sep_node.bl_idname,
                    from_socket_name=out_socket.name,
                    to_node_type=target_node.bl_idname,
                    to_socket_name=input_socket.name,
                    to_socket_identifier=getattr(input_socket, "identifier", input_socket.name),
                    octane_target_type=octane_target_node.bl_idname,
                )

                target_input = octane_target_node.inputs.get(input_name)
                if target_input:
                    links.new(picker.outputs["Texture out"], target_input)


def rebuild_vray_connections(mat) -> None:
    """Rebuild node connections for V-Ray materials."""
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    node_mapping = {
        "ShaderNodeMix": ["VRayNodeTexMix"],
        "ShaderNodeRGBCurve": ["VRayNodeTexRemap"],
        "ShaderNodeTexImage": ["VRayNodeMetaImageTexture"],
        "ShaderNodeNormalMap": ["VRayNodeTexNormalMapFlip"],
        "ShaderNodeOutputMaterial": ["LuxCoreNodeMatOutput"],
        "ShaderNodeMapping": ["VRayNodeUVWMapping"],
        "ShaderNodeBsdfPrincipled": ["VRayNodeBRDFVRayMtl", "VRayNodeBRDFSSS2Complex", "LuxCoreNodeMatGlass"],
        "ShaderNodeBsdfTranslucent": ["VRayNodeBRDFVRayMtl"],
        "ShaderNodeMixShader": ["LuxCoreNodeMatMix"],
        "ShaderNodeBsdfGlass": ["LuxCoreNodeMatGlass"],
        "ShaderNodeHueSaturation": ["VRayNodeColorCorrection"],
        "ShaderNodeValToRGB": ["VRayNodeTexGradRamp"],
        "ShaderNodeBump": ["LuxCoreNodeTexBump"],
        "ShaderNodeInvert": ["VRayNodeTexInvert"],
    }

    output_mapping = {
        "Normal": "Color",
        "Vector": "Mapping",
        "Alpha": "Out Alpha",
        "BSDF": "Material",
        "Result": "Color",
        "A": "Color 1",
        "B": "Color 2",
        "Color": "Color",
    }

    input_mapping = {
        "Normal": "Bump Map",
        "Coat Tint": "Coat Color",
        "Sheen Tint": "Sheen Color",
        "Base Color": "Diffuse Color",
        "Coat Normal": "Coat Bump Map",
        "Vector": "Mapping",
        "Alpha": "Opacity",
        "Fresnel IOR": "IOR",
        "Metallic": "Metalness",
        "Surface": "Material",
        "Roughness": "Reflection Glossiness",
        "Result": "Texture out",
        "A": "Color1",
        "B": "Color2",
        "Color": "Color",
    }

    for key, value_list in node_mapping.items():
        key_nodes = [n for n in nodes if n.bl_idname == key]
        for key_node in key_nodes:
            for output in key_node.outputs:
                for link in output.links:
                    target_node = link.to_node
                    if target_node.bl_idname not in node_mapping:
                        continue
                    for value in value_list:
                        value_nodes = [n for n in nodes if n.bl_idname == value]
                        vray_node = next((n for n in value_nodes if n.label == key_node.label), None)
                        if not vray_node:
                            continue
                        vray_target = next(
                            (
                                n
                                for n in nodes
                                if n.bl_idname in node_mapping[target_node.bl_idname] and n.label == target_node.label
                            ),
                            None,
                        )
                        if not vray_target:
                            continue

                        output_name = output_mapping.get(output.name, output.name)
                        to_socket = link.to_socket
                        input_name = input_mapping.get(to_socket.name, to_socket.name)

                        if target_node.bl_idname == "ShaderNodeMix":
                            input_name = (
                                to_socket.name
                                if vray_target.bl_idname == "OctaneCyclesMixColorNodeWrapper"
                                else input_mapping.get(to_socket.name, to_socket.name)
                            )
                        elif target_node.bl_idname == "ShaderNodeRGBCurve" and to_socket.name == "Color":
                            input_name = "Input Color"
                        elif target_node.bl_idname == "ShaderNodeValToRGB" and vray_target.bl_idname == "VRayNodeTexGradRamp":
                            input_name = "Texture Map"
                        elif target_node.bl_idname == "ShaderNodeBsdfTranslucent" and to_socket.name == "Color":
                            input_name = "Translucency Color"
                        elif vray_target.bl_idname == "VRayNodeColorCorrection" and to_socket.name == "Color":
                            input_name = "Source Color"
                        elif vray_target.bl_idname == "VRayNodeTexRemap" and to_socket.name == "Color":
                            input_name = "Input Color"
                        elif vray_target.bl_idname == "VRayNodeTexInvert" and to_socket.name == "Color":
                            input_name = "Texture"
                        elif target_node.bl_idname == "ShaderNodeTexImage" and to_socket.name == "Vector":
                            input_name = "Mapping"
                        elif target_node.bl_idname == "ShaderNodeNormalMap" and to_socket.name == "Color":
                            input_name = "Texmap"
                        elif to_socket.name == "Normal" and target_node.bl_idname == "ShaderNodeBsdfPrincipled":
                            input_name = "Bump Map"
                        elif to_socket.name == "Coat Normal" and target_node.bl_idname == "ShaderNodeBsdfPrincipled":
                            input_name = "Coat Bump Map"

                        out_sock = next((s for s in vray_node.outputs if s.name == output_name), None)
                        in_sock = next((s for s in vray_target.inputs if s.name == input_name), None)
                        if out_sock and in_sock:
                            links.new(in_sock, out_sock)


def rebuild_Luxcore_connections(mat) -> None:
    """Rebuild node connections for LuxCore materials."""
    cycles_nodes = mat.node_tree.nodes
    luxcore_node_tree = mat.luxcore.node_tree
    luxcore_nodes = luxcore_node_tree.nodes
    luxcore_links = luxcore_node_tree.links

    node_mapping = {
        "ShaderNodeMix": ["LuxCoreNodeTexColorMix"],
        "ShaderNodeRGBCurve": ["NodeReroute"],
        "ShaderNodeTexImage": ["LuxCoreNodeTexImagemap"],
        "ShaderNodeNormalMap": ["LuxCoreNodeTexNormalmap"],
        "ShaderNodeOutputMaterial": ["LuxCoreNodeMatOutput"],
        "ShaderNodeMapping": ["LuxCoreNodeTexMapping2D"],
        "ShaderNodeBsdfPrincipled": ["LuxCoreNodeMatDisney", "LuxCoreNodeMatGlossyTranslucent", "LuxCoreNodeMatGlass"],
        "ShaderNodeBsdfTranslucent": ["LuxCoreNodeMatGlossyTranslucent"],
        "ShaderNodeMixShader": ["LuxCoreNodeMatMix"],
        "ShaderNodeBsdfGlass": ["LuxCoreNodeMatGlass"],
        "ShaderNodeHueSaturation": ["LuxCoreNodeTexHSV"],
        "ShaderNodeValToRGB": ["LuxCoreNodeTexBand"],
        "ShaderNodeBump": ["LuxCoreNodeTexBump"],
        "ShaderNodeInvert": ["LuxCoreNodeTexInvert"],
    }

    output_mapping = {
        "Normal": "Bump",
        "Vector": "2D Mapping",
        "Alpha": "Out Alpha",
        "BSDF": "Material",
        "Result": "Color",
        "A": "First texture",
        "B": "Second texture",
        "Color": "Color",
    }

    input_mapping = {
        "Normal": "Bump",
        "Coat Tint": "Coat Color",
        "Sheen Tint": "Sheen Color",
        "Base Color": "Diffuse Color",
        "Coat Normal": "Coat Bump Map",
        "Vector": "2D Mapping",
        "Alpha": "Opacity",
        "Fresnel IOR": "IOR",
        "Metallic": "Metalness",
        "Surface": "Material",
        "Roughness": "Roughness",
        "Result": "Texture out",
        "A": "Color 1",
        "B": "Color 2",
        "Color": "Color",
    }

    for key, value_list in node_mapping.items():
        cycles_type_nodes = [n for n in cycles_nodes if n.bl_idname == key]
        for cycles_node in cycles_type_nodes:
            for value in value_list:
                luxcore_type_nodes = [n for n in luxcore_nodes if n.bl_idname == value]
                luxcore_node = next((n for n in luxcore_type_nodes if n.label == cycles_node.label), None)
                if not luxcore_node:
                    continue

                for output in cycles_node.outputs:
                    for link in output.links:
                        target_node = link.to_node
                        if target_node.bl_idname not in node_mapping:
                            continue

                        luxcore_target_nodes = [
                            n
                            for n in luxcore_nodes
                            if n.bl_idname in node_mapping[target_node.bl_idname]
                        ]
                        luxcore_target_node = next(
                            (n for n in luxcore_target_nodes if n.label == target_node.label),
                            None,
                        )
                        if not luxcore_target_node:
                            continue

                        output_name = output_mapping.get(output.name, output.name)
                        to_socket = link.to_socket
                        input_name = input_mapping.get(to_socket.name, to_socket.name)

                        if target_node.bl_idname == "ShaderNodeMixShader":
                            input_name = (
                                "Material 1"
                                if to_socket.identifier == "Shader"
                                else "Material 2"
                                if to_socket.identifier == "Shader_001"
                                else to_socket.name
                            )
                        elif target_node.bl_idname == "ShaderNodeBsdfPrincipled":
                            if luxcore_target_node.bl_idname == "LuxCoreNodeMatDisney" and to_socket.name == "Base Color":
                                input_name = "Base Color"
                        elif target_node.bl_idname == "ShaderNodeBsdfTranslucent":
                            if luxcore_target_node.bl_idname == "LuxCoreNodeMatGlossyTranslucent" and to_socket.name == "Color":
                                input_name = "Transmission Color"
                        elif target_node.bl_idname == "ShaderNodeValToRGB":
                            if to_socket.name == "Fac":
                                input_name = "Amount"
                        elif target_node.bl_idname == "ShaderNodeBsdfGlass":
                            if luxcore_target_node.bl_idname == "LuxCoreNodeMatGlass" and to_socket.name == "Color":
                                input_name = "Transmission Color"
                        elif target_node.bl_idname == "ShaderNodeBump":
                            if luxcore_target_node.bl_idname == "LuxCoreNodeTexBump" and to_socket.name == "Height":
                                input_name = "Value"
                        elif target_node.bl_idname == "ShaderNodeTexImage":
                            input_name = "2D Mapping" if to_socket.name == "Vector" else to_socket.name
                        elif target_node.bl_idname == "ShaderNodeNormalMap":
                            input_name = "Texmap" if to_socket.name == "Color" else to_socket.name
                        elif to_socket.name == "Base Color" and target_node.bl_idname == "ShaderNodeBsdfPrincipled":
                            input_name = "Bump Map"
                        elif to_socket.name == "Coat Normal" and target_node.bl_idname == "ShaderNodeBsdfPrincipled":
                            input_name = "Coat Bump Map"
                        elif to_socket.name == "Fac" and target_node.bl_idname == "ShaderNodeValToRGB":
                            input_name = "Input texture"

                        out_sock = next((s for s in luxcore_node.outputs if s.name == output_name), None)
                        in_sock = next((s for s in luxcore_target_node.inputs if s.name == input_name), None)
                        if out_sock and in_sock:
                            luxcore_links.new(in_sock, out_sock)

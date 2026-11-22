"""Node connection and texture labeling utilities."""

from __future__ import annotations

import math
from pathlib import Path

import bpy

from ..core.node_mappings import get_octane_material_prefix_map
from ..core.texture_classifier import classify_texture_filename
from ..executor.addon_helpers import get_addon_preferences
from ..executor.octane_executor import apply_octane_alpha_clip_bypass


def connect_to_closest_octane_group_node(mat) -> None:
    prefix_to_input_name = {
        "Diffuse": "Albedo",
        "Specular": "Reflection Color",
        "Metallic": "Metallic",
        "Normal": "Bump",
        "Roughness": "Roughness",
        "Gloss": "Roughness",
        "Displacement": "Displacement",
        "Bump": "Bump",
        "Transmission": "Transmission",
        "Coat Tint": "Coating",
        "Opacity": "Opacity",
    }
    node_tree = mat.node_tree
    if not node_tree:
        return

    nodes = node_tree.nodes
    links = node_tree.links
    octane_group_node = next((node for node in nodes if "Universal" in node.bl_idname), None)
    if not octane_group_node:
        return

    group_node_inputs = {inp.name: inp for inp in octane_group_node.inputs}
    other_nodes = [node for node in nodes if node != octane_group_node]

    def distance(node) -> float:
        return math.sqrt((octane_group_node.location.y - node.location.y) ** 2)

    for node in sorted(other_nodes, key=distance):
        if node.bl_idname.startswith("Octane") and node.label:
            for prefix, input_name in prefix_to_input_name.items():
                if prefix in node.label and input_name in group_node_inputs:
                    input_socket = group_node_inputs[input_name]
                    if node.outputs:
                        while input_socket.is_linked:
                            links.remove(input_socket.links[0])
                        links.new(node.outputs[0], input_socket)
                        break


def connect_to_closest_luxcore_group_node(mat) -> None:
    prefix_to_input_name = {
        "Diffuse": "Base Color",
        "Specular": "Specular",
        "Metallic": "Metallic",
        "Normal": "Bump",
        "Roughness": "Roughness",
        "Displacement": "Displacement",
        "Bump": "Bump",
        "Transmission": "Translusency Color",
        "Opacity": "Opacity",
    }
    node_tree = mat.luxcore.node_tree
    if not node_tree:
        return

    nodes = node_tree.nodes
    links = node_tree.links
    luxcore_group_node = next(
        (node for node in nodes if node.bl_idname.startswith("LuxCoreNodeMat") and "Material" in node.label),
        None,
    )
    if not luxcore_group_node:
        return

    group_node_inputs = {inp.name: inp for inp in luxcore_group_node.inputs}
    other_nodes = [node for node in nodes if node != luxcore_group_node]

    def distance(node) -> float:
        return math.sqrt((luxcore_group_node.location.y - node.location.y) ** 2)

    for node in sorted(other_nodes, key=distance):
        if node.label:
            for prefix, input_name in prefix_to_input_name.items():
                if prefix in node.label and input_name in group_node_inputs:
                    input_socket = group_node_inputs[input_name]
                    while input_socket.is_linked:
                        links.remove(input_socket.links[0])
                    if node.outputs:
                        current_output = node.outputs[2] if getattr(node, "is_normal_map", False) else node.outputs[0]
                        links.new(current_output, input_socket)
                        break


def connect_to_closest_Vray_mat(mat) -> None:
    prefix_to_input_name = {
        "Diffuse": "Diffuse Color",
        "Specular": "Specular",
        "Metallic": "Metalness",
        "Normal": "Bump Map",
        "Roughness": "Reflection Glossiness",
        "Displacement": "Displacement",
        "Bump": "Bump",
        "Opacity": "Opacity",
        "Translucency": "Translucency Color",
        "Coat Tint": "Coat Color",
    }
    node_tree = mat.node_tree
    if not node_tree:
        return

    nodes = node_tree.nodes
    links = node_tree.links
    vray_mat = next(
        (node for node in nodes if node.bl_idname.startswith("VRay") and "Material" in node.label),
        None,
    )
    if not vray_mat:
        return

    group_node_inputs = {inp.name: inp for inp in vray_mat.inputs}
    use_normal = None
    normal_texture = None
    for n in nodes:
        if n.label == "Normal" and n.bl_idname == "VRayNodeTexNormalMapFlip":
            use_normal = n
        elif n.label == "Normal" and n.bl_idname == "VRayNodeMetaImageTexture":
            normal_texture = n
    if not use_normal and normal_texture:
        use_normal = nodes.new("VRayNodeTexNormalMapFlip")
        use_normal.location = (normal_texture.location[0] + 200, normal_texture.location[1])
        use_normal.label = "Normal"
        links.new(normal_texture.outputs[0], use_normal.inputs[4])

    other_nodes = [node for node in nodes if node.bl_idname.startswith("VRay")]

    def distance(node) -> float:
        return math.sqrt((vray_mat.location.x - node.location.x) ** 2)

    sorted_nodes = sorted(other_nodes, key=distance)
    for prefix, input_name in prefix_to_input_name.items():
        if input_name not in group_node_inputs:
            continue
        input_socket = group_node_inputs[input_name]
        if input_socket.is_linked:
            continue
        for node in sorted_nodes:
            if node.label and prefix in node.label:
                if node.outputs:
                    links.new(node.outputs[0], input_socket)
                break


def connect_to_closest_Cycles_mat(mat) -> None:
    prefix_to_input_name = {
        "Diffuse": "Base Color",
        "Specular": "Specular",
        "Metallic": "Metalness",
        "Normal": "Normal",
        "Roughness": "Roughness",
        "Displacement": "Displacement",
        "Bump": "Normal",
        "Opacity": "Alpha",
        "Translucency": "Translucency Color",
        "Coat Tint": "Coat Color",
        "IOR": "IOR",
    }
    node_tree = mat.node_tree
    if not node_tree:
        return

    nodes = node_tree.nodes
    links = node_tree.links
    cycles_mat = next((node for node in nodes if node.bl_idname.startswith("Shader") and "Material" in node.label), None)
    cycles_output = next(
        (node for node in nodes if node.bl_idname == "ShaderNodeOutputMaterial" and "Cycles Output" in node.label),
        None,
    )
    eevee_output = next(
        (node for node in nodes if node.bl_idname == "ShaderNodeOutputMaterial" and "EEVEE Output" in node.label),
        None,
    )
    cycles_images = [node for node in nodes if node.bl_idname.startswith("ShaderNodeTexImage")]
    ao_textures = [node for node in cycles_images if "AO" in node.label]
    ao_nodes = [
        node
        for node in nodes
        if node.bl_idname.startswith("ShaderNodeMix")
        and any(word in node.label for word in ["Diffuse", "COLOR * AO"])
    ]
    normal_textures = [node for node in cycles_images if "Normal" in node.label]
    normal_nodes = [node for node in nodes if node.bl_idname.startswith("ShaderNodeNormalMap")]
    bump_textures = [node for node in cycles_images if "Bump" in node.label]
    bump_nodes = [node for node in nodes if node.bl_idname.startswith("ShaderNodeBump")]
    disp_textures = [node for node in cycles_images if "Displacement" in node.label]
    disp_nodes = [
        node for node in nodes if node.bl_idname.startswith("ShaderNodeDisplacement") and "Displacement" in node.label
    ]

    if not cycles_mat:
        return

    group_node_inputs = {inp.name: inp for inp in cycles_mat.inputs}
    bump_node = bump_nodes[0] if bump_nodes else None
    if bump_textures:
        bump_tex = bump_textures[0]
        if not bump_node:
            bump_node = nodes.new("ShaderNodeBump")
            bump_node.label = "Bump"
        links.new(bump_tex.outputs[0], bump_node.inputs[2])
        links.new(bump_node.outputs[0], cycles_mat.inputs[1])
        bump_node.location = (bump_tex.location[0] + 300, bump_tex.location[1])

    if normal_textures:
        normal_tex = normal_textures[0]
        if normal_nodes:
            normal_node = normal_nodes[0]
        else:
            normal_node = nodes.new("ShaderNodeNormalMap")
            normal_node.location = (normal_tex.location[0] + 200, normal_tex.location[1])
            normal_node.label = "Normal"
        links.new(normal_tex.outputs[0], normal_node.inputs[1])
        if not bump_textures:
            links.new(normal_node.outputs[0], cycles_mat.inputs[5])
        elif bump_node:
            links.new(normal_node.outputs[0], bump_node.inputs[3])
            bump_node.location = (normal_node.location[0] + 300, normal_node.location[1])

    if disp_textures and cycles_output and eevee_output:
        disp_tex = disp_textures[0]
        disp_node = disp_nodes[0] if disp_nodes else nodes.new("ShaderNodeDisplacement")
        disp_node.label = "Displacement"
        links.new(disp_tex.outputs[0], disp_node.inputs[0])
        links.new(disp_node.outputs[0], cycles_output.inputs[2])
        links.new(disp_node.outputs[0], eevee_output.inputs[2])
        disp_node.location = (disp_tex.location[0] + 600, disp_tex.location[1])

    diffuse_node = next((d for d in nodes if "Diffuse" in d.label and d.bl_idname != "ShaderNodeMix"), None)
    if ao_textures and diffuse_node:
        ao_tex = ao_textures[0]
        if ao_nodes:
            ao_node = ao_nodes[0]
        else:
            ao_node = nodes.new("ShaderNodeMix")
            ao_node.label = "Diffuse"
            ao_node.blend_type = "MULTIPLY"
            ao_node.data_type = "RGBA"
        ao_node.location = (diffuse_node.location[0] + 300, diffuse_node.location[1])
        links.new(ao_tex.outputs[0], ao_node.inputs[7])
        links.new(diffuse_node.outputs[0], ao_node.inputs[6])
        links.new(ao_node.outputs[1], cycles_mat.inputs[0])

    other_nodes = [
        node for node in nodes if node.bl_idname.startswith("Shader") and node.bl_idname != "ShaderNodeOutputMaterial"
    ]

    def distance(node) -> float:
        return math.sqrt((cycles_mat.location.x + node.location.x) ** 2)

    for node in sorted(other_nodes, key=distance):
        if not node.label:
            continue
        for prefix, input_name in prefix_to_input_name.items():
            if prefix in node.label and input_name in group_node_inputs:
                input_socket = group_node_inputs[input_name]
                while input_socket.is_linked:
                    links.remove(input_socket.links[0])
                if node.outputs:
                    current_output = (
                        node.outputs[2]
                        if (node.label == "Diffuse" and node.bl_idname == "ShaderNodeMix")
                        else node.outputs[0]
                    )
                    links.new(current_output, input_socket)
                    if node.label == "AO Multiply":
                        links.new(node.outputs[2], cycles_mat.inputs[0])


def Connect_Poliigon(mat) -> None:
    engine = bpy.context.scene.render.engine
    node_tree = mat.luxcore.node_tree if engine == "LUXCORE" else mat.node_tree
    if not node_tree:
        return

    nodes = node_tree.nodes
    links = node_tree.links

    if engine == "LUXCORE":
        material_node = next(
            (node for node in nodes if node.bl_idname.startswith("LuxCoreNodeMat") and "Material" in node.label),
            None,
        )
        other_nodes = [node for node in nodes if node != material_node and node.bl_idname.startswith("LuxCore")]
        prefix_to_input_name = {
            "Diffuse": "Base Color",
            "REFL": "Specular",
            "Metallic": "Metallic",
            "METALNESS": "Metallic",
            "NRM": "Bump",
            "NORMAL": "Bump",
            "GLOSS": "Roughness",
            "ROUGHNESS": "Roughness",
            "Displacement": "Displacement",
            "BUMP": "Bump",
            "Transmission": "Translusency Color",
            "Coat Tint": "Coat Color",
        }
    elif engine == "octane":
        material_node = next(
            (node for node in nodes if node.bl_idname.startswith("Octane") and "Material" in node.label),
            None,
        )
        other_nodes = [node for node in nodes if node != material_node and node.bl_idname.startswith("Octane")]
        prefix_to_input_name = {
            "Diffuse": "Albedo",
            "REFL": "Specular",
            "Metallic": "Metallic",
            "METALNESS": "Metallic",
            "NRM": "Bump",
            "NORMAL": "Bump",
            "GLOSS": "Roughness",
            "ROUGHNESS": "Roughness",
            "Displacement": "Displacement",
            "BUMP": "Bump",
            "Transmission": "Transmission",
            "Coat Tint": "Coating",
        }
    elif engine == "VRAY_RENDER_RT":
        material_node = next(
            (node for node in nodes if node.bl_idname.startswith("VRay") and "Material" in node.label),
            None,
        )
        other_nodes = [node for node in nodes if node != material_node and node.bl_idname.startswith("VRay")]
        prefix_to_input_name = {
            "Diffuse": "Albedo",
            "REFL": "Specular",
            "Metallic": "Metallic",
            "METALNESS": "Metallic",
            "NRM": "Bump",
            "NORMAL": "Bump",
            "GLOSS": "Roughness",
            "ROUGHNESS": "Roughness",
            "Displacement": "Displacement",
            "BUMP": "Bump",
            "Transmission": "Transmission",
            "Coat Tint": "Coating",
        }
    else:
        return

    if not material_node:
        return

    group_node_inputs = {inp.name: inp for inp in material_node.inputs}

    def distance(node) -> float:
        return math.sqrt((material_node.location.y - node.location.y) ** 2)

    for node in sorted(other_nodes, key=distance):
        if not node.label:
            continue
        effective_label = node.label
        if any(item in node.label for item in ("COL", "COLOR", "COLOR * AO")):
            effective_label = "Diffuse"
        elif any(item in node.label for item in ("ROUGHNESS", "GLOSSINESS")):
            effective_label = "Roughness"

        for prefix, input_name in prefix_to_input_name.items():
            if prefix in effective_label.upper() and input_name in group_node_inputs:
                input_socket = group_node_inputs[input_name]
                if not input_socket.is_linked and node.outputs:
                    links.new(node.outputs[0], input_socket)
                    break


def Connect_Vray_Mapping_Node(mat) -> None:
    node_tree = mat.node_tree
    render_engine = bpy.context.scene.render.engine
    if not node_tree:
        return

    nodes = node_tree.nodes
    links = node_tree.links

    if render_engine == "VRAY_RENDER_RT":
        image_nodes = [node for node in nodes if node.bl_idname.startswith("VRayNodeMetaImageTexture")]
        mapping_nodes = [node for node in nodes if node.bl_idname.startswith("VRayNodeUVWMapping")]
        input_nr = 0
        mapping_type = "VRayNodeUVWMapping"
    elif render_engine == "octane":
        image_nodes = [
            node for node in nodes if any(z in node.bl_idname for z in ("OctaneAlphaImage", "OctaneRGBImage"))
        ]
        mapping_nodes = [node for node in nodes if node.bl_idname.startswith("Octane3DTransformation")]
        input_nr = 5
        mapping_type = "Octane3DTransformation"
    else:
        return

    if image_nodes:
        mapping_node = mapping_nodes[0] if mapping_nodes else nodes.new(mapping_type)
        mapping_node.location = (image_nodes[0].location[0] - 300, image_nodes[0].location[1])
        for image in image_nodes:
            for input_socket in image.inputs:
                if not input_socket.is_linked:
                    links.new(mapping_node.outputs[0], image.inputs[input_nr])


def label_texture_nodes(mat) -> None:
    """Label unlabeled texture nodes using ``core.texture_classifier``."""
    engine = bpy.context.scene.render.engine
    for image in bpy.data.images:
        if "Render Result" not in image.name and "Vray" not in image.name and image.filepath:
            full_filepath = bpy.path.abspath(image.filepath)
            image.name = Path(full_filepath).name

    node_tree = mat.luxcore.node_tree if engine == "LUXCORE" else mat.node_tree
    if not node_tree:
        return

    node_types = {
        "VRAY_RENDER_RT": "VRayNodeMetaImageTexture",
        "octane": "OctaneRGBImage",
        "LUXCORE": "LuxCoreNodeTexImagemap",
        "CYCLES": "ShaderNodeTexImage",
    }
    node_type = node_types.get(engine)
    if not node_type:
        return

    image_nodes = [node for node in node_tree.nodes if node.bl_idname.startswith(node_type)]
    for node in image_nodes:
        if not node.label and getattr(node, "image", None):
            classification = classify_texture_filename(node.image.name)
            if classification.category:
                node.label = classification.category


def Connect_To_Material(mat) -> None:
    engine = bpy.context.scene.render.engine
    node_tree = mat.luxcore.node_tree if engine == "LUXCORE" else mat.node_tree
    if not node_tree:
        return

    nodes = node_tree.nodes
    links = node_tree.links

    if engine == "LUXCORE":
        material_node = next(
            (node for node in nodes if node.bl_idname.startswith("LuxCoreNodeMat") and "Material" in node.label),
            None,
        )
        other_nodes = [node for node in nodes if node != material_node and node.bl_idname.startswith("LuxCore")]
        prefix_to_input_name = {
            ("Diffuse", "COL", "COLOR", "COLOR * AO"): "Base Color",
            ("Specular", "REFL", "REFLECTION"): "Specular",
            ("Metallic", "METALNESS", "METAL"): "Metallic",
            ("NRM", "NORMAL", "Normal Map"): "Bump",
            ("GLOSS", "ROUGHNESS", "Invert Gloss", "Roughness"): "Roughness",
            ("Displacement", "DISP", "HEIGHT"): "Displacement",
            ("BUMP",): "Bump",
            ("Opacity", "OPACITY"): "Opacity",
            ("Transmission", "TRANS"): "Transmission Color",
            ("IOR", "ior"): "IOR",
            ("Coat", "COATING"): "Coat Color",
        }
        if material_node and material_node.bl_idname == "LuxCoreNodeMatGlossyTranslucent":
            for key, value in list(prefix_to_input_name.items()):
                if value == "Specular":
                    prefix_to_input_name[key] = "Specular Color"
                elif value == "Base Color":
                    prefix_to_input_name[key] = "Diffuse Color"
    elif engine == "octane":
        material_node = next(
            (node for node in nodes if node.bl_idname.startswith("Octane") and "Material" in node.label),
            None,
        )
        other_nodes = [node for node in nodes if node != material_node and node.bl_idname.startswith("Octane")]
        prefs = get_addon_preferences()
        base_mat = prefs.octane_preferences.octane_base_material if prefs else "UNIVERSAL"
        prefix_to_input_name = get_octane_material_prefix_map(base_mat)
    elif engine == "VRAY_RENDER_RT":
        material_node = next(
            (node for node in nodes if node.bl_idname.startswith("VRay") and "Material" in node.label),
            None,
        )
        other_nodes = [node for node in nodes if node != material_node and node.bl_idname.startswith("VRay")]
        prefix_to_input_name = {
            ("Diffuse", "COL", "COLOR", "COLOR * AO"): "Diffuse Color",
            ("Specular", "REFL", "REFLECTION"): "Reflection Color",
            ("Metallic", "METALNESS", "METAL"): "Metalness",
            ("NRM", "NORMAL", "Normal Map"): "Bump Map",
            ("GLOSS", "ROUGHNESS"): "Reflection Glossiness",
            ("Displacement", "DISP", "HEIGHT"): "Displacement",
            ("BUMP",): "Bump Map",
            ("SSS",): "Translucency Color",
            ("Transmission", "TRANS"): "Transmission",
            ("Opacity", "OPACITY"): "Opacity",
            ("Coat", "COATING"): "Coat Color",
        }
    else:
        return

    if not material_node:
        return

    group_node_inputs = {inp.name: inp for inp in material_node.inputs}

    def distance(node) -> float:
        return math.sqrt(
            (material_node.location.x - node.location.x) ** 2
            + (material_node.location.y - node.location.y) ** 2
        )

    for node in sorted(other_nodes, key=distance):
        if not node.label:
            continue
        node_label_upper = node.label.upper()
        for prefixes, input_name in prefix_to_input_name.items():
            if any(prefix.upper() in node_label_upper for prefix in prefixes) and input_name in group_node_inputs:
                input_socket = group_node_inputs[input_name]
                if not input_socket.is_linked and node.outputs:
                    if node.bl_idname == "LuxCoreNodeTexImagemap" and any(
                        x in node.label for x in ("NRM", "NORMAL", "Normal Map")
                    ):
                        current_output = node.outputs[2]
                    elif node.bl_idname == "VRayNodeMetaImageTexture" and any(
                        label in node.label for label in ("GLOSS", "ROUGHNESS", "Metallic", "METALNESS", "METAL")
                    ):
                        current_output = node.outputs[3]
                    else:
                        current_output = node.outputs[0]

                    if node.bl_idname == "VRayNodeMetaImageTexture" and any(
                        z in node.label for z in ("SSS", "Subsurface")
                    ):
                        links.new(node.outputs[0], material_node.inputs["Fog Color"])
                        material_node.inputs["Refraction Color"].value = (0.248867, 0.248867, 0.248867)
                        if material_node.bl_idname == "VRayNodeBRDFVRayMtl":
                            material_node.inputs[49].value = "6"

                    links.new(current_output, input_socket)
                    break


def Connect_Alpha_Clip_Texture(mat) -> None:
    """Delegate Alpha-clip bypass to ``executor.octane_executor``."""
    if bpy.context.scene.render.engine != "octane":
        return
    apply_octane_alpha_clip_bypass(mat)


def reorganize_material_nodes(mat, Render_Engine: str) -> None:
    nodes = mat.node_tree.nodes
    cycles_shader_nodes = [node for node in nodes if node.bl_idname.startswith("Shader")]
    if not cycles_shader_nodes:
        return

    if Render_Engine == "VRAY_RENDER_RT":
        adjusting_nodes = [node for node in nodes if node.bl_idname.startswith("VRay")]
        key_attr = "y"
    elif Render_Engine == "octane":
        adjusting_nodes = [node for node in nodes if node.bl_idname.startswith("Octane")]
        adjusting_nodes.extend([node for node in nodes if node.label == "Octane Output"])
        key_attr = "x"
    else:
        return

    if not adjusting_nodes:
        return

    border_cycles_node = min(cycles_shader_nodes, key=lambda n: getattr(n.location, key_attr))
    new_node_adjustment = getattr(border_cycles_node.location, key_attr)
    if any(getattr(node.location, key_attr) > new_node_adjustment for node in adjusting_nodes):
        highest_node = max(adjusting_nodes, key=lambda n: getattr(n.location, key_attr))
        shift = abs(getattr(highest_node.location, key_attr) - new_node_adjustment) + 200
        for node in adjusting_nodes:
            setattr(node.location, key_attr, getattr(node.location, key_attr) - shift)

    node_groups: dict[float, list] = {}
    for node in adjusting_nodes:
        node_groups.setdefault(node.location.x, []).append(node)

    for group_index, (_, group) in enumerate(sorted(node_groups.items(), key=lambda x: x[0])):
        new_x = group_index * 300
        for node in sorted(group, key=lambda n: -n.location.y):
            node.location.x = new_x

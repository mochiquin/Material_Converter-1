"""Create or reset a metallic Octane material on the active object."""

from __future__ import annotations

import math

import bpy

from ..executor.addon_helpers import get_addon_preferences
from ..scripts.nodes import setup_ao_nodes, setup_disp_nodes


def _switch_node_editors_to_shader(ctx) -> None:
    for screen in ctx.workspace.screens:
        for area in screen.areas:
            if area.type == "NODE_EDITOR" and area.ui_type not in ("GeometryNodeTree", "CompositorNodeTree"):
                area.ui_type = "ShaderNodeTree"


def create_Metallic_material(mat, preferences, render_engine: str) -> None:
    material_names_to_remove = [
        "OctaneClippingMaterial",
        "OctaneCompositeMaterial",
        "OctaneDiffuseMaterial",
        "OctaneGlossyMaterial",
        "OctaneHairMaterial",
        "OctaneLayeredMaterial",
        "OctaneMixMaterial",
        "OctaneNullMaterial",
        "OctanePortalMaterial",
        "OctaneShadowCatcherMaterial",
        "OctaneSpecularMaterial",
        "OctaneToonMaterial",
    ]
    use_metallic = preferences.octane_preferences.use_metallic_material
    chosen_material = preferences.octane_preferences.octane_base_material

    albedo_name = "Diffuse color"
    metallic_input = "Metallic"
    if not use_metallic:
        if chosen_material == "UNIVERSAL":
            material_names_to_remove.append("OctaneStandardSurfaceMaterial")
            material_names_to_remove.append("OctaneMetallicMaterial")
            material_type = "OctaneUniversalMaterial"
            albedo_name = "Albedo"
            roughness_name = "Roughness"
            old_specular = "Specular"
            metallic_input = "Metallic"
        else:
            material_names_to_remove.append("OctaneUniversalMaterial")
            material_names_to_remove.append("OctaneMetallicMaterial")
            material_type = "OctaneStandardSurfaceMaterial"
            albedo_name = "Base color"
            metallic_input = "Metalness"
            roughness_name = "Specular roughness"
            old_specular = "Specular weight"
    else:
        material_names_to_remove.append("OctaneUniversalMaterial")
        material_names_to_remove.append("OctaneStandardSurfaceMaterial")
        material_type = "OctaneMetallicMaterial"
        roughness_name = "Roughness"
        old_specular = "Specular map"

    nodetree = mat.node_tree
    nodes = nodetree.nodes
    links = nodetree.links

    diffuse_texture = [node for node in nodes if node.bl_idname.startswith("OctaneRGBImage") and node.label == "Diffuse"]
    ao_texture = [node for node in nodes if node.bl_idname.startswith("OctaneRGBImage") and node.label == "AO"]
    material_node = [node for node in nodes if node.bl_idname.startswith(material_type) and node.label == "Material"]
    material_output = [
        node for node in nodes if node.bl_idname.startswith("ShaderNodeOutputMaterial") and node.label == "Octane Output"
    ]
    ao_node = [
        node for node in nodes if node.bl_idname.startswith("OctaneCyclesMixColorNodeWrapper") and node.label == "Diffuse AO"
    ]
    displacement_texture = [
        node for node in nodes if node.bl_idname.startswith("OctaneRGBImage") and node.label == "Displacement"
    ]
    displacement_node = [
        node
        for node in nodes
        if ("OctaneTextureDisplacement" in node.bl_idname or "OctaneVertexDisplacement" in node.bl_idname)
        and ("Displacement" in node.label or "COLOR * AO" in node.label)
    ]

    diffuse_color = []
    roughness_value = []
    specular_value = []

    for n in list(nodes):
        if n.bl_idname in material_names_to_remove:
            for inp in n.inputs:
                if inp.name in ("Albedo", "Base Color", "Base color"):
                    diffuse_color.append(inp.default_value[0])
                    diffuse_color.append(inp.default_value[1])
                    diffuse_color.append(inp.default_value[2])
                elif inp.name in ("Roughness", "Specular Roughness", "Specular roughness"):
                    roughness_value.append(inp.default_value)
                elif inp.name in ("Specular", "Specular map", "Specular weight"):
                    specular_value.append(inp.default_value)
            nodes.remove(n)

    delete_nodes = [
        node for node in nodes if node.bl_idname.startswith("Octane") and any(z in node.label for z in ("help", "Viewport"))
    ]
    for nd in delete_nodes:
        nodes.remove(nd)

    texture_node = next((n for n in nodes if n.bl_idname == "OctaneRGBImage"), None)

    if material_output:
        material_output_node = material_output[0]
    else:
        material_output_node = nodetree.nodes.new("ShaderNodeOutputMaterial")
        material_output_node.label = "Octane Output"

    if material_node:
        material = material_node[0]
        material.label = "Material"
    else:
        material = nodetree.nodes.new(material_type)
        material.inputs[roughness_name].default_value = 0
        material.label = "Material"
        if use_metallic:
            material.inputs[roughness_name].default_value = preferences.octane_preferences.octane_metallic_roughness
            material.inputs["Specular map"].default_value = preferences.octane_preferences.octane_metallic_specular_color
            material.inputs["BRDF model"].default_value = preferences.octane_preferences.octane_metallic_BRDF
            material.inputs["Metallic reflection mode"].default_value = (
                preferences.octane_preferences.octane_metallic_reflection
            )
        else:
            material.inputs[albedo_name].default_value = preferences.octane_preferences.octane_albedo_color_addon
            material.inputs[roughness_name].default_value = preferences.octane_preferences.octane_base_roughness
            material.inputs[old_specular].default_value = preferences.octane_preferences.octane_base_specular
            material.inputs[metallic_input].default_value = 1

    if not use_metallic:
        material.inputs[metallic_input].default_value = 1
        if chosen_material != "UNIVERSAL":
            material.inputs["Transmission weight"].default_value = 0
            material.inputs["Subsurface weight"].default_value = 0
            material.inputs["Coating weight"].default_value = 0
            material.inputs["Sheen weight"].default_value = 0
            material.inputs["Emission weight"].default_value = 0
            material.inputs["Film thickness (nm)"].default_value = 0
        else:
            material.inputs["Coating"].default_value = (0, 0, 0)
            material.inputs["Sheen"].default_value = (0, 0, 0)

    if texture_node:
        material.location = (texture_node.location[0] + 600, texture_node.location[1])

    if roughness_value:
        material.inputs[roughness_name].default_value = roughness_value[0]
    if specular_value:
        material.inputs[old_specular].default_value = specular_value[0]

    if material.bl_idname != "OctaneMetallicMaterial":
        material.inputs["Diffuse BRDF model"].default_value = preferences.octane_preferences.octane_BRDF
        if chosen_material == "UNIVERSAL":
            material.inputs["[OctaneGroupTitle]Transmission Layer"].default_value = (
                preferences.octane_preferences.octane_transmission
            )
            material.inputs["BSDF model"].default_value = preferences.octane_preferences.octane_BSDF
            material.inputs["Metallic reflection mode"].default_value = (
                preferences.octane_preferences.octane_metallic_type
            )
        else:
            material.inputs["Dispersion mode"].default_value = preferences.octane_preferences.octane_Dispersion_mode

    if ao_texture:
        ao_tex = ao_texture[0]
        ao_mix = (
            ao_node[0]
            if ao_node
            else setup_ao_nodes(render_engine, nodes, links, diffuse_texture, ao_tex, diffuse_color=None)
        )
        links.new(ao_mix.outputs[0], material.inputs[albedo_name])

    if displacement_texture:
        disp_tex = displacement_texture[0]
        disp_node = (
            displacement_node[0]
            if displacement_node
            else setup_disp_nodes(preferences, render_engine, nodes, links, disp_tex, displacement_node)
        )
        links.new(disp_node.outputs["Displacement out"], material.inputs["Displacement"])

    if material.bl_idname == "OctaneStandardSurfaceMaterial":
        material.inputs["Transmission weight"].default_value = 0

    links.new(material.outputs[0], material_output_node.inputs[0])
    material_output_node.location = (material.location[0] + 300, material.location[1])


def Connect_To_Metal(mat, context=None) -> None:
    ctx = context if context is not None else bpy.context
    engine = ctx.scene.render.engine
    node_tree = mat.node_tree
    if not node_tree:
        return

    nodes = node_tree.nodes
    links = node_tree.links

    material_node = None
    engine_name = engine
    other_nodes = []
    prefix_to_input_name = {}

    if engine == "octane":
        material_node = next(
            (node for node in nodes if node.bl_idname.startswith("Octane") and "Material" in node.label),
            None,
        )
        engine_name = "Octane"
        other_nodes = [node for node in nodes if node != material_node and node.bl_idname.startswith("Octane")]
        prefix_to_input_name = {
            ("Metallic", "METALNESS", "METAL"): "Metalness",
            ("NRM", "NORMAL", "Normal Map"): "Normal",
            ("SSS", "Subsurface"): "Subsurface color",
            ("Displacement", "DISP", "HEIGHT", "displacement"): "Displacement",
            ("BUMP",): "Bump",
            ("Opacity", "OPACITY"): "Opacity",
            ("Transmission", "TRANS"): "Transmission",
            ("Coat", "COATING"): "Coating",
        }
        prefs = get_addon_preferences(context=ctx)
        use_metallic = bool(prefs and prefs.octane_preferences.use_metallic_material)
        base_mat = prefs.octane_preferences.octane_base_material if prefs else "UNIVERSAL"
        if not use_metallic:
            if base_mat == "UNIVERSAL":
                prefix_to_input_name[("Diffuse", "COL", "COLOR", "COLOR * AO")] = "Albedo"
                prefix_to_input_name[("GLOSS", "ROUGHNESS", "Roughness")] = "Roughness"
                prefix_to_input_name[("Specular", "REFL", "REFLECTION")] = "Specular"
            else:
                prefix_to_input_name[("Diffuse", "COL", "COLOR", "COLOR * AO")] = "Base color"
                prefix_to_input_name[("GLOSS", "ROUGHNESS", "Roughness")] = "Specular roughness"
                prefix_to_input_name[("Specular", "REFL", "REFLECTION")] = "Specular"
        else:
            prefix_to_input_name[("Diffuse", "COL", "COLOR", "COLOR * AO")] = "Diffuse color"
            prefix_to_input_name[("GLOSS", "ROUGHNESS", "Roughness")] = "Roughness"
            prefix_to_input_name[("Specular", "REFL", "REFLECTION")] = "Specular map"

    if not material_node:
        print(f"No {engine_name} group node found in material '{mat.name}'.")
        return

    group_node_inputs = {inp.name: inp for inp in material_node.inputs}

    def distance(node) -> float:
        return math.sqrt(
            (material_node.location.x - node.location.x) ** 2 + (material_node.location.y - node.location.y) ** 2
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


def create_metal(context=None) -> None:
    """Entry point for ``material.create_metal`` operator."""
    ctx = context if context is not None else bpy.context
    preferences = get_addon_preferences(context=ctx)
    if preferences is None:
        raise RuntimeError("Material Converter preferences not found.")

    _switch_node_editors_to_shader(ctx)

    obj = getattr(ctx, "object", None) or getattr(ctx, "active_object", None)
    mat = obj.active_material if obj else None
    if not mat:
        raise RuntimeError("No active material found.")
    if not mat.use_nodes:
        mat.use_nodes = True
    nodetree = mat.node_tree
    if not nodetree:
        raise RuntimeError("Active material has no node tree.")

    if not nodetree.nodes:
        m = nodetree.nodes.new("ShaderNodeOutputMaterial")
        m.label = "Octane Output"

    create_Metallic_material(mat, preferences, ctx.scene.render.engine)
    Connect_To_Metal(mat, context=ctx)

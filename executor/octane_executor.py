"""Blender-side execution of pure core/ Octane conversion plans."""

from __future__ import annotations

from typing import Any

from ..core.graph_planner import (
    ConversionWarning,
    audit_material_graph,
    plan_alpha_clip_bypass,
)
from ..core.node_mappings import (
    compute_octane_mapping_transform,
    plan_separate_color_pickers,
    resolve_math_node,
)
from .addon_helpers import get_addon_preferences
from .graph_serializer import serialize_material_graph


def log_material_audit_warnings(mat: Any) -> list[ConversionWarning]:
    """Audit a material graph using core/ and emit explicit warnings."""
    graph = serialize_material_graph(mat)
    warnings = audit_material_graph(graph)
    for warning in warnings:
        print(f"[Material Converter][{warning.code}] {mat.name}: {warning.message}")
    return warnings


def apply_octane_separate_color(mat: Any, separate_nodes: list[Any]) -> None:
    """Create OctaneChannelPicker nodes planned by ``core.node_mappings``."""
    nodes = mat.node_tree.nodes
    for cycles_separate in separate_nodes:
        separate_mode = getattr(cycles_separate, "mode", "RGB")
        linked_indices = [
            ch_index
            for ch_index in range(min(3, len(cycles_separate.outputs)))
            if cycles_separate.outputs[ch_index].is_linked
        ]
        loc = (float(cycles_separate.location[0]), float(cycles_separate.location[1]))
        plans = plan_separate_color_pickers(
            node_name=cycles_separate.name,
            label=cycles_separate.label,
            mode=separate_mode,
            linked_output_indices=linked_indices,
            location=loc,
        )
        for plan in plans:
            picker = nodes.get(plan.picker_name)
            if not picker:
                picker = nodes.new("OctaneChannelPicker")
                picker.name = plan.picker_name
            picker.label = plan.label
            picker.location = plan.location
            picker.inputs["Channel"].default_value = plan.channel_index_value
            picker.inputs["Conversion"].default_value = plan.conversion_value


def apply_octane_math_nodes(mat: Any, math_nodes: list[Any]) -> list[str]:
    """Convert supported Cycles Math nodes and return explicit warnings for unsupported ones."""
    node_tree = mat.node_tree
    nodes = node_tree.nodes
    links = node_tree.links
    warnings: list[str] = []

    for cycles_math in math_nodes:
        resolution = resolve_math_node(cycles_math.operation, cycles_math.name)
        if not resolution.supported or not resolution.octane_bl_idname:
            if resolution.warning:
                warnings.append(resolution.warning)
                print(f"[Material Converter][Math Warning] {resolution.warning}")
            continue

        octane_math_name = f"{cycles_math.name} [Octane {resolution.operation.title()}]"
        octane_math = next(
            (n for n in nodes if n.bl_idname == resolution.octane_bl_idname and n.name == octane_math_name),
            None,
        )
        if not octane_math:
            octane_math = nodes.new(resolution.octane_bl_idname)
            octane_math.name = octane_math_name
            octane_math.location = (cycles_math.location[0] + 1650, cycles_math.location[1])
        octane_math.label = cycles_math.label

        for octane_socket_name, cycles_input in (
            ("Texture 1", cycles_math.inputs[0]),
            ("Texture 2", cycles_math.inputs[1]),
        ):
            if cycles_input.is_linked:
                continue
            const_name = f"{octane_math_name} {octane_socket_name} constant"
            const_node = nodes.get(const_name)
            if not const_node:
                const_node = nodes.new("OctaneFloatValue")
                const_node.name = const_name
                y_offset = 0 if octane_socket_name == "Texture 1" else -150
                const_node.location = (octane_math.location[0] - 300, octane_math.location[1] + y_offset)
            const_node.label = f"{cycles_math.label} constant"
            const_node.a_value = (cycles_input.default_value,) * 3
            links.new(const_node.outputs["Float out"], octane_math.inputs[octane_socket_name])

    return warnings


def apply_octane_mapping_nodes(mat: Any, mapping_nodes: list[Any]) -> None:
    """Convert Cycles Mapping nodes using ``compute_octane_mapping_transform``."""
    nodes = mat.node_tree.nodes
    for cycles_mapping in mapping_nodes:
        octane_mapping_name = cycles_mapping.name.replace("Mapping", "3D transformation")
        octane_mapping = next(
            (n for n in nodes if n.bl_idname == "Octane3DTransformation" and n.name == octane_mapping_name),
            None,
        )
        if not octane_mapping:
            octane_mapping = nodes.new("Octane3DTransformation")
            octane_mapping.location = (cycles_mapping.location[0] + 1650, cycles_mapping.location[1])
            octane_mapping.name = octane_mapping_name

        octane_mapping.label = cycles_mapping.label
        loc = cycles_mapping.inputs[1].default_value
        rot = cycles_mapping.inputs[2].default_value
        scl = cycles_mapping.inputs[3].default_value
        transform = compute_octane_mapping_transform(
            location=(float(loc[0]), float(loc[1]), float(loc[2])),
            rotation_rad=(float(rot[0]), float(rot[1]), float(rot[2])),
            scale=(float(scl[0]), float(scl[1]), float(scl[2])),
        )
        if transform.warning:
            print(f"[Material Converter][Mapping Warning] {cycles_mapping.name}: {transform.warning}")

        for idx in range(3):
            octane_mapping.inputs[1].default_value[idx] = transform.rotation_deg[idx]
            octane_mapping.inputs[2].default_value[idx] = transform.scale[idx]
            octane_mapping.inputs[3].default_value[idx] = transform.translation[idx]


def apply_octane_alpha_clip_bypass(mat: Any) -> None:
    """Execute Alpha-clip bypass planned by ``core.graph_planner.plan_alpha_clip_bypass``."""
    prefs = get_addon_preferences()
    ignore_alpha = bool(
        prefs and getattr(prefs.octane_preferences, "octane_ignore_alpha_clip", False)
    )
    graph = serialize_material_graph(mat)
    plans = plan_alpha_clip_bypass(graph, ignore_alpha_clip=ignore_alpha)
    if not plans:
        return

    node_tree = mat.node_tree
    nodes = node_tree.nodes
    links = node_tree.links

    for plan in plans:
        principled = nodes.get(plan.principled_node)
        image_node = nodes.get(plan.source_image_node)
        if not principled or not image_node or not getattr(image_node, "image", None):
            continue

        octane_material = next(
            (n for n in nodes if n.label == principled.label and "Opacity" in n.inputs),
            None,
        )
        if not octane_material:
            octane_material = next(
                (
                    n
                    for n in nodes
                    if n.bl_idname in ("OctaneUniversalMaterial", "OctaneStandardSurfaceMaterial")
                    and "Opacity" in n.inputs
                ),
                None,
            )
        if not octane_material:
            continue

        octane_alpha_image = nodes.get(plan.alpha_node_name)
        if not octane_alpha_image:
            octane_alpha_image = nodes.new("OctaneAlphaImage")
            octane_alpha_image.name = plan.alpha_node_name
            octane_alpha_image.location = (
                octane_material.location[0] - 300,
                octane_material.location[1] - 300,
            )

        octane_alpha_image.label = f"{image_node.label} Alpha".strip() if image_node.label else "Alpha"
        octane_alpha_image.image = image_node.image
        octane_alpha_image.inputs["Legacy gamma"].default_value = 1.0
        links.new(octane_alpha_image.outputs[0], octane_material.inputs["Opacity"])

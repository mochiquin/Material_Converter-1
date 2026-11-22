"""Unit tests for pure graph planning, alpha-clip tracing, and audit."""

from __future__ import annotations

import pytest

from core.graph_planner import (
    SerializedLink,
    SerializedMaterialGraph,
    SerializedNode,
    SerializedSocket,
    audit_material_graph,
    compute_branch_labels,
    find_alpha_clip_source_image,
    plan_alpha_clip_bypass,
    trace_alpha_source,
)


def _gltf_mask_graph(
    *,
    cutoff: float | None = 0.5,
    image_socket: str = "Alpha",
    has_alpha: bool = True,
) -> SerializedMaterialGraph:
    """Principled <- Subtract <- LessThan <- image, as the glTF importer builds it."""
    less_than_inputs = (
        SerializedSocket("Value", "Value", is_linked=True, value=1.0),
        SerializedSocket("Value", "Value_001", is_linked=False, value=cutoff),
    )
    return SerializedMaterialGraph(
        material_name="GltfMask",
        nodes=(
            SerializedNode(name="Principled BSDF", bl_idname="ShaderNodeBsdfPrincipled"),
            SerializedNode(name="Subtract", bl_idname="ShaderNodeMath", operation="SUBTRACT"),
            SerializedNode(
                name="LessThan",
                bl_idname="ShaderNodeMath",
                operation="LESS_THAN",
                inputs=less_than_inputs,
            ),
            SerializedNode(
                name="Tex",
                bl_idname="ShaderNodeTexImage",
                image_name="hair_a.png",
                image_has_alpha=has_alpha,
            ),
        ),
        links=(
            SerializedLink("Subtract", "Value", "Principled BSDF", "Alpha", "Alpha"),
            SerializedLink("LessThan", "Value", "Subtract", "Value", "Value_001"),
            SerializedLink("Tex", image_socket, "LessThan", "Value", "Value"),
        ),
    )


def test_compute_branch_labels_disambiguates_multi_input_branches() -> None:
    graph = SerializedMaterialGraph(
        material_name="TestMat",
        nodes=(
            SerializedNode(name="Principled BSDF", bl_idname="ShaderNodeBsdfPrincipled"),
            SerializedNode(name="Math", bl_idname="ShaderNodeMath", operation="MULTIPLY"),
            SerializedNode(name="Image_A", bl_idname="ShaderNodeTexImage"),
            SerializedNode(name="Image_B", bl_idname="ShaderNodeTexImage"),
        ),
        links=(
            SerializedLink("Math", "Value", "Principled BSDF", "Roughness", "Roughness"),
            SerializedLink("Image_A", "Color", "Math", "Value", "Value"),
            SerializedLink("Image_B", "Color", "Math", "Value", "Value_001"),
        ),
    )

    labels = compute_branch_labels(graph)
    assert labels["Principled BSDF"] == "Material"
    assert labels["Image_A"] != labels["Image_B"]
    assert labels["Image_A"].endswith("Value")
    assert labels["Image_B"].endswith("Value_001")


def test_alpha_clip_tracing_through_gltf_cutoff_chain_and_ignore_flag() -> None:
    graph = SerializedMaterialGraph(
        material_name="Foliage",
        nodes=(
            SerializedNode(name="Principled BSDF", bl_idname="ShaderNodeBsdfPrincipled"),
            SerializedNode(name="LessThan", bl_idname="ShaderNodeMath", operation="LESS_THAN"),
            SerializedNode(name="Subtract", bl_idname="ShaderNodeMath", operation="SUBTRACT"),
            SerializedNode(
                name="LeafTex",
                bl_idname="ShaderNodeTexImage",
                image_name="leaf_color.png",
            ),
        ),
        links=(
            SerializedLink("LessThan", "Value", "Principled BSDF", "Alpha", "Alpha"),
            SerializedLink("Subtract", "Value", "LessThan", "Value", "Value"),
            SerializedLink("LeafTex", "Alpha", "Subtract", "Value", "Value"),
        ),
    )

    assert find_alpha_clip_source_image(graph, "Principled BSDF") == "LeafTex"

    plans = plan_alpha_clip_bypass(graph, alpha_mode="RAW")
    assert len(plans) == 1
    assert plans[0].source_image_node == "LeafTex"
    assert plans[0].alpha_node_name == "LeafTex [Octane Alpha Image]"
    assert plans[0].mode == "RAW"
    assert plans[0].cutoff is None

    assert plan_alpha_clip_bypass(graph, alpha_mode="IGNORE") == []
    # RAW is the default mode.
    assert plan_alpha_clip_bypass(graph) == plans


def test_alpha_trace_ignores_image_color_output() -> None:
    graph = _gltf_mask_graph(image_socket="Color")

    assert trace_alpha_source(graph, "Principled BSDF") is None
    assert find_alpha_clip_source_image(graph, "Principled BSDF") is None
    assert plan_alpha_clip_bypass(graph, alpha_mode="RAW") == []


def test_alpha_trace_finds_alpha_output_after_color_output_of_same_image() -> None:
    graph = SerializedMaterialGraph(
        material_name="Diamond",
        nodes=(
            SerializedNode(name="Principled BSDF", bl_idname="ShaderNodeBsdfPrincipled"),
            SerializedNode(name="Mul", bl_idname="ShaderNodeMath", operation="MULTIPLY"),
            SerializedNode(name="Tex", bl_idname="ShaderNodeTexImage", image_name="a.png"),
        ),
        links=(
            SerializedLink("Mul", "Value", "Principled BSDF", "Alpha", "Alpha"),
            SerializedLink("Tex", "Color", "Mul", "Value", "Value"),
            SerializedLink("Tex", "Alpha", "Mul", "Value", "Value_001"),
        ),
    )

    trace = trace_alpha_source(graph, "Principled BSDF")
    assert trace is not None
    assert trace.image_node == "Tex"


def test_alpha_trace_reads_gltf_cutoff_and_chain() -> None:
    trace = trace_alpha_source(_gltf_mask_graph(cutoff=0.35), "Principled BSDF")

    assert trace is not None
    assert trace.image_node == "Tex"
    assert trace.chain_nodes == ("Subtract", "LessThan")
    assert trace.cutoff == pytest.approx(0.35)


def test_plan_alpha_clip_bypass_cutoff_mode_adds_step_bounds() -> None:
    plans = plan_alpha_clip_bypass(_gltf_mask_graph(cutoff=0.5), alpha_mode="CUTOFF")

    assert len(plans) == 1
    assert plans[0].mode == "CUTOFF"
    assert plans[0].cutoff == pytest.approx(0.5)
    assert plans[0].step_min == pytest.approx(0.49)
    assert plans[0].step_max == pytest.approx(0.51)


def test_plan_alpha_clip_bypass_cutoff_step_is_clamped_to_unit_range() -> None:
    plans = plan_alpha_clip_bypass(_gltf_mask_graph(cutoff=0.0), alpha_mode="CUTOFF")

    assert plans[0].step_min == 0.0
    assert plans[0].step_max == pytest.approx(0.01)


def test_plan_alpha_clip_bypass_cutoff_without_readable_cutoff_falls_back_to_raw() -> None:
    plans = plan_alpha_clip_bypass(_gltf_mask_graph(cutoff=None), alpha_mode="CUTOFF")

    assert len(plans) == 1
    assert plans[0].mode == "RAW"
    assert plans[0].cutoff is None
    assert plans[0].step_min is None


def test_plan_alpha_clip_bypass_raw_mode_keeps_soft_edges_without_cutoff() -> None:
    plans = plan_alpha_clip_bypass(_gltf_mask_graph(cutoff=0.5), alpha_mode="RAW")

    assert len(plans) == 1
    assert plans[0].mode == "RAW"
    assert plans[0].cutoff is None
    assert plans[0].step_min is None
    assert plans[0].step_max is None


def test_plan_alpha_clip_bypass_skips_images_without_alpha_channel() -> None:
    assert plan_alpha_clip_bypass(_gltf_mask_graph(has_alpha=False), alpha_mode="RAW") == []


def test_audit_does_not_flag_alpha_chain_math_when_bypassed() -> None:
    warnings = audit_material_graph(_gltf_mask_graph(), alpha_mode="RAW")

    assert "UNSUPPORTED_MATH_OP" not in {w.code for w in warnings}
    info = [w for w in warnings if w.code == "ALPHA_CLIP_BYPASSED"]
    assert len(info) == 1
    assert info[0].severity == "info"


def test_audit_reports_alpha_ignored_instead_of_silently_dropping() -> None:
    warnings = audit_material_graph(_gltf_mask_graph(), alpha_mode="IGNORE")

    assert [w.code for w in warnings] == ["ALPHA_IGNORED"]
    assert warnings[0].severity == "warning"


def test_audit_still_flags_unsupported_math_outside_alpha_chain() -> None:
    graph = SerializedMaterialGraph(
        material_name="RoughMath",
        nodes=(
            SerializedNode(name="Principled BSDF", bl_idname="ShaderNodeBsdfPrincipled"),
            SerializedNode(name="LessThan", bl_idname="ShaderNodeMath", operation="LESS_THAN"),
            SerializedNode(name="Tex", bl_idname="ShaderNodeTexImage", image_name="r.png"),
        ),
        links=(
            SerializedLink("LessThan", "Value", "Principled BSDF", "Roughness", "Roughness"),
            SerializedLink("Tex", "Color", "LessThan", "Value", "Value"),
        ),
    )

    codes = [w.code for w in audit_material_graph(graph, alpha_mode="RAW")]
    assert codes == ["UNSUPPORTED_MATH_OP"]


def test_alpha_clip_tracing_handles_cycles_without_infinite_recursion() -> None:
    cyclic_graph = SerializedMaterialGraph(
        material_name="CyclicMat",
        nodes=(
            SerializedNode(name="Principled BSDF", bl_idname="ShaderNodeBsdfPrincipled"),
            SerializedNode(name="NodeA", bl_idname="ShaderNodeMath", operation="ADD"),
            SerializedNode(name="NodeB", bl_idname="ShaderNodeMath", operation="ADD"),
        ),
        links=(
            SerializedLink("NodeA", "Value", "Principled BSDF", "Alpha", "Alpha"),
            SerializedLink("NodeB", "Value", "NodeA", "Value", "Value"),
            SerializedLink("NodeA", "Value", "NodeB", "Value", "Value"),
        ),
    )

    assert find_alpha_clip_source_image(cyclic_graph, "Principled BSDF") is None


def test_audit_material_graph_flags_unsupported_math_and_procedural_nodes() -> None:
    graph = SerializedMaterialGraph(
        material_name="ComplexMat",
        nodes=(
            SerializedNode(name="Add", bl_idname="ShaderNodeMath", operation="ADD"),
            SerializedNode(name="Div", bl_idname="ShaderNodeMath", operation="DIVIDE"),
            SerializedNode(name="Noise", bl_idname="ShaderNodeTexNoise"),
            SerializedNode(name="VecMath", bl_idname="ShaderNodeVectorMath"),
        ),
    )

    warnings = audit_material_graph(graph)
    assert len(warnings) == 3
    codes = {w.node_name: w.code for w in warnings}
    assert codes == {
        "Div": "UNSUPPORTED_MATH_OP",
        "Noise": "UNSUPPORTED_CYCLES_NODE",
        "VecMath": "UNSUPPORTED_CYCLES_NODE",
    }

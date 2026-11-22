"""Unit tests for pure graph planning, alpha-clip tracing, and audit."""

from __future__ import annotations

from core.graph_planner import (
    SerializedLink,
    SerializedMaterialGraph,
    SerializedNode,
    audit_material_graph,
    compute_branch_labels,
    find_alpha_clip_source_image,
    plan_alpha_clip_bypass,
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

    plans = plan_alpha_clip_bypass(graph, ignore_alpha_clip=False)
    assert len(plans) == 1
    assert plans[0].source_image_node == "LeafTex"
    assert plans[0].alpha_node_name == "LeafTex [Octane Alpha Image]"

    assert plan_alpha_clip_bypass(graph, ignore_alpha_clip=True) == []


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

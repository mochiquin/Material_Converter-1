"""Unit tests for Cycles -> Octane node and socket mapping rules."""

from __future__ import annotations

import math

import pytest

from core.node_mappings import (
    check_unsupported_cycles_node,
    compute_octane_mapping_transform,
    get_octane_material_prefix_map,
    plan_separate_color_pickers,
    resolve_math_node,
    resolve_octane_socket_names,
)


@pytest.mark.parametrize(
    ("operation", "expected_node"),
    [
        ("ADD", "OctaneAddTexture"),
        ("SUBTRACT", "OctaneSubtractTexture"),
        ("MULTIPLY", "OctaneMultiplyTexture"),
        ("multiply", "OctaneMultiplyTexture"),
    ],
)
def test_resolve_supported_math_operations(operation: str, expected_node: str) -> None:
    res = resolve_math_node(operation, node_name="Math.001")
    assert res.supported is True
    assert res.octane_bl_idname == expected_node
    assert res.warning is None


@pytest.mark.parametrize("unsupported_op", ["DIVIDE", "LESS_THAN", "GREATER_THAN", "POWER", "SQRT"])
def test_resolve_unsupported_math_operations_emit_explicit_warning(unsupported_op: str) -> None:
    res = resolve_math_node(unsupported_op, node_name="Math.AlphaClip")
    assert res.supported is False
    assert res.octane_bl_idname is None
    assert res.warning is not None
    assert "OctaneCyclesNodeMathNodeWrapper" in res.warning
    assert unsupported_op in res.warning


def test_check_unsupported_vector_math_and_procedural_textures() -> None:
    vec_warn = check_unsupported_cycles_node("ShaderNodeVectorMath", "VecMath.001")
    assert vec_warn is not None
    assert "OctaneCyclesNodeVectorMathNodeWrapper" in vec_warn

    noise_warn = check_unsupported_cycles_node("ShaderNodeTexNoise", "Noise.001")
    assert noise_warn is not None
    assert "Noise" in noise_warn

    assert check_unsupported_cycles_node("ShaderNodeTexImage", "Img.001") is None


def test_compute_octane_mapping_transform_zero_scale_guard() -> None:
    normal = compute_octane_mapping_transform(
        location=(0.5, -0.25, 0.0),
        rotation_rad=(math.pi / 2, math.pi, 0.0),
        scale=(2.0, 4.0, 0.5),
    )
    assert normal.warning is None
    assert normal.rotation_deg == pytest.approx((90.0, 180.0, 0.0))
    assert normal.scale == pytest.approx((0.5, 0.25, 2.0))
    assert normal.translation == (0.5, -0.25, 0.0)

    zero_scale = compute_octane_mapping_transform(
        location=(0.0, 0.0, 0.0),
        rotation_rad=(0.0, 0.0, 0.0),
        scale=(0.0, 2.0, 0.0),
    )
    assert zero_scale.warning is not None
    assert "X, Z" in zero_scale.warning
    assert zero_scale.scale == pytest.approx((1.0, 0.5, 1.0))


def test_plan_separate_color_pickers_only_for_linked_channels() -> None:
    plans = plan_separate_color_pickers(
        node_name="Separate Color",
        label="ORM Split",
        mode="HSV",
        linked_output_indices=[0, 2, 99],
        location=(100.0, 200.0),
    )
    assert len(plans) == 2
    assert plans[0].picker_name == "Separate Color__ch0"
    assert plans[0].channel_index_value == "1"
    assert plans[0].conversion_value == "HSV|RGB to HSV"
    assert plans[1].picker_name == "Separate Color__ch2"
    assert plans[1].channel_index_value == "3"
    assert plans[1].location == (1750.0, -100.0)
    assert [plan.label for plan in plans] == ["ORM Split H", "ORM Split V"]


def test_plan_separate_color_pickers_label_distinguishes_rgb_channels() -> None:
    plans = plan_separate_color_pickers(
        node_name="Separate Color",
        label=" Metallic",
        mode="RGB",
        linked_output_indices=[1, 2],
        location=(0.0, 0.0),
    )
    labels = [plan.label for plan in plans]
    assert labels == ["Metallic G", "Metallic B"]
    assert len(set(labels)) == len(labels)


def test_resolve_octane_socket_names_and_material_prefix_map() -> None:
    out_name, in_name = resolve_octane_socket_names(
        from_node_type="ShaderNodeValue",
        from_socket_name="Value",
        to_node_type="ShaderNodeMath",
        to_socket_name="Value",
        to_socket_identifier="Value_001",
        octane_target_type="OctaneMultiplyTexture",
    )
    assert out_name == "Float out"
    assert in_name == "Texture 2"

    _, std_rough = resolve_octane_socket_names(
        from_node_type="ShaderNodeTexImage",
        from_socket_name="Color",
        to_node_type="ShaderNodeBsdfPrincipled",
        to_socket_name="Roughness",
        to_socket_identifier="Roughness",
        octane_target_type="OctaneStandardSurfaceMaterial",
    )
    assert std_rough == "Specular roughness"

    uni_prefixes = get_octane_material_prefix_map("UNIVERSAL")
    assert uni_prefixes[("Diffuse", "COL", "COLOR", "COLOR * AO")] == "Albedo"
    assert uni_prefixes[("Transmission", "TRANS")] == "Transmission"

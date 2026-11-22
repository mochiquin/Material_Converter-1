"""Pure Python Cycles -> Octane node and socket mapping rules."""

from __future__ import annotations

import math
from dataclasses import dataclass

SUPPORTED_MATH_OPS: dict[str, str] = {
    "ADD": "OctaneAddTexture",
    "SUBTRACT": "OctaneSubtractTexture",
    "MULTIPLY": "OctaneMultiplyTexture",
}

KNOWN_UNSUPPORTED_OCTANE_NODES: dict[str, str] = {
    "OctaneCyclesNodeMathNodeWrapper": (
        "Does not evaluate for texture/RGB inputs in Octane real renders"
    ),
    "OctaneCyclesNodeVectorMathNodeWrapper": (
        "Does not evaluate for texture/RGB inputs in Octane real renders"
    ),
    "OctaneBinaryMathOperation": (
        "Evaluates scalar/coordinate math only, not texture-domain RGB/float inputs"
    ),
    "OctaneComparison": (
        "Does not evaluate texture-domain inputs in Octane real renders"
    ),
}

UNSUPPORTED_CYCLES_NODE_TYPES: dict[str, str] = {
    "ShaderNodeVectorMath": (
        "Vector Math is not converted: OctaneCyclesNodeVectorMathNodeWrapper "
        "does not evaluate in Octane texture domain."
    ),
    "ShaderNodeTexNoise": "Procedural Noise texture has no 1:1 Octane texture mapping yet.",
    "ShaderNodeTexVoronoi": "Procedural Voronoi texture has no 1:1 Octane texture mapping yet.",
    "ShaderNodeTexWave": "Procedural Wave texture has no 1:1 Octane texture mapping yet.",
    "ShaderNodeTexChecker": "Procedural Checker texture has no 1:1 Octane texture mapping yet.",
    "ShaderNodeTexBrick": "Procedural Brick texture has no 1:1 Octane texture mapping yet.",
    "ShaderNodeTexGradient": "Procedural Gradient texture has no 1:1 Octane texture mapping yet.",
    "ShaderNodeTexMagic": "Procedural Magic texture has no 1:1 Octane texture mapping yet.",
    "ShaderNodeTexWhiteNoise": "Procedural White Noise texture has no 1:1 Octane texture mapping yet.",
}

SEPARATE_CHANNEL_INDEX_MAP: dict[int, str] = {0: "1", 1: "2", 2: "3"}
SEPARATE_CONVERSION_MAP: dict[str, str] = {
    "RGB": "No conversion",
    "HSV": "HSV|RGB to HSV",
    "HSL": "HSL|RGB to HSL",
}

BLEND_TYPE_MAPPING: dict[str, str] = {
    "DARKEN": "Darken",
    "MULTIPLY": "Multiply",
    "COLOR_BURN": "Color Burn",
    "LINEAR_BURN": "Linear Burn",
    "LIGHTEN": "Lighten",
    "SCREEN": "Screen",
    "COLOR_DODGE": "Color Dodge",
    "ADD": "Add",
    "OVERLAY": "Overlay",
    "SOFT_LIGHT": "Soft Light",
    "HARD_LIGHT": "Hard Light",
    "VIVID_LIGHT": "Vivid Light",
    "LINEAR_LIGHT": "Linear Light",
    "PIN_LIGHT": "Pin Light",
    "HARD_MIX": "Hard Mix",
    "DIFFERENCE": "Difference",
    "EXCLUSION": "Exclusion",
    "SUBTRACT": "Subtract",
    "DIVIDE": "Divide",
    "HUE": "Hue",
    "SATURATION": "Saturation",
    "COLOR": "Color",
    "LUMINOSITY": "Luminosity",
}

VECTOR_MODE_MAPPING: dict[str, str] = {
    "UNIFORM": "Uniform",
    "NON_UNIFORM": "Non-Uniform",
}

OCTANE_NODE_MAPPING: dict[str, list[str]] = {
    "ShaderNodeMix": [
        "OctaneMixTexture",
        "OctaneCyclesMixColorNodeWrapper",
        "OctaneCyclesMixFloatNodeWrapper",
        "OctaneCyclesMixFloat3NodeWrapper",
    ],
    "ShaderNodeTexImage": ["OctaneRGBImage"],
    "ShaderNodeNormalMap": ["LuxCoreNodeTexNormalmap"],
    "ShaderNodeOutputMaterial": ["LuxCoreNodeMatOutput"],
    "ShaderNodeMapping": ["Octane3DTransformation"],
    "ShaderNodeBsdfPrincipled": [
        "OctaneUniversalMaterial",
        "OctaneStandardSurfaceMaterial",
        "LuxCoreNodeMatGlass",
    ],
    "ShaderNodeBsdfTranslucent": ["OctaneUniversalMaterial"],
    "ShaderNodeMixShader": ["OctaneMixMaterial"],
    "ShaderNodeBsdfGlass": ["OctaneUniversalMaterial"],
    "ShaderNodeHueSaturation": ["OctaneColorCorrection"],
    "ShaderNodeValToRGB": ["OctaneGradientMap"],
    "ShaderNodeBump": ["LuxCoreNodeTexBump"],
    "ShaderNodeInvert": ["OctaneInvertTexture"],
    "ShaderNodeRGBCurve": ["NodeReroute"],
    "ShaderNodeMath": ["OctaneAddTexture", "OctaneSubtractTexture", "OctaneMultiplyTexture"],
    "ShaderNodeRGB": ["OctaneRGBColor"],
    "ShaderNodeValue": ["OctaneFloatValue"],
}

OCTANE_OUTPUT_MAPPING: dict[str, str] = {
    "Normal": "Bump",
    "Vector": "Transform out",
    "Alpha": "Out Alpha",
    "BSDF": "Material out",
    "Result": "Texture out",
    "A": "First texture",
    "B": "Second texture",
    "Color": "Texture out",
}

OCTANE_INPUT_MAPPING: dict[str, str] = {
    "Normal": "Normal",
    "Coat Tint": "Coat Color",
    "Sheen Tint": "Sheen Color",
    "Base Color": "Albedo",
    "Coat Normal": "Coat Bump Map",
    "Vector": "UV transform",
    "Alpha": "Opacity",
    "Fresnel IOR": "Dielectric IOR",
    "Metallic": "Metallic",
    "Specular IOR Level": "Specular",
    "Surface": "Material",
    "Roughness": "Roughness",
    "Result": "Texture out",
    "A": "First texture",
    "B": "Second texture",
    "Color": "Texture",
}

UNIVERSAL_MATERIAL_INPUT_INDICES: dict[str, int | None] = {
    "Base Color": 5,
    "Metallic": 7,
    "Roughness": 13,
    "Normal": None,
    "Alpha": 43,
    "Specular IOR Level": 10,
    "IOR": 18,
    "Anisotropic": 14,
    "Anisotropic Rotation": 15,
}

STANDARD_SURFACE_INPUT_NAMES: dict[str, str] = {
    "Base Color": "Base color",
    "Metallic": "Metalness",
    "Roughness": "Specular roughness",
    "Specular IOR Level": "Specular weight",
    "Normal": "Normal",
}

MATH_IDENTIFIER_TO_OCTANE_INPUT: dict[str, str] = {
    "Value": "Texture 1",
    "Value_001": "Texture 2",
}


@dataclass(frozen=True, slots=True)
class MathResolution:
    """Outcome of resolving a Cycles ShaderNodeMath operation for Octane."""

    operation: str
    supported: bool
    octane_bl_idname: str | None
    warning: str | None = None


@dataclass(frozen=True, slots=True)
class SeparatePickerPlan:
    """Planned OctaneChannelPicker node for one linked Separate Color/RGB output."""

    picker_name: str
    label: str
    channel_index_value: str
    conversion_value: str
    location: tuple[float, float]


@dataclass(frozen=True, slots=True)
class MappingTransform:
    """Converted Octane 3D Transformation parameters from Cycles Mapping."""

    rotation_deg: tuple[float, float, float]
    scale: tuple[float, float, float]
    translation: tuple[float, float, float]
    warning: str | None = None


def resolve_math_node(operation: str, node_name: str = "") -> MathResolution:
    """Resolve a Cycles Math operation to an Octane node or explicit warning.

    Known non-evaluating Octane math wrappers (e.g. ``OctaneCyclesNodeMathNodeWrapper``)
    are explicitly intercepted instead of failing silently.
    """
    op_upper = operation.upper()
    octane_bl_idname = SUPPORTED_MATH_OPS.get(op_upper)
    if octane_bl_idname is not None:
        return MathResolution(
            operation=op_upper,
            supported=True,
            octane_bl_idname=octane_bl_idname,
        )

    label_prefix = f"Node '{node_name}': " if node_name else ""
    return MathResolution(
        operation=op_upper,
        supported=False,
        octane_bl_idname=None,
        warning=(
            f"{label_prefix}Cycles Math operation '{op_upper}' has no working "
            "Octane texture-domain node (OctaneCyclesNodeMathNodeWrapper / "
            "OctaneBinaryMathOperation / OctaneComparison do not evaluate "
            "texture inputs) and will be left unconverted."
        ),
    )


def check_unsupported_cycles_node(bl_idname: str, node_name: str = "") -> str | None:
    """Return an explicit warning if a Cycles node type is unsupported in Octane."""
    reason = UNSUPPORTED_CYCLES_NODE_TYPES.get(bl_idname)
    if reason is None:
        return None
    if node_name:
        return f"Node '{node_name}' ({bl_idname}): {reason}"
    return f"{bl_idname}: {reason}"


def plan_separate_color_pickers(
    node_name: str,
    label: str,
    mode: str,
    linked_output_indices: list[int],
    location: tuple[float, float],
) -> list[SeparatePickerPlan]:
    """Plan one OctaneChannelPicker per linked output channel (R/G/B or H/S/V)."""
    conversion_value = SEPARATE_CONVERSION_MAP.get(mode, "No conversion")
    plans: list[SeparatePickerPlan] = []
    for ch_index in linked_output_indices:
        if ch_index not in SEPARATE_CHANNEL_INDEX_MAP:
            continue
        plans.append(
            SeparatePickerPlan(
                picker_name=f"{node_name}__ch{ch_index}",
                label=label,
                channel_index_value=SEPARATE_CHANNEL_INDEX_MAP[ch_index],
                conversion_value=conversion_value,
                location=(location[0] + 1650.0, location[1] - ch_index * 150.0),
            )
        )
    return plans


def compute_octane_mapping_transform(
    location: tuple[float, float, float],
    rotation_rad: tuple[float, float, float],
    scale: tuple[float, float, float],
) -> MappingTransform:
    """Convert Cycles Mapping (radians, forward scale) to Octane 3D Transformation."""
    rad_to_deg = 180.0 / math.pi
    rotation_deg = (
        rotation_rad[0] * rad_to_deg,
        rotation_rad[1] * rad_to_deg,
        rotation_rad[2] * rad_to_deg,
    )
    inv_scale: list[float] = []
    zero_axes: list[str] = []
    for axis_name, value in zip(("X", "Y", "Z"), scale, strict=True):
        if abs(value) <= 1e-8:
            inv_scale.append(1.0)
            zero_axes.append(axis_name)
        else:
            inv_scale.append(1.0 / value)

    warning = (
        f"Cycles Mapping scale is zero on axis {', '.join(zero_axes)}; clamped inverse scale to 1.0."
        if zero_axes
        else None
    )
    return MappingTransform(
        rotation_deg=rotation_deg,
        scale=(inv_scale[0], inv_scale[1], inv_scale[2]),
        translation=(location[0], location[1], location[2]),
        warning=warning,
    )


def resolve_octane_socket_names(
    from_node_type: str,
    from_socket_name: str,
    to_node_type: str,
    to_socket_name: str,
    to_socket_identifier: str,
    octane_target_type: str,
) -> tuple[str, str]:
    """Resolve ``(octane_output_name, octane_input_name)`` for a Cycles link."""
    if from_node_type == "ShaderNodeMath":
        output_name = "Texture out"
    elif from_node_type == "ShaderNodeValue":
        output_name = "Float out"
    else:
        output_name = OCTANE_OUTPUT_MAPPING.get(from_socket_name, from_socket_name)

    if to_node_type == "ShaderNodeMath":
        input_name = MATH_IDENTIFIER_TO_OCTANE_INPUT.get(to_socket_identifier, to_socket_name)
    elif to_node_type == "ShaderNodeMixShader":
        if to_socket_name == "Fac":
            input_name = "Amount"
        elif to_socket_identifier == "Shader":
            input_name = "First material"
        elif to_socket_identifier == "Shader_001":
            input_name = "Second material"
        else:
            input_name = to_socket_name
    elif to_node_type == "ShaderNodeMix" and octane_target_type == "OctaneCyclesMixColorNodeWrapper":
        input_name = to_socket_name if to_socket_name in {"A", "B", "Factor"} else to_socket_name
    elif to_node_type == "ShaderNodeBsdfPrincipled":
        if octane_target_type == "OctaneStandardSurfaceMaterial":
            input_name = STANDARD_SURFACE_INPUT_NAMES.get(to_socket_name, to_socket_name)
        else:
            input_name = OCTANE_INPUT_MAPPING.get(to_socket_name, to_socket_name)
    elif to_node_type == "ShaderNodeRGBCurve":
        input_name = "Texture"
    elif to_node_type == "ShaderNodeBsdfTranslucent":
        if octane_target_type == "OctaneUniversalMaterial" and to_socket_name == "Color":
            input_name = "Transmission"
        else:
            input_name = OCTANE_INPUT_MAPPING.get(to_socket_name, to_socket_name)
    elif to_node_type == "ShaderNodeHueSaturation":
        if octane_target_type == "OctaneColorCorrection" and to_socket_name == "Color":
            input_name = "Input"
        else:
            input_name = OCTANE_INPUT_MAPPING.get(to_socket_name, to_socket_name)
    elif to_node_type == "ShaderNodeValToRGB":
        if to_socket_name == "Fac":
            input_name = "Input texture"
        else:
            input_name = OCTANE_INPUT_MAPPING.get(to_socket_name, to_socket_name)
    elif to_node_type == "ShaderNodeTexImage":
        input_name = "UV transform" if to_socket_name == "Vector" else to_socket_name
    elif to_node_type == "ShaderNodeNormalMap":
        input_name = "Texmap" if to_socket_name == "Color" else to_socket_name
    elif to_socket_name == "Fac":
        input_name = (
            "Input texture"
            if to_node_type == "ShaderNodeValToRGB"
            else OCTANE_INPUT_MAPPING.get(to_socket_name, to_socket_name)
        )
    else:
        input_name = OCTANE_INPUT_MAPPING.get(to_socket_name, to_socket_name)

    return output_name, input_name


def get_octane_material_prefix_map(base_material: str) -> dict[tuple[str, ...], str]:
    """Return label-prefix -> material-input mapping for Octane Universal/Standard."""
    mapping: dict[tuple[str, ...], str] = {
        ("Specular", "REFL", "REFLECTION"): "Specular",
        ("Metallic", "METALNESS", "METAL"): "Metalness",
        ("NRM", "NORMAL", "Normal Map"): "Normal",
        ("SSS", "Subsurface"): "Subsurface color",
        ("Displacement", "DISP", "HEIGHT", "displacement"): "Displacement",
        ("BUMP",): "Bump",
        ("Opacity", "OPACITY"): "Opacity",
        ("Transmission", "TRANS"): "Transmission",
        ("Coat", "COATING"): "Coating",
    }
    if base_material == "UNIVERSAL":
        mapping[("Diffuse", "COL", "COLOR", "COLOR * AO")] = "Albedo"
        mapping[("GLOSS", "ROUGHNESS", "Roughness")] = "Roughness"
    else:
        mapping[("Diffuse", "COL", "COLOR", "COLOR * AO")] = "Base color"
        mapping[("GLOSS", "ROUGHNESS", "Roughness")] = "Specular roughness"
    return mapping

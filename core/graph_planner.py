"""Pure Python graph traversal, labeling, and conversion planning algorithms."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .node_mappings import check_unsupported_cycles_node, resolve_math_node

AlphaMode = Literal["RAW", "CUTOFF", "IGNORE"]
"""How a source image's alpha channel is mapped onto Octane Opacity.

``RAW``: use the image's alpha channel as-is (keeps soft, anti-aliased edges).
``CUTOFF``: re-apply the glTF alpha-cutoff threshold as a hard step.
``IGNORE``: leave the material fully opaque.
"""

# Half-width of the near-hard step used by the CUTOFF mode (alpha units).
CUTOFF_STEP_HALF_WIDTH = 0.01

ALPHA_MODES: tuple[str, ...] = ("RAW", "CUTOFF", "IGNORE")
DEFAULT_ALPHA_MODE: AlphaMode = "RAW"


@dataclass(frozen=True, slots=True)
class SerializedSocket:
    """Serialized representation of a Blender node socket."""

    name: str
    identifier: str
    is_linked: bool = False
    value: float | None = None


@dataclass(frozen=True, slots=True)
class SerializedLink:
    """Serialized directed link inside a material node tree."""

    from_node: str
    from_socket: str
    to_node: str
    to_socket: str
    to_socket_identifier: str = ""


@dataclass(frozen=True, slots=True)
class SerializedNode:
    """Serialized Cycles/Octane node metadata."""

    name: str
    bl_idname: str
    label: str = ""
    operation: str = ""
    image_name: str = ""
    image_has_alpha: bool = True
    location: tuple[float, float] = (0.0, 0.0)
    inputs: tuple[SerializedSocket, ...] = ()


@dataclass(frozen=True, slots=True)
class SerializedMaterialGraph:
    """Pure Python snapshot of a Blender material node tree."""

    material_name: str
    nodes: tuple[SerializedNode, ...] = ()
    links: tuple[SerializedLink, ...] = ()

    def node_map(self) -> dict[str, SerializedNode]:
        return {node.name: node for node in self.nodes}


@dataclass(frozen=True, slots=True)
class ConversionWarning:
    """Explicit warning generated during graph planning."""

    code: str
    node_name: str
    message: str
    severity: str = "warning"


@dataclass(frozen=True, slots=True)
class AlphaClipPlan:
    """Plan to bypass Cycles Alpha-clip chains via OctaneAlphaImage."""

    principled_node: str
    source_image_node: str
    source_image_name: str
    alpha_node_name: str
    mode: AlphaMode = "RAW"
    cutoff: float | None = None
    step_min: float | None = None
    step_max: float | None = None


@dataclass(frozen=True, slots=True)
class AlphaTrace:
    """Result of tracing a Principled BSDF's Alpha input back to an image alpha."""

    image_node: str
    chain_nodes: tuple[str, ...] = ()
    cutoff: float | None = None


def compute_branch_labels(graph: SerializedMaterialGraph) -> dict[str, str]:
    """Compute unique downstream-derived labels for nodes in a Cycles graph.

    Handles multi-input nodes (such as ShaderNodeMath or ShaderNodeMix) by
    appending socket identifiers/names so two upstream branches never collide
    on identical labels during connection rebuilding.
    """
    nodes_by_name = graph.node_map()
    incoming_by_node: dict[str, list[SerializedLink]] = {n.name: [] for n in graph.nodes}
    for link in graph.links:
        if link.to_node in incoming_by_node:
            incoming_by_node[link.to_node].append(link)

    labels: dict[str, str] = {n.name: n.label for n in graph.nodes if n.label}

    input_prefix_map = {
        "Base Color": "Diffuse",
        "Specular IOR Level": "Specular",
    }
    mapping_prefix_map = {
        "Normal": "3",
        "Diffuse": "1",
        "Roughness": "2",
        "Specular": "5",
        "Transmission": "4",
    }

    def assign_recursive(node_name: str, label_prefix: str, visited: set[str]) -> None:
        if node_name in visited:
            return
        node = nodes_by_name.get(node_name)
        if node is None:
            return
        visited = visited | {node_name}

        if node.bl_idname == "ShaderNodeMix":
            labels.setdefault(node_name, label_prefix)
            mix_links = [
                lnk for lnk in incoming_by_node.get(node_name, []) if lnk.to_socket in {"A", "B"}
            ]
            for lnk in mix_links:
                assign_recursive(lnk.from_node, f"{label_prefix} {lnk.to_socket}", visited)
            return

        if node.bl_idname == "ShaderNodeMapping":
            if not labels.get(node_name):
                mapped = mapping_prefix_map.get(label_prefix, label_prefix)
                labels[node_name] = f"Mapping {mapped}"
            return

        if not labels.get(node_name):
            labels[node_name] = label_prefix

        in_links = incoming_by_node.get(node_name, [])
        if len(in_links) > 1:
            for lnk in in_links:
                suffix = lnk.to_socket_identifier or lnk.to_socket
                assign_recursive(lnk.from_node, f"{label_prefix} {suffix}", visited)
        else:
            for lnk in in_links:
                assign_recursive(lnk.from_node, label_prefix, visited)

    principled_nodes = [n for n in graph.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"]
    for idx, node in enumerate(principled_nodes):
        mat_label = "Material" if idx == 0 else f"Material {idx}"
        labels[node.name] = mat_label
        index_suffix = mat_label.replace("Material", "").strip()
        for lnk in incoming_by_node.get(node.name, []):
            prefix = input_prefix_map.get(lnk.to_socket, lnk.to_socket)
            full_prefix = f"{index_suffix} {prefix}" if index_suffix else f" {prefix}"
            assign_recursive(lnk.from_node, full_prefix, set())

    return labels


def _cutoff_from_chain(
    nodes_by_name: dict[str, SerializedNode],
    chain: list[str],
) -> float | None:
    """Return the glTF alpha-cutoff constant from a LESS_THAN node in the chain."""
    for name in chain:
        node = nodes_by_name.get(name)
        if node is None or node.operation != "LESS_THAN":
            continue
        for socket in node.inputs[:2]:
            if not socket.is_linked and socket.value is not None:
                return float(socket.value)
    return None


def trace_alpha_source(
    graph: SerializedMaterialGraph,
    principled_node_name: str,
    *,
    max_depth: int = 12,
) -> AlphaTrace | None:
    """Trace a Principled BSDF's Alpha input upstream to a TexImage *Alpha* output.

    Only a link leaving the image's ``Alpha`` socket counts: an image whose
    ``Color`` output feeds Alpha is not an alpha-channel source.
    """
    nodes_by_name = graph.node_map()
    incoming_by_node: dict[str, list[SerializedLink]] = {}
    for link in graph.links:
        incoming_by_node.setdefault(link.to_node, []).append(link)

    alpha_links = [
        lnk
        for lnk in incoming_by_node.get(principled_node_name, [])
        if lnk.to_socket == "Alpha"
    ]
    if not alpha_links:
        return None

    visited: set[str] = set()

    def walk(node_name: str, from_socket: str, depth: int, chain: list[str]) -> AlphaTrace | None:
        if depth > max_depth:
            return None
        node = nodes_by_name.get(node_name)
        if node is None:
            return None
        if node.bl_idname == "ShaderNodeTexImage":
            if from_socket != "Alpha":
                return None
            return AlphaTrace(
                image_node=node.name,
                chain_nodes=tuple(chain),
                cutoff=_cutoff_from_chain(nodes_by_name, chain),
            )
        if node_name in visited:
            return None
        visited.add(node_name)
        for lnk in incoming_by_node.get(node_name, []):
            found = walk(lnk.from_node, lnk.from_socket, depth + 1, [*chain, node_name])
            if found is not None:
                return found
        return None

    first = alpha_links[0]
    return walk(first.from_node, first.from_socket, 0, [])


def find_alpha_clip_source_image(
    graph: SerializedMaterialGraph,
    principled_node_name: str,
    *,
    max_depth: int = 12,
) -> str | None:
    """Name of the TexImage whose Alpha output drives a Principled BSDF's Alpha."""
    trace = trace_alpha_source(graph, principled_node_name, max_depth=max_depth)
    return trace.image_node if trace else None


def plan_alpha_clip_bypass(
    graph: SerializedMaterialGraph,
    *,
    alpha_mode: AlphaMode = DEFAULT_ALPHA_MODE,
) -> list[AlphaClipPlan]:
    """Generate OctaneAlphaImage plans for all Principled BSDF nodes.

    ``RAW`` wires the image's alpha channel straight to Opacity. ``CUTOFF`` does
    the same but records the glTF cutoff so the executor can add a hard step;
    without a readable cutoff it degrades to ``RAW``. ``IGNORE`` plans nothing.
    """
    if alpha_mode == "IGNORE":
        return []

    nodes_by_name = graph.node_map()
    plans: list[AlphaClipPlan] = []
    for node in graph.nodes:
        if node.bl_idname != "ShaderNodeBsdfPrincipled":
            continue
        trace = trace_alpha_source(graph, node.name)
        if trace is None:
            continue
        source_node = nodes_by_name.get(trace.image_node)
        if source_node is None or not source_node.image_name or not source_node.image_has_alpha:
            continue
        use_cutoff = alpha_mode == "CUTOFF" and trace.cutoff is not None
        plans.append(
            AlphaClipPlan(
                principled_node=node.name,
                source_image_node=trace.image_node,
                source_image_name=source_node.image_name,
                alpha_node_name=f"{trace.image_node} [Octane Alpha Image]",
                mode="CUTOFF" if use_cutoff else "RAW",
                cutoff=trace.cutoff if use_cutoff else None,
                step_min=max(0.0, trace.cutoff - CUTOFF_STEP_HALF_WIDTH) if use_cutoff else None,
                step_max=min(1.0, trace.cutoff + CUTOFF_STEP_HALF_WIDTH) if use_cutoff else None,
            )
        )
    return plans


def audit_material_graph(
    graph: SerializedMaterialGraph,
    *,
    alpha_mode: AlphaMode = DEFAULT_ALPHA_MODE,
) -> list[ConversionWarning]:
    """Audit a serialized Cycles graph for known Octane conversion limitations.

    Math nodes that only form a glTF alpha-clip chain are replaced by the alpha
    bypass (or deliberately dropped with ``IGNORE``), so they are reported once
    as ``ALPHA_CLIP_BYPASSED`` / ``ALPHA_IGNORED`` instead of as unsupported.
    """
    warnings: list[ConversionWarning] = []
    alpha_chain_nodes: set[str] = set()
    for principled in graph.nodes:
        if principled.bl_idname != "ShaderNodeBsdfPrincipled":
            continue
        trace = trace_alpha_source(graph, principled.name)
        if trace is None:
            continue
        alpha_chain_nodes.update(trace.chain_nodes)
        if alpha_mode == "IGNORE":
            warnings.append(
                ConversionWarning(
                    code="ALPHA_IGNORED",
                    node_name=principled.name,
                    message=(
                        f"Alpha from image node '{trace.image_node}' is ignored by the "
                        "'Ignore' alpha mode; Opacity stays fully opaque."
                    ),
                )
            )
        elif trace.chain_nodes:
            warnings.append(
                ConversionWarning(
                    code="ALPHA_CLIP_BYPASSED",
                    node_name=principled.name,
                    message=(
                        f"Alpha-clip math chain {list(trace.chain_nodes)} replaced by the "
                        f"image alpha channel of '{trace.image_node}'."
                    ),
                    severity="info",
                )
            )

    for node in graph.nodes:
        if node.name in alpha_chain_nodes:
            continue
        if node.bl_idname == "ShaderNodeMath":
            resolution = resolve_math_node(node.operation, node.name)
            if not resolution.supported and resolution.warning:
                warnings.append(
                    ConversionWarning(
                        code="UNSUPPORTED_MATH_OP",
                        node_name=node.name,
                        message=resolution.warning,
                    )
                )
        else:
            unsupported_msg = check_unsupported_cycles_node(node.bl_idname, node.name)
            if unsupported_msg is not None:
                warnings.append(
                    ConversionWarning(
                        code="UNSUPPORTED_CYCLES_NODE",
                        node_name=node.name,
                        message=unsupported_msg,
                    )
                )
    return warnings


@dataclass(frozen=True, slots=True)
class GraphAuditSummary:
    """Aggregated conversion audit summary for reporting to host UI/logs."""

    material_name: str
    warnings: tuple[ConversionWarning, ...] = field(default_factory=tuple)

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)

"""Pure Python graph traversal, labeling, and conversion planning algorithms."""

from __future__ import annotations

from dataclasses import dataclass, field

from .node_mappings import check_unsupported_cycles_node, resolve_math_node


@dataclass(frozen=True, slots=True)
class SerializedSocket:
    """Serialized representation of a Blender node socket."""

    name: str
    identifier: str
    is_linked: bool = False


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


@dataclass(frozen=True, slots=True)
class AlphaClipPlan:
    """Plan to bypass Cycles Alpha-clip chains via OctaneAlphaImage."""

    principled_node: str
    source_image_node: str
    source_image_name: str
    alpha_node_name: str


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


def find_alpha_clip_source_image(
    graph: SerializedMaterialGraph,
    principled_node_name: str,
    *,
    max_depth: int = 12,
) -> str | None:
    """Trace upstream from a Principled BSDF's Alpha input to a ShaderNodeTexImage."""
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

    def walk(node_name: str, depth: int) -> str | None:
        if depth > max_depth or node_name in visited:
            return None
        visited.add(node_name)
        node = nodes_by_name.get(node_name)
        if node is None:
            return None
        if node.bl_idname == "ShaderNodeTexImage":
            return node.name
        for lnk in incoming_by_node.get(node_name, []):
            found = walk(lnk.from_node, depth + 1)
            if found is not None:
                return found
        return None

    return walk(alpha_links[0].from_node, 0)


def plan_alpha_clip_bypass(
    graph: SerializedMaterialGraph,
    *,
    ignore_alpha_clip: bool,
) -> list[AlphaClipPlan]:
    """Generate OctaneAlphaImage bypass plans for all Principled BSDF nodes."""
    if ignore_alpha_clip:
        return []

    nodes_by_name = graph.node_map()
    plans: list[AlphaClipPlan] = []
    for node in graph.nodes:
        if node.bl_idname != "ShaderNodeBsdfPrincipled":
            continue
        source_img_name = find_alpha_clip_source_image(graph, node.name)
        if not source_img_name:
            continue
        source_node = nodes_by_name.get(source_img_name)
        if source_node is None or not source_node.image_name:
            continue
        plans.append(
            AlphaClipPlan(
                principled_node=node.name,
                source_image_node=source_img_name,
                source_image_name=source_node.image_name,
                alpha_node_name=f"{source_img_name} [Octane Alpha Image]",
            )
        )
    return plans


def audit_material_graph(graph: SerializedMaterialGraph) -> list[ConversionWarning]:
    """Audit a serialized Cycles graph for known Octane conversion limitations."""
    warnings: list[ConversionWarning] = []
    for node in graph.nodes:
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

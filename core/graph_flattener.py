"""Pure Python node tree flattening (unfolding node groups) on graph DTOs."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping

from .graph_planner import SerializedLink, SerializedMaterialGraph


@dataclass(frozen=True, slots=True)
class FlattenedGraphResult:
    """Result of pure Python node group flattener on a SerializedMaterialGraph."""

    graph: SerializedMaterialGraph
    unfolded_group_count: int
    warnings: tuple[str, ...]


def flatten_graph_ir(
    graph: SerializedMaterialGraph,
    group_trees: Mapping[str, SerializedMaterialGraph] | None = None,
    max_iterations: int = 50,
) -> FlattenedGraphResult:
    """Flatten all node groups inside a SerializedMaterialGraph in pure Python.

    Args:
        graph: Main material graph IR.
        group_trees: Optional dictionary mapping group_tree_name -> internal SerializedMaterialGraph.
        max_iterations: Guard limit to prevent infinite recursion on circular node groups.

    Returns:
        FlattenedGraphResult containing the new graph IR without ShaderNodeGroup nodes.
    """
    if group_trees is None:
        group_trees = {}

    current_nodes = list(graph.nodes)
    current_links = list(graph.links)
    warnings: list[str] = []
    unfolded_count = 0
    iteration = 0

    while iteration < max_iterations:
        group_node_indices = [
            i for i, node in enumerate(current_nodes) if node.bl_idname == "ShaderNodeGroup"
        ]
        if not group_node_indices:
            break

        iteration += 1
        target_idx = group_node_indices[0]
        group_node = current_nodes.pop(target_idx)
        group_tree_name = group_node.operation or group_node.label or group_node.name

        internal_tree = group_trees.get(group_tree_name)
        if internal_tree is None:
            warnings.append(f"Node group '{group_node.name}' (tree '{group_tree_name}') data not found; skipped.")
            continue

        unfolded_count += 1
        prefix = f"{group_node.name}__"

        # 1. Create mapped internal nodes (skipping NodeGroupInput / NodeGroupOutput)
        node_id_map: dict[str, str] = {}
        for internal_node in internal_tree.nodes:
            if internal_node.bl_idname in ("NodeGroupInput", "NodeGroupOutput"):
                continue

            new_name = f"{prefix}{internal_node.name}"
            node_id_map[internal_node.name] = new_name
            loc = (
                group_node.location[0] + internal_node.location[0],
                group_node.location[1] + internal_node.location[1],
            )
            copied_node = replace(
                internal_node,
                name=new_name,
                location=loc,
            )
            current_nodes.append(copied_node)

        # 2. Add internal links
        for internal_link in internal_tree.links:
            from_in_map = internal_link.from_node in node_id_map
            to_in_map = internal_link.to_node in node_id_map

            if from_in_map and to_in_map:
                current_links.append(
                    SerializedLink(
                        from_node=node_id_map[internal_link.from_node],
                        from_socket=internal_link.from_socket,
                        to_node=node_id_map[internal_link.to_node],
                        to_socket=internal_link.to_socket,
                        to_socket_identifier=internal_link.to_socket_identifier,
                    )
                )

        # 3. Rewire external links coming into group_node
        input_links = [link for link in current_links if link.to_node == group_node.name]
        current_links = [link for link in current_links if link.to_node != group_node.name]

        # Find NodeGroupInput in internal tree
        input_node = next((n for n in internal_tree.nodes if n.bl_idname == "NodeGroupInput"), None)
        if input_node:
            for ext_link in input_links:
                # Internal links starting from NodeGroupInput.socket matching ext_link.to_socket
                matching_internal_links = [
                    link
                    for link in internal_tree.links
                    if link.from_node == input_node.name
                    and (link.from_socket == ext_link.to_socket or link.to_socket_identifier == ext_link.to_socket_identifier)
                ]
                for int_link in matching_internal_links:
                    if int_link.to_node in node_id_map:
                        current_links.append(
                            SerializedLink(
                                from_node=ext_link.from_node,
                                from_socket=ext_link.from_socket,
                                to_node=node_id_map[int_link.to_node],
                                to_socket=int_link.to_socket,
                                to_socket_identifier=int_link.to_socket_identifier,
                            )
                        )

        # 4. Rewire external links coming out of group_node
        output_links = [link for link in current_links if link.from_node == group_node.name]
        current_links = [link for link in current_links if link.from_node != group_node.name]

        output_node = next((n for n in internal_tree.nodes if n.bl_idname == "NodeGroupOutput"), None)
        if output_node:
            for ext_link in output_links:
                matching_internal_links = [
                    link
                    for link in internal_tree.links
                    if link.to_node == output_node.name
                    and link.to_socket == ext_link.from_socket
                ]
                for int_link in matching_internal_links:
                    if int_link.from_node in node_id_map:
                        current_links.append(
                            SerializedLink(
                                from_node=node_id_map[int_link.from_node],
                                from_socket=int_link.from_socket,
                                to_node=ext_link.to_node,
                                to_socket=ext_link.to_socket,
                                to_socket_identifier=ext_link.to_socket_identifier,
                            )
                        )

    if iteration >= max_iterations:
        warnings.append(f"Reached maximum iteration limit ({max_iterations}) during node group flattening.")

    return FlattenedGraphResult(
        graph=SerializedMaterialGraph(
            material_name=graph.material_name,
            nodes=tuple(current_nodes),
            links=tuple(current_links),
        ),
        unfolded_group_count=unfolded_count,
        warnings=tuple(warnings),
    )

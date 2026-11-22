"""Serialize Blender ShaderNodeTree objects into pure Python graph DTOs."""

from __future__ import annotations

from typing import Any

from ..core.graph_planner import (
    SerializedLink,
    SerializedMaterialGraph,
    SerializedNode,
    SerializedSocket,
)


def serialize_material_graph(mat: Any) -> SerializedMaterialGraph:
    """Read a Blender material's node_tree into a ``SerializedMaterialGraph``."""
    node_tree = getattr(mat, "node_tree", None)
    if node_tree is None:
        return SerializedMaterialGraph(material_name=getattr(mat, "name", "<unknown>"))

    serialized_nodes: list[SerializedNode] = []
    for node in node_tree.nodes:
        image_name = ""
        image = getattr(node, "image", None)
        if image is not None and getattr(image, "name", None):
            image_name = image.name

        inputs = tuple(
            SerializedSocket(
                name=inp.name,
                identifier=getattr(inp, "identifier", inp.name),
                is_linked=bool(inp.is_linked),
            )
            for inp in getattr(node, "inputs", ())
        )

        loc = getattr(node, "location", (0.0, 0.0))
        serialized_nodes.append(
            SerializedNode(
                name=node.name,
                bl_idname=node.bl_idname,
                label=getattr(node, "label", ""),
                operation=str(getattr(node, "operation", "")),
                image_name=image_name,
                location=(float(loc[0]), float(loc[1])),
                inputs=inputs,
            )
        )

    serialized_links: list[SerializedLink] = []
    for link in node_tree.links:
        if not link.from_node or not link.to_node:
            continue
        to_socket = link.to_socket
        serialized_links.append(
            SerializedLink(
                from_node=link.from_node.name,
                from_socket=link.from_socket.name if link.from_socket else "",
                to_node=link.to_node.name,
                to_socket=to_socket.name if to_socket else "",
                to_socket_identifier=getattr(to_socket, "identifier", "") if to_socket else "",
            )
        )

    return SerializedMaterialGraph(
        material_name=getattr(mat, "name", "<unknown>"),
        nodes=tuple(serialized_nodes),
        links=tuple(serialized_links),
    )

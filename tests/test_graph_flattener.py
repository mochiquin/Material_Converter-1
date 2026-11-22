"""Unit tests for pure Python node group flattener in core/graph_flattener.py."""

from __future__ import annotations

from core.graph_flattener import flatten_graph_ir
from core.graph_planner import SerializedLink, SerializedMaterialGraph, SerializedNode


def test_flatten_graph_ir_single_node_group_unfolds_and_rewires() -> None:
    # Internal node group topology
    group_tree = SerializedMaterialGraph(
        material_name="MyGroup",
        nodes=(
            SerializedNode(name="Group Input", bl_idname="NodeGroupInput"),
            SerializedNode(name="Group Output", bl_idname="NodeGroupOutput"),
            SerializedNode(name="InternalMath", bl_idname="ShaderNodeMath", operation="MULTIPLY"),
        ),
        links=(
            SerializedLink("Group Input", "Color", "InternalMath", "Value", "Value"),
            SerializedLink("InternalMath", "Value", "Group Output", "Color", "Color"),
        ),
    )

    # Main material topology
    main_graph = SerializedMaterialGraph(
        material_name="MainMat",
        nodes=(
            SerializedNode(name="TexImage", bl_idname="ShaderNodeTexImage"),
            SerializedNode(name="MyGroupNode", bl_idname="ShaderNodeGroup", operation="MyGroup"),
            SerializedNode(name="Principled", bl_idname="ShaderNodeBsdfPrincipled"),
        ),
        links=(
            SerializedLink("TexImage", "Color", "MyGroupNode", "Color", "Color"),
            SerializedLink("MyGroupNode", "Color", "Principled", "Base Color", "Base Color"),
        ),
    )

    res = flatten_graph_ir(main_graph, group_trees={"MyGroup": group_tree})
    assert res.unfolded_group_count == 1
    assert len(res.warnings) == 0

    node_names = [n.name for n in res.graph.nodes]
    assert "MyGroupNode" not in node_names
    assert "MyGroupNode__InternalMath" in node_names

    # Check rewired connections
    rewired_links = [(link.from_node, link.to_node) for link in res.graph.links]
    assert ("TexImage", "MyGroupNode__InternalMath") in rewired_links
    assert ("MyGroupNode__InternalMath", "Principled") in rewired_links


def test_flatten_graph_ir_nested_node_groups() -> None:
    inner_group = SerializedMaterialGraph(
        material_name="InnerGroup",
        nodes=(
            SerializedNode(name="Group Input", bl_idname="NodeGroupInput"),
            SerializedNode(name="Group Output", bl_idname="NodeGroupOutput"),
            SerializedNode(name="InnerAdd", bl_idname="ShaderNodeMath", operation="ADD"),
        ),
        links=(
            SerializedLink("Group Input", "InVal", "InnerAdd", "Value", "Value"),
            SerializedLink("InnerAdd", "Value", "Group Output", "OutVal", "OutVal"),
        ),
    )

    outer_group = SerializedMaterialGraph(
        material_name="OuterGroup",
        nodes=(
            SerializedNode(name="Group Input", bl_idname="NodeGroupInput"),
            SerializedNode(name="Group Output", bl_idname="NodeGroupOutput"),
            SerializedNode(name="InnerGroupNode", bl_idname="ShaderNodeGroup", operation="InnerGroup"),
        ),
        links=(
            SerializedLink("Group Input", "InVal", "InnerGroupNode", "InVal", "InVal"),
            SerializedLink("InnerGroupNode", "OutVal", "Group Output", "OutVal", "OutVal"),
        ),
    )

    main_graph = SerializedMaterialGraph(
        material_name="NestedMat",
        nodes=(
            SerializedNode(name="StartNode", bl_idname="ShaderNodeValue"),
            SerializedNode(name="OuterGroupNode", bl_idname="ShaderNodeGroup", operation="OuterGroup"),
            SerializedNode(name="EndNode", bl_idname="ShaderNodeBsdfPrincipled"),
        ),
        links=(
            SerializedLink("StartNode", "Value", "OuterGroupNode", "InVal", "InVal"),
            SerializedLink("OuterGroupNode", "OutVal", "EndNode", "Base Color", "Base Color"),
        ),
    )

    res = flatten_graph_ir(
        main_graph,
        group_trees={
            "OuterGroup": outer_group,
            "InnerGroup": inner_group,
        },
    )

    assert res.unfolded_group_count == 2
    assert len(res.warnings) == 0

    node_names = [n.name for n in res.graph.nodes]
    assert "OuterGroupNode" not in node_names
    assert "OuterGroupNode__InnerGroupNode" not in node_names
    assert "OuterGroupNode__InnerGroupNode__InnerAdd" in node_names


def test_flatten_graph_ir_missing_group_tree_emits_warning() -> None:
    main_graph = SerializedMaterialGraph(
        material_name="MissingGroupMat",
        nodes=(
            SerializedNode(name="UnknownGroup", bl_idname="ShaderNodeGroup", operation="GhostTree"),
        ),
    )

    res = flatten_graph_ir(main_graph, group_trees={})
    assert res.unfolded_group_count == 0
    assert len(res.warnings) == 1
    assert "GhostTree" in res.warnings[0]

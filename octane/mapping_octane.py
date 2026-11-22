"""Mapping helper for Octane materials."""

from __future__ import annotations

import bpy

from ..scripts.premade import Add_Mapping_Node


def add_mapping(context=None) -> None:
    ctx = context if context is not None else bpy.context
    mat = ctx.object.active_material
    Add_Mapping_Node(mat)

import bpy
import os
import sys

## Import ##
octane_folder = os.path.dirname(__file__)
if octane_folder not in sys.path:
    sys.path.append(octane_folder)

# All the actual conversion logic lives in convert_core.py, shared by
# convert_active/selected/all_octane.py - see convert_core.py's docstring.
from convert_core import convert_material_to_octane, is_octane_converted

Render_engine = bpy.context.scene.render.engine
if Render_engine != 'octane':
    bpy.context.scene.view_settings.view_transform = 'Raw'
    bpy.context.scene.view_settings.look = 'None'
    bpy.context.scene.render.engine = "octane"

current_workspace = bpy.context.workspace
for screen in current_workspace.screens:
    for area in screen.areas:
        if area.type == 'NODE_EDITOR' and not area.ui_type in ["GeometryNodeTree", "CompositorNodeTree"]:
            area.ui_type = 'ShaderNodeTree'

def get_materials_to_convert():
    """Return the list of materials "Convert All" would touch, without converting
    them yet. Used by MATERIAL_OT_convert_all in __init__.py to drive the
    conversion incrementally (one batch per timer tick) so it can show a
    progress bar and keep Blender's UI responsive instead of freezing while
    every material in the file converts in a single blocking loop."""
    materials = []
    for material in bpy.data.materials:
        if "Dot Stroke" in material.name:
            continue

        mat = material
        if not mat or not hasattr(mat, 'node_tree') or not mat.node_tree:
            continue

        # Skip materials that already have Octane nodes - "convert all" is a bulk
        # operation and shouldn't keep reprocessing already-converted materials.
        # (Unlike "convert active material", which always reconverts on purpose.)
        if is_octane_converted(mat):
            continue

        materials.append(mat)
    return materials

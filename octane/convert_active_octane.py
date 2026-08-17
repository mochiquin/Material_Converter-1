import bpy
import os
import sys

## Import ##
octane_folder = os.path.dirname(__file__)
if octane_folder not in sys.path:
    sys.path.append(octane_folder)

# All the actual conversion logic lives in convert_core.py, shared by
# convert_active/selected/all_octane.py - see convert_core.py's docstring.
from convert_core import convert_material_to_octane

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

mat = bpy.context.object.active_material
convert_material_to_octane(mat)

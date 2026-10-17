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

# Every selected object (plus the active one), not just the active object.
objects = list(bpy.context.selected_objects)
active = bpy.context.active_object
if active and active not in objects:
    objects.append(active)

seen = set()
for obj in objects:
    for slot in obj.material_slots:
        mat = slot.material
        if not mat or mat.name in seen:
            continue
        seen.add(mat.name)
        if not hasattr(mat, 'node_tree') or not mat.node_tree:
            continue

        # Skip materials that already have an Octane material node - "convert
        # selected" is a bulk operation and shouldn't keep reprocessing
        # already-converted materials. (Unlike "convert active material", which
        # always reconverts on purpose.)
        if is_octane_converted(mat):
            continue

        # One broken material must not abort the rest of the selection.
        try:
            convert_material_to_octane(mat)
        except Exception:
            import traceback
            print(f"[Material Converter] Failed to convert '{mat.name}':")
            traceback.print_exc()

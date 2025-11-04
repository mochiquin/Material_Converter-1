import bpy

## Octane Version

##Scene
bpy.context.scene.view_settings.view_transform = 'Raw'
bpy.context.scene.view_settings.look = 'None'
bpy.context.scene.render.engine = "octane"

current_workspace = bpy.context.workspace
for screen in current_workspace.screens:
    for area in screen.areas:
        if area.type == 'NODE_EDITOR'and not area.ui_type in ["GeometryNodeTree", "CompositorNodeTree"]:
            area.ui_type = 'ShaderNodeTree'


mat = bpy.context.object.active_material

nodetree = mat.node_tree
texture = None
if nodetree.nodes:
    for n in nodetree.nodes:
        if n.bl_idname == "OctaneRGBImage":
            texture = n
            break  # Exit the loop if the texture is fo
        
if not nodetree.nodes:
    m = nodetree.nodes.new("ShaderNodeOutputMaterial")
    m.label = "Octane Output"



if not texture:
    bpy.ops.shader.import_images_to_shadernodes('INVOKE_DEFAULT')







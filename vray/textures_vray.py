import bpy


bpy.context.scene.view_settings.view_transform = 'AgX'
bpy.context.scene.view_settings.look = 'None'


bpy.context.scene.render.engine = "VRAY_RENDER_RT"

current_workspace = bpy.context.workspace
for screen in current_workspace.screens:
    for area in screen.areas:
        if area.type == 'NODE_EDITOR'and not area.ui_type in ["GeometryNodeTree", "CompositorNodeTree"]:
            area.ui_type = 'VRayNodeTreeEditor'


mat = bpy.context.object.active_material

nodetree = mat.node_tree
texture = None
if nodetree.nodes:
    for n in nodetree.nodes:
        if n.bl_idname == "VRayNodeMetaImageTexture":
            texture = n
            break  # Exit the loop if the texture is fo
        
if not nodetree.nodes:
    m = nodetree.nodes.new("VRayNodeOutputMaterial")
    m.label = "V-Ray Output Output"



if not texture:
    bpy.ops.shader.import_images_to_shadernodes('INVOKE_DEFAULT')







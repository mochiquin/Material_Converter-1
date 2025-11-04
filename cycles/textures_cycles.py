import bpy

## Cycles Import Textures

bpy.context.scene.render.engine = "CYCLES"
current_workspace = bpy.context.workspace
for screen in current_workspace.screens:
    for area in screen.areas:
        if area.type == 'NODE_EDITOR'and not area.ui_type in ["GeometryNodeTree", "CompositorNodeTree"]:
            area.ui_type = 'ShaderNodeTree'


mat = bpy.context.object.active_material
mat.use_nodes = True
nodetree = mat.node_tree
texture = None
if nodetree.nodes:
    for n in nodetree.nodes:
        if n.bl_idname == "ShaderNodeTexImage":
            texture = n
            break  # Exit the loop if the texture is fo
        
if not nodetree.nodes:
    m = nodetree.nodes.new("ShaderNodeOutputMaterial")
    
if not texture:
   bpy.ops.shader.import_images_to_shadernodes('INVOKE_DEFAULT')







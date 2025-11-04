import bpy

render_engine = bpy.context.scene.render.engine 
if render_engine != "LUXCORE":
    bpy.context.scene.view_settings.view_transform = 'AgX'
    bpy.context.scene.view_settings.look = 'None'
    bpy.context.scene.render.engine = "LUXCORE"

    current_workspace = bpy.context.workspace
    for screen in current_workspace.screens:
        for area in screen.areas:
            if area.type == 'NODE_EDITOR' and not area.ui_type in ["GeometryNodeTree", "CompositorNodeTree"]:
                area.ui_type = 'luxcore_material_nodes'


mat = bpy.context.object.active_material
nodetree = mat.luxcore.node_tree
material_name = mat.name
if not mat.luxcore.node_tree:
    color = []
    color.append(mat.diffuse_color[0])
    color.append(mat.diffuse_color[1])
    color.append(mat.diffuse_color[2])
    color.append(mat.diffuse_color[3])
    mat.luxcore.node_tree = bpy.data.node_groups.new(name=material_name, type="luxcore_material_nodes") 
    mat.luxcore.use_cycles_nodes = False
    mat.luxcore.auto_vp_color = False
    mat.diffuse_color = (color[0],color[1],color[2],color[3])
    nodetree = mat.luxcore.node_tree
    
if not nodetree.nodes:
    m = mat.luxcore.node_tree.nodes.new("LuxCoreNodeTexMapping2D")
    m.label = "LuxCore Mapping"

bpy.ops.shader.import_images_to_shadernodes('INVOKE_DEFAULT')










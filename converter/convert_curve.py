import bpy


def Convert_Curve_node(cycles_curve,mat):
    Render_engine = bpy.context.scene.render.engine
    
    if Render_engine == "octane":
        node_curve = "NodeReroute"
        nodes = mat.node_tree.nodes
        curve_name = "Reroute"
        input_name = "Texture"
        output_name = "Texture out"
        offset_x = 1650
        offset_y = 0
    elif Render_engine == "VRAY_RENDER_RT":
        node_curve = "VRayNodeTexRemap"
        curve_name = "V-Ray Remap"
        nodes = mat.node_tree.nodes
        offset_x = 0
        offset_y = -1650
    elif Render_engine == "LUXCORE":
        node_curve = "NodeReroute"
        curve_name = "Reroute"
        nodes = mat.luxcore.node_tree.nodes
        offset_x = 0
        offset_y = 0
        input_name = "Color"
        output_name = "Color"        
       
    Vray_curve_node = None
    Curve_node_name = cycles_curve.name.replace("RGB Curves","V-Ray Remap")
    for n in nodes:
        if n.bl_idname == node_curve and n.name == Curve_node_name:
            Vray_curve_node = n
            break
    if not Vray_curve_node:
        
        Vray_curve_node = nodes.new(node_curve)
        Vray_curve_node.label = cycles_curve.label
        Vray_curve_node.location = (cycles_curve.location[0] + offset_x, cycles_curve.location[1] + offset_y)
    if Render_engine != "VRAY_RENDER_RT":
        Vray_curve_node.inputs[0].name = input_name
        Vray_curve_node.outputs[0].name = output_name
    else: 
        cycles_curves = cycles_curve.mapping.curves  # R, G, B, C
            

        # Getting Static_ID
        remap_index = str(Vray_curve_node.static_id)

        # Getting NodeGroup ".texRemapTree"
        tex_remap_tree = bpy.data.node_groups.get(".texRemapTree")

        if tex_remap_tree:
            node_name = f"TexRemap{remap_index}"

            if node_name in tex_remap_tree.nodes:
                tex_remap_node = tex_remap_tree.nodes[node_name]

                
                if hasattr(tex_remap_node, "mapping"):
                    tex_remap_curves = tex_remap_node.mapping.curves  # R, G, B, C

                    for i, curve in enumerate(cycles_curves):
                        print(f"Converting Curve {['R', 'G', 'B', 'C'][i]}:")

                        
                        for j, point in enumerate(curve.points):
                            x, y = point.location
                            print(f"  - Cycles: x: {x:.3f}, y: {y:.3f}")

                            
                            if j < len(tex_remap_curves[i].points):
                                
                                tex_remap_curves[i].points[j].location = (x, y)
                            else:
                               
                                tex_remap_curves[i].points.new(x, y)


"""mat = bpy.context.object.active_material
c_nodes = mat.node_tree.nodes
cycles_curves = [node for node in c_nodes if node.bl_idname == "ShaderNodeRGBCurve"]
for cycles_curve in cycles_curves:
                                     
    Convert_Curve_node(cycles_curve,mat)"""
        

                    


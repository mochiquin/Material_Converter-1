import bpy


preferences = bpy.context.preferences.addons["Material_Converter 1"].preferences
Render_Engine = bpy.context.scene.render.engine

mat = bpy.context.object.active_material


def Change_Vray_outputs(mat):
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    material_node = next(
        (node for node in nodes if node.bl_idname.startswith("VRayNodeBRDFVRayMtl") and node.label == "Material"),
        None
    )
    output_node = next(
        (node for node in nodes if node.bl_idname.startswith("VRayNodeOutputMaterial")),
        None
    ) 
    if material_node is None:
        print("Nie znaleziono węzła material_node.")
        return
    
    
    label_to_output = {
        "Float socket": "Out Intensity",
        "Color socket": "Color",
    }
    
    for input_index, input_socket in enumerate(material_node.inputs):
        
        incoming_links = [link for link in input_socket.links if link.from_node.bl_idname.startswith("VRay")]
        
        for link in incoming_links:
            from_node = link.from_node
            from_socket = link.from_socket
            
            
            target_output_name = label_to_output.get(input_socket.bl_label)
            if target_output_name is None:
                continue  
            
            
            matching_outputs = [
                output for output in from_node.outputs if output.name == target_output_name
            ]
            if not matching_outputs:
                print(f"Węzeł: {from_node.bl_idname} nie ma wyjścia {target_output_name}, pomijam.")
            
                continue
            
            
            
            new_output = matching_outputs[0]
            print(f"Zmieniam połączenie: {from_socket.name} -> {new_output.name}")
            
            
            links.remove(link)
            links.new(new_output, input_socket)
    for input_index, input_socket in enumerate(material_node.inputs):
    
        incoming_links = [link for link in input_socket.links if link.from_node.bl_idname.startswith("VRay")]    
        for link in incoming_links:
            
            node = from_node
            nodes = mat.node_tree.nodes
            from_node_input = link.from_node
            
            from_socket = link.from_socket
            target_output_name = label_to_output.get(input_socket.bl_label)
            
            # Sprawdzenie, czy potrzebujemy wstawić nowy węzeł
            
            if from_socket.bl_label == "Color with Alpha socket" and input_socket.bl_label == "Float socket":
                
                
                color_to_float_node = nodes.new("VRayNodeTexColorToFloat")
                print(color_to_float_node.bl_idname)
                color_to_float_node.label = node.label
                color_to_float_node.location = (node.location[0], node.location[1]+100)
                
                # Łączenie węzła Color do nowego węzła
                links.new(from_socket, color_to_float_node.inputs["Input"])  # Zakładam, że input[0] to socket Color
                links.new(color_to_float_node.outputs["Float"], input_socket)
                material_node.location =   (color_to_float_node.location[0] + 300, color_to_float_node.location[1] + 200 )
                output_node.location = (material_node.location[0] + 300, material_node.location[1])
    
            
def split_object_by_material(obj):
    """Split object by materials and name new objects by material names."""
    base_name = obj.name
    
    # Wykonaj podział
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.separate(type='MATERIAL')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Zmień nazwy nowych obiektów
    new_objects = [o for o in bpy.context.selected_objects if o != obj]
    for new_obj in new_objects:
        if new_obj.material_slots:
            material_name = new_obj.material_slots[0].material.name
            new_obj.name = f"{base_name}_{material_name}"
    
    return new_objects

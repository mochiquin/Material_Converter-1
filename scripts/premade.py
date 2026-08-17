# scripts/__init__.py
import bpy

def label_nodes_from_base_color(mat):
    # Iteruj przez wszystkie materiały
    material = mat
        
    # Pobierz drzewo węzłów
    node_tree = material.node_tree
    
    # Znajdź węzeł Principled BSDF
    principled_bsdf = None
    principled_count = 0
    for node in node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            label = "Material" if principled_count == 0 else f"Material {principled_count}"
            node.label = label
            principled_bsdf = node
            principled_count += 1
    
    if principled_count == 0:
        print(f"No Principled BSDF node found in the material '{material.name}'.")
        
    # Definicje prefiksów
    input_prefix_map = {
        "Base Color": "Diffuse",
        "Specular IOR Level": "Specular"
    }
    
    # Iteracja przez wszystkie węzły w materiale
    
    

    
    # Sprawdź Material Output
    material_output = None
    for node in node_tree.nodes:
        if node.type == 'OUTPUT_MATERIAL':
            if node.inputs['Surface'].is_linked:
                output_link = node.inputs['Surface'].links[0]
                if not output_link.from_node.bl_idname.startswith('Octane'):
                    material_output = node
                    material_output.label = "Material Output"
                    break
    # Znalezienie i etykietowanie węzłów Displacement
    for node in node_tree.nodes:
        if node.type == 'DISPLACEMENT':  # Typ Displacement
            if node.label == "":  # Etykieta Displacement, jeśli pusta
                node.label = "Displacement"
            
            # Iteracja po połączonych węzłach
            for input in node.inputs:
                if input.is_linked:
                    link = input.links[0]
                    # Rekursywne ustawienie etykiet na powiązanych węzłach
                    set_labels_recursive(link.from_node, "Displacement")
    for node in node_tree.nodes:
        if node.bl_idname == 'ShaderNodeBump':  # Typ Displacement
            
            node.label = "Bump"
            # Iteracja po połączonych węzłach
            for input in node.inputs:
                if input.is_linked:
                    link = input.links[0]
                    # Rekursywne ustawienie etykiet na powiązanych węzłach
                    set_labels_recursive(link.from_node, "Bump")
            
            # Iteracja po połączonych węzłach
            for input in node.inputs:
                if input.is_linked:
                    link = input.links[0]
                    # Rekursywne ustawienie etykiet na powiązanych węzłach
                    set_labels_recursive(link.from_node, "Displacement")
    for node in node_tree.nodes:
        if node.bl_idname == "ShaderNodeBsdfTranslucent" or node.bl_idname == "ShaderNodeBsdfGlass":
            node.label = "Material"
    for node in node_tree.nodes:
        if node.bl_idname == "ShaderNodeNormalMap":
            node.label = "Normal"
    for node in node_tree.nodes:
        if node.bl_idname == "ShaderNodeBsdfPrincipled":
            # Pobierz i przetwórz indeks z etykiety węzła Principled BSDF
            index = node.label.replace("Material", "").strip()

            # Iteracja przez wszystkie wejścia do Principled BSDF
            
            
            for input_name, input in node.inputs.items():
                if input.is_linked:
                    # Znajdź połączony węzeł
                    link = input.links[0]
                    
                    # Pobierz prefiks etykiety na podstawie nazwy wejścia
                    label_prefix = input_prefix_map.get(input_name, input_name)
                    
                    # Przekaż indeks i prefiks do funkcji etykietującej
                    set_labels_recursive(link.from_node, f"{index} {label_prefix}")
        
       
def set_labels_recursive(node, label_prefix):
    # Specjalne traktowanie dla ShaderNodeMix
    if node.bl_idname == 'ShaderNodeMix':
        if not node.label:  # Sprawdź czy etykieta już istnieje
            node.label = f"{label_prefix}"
        for i, input_name in enumerate(['A', 'B']):
            if node.inputs[6 + i].is_linked:
                link = node.inputs[6 + i].links[0]
                new_label_prefix = f"{label_prefix} {input_name}"
                set_labels_recursive(link.from_node, new_label_prefix)
        return
    
    elif node.bl_idname == 'ShaderNodeMapping':
        if not node.label:  # Sprawdź czy etykieta już istnieje
            prefix_to_label_map = {
                "Normal": "3",
                "Diffuse": "1",
                "Roughness": "2",
                "Specular": "5",
                "Transmission": "4",
            }
            new_label = prefix_to_label_map.get(label_prefix, label_prefix)
            node.label = f"Mapping {new_label}"
        return
   
    # Ustaw etykietę tylko jeśli jej nie ma
    if not node.label:
        node.label = f"{label_prefix}"

    # Przechodź przez podłączone węzły
    linked_inputs = [input for input in node.inputs if input.is_linked]
    if len(linked_inputs) > 1:
        # More than one branch feeds this node (e.g. both Value inputs of a
        # Math node, or two Vector inputs of a Vector Math node). Every
        # renderer's rebuild_*_connections() pairs up Cycles <-> engine nodes
        # by matching bl_idname + label, so if every branch inherited the
        # exact same label_prefix here, two different upstream nodes would
        # end up with identical labels and the connection step can no longer
        # tell them apart (it just grabs the first label match every time).
        # Suffix each branch with its socket identifier - same idea as the
        # ShaderNodeMix 'A'/'B' special case above, just generalized.
        for input in linked_inputs:
            link = input.links[0]
            branch_suffix = input.identifier or input.name
            set_labels_recursive(link.from_node, f"{label_prefix} {branch_suffix}")
    else:
        for input in linked_inputs:
            link = input.links[0]
            set_labels_recursive(link.from_node, label_prefix)

def Add_Mapping_Node(material):
    Render_engine_mat = bpy.context.scene.render.engine
    if Render_engine_mat == "LUXCORE":
        active_mat = material.luxcore
    else:
        active_mat = material
    
    node_tree = active_mat.node_tree
    



    if node_tree:
        nodes = node_tree.nodes
        links = node_tree.links
        
        if Render_engine_mat == "VRAY_RENDER_RT":
            
            Mapping_node = "VRayNodeUVWMapping"
            Image_nodes = [node for node in node_tree.nodes if node.bl_idname.startswith("VRayNodeMetaImageTexture")]
            Engine_Mapping = [node for node in node_tree.nodes if node.bl_idname.startswith("VRayNodeUVWMapping")]
            input_nr = 0
            
        elif Render_engine_mat == "octane":
            Mapping_node = "Octane3DTransformation"
            Image_nodes = [node for node in node_tree.nodes if node.bl_idname.startswith("OctaneRGBImage")]
            Engine_Mapping = [node for node in node_tree.nodes if node.bl_idname.startswith("Octane3DTransformation")]
            input_nr = 5
            
        elif Render_engine_mat == "LUXCORE":
            Mapping_node = "LuxCoreNodeTexMapping2D"
            Image_nodes = [node for node in node_tree.nodes if node.bl_idname.startswith("LuxCoreNodeTexImagemap")]
            Engine_Mapping = [node for node in node_tree.nodes if node.bl_idname.startswith("LuxCoreNodeTexMapping2D")]
            input_nr = 0
        
        
        if Image_nodes:
            if Engine_Mapping:
                Engine_Mapping = Engine_Mapping[0]
            else: Engine_Mapping = nodes.new(Mapping_node)
            Engine_Mapping.location = (Image_nodes[0].location[0] - 600, Image_nodes[0].location[1])
            
            for image in Image_nodes:
                for input_socket in image.inputs:
                    if not input_socket.is_linked:
                 
                        links.new(Engine_Mapping.outputs[0],image.inputs[input_nr])

def remove_reroutes_from_material(material):
    if not material or not material.use_nodes:
        return

    
    node_tree = material.node_tree
    reroute_nodes = [node for node in node_tree.nodes if node.type == 'REROUTE']
    if not reroute_nodes:
        return

    
    def remove_reroute_and_reconnect(reroute_node):
        if reroute_node.inputs[0].is_linked and reroute_node.outputs[0].is_linked:
            input_link = reroute_node.inputs[0].links[0]
            from_socket = input_link.from_socket
            
            for output_link in reroute_node.outputs[0].links:
                to_socket = output_link.to_socket
                node_tree.links.new(from_socket, to_socket)
        node_tree.nodes.remove(reroute_node)
    for reroute_node in reroute_nodes:
        remove_reroute_and_reconnect(reroute_node)
    

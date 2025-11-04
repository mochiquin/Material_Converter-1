# scripts/__init__.py
import bpy
import math
import os
import re

def connect_to_closest_octane_group_node(mat):
    # Słownik przypisujący prefiksy do nazw wejść grupy Octane
    prefix_to_input_name = {
        "Diffuse": "Albedo",
        "Specular": "Reflection Color",
        "Metallic": "Metallic",
        "Normal": "Bump",
        "Roughness": "Roughness",
        "Gloss": "Roughness",
        "Displacement": "Displacement",
        "Bump": "Bump",
        "Transmission": "Transmission",
        "Coat Tint": "Coating",
        "Opacity": "Opacity"
    }
    active_mat = mat
    
    # Use LuxCore node tree
    node_tree = active_mat.node_tree

    
    if node_tree:
        nodes = node_tree.nodes
        links = node_tree.links

        # Find the Octane group node
        octane_group_node = next((node for node in nodes if 'Universal' in node.bl_idname), None)
        if not octane_group_node:
            print(f"No 'Octane' group node found in material '{active_mat.name}'.")
            return

        # Create a dictionary to store inputs of the group node
        group_node_inputs = {input.name: input for input in octane_group_node.inputs}

        # Find all nodes that are not the Octane group node
        other_nodes = [node for node in nodes if node != octane_group_node]

        # Create a list of nodes to connect, sorted by distance to the Octane group node
        def distance(node):
            return math.sqrt((octane_group_node.location.y - node.location.y)**2)
                            

        # Debugging prints to verify node locations and distances
        print(f"Octane group node location: ({octane_group_node.location.x}, {octane_group_node.location.y})")
        sorted_nodes = sorted(other_nodes, key=distance)

        print(f"Sorted nodes for material '{active_mat.name}':")
        for node in sorted_nodes:
            dist = distance(node)
            print(f"Node {node.name} at ({node.location.x}, {node.location.y}) is {dist:.2f} units away")

        # Connect nodes to group node inputs based on prefix and distance
        for node in sorted_nodes:
            if node.bl_idname.startswith("Octane") and node.label:
                # Find the appropriate input name in the group node based on the node's label prefix
                for prefix, input_name in prefix_to_input_name.items():
                    if prefix in node.label:
                        if input_name in group_node_inputs:
                            input_socket = group_node_inputs[input_name]
                            if node.outputs:
                                # Remove existing links to this input socket
                                while input_socket.is_linked:
                                    link_to_remove = input_socket.links[0]
                                    links.remove(link_to_remove)

                                # Connect the node's output to the input of the group node
                                current_output = node.outputs[0]
                                links.new(current_output, input_socket)
                                print(f"Connecting '{node.label}' output to '{octane_group_node.name}' group's '{input_name}' input")
                                break  # Stop once connected to an available input
                                
                                
def connect_to_closest_luxcore_group_node(mat):
    # Dictionary mapping prefixes to input names
    prefix_to_input_name = {
        "Diffuse": "Base Color",
        "Specular": "Specular",
        "Metallic": "Metallic",
        "Normal": "Bump",
        "Roughness": "Roughness",
        "Displacement": "Displacement",
        "Bump": "Bump",
        "Transmission": "Translusency Color",
        "Opacity": "Opacity"
    }
    active_mat = mat
    
    


    # Use LuxCore node tree
    node_tree = active_mat.luxcore.node_tree
    
    if node_tree:
        nodes = node_tree.nodes
        links = node_tree.links
        
        # Find the LuxCore group node (first node starting with LuxCoreNodeMat)
        luxcore_group_node = next((node for node in nodes if node.bl_idname.startswith("LuxCoreNodeMat") and "Material" in node.label), None)
        
        if not luxcore_group_node:
            print(f"No LuxCore group node found in material '{active_mat.name}'.")
            return
        
        # Create a dictionary to store inputs of the group node
        group_node_inputs = {input.name: input for input in luxcore_group_node.inputs}
        
        # Find all nodes that are not the LuxCore group node
        other_nodes = [node for node in nodes if node != luxcore_group_node]
        
        # Distance calculation function
        def distance(node):
            return math.sqrt((luxcore_group_node.location.y - node.location.y)**2)
        
        # Sort nodes by distance
        sorted_nodes = sorted(other_nodes, key=distance)
        
        # Debug print node locations and distances
        print(f"LuxCore group node({luxcore_group_node.name}) location: ({luxcore_group_node.location.x}, {luxcore_group_node.location.y})")
        for node in sorted_nodes:
            dist = distance(node)
            print(f"Node {node.name} at ({node.location.x}, {node.location.y}) is {dist:.2f} units away")
        
        # Connect nodes to group node inputs
        for node in sorted_nodes:
            if node.label:
                # Find the appropriate input name in the group node based on the node's label prefix
                for prefix, input_name in prefix_to_input_name.items():
                    if prefix in node.label:
                        if input_name in group_node_inputs:
                            input_socket = group_node_inputs[input_name]
                            
                            # Remove existing links to this input socket
                            while input_socket.is_linked:
                                link_to_remove = input_socket.links[0]
                                links.remove(link_to_remove)
                            
                            # Connect the node's output to the input of the group node
                            if node.outputs:
                                current_output = node.outputs[0]
                                if node.is_normal_map:
                                    current_output = node.outputs[2]
                                links.new(current_output, input_socket)
                                print(f"Connecting '{node.label}' output to '{luxcore_group_node.name}' group's '{input_name}' input")
                                break  # Stop once connected to an available input
def connect_to_closest_Vray_mat(mat):
   
    # Dictionary mapping prefixes to input names
    prefix_to_input_name = {
        "Diffuse": "Diffuse Color",
        "Specular": "Specular",
        "Metallic": "Metalness",
        "Normal": "Bump Map",
        "Roughness": "Reflection Glossiness",
        "Displacement": "Displacement",
        "Bump": "Bump",
        "Opacity": "Opacity",
        "Translucency": "Translucency Color",
        "Coat Tint": "Coat Color"
    }
    active_mat = mat
    
    node_tree = active_mat.node_tree
    
    if node_tree:
        nodes = node_tree.nodes
        links = node_tree.links
        
        # Find the LuxCore group node (first node starting with LuxCoreNodeMat)
        Vray_mat = next((node for node in nodes if node.bl_idname.startswith("VRay") and "Material" in node.label), None)
        
        if not Vray_mat:
            print(f"No Vray group node found in material '{active_mat.name}'.")
            return
        
        # Create a dictionary to store inputs of the group node
        group_node_inputs = {input.name: input for input in Vray_mat.inputs}
        
            
        
        use_normal = None
        normal_texture = None
        for n in nodes:
            if n.label == "Normal" and n.bl_idname == "VRayNodeTexNormalMapFlip":
                use_normal = n
                use_normal.label = "Normal"
                continue
            elif n.label == "Normal" and n.bl_idname == "VRayNodeMetaImageTexture":
                normal_texture = n
        if not use_normal and normal_texture:
            use_normal = nodes.new("VRayNodeTexNormalMapFlip")
            use_normal.location = (normal_texture.location[0] + 200,normal_texture.location[1])
            use_normal.label = "Normal" 
            links.new(normal_texture.outputs[0],use_normal.inputs[4])
            
        other_nodes = [node for node in nodes if node.bl_idname.startswith('VRay')] 
        
        def distance(node):
            return math.sqrt((Vray_mat.location.x - node.location.x)**2)
        
        # Sort nodes by distance
        sorted_nodes = sorted(other_nodes, key=distance)
        
        # Debug print node locations and distances
        print(f"LuxCore group node({Vray_mat.name}) location: ({Vray_mat.location.x}, {Vray_mat.location.y})")
        for node in sorted_nodes:
            dist = distance(node)
            print(f"Node {node.name} with label {node.label} at ({node.location.x}, {node.location.y}) is {dist:.2f} units away")
        
        # Connect nodes to group node inputs
        for prefix, input_name in prefix_to_input_name.items():
            # Check if the input exists in the group node
            if input_name in group_node_inputs:
                input_socket = group_node_inputs[input_name]
                
                # Skip if the input is already connected
                if input_socket.is_linked:
                    continue
                
                # Find the nearest node with a matching prefix
                for node in sorted_nodes:
                    if node.label and prefix in node.label:
                        # Connect the nearest node's output to the input
                        if node.outputs:
                            current_output = node.outputs[0]
                            links.new(current_output, input_socket)
                            print(f"Connecting '{node.bl_idname}' with label '{node.label}' output to '{Vray_mat.name}' group's '{input_name}' input")
                        break  
                                

def connect_to_closest_Cycles_mat(mat):
    # Dictionary mapping prefixes to input names
    prefix_to_input_name = {
        "Diffuse": "Base Color",
        "Specular": "Specular",
        "Metallic": "Metalness",
        "Normal": "Normal",
        "Roughness": "Roughness",
        "Displacement": "Displacement",
        "Bump": "Normal",
        "Opacity": "Alpha",
        "Translucency": "Translucency Color",
        "Coat Tint": "Coat Color",
        "IOR": "IOR",
        
    }
    active_mat = mat
    
    node_tree = active_mat.node_tree
    
    if node_tree:
        nodes = node_tree.nodes
        links = node_tree.links
        
        # Find the Cycles  Material node (first node starting with LuxCoreNodeMat)
        Cycles_mat = next((node for node in nodes if node.bl_idname.startswith("Shader") and "Material" in node.label), None)
        Cycles_output = next((node for node in nodes if node.bl_idname == ("ShaderNodeOutputMaterial") and "Cycles Output" in node.label), None)
        Eevee_output = next((node for node in nodes if node.bl_idname == ("ShaderNodeOutputMaterial") and "EEVEE Output" in node.label), None)
        Cycles_Images_nodes = [node for node in node_tree.nodes if node.bl_idname.startswith("ShaderNodeTexImage")]
        Opacity_texture =[node for node in Cycles_Images_nodes if "Opacity" in node.label] 
        Diffuse_texture = [node for node in Cycles_Images_nodes if "Diffuse" in node.label]
        AO_texture = [node for node in Cycles_Images_nodes if "AO" in node.label]
        AO_node = [node for node in node_tree.nodes if node.bl_idname.startswith("ShaderNodeMix") and any(word in node.label for word in ["Diffuse", "COLOR * AO"])]
        Transmission_texture = [node for node in Cycles_Images_nodes if "Transmission" in node.label]
        Normal_texture = [node for node in Cycles_Images_nodes if "Normal" in node.label]
        Normal_node = [node for node in node_tree.nodes if node.bl_idname.startswith("ShaderNodeNormalMap")]
        Bump_texture = [node for node in Cycles_Images_nodes if "Bump" in node.label]
        Bump_node = [node for node in node_tree.nodes if node.bl_idname.startswith("ShaderNodeBump")]
        Displacement_texture = [node for node in Cycles_Images_nodes if "Displacement" in node.label]
        Displacement_node = [node for node in node_tree.nodes if node.bl_idname.startswith("ShaderNodeDisplacement") and "Displacement" in node.label]
        
        if not Cycles_mat:
            print(f"No Cycles group node found in material '{active_mat.name}'.")
            return
        
        # Create a dictionary to store inputs of the group node
        group_node_inputs = {input.name: input for input in Cycles_mat.inputs}
        
        #Bump
        if Bump_texture:
            Bump_texture = Bump_texture[0]
            if Bump_node:
                Bump_node = Bump_node[0]
            if not Bump_node:
                Bump_node = nodes.new("ShaderNodeBump")
                Bump_node.label = "Bump"
            links.new(Bump_texture.outputs[0],Bump_node.inputs[2])
            links.new(Bump_node.outputs[0],Cycles_mat.inputs[1])
            Bump_node.location = (Bump_texture.location[0] + 300, Bump_texture.location[1] )
            
        #Normal:
        
        if Normal_texture:
            Normal_texture = Normal_texture[0]
            if Normal_node:
                Normal_node = Normal_node[0]
                
            else:
                Normal_node = nodes.new("ShaderNodeNormalMap")
                Normal_node.location = (Normal_texture.location[0] + 200,Normal_texture.location[1])
                Normal_node.label = "Normal"
            if not Bump_texture:
                links.new(Normal_texture.outputs[0],Normal_node.inputs[1])
                links.new(Normal_node.outputs[0],Cycles_mat.inputs[5])
            else:
                links.new(Normal_texture.outputs[0],Normal_node.inputs[1])
                links.new(Normal_node.outputs[0],Bump_node.inputs[3])
                Bump_node.location = (Normal_node.location[0] + 300, Normal_node.location[1] )
                    
        #Displacement
        if Displacement_texture:
            Displacement_texture = Displacement_texture[0]
            if Displacement_node:
                Displacement_node = Displacement_node[0]
            if not Displacement_node:
            
                Displacement_node = nodes.new("ShaderNodeDisplacement")
                Displacement_node.label = "Displacement"
            
            links.new(Displacement_texture.outputs[0],Displacement_node.inputs[0])
            links.new(Displacement_node.outputs[0],Cycles_output.inputs[2])
            links.new(Displacement_node.outputs[0],Eevee_output.inputs[2])
            Displacement_node.location = (Displacement_texture.location[0] + 600 ,Displacement_texture.location[1])
        
        
        
        
        
        for d in nodes:
            if "Diffuse" in d.label and d.bl_idname !="ShaderNodeMix":
                Diffuse_node = d
                
        #AO
        if AO_texture:
            AO_texture = AO_texture[0]
            if AO_node:
                AO_node = AO_node[0]
            else:
                AO_node = nodes.new("ShaderNodeMix")
                AO_node.label = "Diffuse"
                AO_node.blend_type = "MULTIPLY"
                AO_node.data_type = "RGBA"
            AO_node.location = (Diffuse_node.location[0] + 300, Diffuse_node.location[1])    
            links.new(AO_texture.outputs[0],AO_node.inputs[7])
            links.new(Diffuse_node.outputs[0],AO_node.inputs[6])
            links.new(AO_node.outputs[1],Cycles_mat.inputs[0])
                        
            
            
        other_nodes = [node for node in nodes if node.bl_idname.startswith('Shader') and node.bl_idname != "ShaderNodeOutputMaterial"]
        # Distance calculation function   
        def distance(node):
            return math.sqrt((Cycles_mat.location.x + node.location.x)**2)
        
        # Sort nodes by distance
        sorted_nodes = sorted(other_nodes, key=distance)
        
        # Debug print node locations and distances
        print(f"Cycles  Material node({Cycles_mat.name}) location: ({Cycles_mat.location.x}, {Cycles_mat.location.y})")
        for node in sorted_nodes:
            dist = distance(node)
            print(f"Node {node.name} at ({node.location.x}, {node.location.y}) is {dist:.2f} units away")
        
        # Connect nodes to group node inputs
        for node in sorted_nodes:
            if node.label:
               
                # Find the appropriate input name in the group node based on the node's label prefix
                for prefix, input_name in prefix_to_input_name.items():
                    if prefix in node.label:
                        if input_name in group_node_inputs:
                            input_socket = group_node_inputs[input_name]
                            
                            # Remove existing links to this input socket
                            while input_socket.is_linked:
                                link_to_remove = input_socket.links[0]
                                links.remove(link_to_remove)
                            
                            # Connect the node's output to the input of the group node
                            if node.outputs:
                                if node.label == "Diffuse" and node.bl_idname == "ShaderNodeMix":
                                    current_output = node.outputs[2]
                                else:
                                    current_output = node.outputs[0]
                                links.new(current_output, input_socket)
                                print(f"Connecting '{node.label}' output to '{Cycles_mat.name}' group's '{input_name}' input")
                                if node.label == "AO Multiply":
                                   links.new(node.outputs[2],Cycles_mat.inputs[0])
                                #break  # Stop once connected to an available input
def Connect_Poliigon(mat):
    
    active_mat = mat
    
    engine = bpy.context.scene.render.engine
    

    
    if engine == 'LUXCORE':
        node_tree = active_mat.luxcore.node_tree
        
    else:
        node_tree = active_mat.node_tree
        
    
    if node_tree:
        nodes = node_tree.nodes
        links = node_tree.links
        
        if engine == 'LUXCORE':
            
            Material_node = next((node for node in nodes if node.bl_idname.startswith("LuxCoreNodeMat") and "Material" in node.label), None)
            other_nodes = [node for node in nodes if node != Material_node and node.bl_idname.startswith("LuxCore")]
            engine_name = "LuxCore"
            prefix_to_input_name = {
                "Diffuse": "Base Color",
                "REFL": "Specular",
                "Metallic": "Metallic",
                "METALNESS": "Metallic",
                "NRM": "Bump",
                "NORMAL": "Bump",
                "GLOSS": "Roughness",
                "ROUGHNESS": "Roughness",
                "Displacement": "Displacement",
                "BUMP": "Bump",
                "Transmission": "Translusency Color",
                "Coat Tint": "Coat Color"
            }
        elif engine == "octane":
            Material_node = next((node for node in nodes if node.bl_idname.startswith("Octane") and "Material" in node.label), None)
            engine_name = "Octane"
            other_nodes = [node for node in nodes if node != Material_node and node.bl_idname.startswith("Octane")]
            prefix_to_input_name = {
                "Diffuse": "Albedo",
                "REFL": "Specular",
                "Metallic": "Metallic",
                "METALNESS": "Metallic",
                "NRM": "Bump",
                "NORMAL": "Bump",
                "GLOSS": "Roughness",
                "ROUGHNESS": "Roughness",
                "Displacement": "Displacement",
                "BUMP": "Bump",
                "Transmission": "Transmissionr",
                "Coat Tint": "Coating"
            }
        elif engine == "VRAY_RENDER_RT":
            Material_node = next((node for node in nodes if node.bl_idname.startswith("VRay") and "Material" in node.label), None)
            engine_name = "V-Ray"
            other_nodes = [node for node in nodes if node != Material_node and node.bl_idname.startswith("VRay")]
            prefix_to_input_name = {
                "Diffuse": "Albedo",
                "REFL": "Specular",
                "Metallic": "Metallic",
                "METALNESS": "Metallic",
                "NRM": "Bump",
                "NORMAL": "Bump",
                "GLOSS": "Roughness",
                "ROUGHNESS": "Roughness",
                "Displacement": "Displacement",
                "BUMP": "Bump",
                "Transmission": "Transmissionr",
                "Coat Tint": "Coating"
            }
            
        if not Material_node:
            print(f"No LuxCore group node found in material '{active_mat.name}'.")
            return
        
        # Create a dictionary to store inputs of the group node
        group_node_inputs = {input.name: input for input in Material_node.inputs}
        
        # Find all nodes that are not the LuxCore group node
        #other_nodes = [node for node in nodes if node != Material_node]
        
        # Distance calculation function
        def distance(node):
            return math.sqrt((Material_node.location.y - node.location.y)**2)
        
        # Sort nodes by distance
        sorted_nodes = sorted(other_nodes, key=distance)
        
        # Debug print node locations and distances
        print(f"Material node for {engine_name} : ({Material_node.name}) location: ({Material_node.location.x}, {Material_node.location.y})")
        for node in sorted_nodes:
            dist = distance(node)
            print(f"Node {node.name} at ({node.location.x}, {node.location.y}) is {dist:.2f} units away")
        
        # Connect nodes to group node inputs
        for node in sorted_nodes:
            if node.label:
                # Treat "COL" as "Diffuse"
                effective_label = node.label  # Start with the original label

                if any(item in node.label for item in ("COL", "COLOR", "COLOR * AO")):
                    effective_label = "Diffuse"
                elif any(item in node.label for item in ("ROUGHNESS", "GLOSSINESS")):
                    effective_label = "Roughness"
                
                # Find the appropriate input name in the group node based on the node's label prefix
                for prefix, input_name in prefix_to_input_name.items():
                    if prefix in effective_label.upper(): # Case-insensitive comparison
                        if input_name in group_node_inputs:
                            input_socket = group_node_inputs[input_name]
                            if not input_socket.is_linked:
                                if node.outputs:
                                    current_output = node.outputs[0]
                                    links.new(current_output, input_socket)
                                    print(f"Connecting '{node.label}' output to '{Material_node.name}' group's '{input_name}' input")
                                    break 
            
                                
def Connect_Vray_Mapping_Node(mat):
    
    
    active_mat = mat
    
    node_tree = active_mat.node_tree
    Render_engine_mat = bpy.context.scene.render.engine



    if node_tree:
        nodes = node_tree.nodes
        links = node_tree.links
        
        if Render_engine_mat == "VRAY_RENDER_RT":
                        
            Vray_Images_nodes = [node for node in nodes if node.bl_idname.startswith("VRayNodeMetaImageTexture")]
            Vray_Mapping = [node for node in nodes if node.bl_idname.startswith("VRayNodeUVWMapping")]
            input_nr = 0
            Node_Mapping = "VRayNodeUVWMapping" 
        elif Render_engine_mat == "octane":
            
            Vray_Images_nodes = [node for node in nodes if any(z in node.bl_idname for z in ["OctaneAlphaImage", "OctaneRGBImage"])]
            Vray_Mapping = [node for node in nodes if node.bl_idname.startswith("Octane3DTransformation")] 

            input_nr = 5
            Node_Mapping = "Octane3DTransformation" 
        
        
        if Vray_Images_nodes:
            if Vray_Mapping:
                Vray_Mapping = Vray_Mapping[0]
                
            if not Vray_Mapping:
                Vray_Mapping = nodes.new(Node_Mapping)
            for image in Vray_Images_nodes:
                Vray_Mapping.location = (Vray_Images_nodes[0].location[0] - 300, Vray_Images_nodes[0].location[1])
                for input_socket in image.inputs:
                    if not input_socket.is_linked:
                 
                        links.new(Vray_Mapping.outputs[0],image.inputs[input_nr])
                
                            
def label_texture_nodes(mat):
     
    texture_categories = {
        "Diffuse": ("Albedo", "Diffuse", "BaseColor", "diff", "COL"),
        "Reflection": ("Reflection", "Specular", "reflect", "refl", "spec"),
        "Roughness": ("Glossiness", "Roughness", "RGH", "gloss", "rough"),
        "Metal": ("Gold", "Chrome", "Metal", "alum", "brass", "steel", "metallic"),
        "Normal": ("Normal", "nrm", "nor", "NRM"),
        "Bump": ("Bump", "bump"),
        "Glass": ("glass", "water", "milk", "juice"),
        "Transmission": ("Transmission", "Translucency", "trans", "SubsurfaceColor"),
        "Opacity": ("Opacity", "alpha"),
        "Displacement": ("Displacement", "disp", "Height"),
        "Fabrics": ("wool", "fabric"),
        "IOR": ("IOR", "ior"),
        "AO": ("AO", "ambient"),
        "Cavity": ("Cavity", "CAVITY")
    }
    
    
    engine = bpy.context.scene.render.engine
    
    for image in bpy.data.images:
        # We slaan "Render Result" en "Vray" over, zoals in je originele code
        if "Render Result" not in image.name and "Vray" not in image.name:
            
            
            full_filepath = bpy.path.abspath(image.filepath)
            new_name_base = os.path.basename(full_filepath)        
            normalized_filepath = os.path.normpath(full_filepath)   
            image.name = new_name_base
        
    
    if engine != "LUXCORE":
        node_tree = mat.node_tree
    else:
        node_tree = mat.luxcore.node_tree
    if not node_tree:
        return
    
    # Define image node types based on render engine
    node_types = {
        "VRAY_RENDER_RT": "VRayNodeMetaImageTexture",
        "octane": "OctaneRGBImage",
        "LUXCORE": "LuxCoreNodeTexImagemap",
        "CYCLES": "ShaderNodeTexImage"
    }
    
    # Get the appropriate node type for the current render engine
    node_type = node_types.get(engine)
    if not node_type:
        print(f"Unsupported render engine: {engine}")
        return
    
    # Get all image texture nodes
    image_nodes = [node for node in node_tree.nodes if node.bl_idname.startswith(node_type)]
    
    # Label unlabeled nodes based on their image names
    for node in image_nodes:
        if not node.label and hasattr(node, 'image') and node.image:
            for category, patterns in texture_categories.items():
                if any(re.search(pattern, node.image.name, re.IGNORECASE) for pattern in patterns):
                    node.label = category
                    break
                    
def Connect_To_Material(mat):
    active_mat = mat
    engine = bpy.context.scene.render.engine
    
    if engine == 'LUXCORE':
        node_tree = active_mat.luxcore.node_tree
    else:
        node_tree = active_mat.node_tree
    
    if node_tree:
        nodes = node_tree.nodes
        links = node_tree.links
        
        if engine == 'LUXCORE':
            Material_node = next((node for node in nodes if node.bl_idname.startswith("LuxCoreNodeMat") and "Material" in node.label), None)
            other_nodes = [node for node in nodes if node != Material_node and node.bl_idname.startswith("LuxCore")]
            engine_name = "LuxCore"
            prefix_to_input_name = {
                ("Diffuse", "COL", "COLOR", "COLOR * AO"): "Base Color",
                ("Specular", "REFL", "REFLECTION"): "Specular",
                
                ("Metallic", "METALNESS", "METAL"): "Metallic",
                ("NRM", "NORMAL", "Normal Map"): "Bump",
                ("GLOSS", "ROUGHNESS", "Invert Gloss", "Roughness"): "Roughness",
                ("Displacement", "DISP", "HEIGHT"): "Displacement",
                ("BUMP",): "Bump",
                ("Opacity", "OPACITY"): "Opacity",
                ("Transmission", "TRANS"): "Transmission Color",
                ("IOR", "ior"): "IOR",
                ("Coat", "COATING"): "Coat Color"
            }
            if Material_node and Material_node.bl_idname == "LuxCoreNodeMatGlossyTranslucent":
                
                for key, value in list(prefix_to_input_name.items()):
                    if value == "Specular":
                        prefix_to_input_name[key] = "Specular Color"
                    if value == "Base Color":
                        prefix_to_input_name[key] = "Diffuse Color"
                        
            
        elif engine == "octane":
            Material_node = next((node for node in nodes if node.bl_idname.startswith("Octane") and "Material" in node.label), None)
            engine_name = "Octane"
            other_nodes = [node for node in nodes if node != Material_node and node.bl_idname.startswith("Octane")]
            
            prefix_to_input_name = {
                
                ("Specular", "REFL", "REFLECTION"): "Specular",
                ("Metallic", "METALNESS", "METAL"): "Metalness",
                ("NRM", "NORMAL", "Normal Map"): "Normal",
                ("SSS", "Subsurface"): "Subsurface color",
                ("Displacement", "DISP", "HEIGHT", "displacement"): "Displacement",
                ("BUMP",): "Bump",
                ("Opacity", "OPACITY"): "Opacity",
                ("Transmission", "TRANS"): "Transmission",
                ("Coat", "COATING"): "Coating"
            }
            if bpy.context.preferences.addons["Material_Converter 1"].preferences.octane_preferences.octane_base_material == "UNIVERSAL":
                prefix_to_input_name[("Diffuse", "COL", "COLOR", "COLOR * AO")] = "Albedo"
                prefix_to_input_name[("GLOSS", "ROUGHNESS", "Roughness")] =  "Roughness"
            else:
                prefix_to_input_name[("Diffuse", "COL", "COLOR", "COLOR * AO")] = "Base color"
                prefix_to_input_name[("GLOSS", "ROUGHNESS", "Roughness")] =  "Specular roughness"
            
                
        elif engine == "VRAY_RENDER_RT":
            Material_node = next((node for node in nodes if node.bl_idname.startswith("VRay") and "Material" in node.label), None)
            engine_name = "V-Ray"
            other_nodes = [node for node in nodes if node != Material_node and node.bl_idname.startswith("VRay")]
            prefix_to_input_name = {
                ("Diffuse", "COL", "COLOR", "COLOR * AO"): "Diffuse Color",
                ("Specular", "REFL", "REFLECTION"): "Reflection Color",
                ("Metallic", "METALNESS", "METAL"): "Metalness",
                ("NRM", "NORMAL", "Normal Map"): "Bump Map",
                ("GLOSS", "ROUGHNESS"): "Reflection Glossiness",
                ("Displacement", "DISP", "HEIGHT"): "Displacement",
                ("BUMP",): "Bump Map",
                ("SSS",): "Fog Color",
                ("SSS",): "Translucency Color", 
                
                ("Transmission", "TRANS"): "Transmission",
                ("Opacity", "OPACITY"): "Opacity",
                ("Coat", "COATING"): "Coat Color"
                
            }
            
        if not Material_node:
            print(f"No {engine_name} group node found in material '{active_mat.name}'.")
            return

        print("Active Nodetree: ", node_tree)
        
        # Create a dictionary to store inputs of the group node
        group_node_inputs = {input.name: input for input in Material_node.inputs}
        
        # Distance calculation function
        def distance(node):
            return math.sqrt(
                (Material_node.location.x - node.location.x)**2 + 
                (Material_node.location.y - node.location.y)**2
            )
        
        # Sort nodes by distance
        sorted_nodes = sorted(other_nodes, key=distance)
        
        # Debug print
        print(f"Material node for {engine_name} : ({Material_node.name}) location: ({Material_node.location.x}, {Material_node.location.y})")
        for node in sorted_nodes:
            dist = distance(node)
            print(f"Node {node.name} at ({node.location.x}, {node.location.y}) is {dist:.2f} units away")
        
        # Connect nodes to group node inputs
        for node in sorted_nodes:
            
            if node.label:
                node_label_upper = node.label.upper()
                
                # Try to match the node label with our prefix groups
                for prefixes, input_name in prefix_to_input_name.items():
                    if any(prefix.upper() in node_label_upper for prefix in prefixes):
                        if input_name in group_node_inputs:
                            input_socket = group_node_inputs[input_name]
                            
                            if not input_socket.is_linked:
                                if node.outputs:
                                    #current_output = node.outputs[0]
                                    if node.bl_idname == "LuxCoreNodeTexImagemap" and any(x in node.label for x in ["NRM", "NORMAL", "Normal Map"]):
                                        current_output = node.outputs[2]
                                    
                                    elif node.bl_idname == "VRayNodeMetaImageTexture" and any(l in node.label for l in ["GLOSS", "ROUGHNESS", "Metallic", "METALNESS", "METAL"]):
                                        current_output = node.outputs[3]
                                    else:
                                        current_output = node.outputs[0]
                                    if node.bl_idname == "VRayNodeMetaImageTexture" and any(z in node.label for z in ["SSS", "Subsurface"]):
                                        
                                        links.new(node.outputs[0], Material_node.inputs["Fog Color"])
                                        #links.new(node.outputs[0], Material_node.inputs["Refraction Color"])
                                        Material_node.inputs["Refraction Color"].value = (0.248867, 0.248867, 0.248867)
                                        if Material_node.bl_idname == "VRayNodeBRDFVRayMtl":
                                            Material_node.inputs[49].value ="6"
                                    
                                        
                                    links.new(current_output, input_socket)
                                    print(f"Connecting '{node.label}' output to '{Material_node.name}' group's '{input_name}' input")
                                    break
                                    


def reorganize_material_nodes(mat,Render_Engine):
    # Get active material
    
    nodes = mat.node_tree.nodes
    
    # Find lowest Cycles Shader node
    cycles_shader_nodes = [node for node in nodes if node.bl_idname.startswith('Shader')]
    
    if not cycles_shader_nodes:
        print("No Cycles Shader nodes found")
        return
    
    
    
    if Render_Engine == "VRAY_RENDER_RT":
       
        Adjusting_nodes = [node for node in nodes if node.bl_idname.startswith('VRay')]
        key_attr = 'y'
    if Render_Engine == "octane":
        Adjusting_nodes = [node for node in nodes if node.bl_idname.startswith('Octane')]
        Adjusting_nodes.extend([node for node in nodes if node.label == "Octane Output"])
        key_attr = 'x'

    # Find lowest Cycles node by specified position
    Border_cycles_node = min(cycles_shader_nodes, key=lambda n: getattr(n.location, key_attr))
    New_node_adjustment = getattr(Border_cycles_node.location, key_attr)
            
        
    
    
    # Check if any node is above Cycles nodes
    Nodes_on_Cycles = any(getattr(node.location, key_attr) > New_node_adjustment for node in Adjusting_nodes)

    # If any node is above, calculate precise shift
    if Nodes_on_Cycles:
        # Find highest node
        highest_node = max(Adjusting_nodes, key=lambda n: getattr(n.location, key_attr))
        vertical_shift = abs(getattr(highest_node.location, key_attr) - New_node_adjustment) + 200
        
        # Shift all nodes
        for node in Adjusting_nodes:
            setattr(node.location, key_attr, getattr(node.location, key_attr) - vertical_shift)
        
    
    def redistribute_nodes_horizontally(node_list):
        # Group nodes by exact X coordinate
        node_groups = {}
        for node in node_list:
            x = node.location.x
            if x not in node_groups:
                node_groups[x] = []
            node_groups[x].append(node)

        # Sort groups
        sorted_groups = sorted(node_groups.items(), key=lambda x: x[0])

        # Redistribute horizontally
        for group_index, (original_x, group) in enumerate(sorted_groups):
            new_x = group_index * 300
            
            # Sort group vertically (top to bottom)
            group_sorted = sorted(group, key=lambda n: -n.location.y)
            
            for node in group_sorted:
                node.location.x = new_x
    
    
    # Redistribute nodes
    redistribute_nodes_horizontally(Adjusting_nodes)


                                    
                              
    

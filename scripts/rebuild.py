# scripts/__init__.py
import bpy

def rebuild_octane_connections(mat):
    
    active_mat = mat

    # Get Cycles nodes
    cycles_nodes = active_mat.node_tree.nodes
    cycles_links = active_mat.node_tree.links

    # Get LuxCore nodes
    octane_node_tree = active_mat.node_tree
    octane_nodes = octane_node_tree.nodes
    octane_links = octane_node_tree.links

    # Dictionary mapping Cycles node types to LuxCore node types
    node_mapping = {
    "ShaderNodeMix": ["OctaneMixTexture","OctaneCyclesMixColorNodeWrapper","OctaneCyclesMixFloatNodeWrapper","OctaneCyclesMixFloat3NodeWrapper"],
    "ShaderNodeTexImage": ["OctaneRGBImage"],
    "ShaderNodeNormalMap": ["LuxCoreNodeTexNormalmap"],
    "ShaderNodeOutputMaterial": ["LuxCoreNodeMatOutput"],
    "ShaderNodeMapping": ["Octane3DTransformation"],
    "ShaderNodeBsdfPrincipled": ["OctaneUniversalMaterial","OctaneStandardSurfaceMaterial","LuxCoreNodeMatGlass"],
    "ShaderNodeBsdfTranslucent" : ["OctaneUniversalMaterial"],
    "ShaderNodeMixShader": ["OctaneMixMaterial"],
    "ShaderNodeBsdfGlass": ["OctaneUniversalMaterial"],
    "ShaderNodeHueSaturation": ["OctaneColorCorrection"],
    "ShaderNodeValToRGB":["OctaneGradientMap"],
    "ShaderNodeBump": ["LuxCoreNodeTexBump"],
    "ShaderNodeInvert": ["OctaneInvertTexture"],
    "ShaderNodeRGBCurve": ["NodeReroute"],
    "ShaderNodeSeparateColor": ["OctaneChannelPicker"],
    "ShaderNodeSeparateRGB": ["OctaneChannelPicker"],
    }

    # Output socket name mapping
    output_mapping = {
    'Normal': 'Bump',
    'Vector': 'Transform out',
    'Alpha': 'Out Alpha',
    'BSDF': 'Material out',
    'Result': 'Texture out',
    'A': 'First texture',
    'B': 'Second texture',
    'Color': 'Texture out'
    }

    # Input socket name mapping
    input_mapping = {
    'Normal': "Normal",
    'Coat Tint': 'Coat Color',
    'Sheen Tint': 'Sheen Color',
    'Base Color': 'Albedo',    
    'Coat Normal': 'Coat Bump Map',
    'Vector': 'UV transform',
    'Alpha': 'Opacity',
    'Fresnel IOR': 'Dielectric IOR',
    'Metallic': 'Metallic',
    'Specular IOR Level': 'Specular',
    'Surface': 'Material',
    'Roughness': 'Roughness',
    
    'Result': 'Texture out',
    'A': 'First texture',
    'B': 'Second texture',
    'Color': 'Texture'
    }

    # Iterate through Cycles nodes
    for key, value_list in node_mapping.items():
        # Find Cycles nodes of specific type
        cycles_type_nodes = [n for n in cycles_nodes if n.bl_idname == key]

        for cycles_node in cycles_type_nodes:
            # Find corresponding LuxCore node types
            for value in value_list:
                # Find LuxCore nodes of corresponding type
                octane_type_nodes = [n for n in octane_nodes if n.bl_idname == value]
                
                # Find LuxCore node with matching label
                octane_node = next((n for n in octane_type_nodes if n.label == cycles_node.label), None)
                
                if octane_node:
                    # Check output connections in Cycles node
                    for output in cycles_node.outputs:
                        for link in output.links:
                            target_node = link.to_node
                            
                            # Check if target node is in node mapping
                            if target_node.bl_idname in node_mapping:
                                # Find corresponding LuxCore target node
                                octane_target_nodes = [n for n in octane_nodes if n.bl_idname in node_mapping[target_node.bl_idname]]
                                octane_target_node = next((n for n in octane_target_nodes if n.label == target_node.label), None)
                                
                                if octane_target_node:
                                    # Determine output and input socket names
                                    output_name = output_mapping.get(output.name, output.name)
                                    input_socket = link.to_socket
                                    
                                    # Custom input name mapping logic
                                    if target_node.bl_idname == "ShaderNodeMixShader":
                                        input_name = "First material" if input_socket.identifier == "Shader" else "Second material" if input_socket.identifier == "Shader_001" else input_socket.name
                                        if input_socket.name == "Fac":
                                            input_name = "Amount"
                                            
                                    elif target_node.bl_idname == "ShaderNodeMix":
                                        if octane_target_node.bl_idname == "OctaneCyclesMixColorNodeWrapper":
                                            input_name = "A" if input_socket.name == "A" else "B" if input_socket.name == "B" else "Factor" if input_socket.name == "Factor" else input_socket.name
                                        
                                    elif target_node.bl_idname == "ShaderNodeBsdfPrincipled":
                                        # Special case for Disney material
                                        if octane_target_node.bl_idname == "LuxCoreNodeMatDisney" and input_socket.name == "Base Color":
                                            input_name = "Base Color"
                                        if octane_target_node.bl_idname == "OctaneStandardSurfaceMaterial":
                                            if input_socket.name == "Base Color":
                                                input_name = "Base color"
                                            if input_socket.name == "Metallic":
                                                input_name = "Metalness"
                                            if input_socket.name == "Roughness":
                                                input_name = "Specular roughness"
                                            if input_socket.name == "Specular IOR Level":
                                                input_name = "Specular weight"
                                            if input_socket.name == "Normal":
                                                input_name = "Normal"  
                                        else:
                                            # Default to the LuxCore equivalent
                                            input_name = input_mapping.get(input_socket.name, input_socket.name)
                                    elif target_node.bl_idname == "ShaderNodeRGBCurve":
                                        input_name = "Texture"
                                       
                                        
                                    elif target_node.bl_idname =="ShaderNodeBsdfTranslucent":
                                        if octane_target_node.bl_idname =="OctaneUniversalMaterial" and input_socket.name == "Color":
                                            input_name = "Transmission"
                                        else:
                                            input_name = input_mapping.get(input_socket.name, input_socket.name)
                                    elif target_node.bl_idname =="ShaderNodeHueSaturation":
                                        if octane_target_node.bl_idname =="OctaneColorCorrection" and input_socket.name == "Color":
                                            input_name = "Input"
                                        else:
                                            input_name = input_mapping.get(input_socket.name, input_socket.name)
                                            
                                    elif target_node.bl_idname == "ShaderNodeValToRGB":
                                        if input_socket.name == "Fac":
                                            input_name = "Input texture"
                                        else:
                                            input_name = input_mapping.get(input_socket.name, input_socket.name)
                                            
                                    elif target_node.bl_idname == "ShaderNodeBsdfGlass":
                                        print(input_socket.name)
                                        if octane_target_node.bl_idname == "LuxCoreNodeMatGlass" and input_socket.name == "Color":
                                            input_name = "Transmission Color"
                                        else:
                                            input_name = input_mapping.get(input_socket.name, input_socket.name)
                                    elif target_node.bl_idname =="ShaderNodeBump":
                                        if octane_target_node.bl_idname == "LuxCoreNodeTexBump" and input_socket.name == "Height":
                                            input_name = "Value"
                                    

                                            
                                    elif target_node.bl_idname == "ShaderNodeTexImage":
                                        input_name = "UV transform" if input_socket.name == "Vector" else input_socket.name
                                    elif target_node.bl_idname == "ShaderNodeNormalMap":
                                        input_name = "Texmap" if input_socket.name == "Color" else input_socket.name
                                    #elif input_socket.name == "Base Color":
                                    #    input_name = "Bump Map" if target_node.bl_idname == "ShaderNodeBsdfPrincipled" else input_socket.name
                                    #elif input_socket.name == "Coat Normal":
                                    #    input_name = "Coat Bump Map" if target_node.bl_idname == "ShaderNodeBsdfPrincipled" else input_socket.name
                                    elif input_socket.name == 'Fac':
                                        input_name = "Input texture" if target_node.bl_idname == 'ShaderNodeValToRGB' else input_mapping.get(input_socket.name, input_socket.name)
                                    else:
                                        input_name = input_mapping.get(input_socket.name, input_socket.name)
                                    
                                    # Find matching output and input sockets
                                    output_socket = next((s for s in octane_node.outputs if s.name == output_name), None)
                                    input_socket = next((s for s in octane_target_node.inputs if s.name == input_name), None)
                                    
                                    # Create link in LuxCore node tree
                                    if output_socket and input_socket:
                                        octane_links.new(input_socket, output_socket)
                                        
                                        



def rebuild_vray_connections(mat):
    active_mat = mat

    
    nodes = active_mat.node_tree.nodes
    cycles_links = active_mat.node_tree.links

    
    # Dictionary mapping Cycles node types to Vray node types
    node_mapping = {
    "ShaderNodeMix": ["VRayNodeTexMix"],
    "ShaderNodeRGBCurve": ["VRayNodeTexRemap"], 
    "ShaderNodeTexImage": ["VRayNodeMetaImageTexture"],
    "ShaderNodeNormalMap": ["VRayNodeTexNormalMapFlip"],
    "ShaderNodeOutputMaterial": ["LuxCoreNodeMatOutput"],
    "ShaderNodeMapping": ["VRayNodeUVWMapping"],
    "ShaderNodeBsdfPrincipled": ["VRayNodeBRDFVRayMtl","VRayNodeBRDFSSS2Complex","LuxCoreNodeMatGlass"],
    "ShaderNodeBsdfTranslucent" : ["VRayNodeBRDFVRayMtl"],
    "ShaderNodeMixShader": ["LuxCoreNodeMatMix"],
    "ShaderNodeBsdfGlass": ["LuxCoreNodeMatGlass"],
    "ShaderNodeHueSaturation": ["VRayNodeColorCorrection"],
    "ShaderNodeValToRGB": ["VRayNodeTexGradRamp"],
    "ShaderNodeBump": ["LuxCoreNodeTexBump"],
    "ShaderNodeInvert": ["VRayNodeTexInvert"]
    }

    # Output socket name mapping
    output_mapping = {
    'Normal': 'Color',
    'Vector': 'Mapping',
    'Alpha': 'Out Alpha',
    'BSDF': 'Material',
    'Result': 'Color',
    'A': 'Color 1',
    'B': 'Color 2',
    'Color': 'Color'
    }

    # Input socket name mapping
    input_mapping = {
    'Normal': "Bump",

    'Coat Tint': 'Coat Color',
    'Sheen Tint': 'Sheen Color',
    'Base Color': 'Diffuse Color',
    'Coat Normal': 'Coat Bump Map',
    'Vector': 'Mapping',
    'Alpha': 'Opacity',
    'Fresnel IOR': 'IOR',
    'Metallic': 'Metalness',
    'Surface': 'Material',
    'Normal' : 'Bump Map',
    'Roughness': 'Reflection Glossiness',
    'Result': 'Texture out',
    'A': 'Color1',
    'B': 'Color2',
    'Color': 'Color'
    }

   
   
   
    
    links = active_mat.node_tree.links

    for key, value_list in node_mapping.items():
        key_nodes = [n for n in nodes if n.bl_idname == key]
        

        for key_node in key_nodes:
            for output in key_node.outputs:
                for link in output.links:
                    target_node = link.to_node

                    # Check if the node is in the node_mapping dictionary
                    if target_node.bl_idname in node_mapping:
                        for value in value_list:
                            value_nodes = [n for n in nodes if n.bl_idname == value]

                            # Find Octane node with the same label
                            Vray_node = next((n for n in value_nodes if n.label == key_node.label), None)
                            if Vray_node:
                                # Find Octane node with the same label as target_node
                                Vray_Target = next((n for n in nodes if n.bl_idname in node_mapping[target_node.bl_idname] and n.label == target_node.label), None)
                                if Vray_Target:
                                    # Determine input name
                                    output_name = output_mapping.get(output.name, output.name)  # Get name from mapping, default to original name
                                    input_socket = link.to_socket
                                    print(target_node.bl_idname,Vray_Target.bl_idname  )

                                    # Custom logic to handle specific input values
                                    if target_node.bl_idname == "ShaderNodeMix":
                                        if Vray_Target.bl_idname == "OctaneCyclesMixColorNodeWrapper":
                                            input_name = input_socket.name
                                        else:
                                            input_name = input_mapping.get(input_socket.name, input_socket.name)
                                    elif target_node.bl_idname == "ShaderNodeRGBCurve":
                                        if input_socket.name == "Color":
                                            input_name = "Input Color"        
                                    elif target_node.bl_idname == 'ShaderNodeValToRGB':
                                        if Vray_Target.bl_idname  == "VRayNodeTexGradRamp":
                                            input_name = "Texture Map" 
                                        else: 
                                            input_name = input_mapping.get(input_socket.name, input_socket.name)
                                            
                                    elif target_node.bl_idname == "ShaderNodeBsdfTranslucent":
                                        if input_socket.name == "Color":
                                            input_name = "Translucency Color"
                                    elif Vray_Target.bl_idname == "VRayNodeColorCorrection":
                                        if input_socket.name == "Color":
                                            input_name = "Source Color"
                                    elif Vray_Target.bl_idname == "VRayNodeTexRemap":
                                        
                                        if input_socket.name == "Color":
                                            input_name = "Input Color"
                                    elif Vray_Target.bl_idname == "VRayNodeTexInvert":
                                        if input_socket.name == "Color":
                                            input_name = "Texture"
                                        
                                            
                                    elif target_node.bl_idname == "ShaderNodeTexImage":
                                        if input_socket.name == "Vector":
                                            input_name = "Mapping"
                                    elif target_node.bl_idname == "ShaderNodeNormalMap":
                                        
                                        if input_socket.name == "Color":
                                            input_name = "Texmap"
                                    elif input_socket.name == "Normal":
                                        
                                      
                                        if target_node.bl_idname == "ShaderNodeBsdfPrincipled":
                                            input_name = "Bump Map"
                                    elif input_socket.name == "Coat Normal":
                                        if target_node.bl_idname == "ShaderNodeBsdfPrincipled":
                                            input_name = "Coat Bump Map"
                                                                       
                                    
                                    else:
                                        input_name = input_mapping.get(input_socket.name, input_socket.name)

                                     # Connect nodes
                                    output_socket = next((s for s in Vray_node.outputs if s.name == output_name), None)
                                    input_socket = next((s for s in Vray_Target.inputs if s.name == input_name), None)
                                    if output_socket and input_socket:
                                        links.new(input_socket, output_socket)
                                        
def rebuild_Luxcore_connections(mat):
        
    active_mat = mat

    # Get Cycles nodes
    cycles_nodes = active_mat.node_tree.nodes
    cycles_links = active_mat.node_tree.links

    # Get LuxCore nodes
    luxcore_node_tree = active_mat.luxcore.node_tree
    luxcore_nodes = luxcore_node_tree.nodes
    luxcore_links = luxcore_node_tree.links

    # Dictionary mapping Cycles node types to LuxCore node types
    node_mapping = {
    "ShaderNodeMix": ["LuxCoreNodeTexColorMix"],
    "ShaderNodeRGBCurve": ["NodeReroute"],    
    "ShaderNodeTexImage": ["LuxCoreNodeTexImagemap"],
    "ShaderNodeNormalMap": ["LuxCoreNodeTexNormalmap"],
    "ShaderNodeOutputMaterial": ["LuxCoreNodeMatOutput"],
    "ShaderNodeMapping": ["LuxCoreNodeTexMapping2D"],
    "ShaderNodeBsdfPrincipled": ["LuxCoreNodeMatDisney","LuxCoreNodeMatGlossyTranslucent","LuxCoreNodeMatGlass"],
    "ShaderNodeBsdfTranslucent" : ["LuxCoreNodeMatGlossyTranslucent"],
    "ShaderNodeMixShader": ["LuxCoreNodeMatMix"],
    "ShaderNodeBsdfGlass": ["LuxCoreNodeMatGlass"],
    "ShaderNodeHueSaturation": ["LuxCoreNodeTexHSV"],
    "ShaderNodeValToRGB":["LuxCoreNodeTexBand"],
    "ShaderNodeBump": ["LuxCoreNodeTexBump"],
    "ShaderNodeInvert": ["LuxCoreNodeTexInvert"]
    }

    # Output socket name mapping
    output_mapping = {
    'Normal': 'Bump',
    'Vector': '2D Mapping',
    'Alpha': 'Out Alpha',
    'BSDF': 'Material',
    'Result': 'Color',
    'A': 'First texture',
    'B': 'Second texture',
    'Color': 'Color'
    }

    # Input socket name mapping
    input_mapping = {
    'Normal': "Bump",

    'Coat Tint': 'Coat Color',
    'Sheen Tint': 'Sheen Color',
    'Base Color': 'Diffuse Color',
    'Coat Normal': 'Coat Bump Map',
    'Vector': '2D Mapping',
    'Alpha': 'Opacity',
    'Fresnel IOR': 'IOR',
    'Metallic': 'Metalness',
    'Surface': 'Material',
    'Roughness': 'Roughness',
    'Result': 'Texture out',
    'A': 'Color 1',
    'B': 'Color 2',
    'Color': 'Color'
    }

    # Iterate through Cycles nodes
    for key, value_list in node_mapping.items():
        # Find Cycles nodes of specific type
        cycles_type_nodes = [n for n in cycles_nodes if n.bl_idname == key]

        for cycles_node in cycles_type_nodes:
            # Find corresponding LuxCore node types
            for value in value_list:
                # Find LuxCore nodes of corresponding type
                luxcore_type_nodes = [n for n in luxcore_nodes if n.bl_idname == value]
                
                # Find LuxCore node with matching label
                luxcore_node = next((n for n in luxcore_type_nodes if n.label == cycles_node.label), None)
                
                if luxcore_node:
                    # Check output connections in Cycles node
                    for output in cycles_node.outputs:
                        for link in output.links:
                            target_node = link.to_node
                            
                            # Check if target node is in node mapping
                            if target_node.bl_idname in node_mapping:
                                # Find corresponding LuxCore target node
                                luxcore_target_nodes = [n for n in luxcore_nodes if n.bl_idname in node_mapping[target_node.bl_idname]]
                                luxcore_target_node = next((n for n in luxcore_target_nodes if n.label == target_node.label), None)
                                
                                if luxcore_target_node:
                                    # Determine output and input socket names
                                    output_name = output_mapping.get(output.name, output.name)
                                    input_socket = link.to_socket
                                    
                                    # Custom input name mapping logic
                                    if target_node.bl_idname == "ShaderNodeMixShader":
                                        input_name = "Material 1" if input_socket.identifier == "Shader" else "Material 2" if input_socket.identifier == "Shader_001" else input_socket.name
                                    elif target_node.bl_idname == "ShaderNodeBsdfPrincipled":
                                        # Special case for Disney material
                                        if luxcore_target_node.bl_idname == "LuxCoreNodeMatDisney" and input_socket.name == "Base Color":
                                            input_name = "Base Color"
                                        else:
                                            # Default to the LuxCore equivalent
                                            input_name = input_mapping.get(input_socket.name, input_socket.name)
                                    elif target_node.bl_idname =="ShaderNodeBsdfTranslucent":
                                        if luxcore_target_node.bl_idname =="LuxCoreNodeMatGlossyTranslucent" and input_socket.name == "Color":
                                            input_name = "Transmission Color"
                                        else:
                                            input_name = input_mapping.get(input_socket.name, input_socket.name)
                                            
                                    elif target_node.bl_idname == "ShaderNodeValToRGB":
                                        if input_socket.name == "Fac":
                                            input_name = "Amount"
                                        else:
                                            input_name = input_mapping.get(input_socket.name, input_socket.name)
                                            
                                    elif target_node.bl_idname == "ShaderNodeBsdfGlass":
                                        print(input_socket.name)
                                        if luxcore_target_node.bl_idname == "LuxCoreNodeMatGlass" and input_socket.name == "Color":
                                            input_name = "Transmission Color"
                                        else:
                                            input_name = input_mapping.get(input_socket.name, input_socket.name)
                                    elif target_node.bl_idname =="ShaderNodeBump":
                                        if luxcore_target_node.bl_idname == "LuxCoreNodeTexBump" and input_socket.name == "Height":
                                            input_name = "Value"
                                            
                                    elif target_node.bl_idname == "ShaderNodeTexImage":
                                        input_name = "2D Mapping" if input_socket.name == "Vector" else input_socket.name
                                    elif target_node.bl_idname == "ShaderNodeNormalMap":
                                        input_name = "Texmap" if input_socket.name == "Color" else input_socket.name
                                    elif input_socket.name == "Base Color":
                                        input_name = "Bump Map" if target_node.bl_idname == "ShaderNodeBsdfPrincipled" else input_socket.name
                                    elif input_socket.name == "Coat Normal":
                                        input_name = "Coat Bump Map" if target_node.bl_idname == "ShaderNodeBsdfPrincipled" else input_socket.name
                                    elif input_socket.name == 'Fac':
                                        input_name = "Input texture" if target_node.bl_idname == 'ShaderNodeValToRGB' else input_mapping.get(input_socket.name, input_socket.name)
                                    else:
                                        input_name = input_mapping.get(input_socket.name, input_socket.name)
                                    
                                    # Find matching output and input sockets
                                    output_socket = next((s for s in luxcore_node.outputs if s.name == output_name), None)
                                    input_socket = next((s for s in luxcore_target_node.inputs if s.name == input_name), None)
                                    
                                    # Create link in LuxCore node tree
                                    if output_socket and input_socket:
                                        luxcore_links.new(input_socket, output_socket)





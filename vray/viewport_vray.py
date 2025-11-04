import bpy

def Create_viewport_emission_vray(mat, selected_node):
    #if not hasattr(mat, "luxcore") or not hasattr(mat.luxcore, "node_tree"):
    #    print(f"Material {mat.name} nie ma LuxCore node tree.")
    #    return None, None
    
    if "VRay" not in selected_node.bl_idname:
        return "Non V-ray node selected, Please select V-ray Node"
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    if not nodes:
        print("There is no V-reay nodes available")

    
    Emission_material = next((node for node in nodes if node.bl_idname.startswith("VRayNodeBRDFLight") and node.label == "Viewport Emission"), None)

    Material_output = next((node for node in nodes if node.bl_idname.startswith("VRayNodeOutputMaterial")), None)

   

    
    

    if not Emission_material:
        Emission_material = nodes.new("VRayNodeBRDFLight")
        Emission_material.label = "Viewport Emission"
        

        
    if not Material_output:
        Material_output = nodes.new("VRayNodeOutputMaterial")
        Material_output.label = "V-ray Output"
    
    links.new(Emission_material.outputs["BRDF"],Material_output.inputs["Material"])
    links.new(selected_node.outputs[0],Emission_material.inputs[0])
    Emission_material.location = (Material_output.location[0]-300, Material_output.location[1] -850)
    

    return "Success"


#mat = bpy.context.object.active_material

#if mat:
#    nodes = mat.node_tree.nodes
#    nodetree = mat.luxcore.node_tree if hasattr(mat, "luxcore") and hasattr(mat.luxcore, "node_tree") else None
#    selected_node = nodes.active if nodes else None

#    if nodes and selected_node:
#        Create_viewport_emission_vray(mat, selected_node)
    #else:
     #   print("Brak aktywnego nodetree lub wybranego noda.")
#else:
  #  print("Brak aktywnego materiału.")

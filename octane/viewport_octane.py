import bpy

def Create_viewport_emission_octane(mat, selected_node):
    
    if "Octane" not in selected_node.bl_idname:
        return "Non Octane node selected, Please select Octane Node"
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    Matte_material = next((node for node in nodes if node.bl_idname.startswith("OctaneDiffuseMaterial") and node.label == "Viewport Diffuse"), None)
    Emission_material = next((node for node in nodes if node.bl_idname.startswith("OctaneTextureEmission") and node.label == "Viewport Emission"), None)
    Material_output = next((node for node in nodes if node.bl_idname.startswith("ShaderNodeOutputMaterial") and node.target == "ALL"), None)
   

    
    if not Matte_material:
        Matte_material = nodes.new("OctaneDiffuseMaterial")
        Matte_material.label = "Viewport Diffuse"

    if not Emission_material:
        Emission_material = nodes.new("OctaneTextureEmission")
        Emission_material.label = "Viewport Emission"
        Emission_material.exposure = 0

        
    if not Material_output:
        Material_output = nodes.new("ShaderNodeOutputMaterial")
        Material_output.label = "Octane Output"
    links.new(Matte_material.outputs[0],Material_output.inputs[0])
    links.new(Emission_material.outputs["Emission out"],Matte_material.inputs["Emission"])
    links.new(selected_node.outputs[0],Emission_material.inputs[0])
    Matte_material.location = (Material_output.location[0]-300, Material_output.location[1] -850)
    Emission_material.location = (Matte_material.location[0]-300, Matte_material.location[1] )

    return "Success"

#mat = bpy.context.object.active_material

#if mat:
 #   nodes = mat.node_tree.nodes
    #nodetree = mat.luxcore.node_tree if hasattr(mat, "luxcore") and hasattr(mat.luxcore, "node_tree") else None
  #  selected_node = nodes.active if nodes else None

#    if nodes and selected_node:
 #       Create_viewport_emission_vray(mat, selected_node)
    #else:
     #   print("Brak aktywnego nodetree lub wybranego noda.")
#else:
  #  print("Brak aktywnego materiału.")

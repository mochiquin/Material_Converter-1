import bpy

def Create_viewport_emission_luxcore(mat, selected_node):
    
    if "LuxCore" not in selected_node.bl_idname:
        return "Non LuxCore node selected, Please select LuxCore Node"
    
    if not hasattr(mat, "luxcore") or not hasattr(mat.luxcore, "node_tree"):
        print(f"Material {mat.name} nie ma LuxCore node tree.")
        return None, None
    
    nodes = mat.luxcore.node_tree.nodes
    links = mat.luxcore.node_tree.links

    Matte_material = next((node for node in nodes if node.bl_idname.startswith("LuxCoreNodeMatMatte") and node.label == "Viewport Matte"), None)
    Emission_material = next((node for node in nodes if node.bl_idname.startswith("LuxCoreNodeMatEmission") and node.label == "Viewport Emission"), None)
    Material_output = next((node for node in nodes if node.bl_idname.startswith("LuxCoreNodeMatOutput") and node.label == "LuxCore Output"), None)
   

    
    if not Matte_material:
        Matte_material = nodes.new("LuxCoreNodeMatMatte")
        Matte_material.label = "Viewport Matte"

    if not Emission_material:
        Emission_material = nodes.new("LuxCoreNodeMatEmission")
        Emission_material.label = "Viewport Emission"
        Emission_material.exposure = 0

        
    if not Material_output:
        Material_output = nodes.new("LuxCoreNodeMatOutput")
        Material_output.label = "LuxCore Output"
    links.new(Matte_material.outputs[0],Material_output.inputs[0])
    links.new(Emission_material.outputs["Emission"],Matte_material.inputs["Emission"])
    links.new(selected_node.outputs[0],Emission_material.inputs[0])
    Matte_material.location = (Material_output.location[0]-300, Material_output.location[1] -850)
    Emission_material.location = (Matte_material.location[0]-300, Matte_material.location[1] )

    return "Success"

#mat = bpy.context.object.active_material

#if mat:
 #   nodetree = mat.luxcore.node_tree if hasattr(mat, "luxcore") and hasattr(mat.luxcore, "node_tree") else None
  #  selected_node = nodetree.nodes.active if nodetree else None

    #if nodetree and selected_node:
     #   Create_viewport_emission_luxcore(mat, selected_node)
    #else:
     #   print("Brak aktywnego nodetree lub wybranego noda.")
#else:
  #  print("Brak aktywnego materiału.")

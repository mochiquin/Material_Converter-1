import bpy
import math
import sys
import os

## Import ##
script_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if script_folder not in sys.path:
    sys.path.append(script_folder)


from connect_nodes import connect_to_closest_Cycles_mat

Render_Engine = bpy.context.scene.render.engine
if Render_Engine not in ("CYCLES", "BLENDER_EEVEE_NEXT"):
    bpy.context.scene.view_settings.view_transform = 'AgX'
    bpy.context.scene.view_settings.look = 'None'

    # Ustaw silnik renderujący na Octane dla bieżącej aktywnej sceny
    bpy.context.scene.render.engine = "CYCLES"

current_workspace = bpy.context.workspace
for screen in current_workspace.screens:
    for area in screen.areas:
        if area.type == 'NODE_EDITOR'and not area.ui_type in ["GeometryNodeTree", "CompositorNodeTree"]:
            area.ui_type = 'ShaderNodeTree'

def create_basic_material():
 

    material_names_to_remove = [
        "ShaderNodeAddShader",
        "ShaderNodeBsdfDiffuse",
        "ShaderNodeEmission",
        "ShaderNodeBsdfGlass",
        "ShaderNodeBsdfGlossy",
        "ShaderNodeBsdfHair",
        "ShaderNodeHoldout",
        "ShaderNodeMixShader",
        "ShaderNodeBsdfHairPrincipled",
        "ShaderNodeVolumePrincipled",
        "ShaderNodeBsdfRayPortal",
        "ShaderNodeBsdfRefraction",
        "ShaderNodeBsdfSheen",
        "ShaderNodeSubsurfaceScattering",
        "ShaderNodeBsdfToon",
        "ShaderNodeBsdfTranslucent",
        "ShaderNodeBsdfTransparent",
        "ShaderNodeVolumeAbsorption",
        "ShaderNodeVolumeScatter"
    
        
    ]
    
    #mat = bpy.data.materials.new(name="Octane Basic Material")
    #mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    Diffuse_color =[]
    Roughness_value = []
    IOR_Value = []
    
    for n in nodes:
        if n.bl_idname in material_names_to_remove:
            if 'Color' in n.inputs:
                # Get the diffuse color value
                diffuse_input = n.inputs['Color']
                Diffuse_color.append(diffuse_input.default_value[0])
                Diffuse_color.append(diffuse_input.default_value[1])
                Diffuse_color.append(diffuse_input.default_value[2])
                Diffuse_color.append(diffuse_input.default_value[3])
            if 'Roughness' in n.inputs:
                roughness_input = n.inputs['Roughness']
                Roughness_value.append(roughness_input.default_value)
                
            if 'IOR' in n.inputs:
                IOR_input = n.inputs['IOR']
                IOR_Value.append(IOR_input.default_value)
                
                
            nodes.remove(n)
    for n in nodes:
        if n.bl_idname.startswith("ShaderNode") and "help" in n.label:
            nodes.remove(n)
    
    texture_node = None 
    for n in nodes:
        if n.bl_idname == ("ShaderNodeTexImage"):
            texture_node = n
            break

    Material_output = None
    for n in nodes:
        if n.bl_idname == ("ShaderNodeOutputMaterial"):
            if links:
                for link in links:
                    if link.to_node == n and link.from_node.bl_idname.startswith ("Shader"):
                        Material_output = n
                        Material_output.label = "Cycles Output"
                        continue
            if not links:
                Material_output = n
                Material_output.label = "Cycles Output"
                Material_output.target = "CYCLES"
                continue
            if n.target == "CYCLES":
                Material_output = n
                Material_output.label = "Cycles Output"
                Material_output.target = "CYCLES"
                break
                
    if not Material_output:
        Material_output = nodetree.nodes.new("ShaderNodeOutputMaterial")
        Material_output.label = "Cycles Output"
    Material_output.target = "CYCLES"
    
    EEVEE_output = None
    for n in nodes:
        
        if n.bl_idname == ("ShaderNodeOutputMaterial"):
            if n.target == "EEVEE":
                EEVEE_output = n
                EEVEE_output.label = "EEVEE Output"
                continue
    if not EEVEE_output:
        EEVEE_output = nodetree.nodes.new("ShaderNodeOutputMaterial")
        EEVEE_output.label = "EEVEE Output"
        EEVEE_output.target  = "EEVEE"
        
        
    
    
    Universal = None
    principled_nodes = []

    for n in nodetree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            principled_nodes.append(n)

    if len(principled_nodes) > 0:
        Universal = principled_nodes[0]  
        Universal.label = "Material" 

        # Remove any other Principled BSDFs
        for node in principled_nodes[1:]:
            nodetree.nodes.remove(node) 

    if not Universal:  # If no Principled BSDF was found
        Universal = nodetree.nodes.new("ShaderNodeBsdfPrincipled")
        Universal.label = "Material"
                          
        
    
    if texture_node:    
        Universal.location = (texture_node.location[0] + 600, texture_node.location[1])
    #Diffuse Color:    
    Universal.inputs[0].default_value = Diffuse_color[:4] if Diffuse_color else (0.5,0.5,0.5,1) 
     
    if Roughness_value:
        
        Universal.inputs['Roughness'].default_value = Roughness_value[0]
        
    mat.node_tree.links.new(Universal.outputs[0],Material_output.inputs[0])
    mat.node_tree.links.new(Universal.outputs[0],EEVEE_output.inputs[0])
    Material_output.location = (Universal.location[0] + 300, Universal.location[1] )
    EEVEE_output.location = (Material_output.location[0], Material_output.location[1] - 150 )         
    
mat = bpy.context.object.active_material

nodetree = mat.node_tree
        
    
create_basic_material()
connect_to_closest_Cycles_mat(mat)











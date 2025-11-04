import bpy


def Convert_BDSF_node(Cycles_principled,mat):
    Render_engine = bpy.context.scene.render.engine
    
    #Diffuse:
    Dffuse_Color = Cycles_principled.inputs["Base Color"].default_value[:3]
    
    #Specular
    Specular_value = Cycles_principled.inputs["Specular IOR Level"].default_value
    Specular_Tilt = Cycles_principled.inputs["Specular Tint"].default_value[0]
    
    #Anisotropy 
    Anisotropy_value = Cycles_principled.inputs["Anisotropic"].default_value   # Anisotropy
    Anisotropy_Rotation = Cycles_principled.inputs["Anisotropic Rotation"].default_value  # Anisotropy Rotation
    
    #Subsurface
    Subsurface_value = Cycles_principled.inputs["Subsurface Weight"].default_value
    #Opacity
    Opacity_Value = Cycles_principled.inputs["Alpha"].default_value  # Opacity
    #Roughness
    Reflection_Glossiness = (1 - Cycles_principled.inputs["Roughness"].default_value)  # Roughness
    Roughness_Value = Cycles_principled.inputs["Roughness"].default_value
    #Fresnel IOR
    Fresnel_IOR = Cycles_principled.inputs["IOR"].default_value  # Fresnel IOR
    #Mettalic:
    Metalness_value = Cycles_principled.inputs["Metallic"].default_value 
    
    Used_normal = False
    if Cycles_principled.inputs["Normal"].is_linked:
        linked_normal = Cycles_principled.inputs["Normal"].links[0].from_node
        Normal_value = linked_normal.inputs[0].default_value if linked_normal.bl_idname in ["ShaderNodeNormalMap", "ShaderNodeBump"] else 1
        Used_normal = True
    
    Coat_Amount = Cycles_principled.inputs["Coat Weight"].default_value
    Coat_Glossiness = (1 - Cycles_principled.inputs["Coat Roughness"].default_value)
    Coat_IOR = Cycles_principled.inputs["Coat IOR"].default_value
    Coat_Color = Cycles_principled.inputs["Coat Tint"].default_value[:3]
    
    #Emission:
    Emisson_Strength =  Cycles_principled.inputs["Emission Strength"].default_value 
    Emission_Color = Cycles_principled.inputs["Emission Color"].default_value[:3]
    
    #Converted_Base_Material.inputs[65].value = Cycles_principled.inputs["Emission Strength"].default_value    
    Coat_normal = False 
    if Cycles_principled.inputs["Coat Normal"].is_linked:
        linked_coat_normal = Cycles_principled.inputs["Coat Normal"].links[0].from_node
        Coat_normal = True
        Coat_Normal_Value = linked_coat_normal.inputs[0].default_value if linked_coat_normal.bl_idname in ["ShaderNodeNormalMap", "ShaderNodeBump"] else 1
    
    # Scheen
    Sheen_Amount = Cycles_principled.inputs["Sheen Weight"].default_value
    Sheen_Glossiness = 1 - Cycles_principled.inputs["Sheen Roughness"].default_value
    Sheen_Color = Cycles_principled.inputs["Sheen Tint"].default_value[:3]
    
    # Transmission
    Translucency_Amount = Cycles_principled.inputs["Transmission Weight"].default_value
    # Thickness
    Thickness_Blend = Cycles_principled.inputs["Thin Film Thickness"].default_value
    Thin_Film_IOR = Cycles_principled.inputs["Thin Film IOR"].default_value
    
        
    
    if Render_engine == "octane":
        Engine_material_bl_idname = "NodeReroute"
        nodes = mat.node_tree.nodes
        Converted_Engine_base_name_node = "Reroute"
        input_name = "Texture"
        output_name = "Texture out"
        offset_x = 1650
        offset_y = 0
    elif Render_engine == "VRAY_RENDER_RT":
        Engine_material_bl_idname = "VRayNodeBRDFVRayMtl"
        Converted_Engine_base_name_node = "V-Ray Mtl"
        nodes = mat.node_tree.nodes
        offset_x = 0
        offset_y = -1650
    elif Render_engine == "LUXCORE":
        Engine_material_bl_idname = "LuxCoreNodeMatDisney"
        Converted_Engine_base_name_node = "Disney Material"
        nodes = mat.luxcore.node_tree.nodes
        offset_x = 0
        offset_y = 0 
       
    Converted_Base_Material = None
    Converted_Base_Material_name = Cycles_principled.name.replace("Principled BSDF",Converted_Engine_base_name_node)
            
    for n in nodes:
        if n.bl_idname == Engine_material_bl_idname and n.name == Converted_Base_Material_name:
            Converted_Base_Material = n
            continue
    if not Converted_Base_Material:
        Converted_Base_Material = nodes.new(Engine_material_bl_idname)
        Converted_Base_Material.name = Converted_Base_Material_name
        
    Converted_Base_Material.label = Cycles_principled.label
    Converted_Base_Material.location = (Cycles_principled.location[0] + offset_x, Cycles_principled.location[1] + offset_y)
    
    
    
    if Render_engine == "VRAY_RENDER_RT":
        
        #Diffuse:
        Converted_Base_Material.inputs["Diffuse Color"].value = Dffuse_Color
        
        #Anisotropy 
        Converted_Base_Material.inputs["Anisotropy(-1..1)"].value = Anisotropy_value
        Converted_Base_Material.inputs["Anisotropy Rotation"].value = Anisotropy_Rotation
        #Opacity
        Converted_Base_Material.inputs["Opacity"].value = (Opacity_Value,Opacity_Value,Opacity_Value)
        #Roughness
        Converted_Base_Material.inputs["Reflection Glossiness"].value = Reflection_Glossiness
        #Fresnel IOR
        Converted_Base_Material.inputs["Fresnel IOR"].value = Fresnel_IOR
        #Mettalic:
        Converted_Base_Material.inputs["Metalness"].value = Metalness_value
        # Coat
        Converted_Base_Material.inputs["Coat Amount"].value = Cycles_principled.inputs["Coat Weight"].default_value
        Converted_Base_Material.inputs["Coat Glossiness"].value = Coat_Glossiness
        Converted_Base_Material.inputs["Coat IOR"].value = Coat_IOR
        Converted_Base_Material.inputs["Coat Color"].value = Coat_Color
        
        #Emission:
        if Emisson_Strength != 0:
            Converted_Base_Material.inputs["Self-Illumination Color"].value = Emission_Color
        
        
        if Coat_normal:
            
            Converted_Base_Material.inputs[72].value = Coat_Normal_Value
        
        # Scheen
        Converted_Base_Material.inputs["Sheen Amount"].value = Sheen_Amount
        Converted_Base_Material.inputs["Sheen Glossiness"].value = Sheen_Glossiness
        Converted_Base_Material.inputs["Sheen Color"].value = Sheen_Color
        
        # Transmission
        Converted_Base_Material.inputs["Translucency Amount"].value = Translucency_Amount
        # Thickness
        Converted_Base_Material.inputs["Thickness Blend"].value = Thickness_Blend
        Converted_Base_Material.inputs["Thin Film IOR"].value = Thin_Film_IOR
        # 
        if Used_normal:
            
            Converted_Base_Material.inputs[69].value = Normal_value
        
            
        
        
    elif Render_engine == 'LUXCORE':
        
        Converted_Base_Material.inputs[0].default_value = Dffuse_Color
        Converted_Base_Material.inputs[1].default_value = Subsurface_value
        Converted_Base_Material.inputs[2].default_value = Metalness_value
        Converted_Base_Material.inputs[3].default_value = Specular_value
        Converted_Base_Material.inputs[4].default_value = Specular_Tilt
        Converted_Base_Material.inputs[5].default_value = Roughness_Value
        Converted_Base_Material.inputs[6].default_value = Anisotropy_value
        Converted_Base_Material.inputs[7].default_value = Sheen_Amount
        Converted_Base_Material.inputs[8].default_value = Sheen_Color[0]
        Converted_Base_Material.inputs[9].default_value = Coat_Amount
        Converted_Base_Material.inputs[10].default_value = Sheen_Glossiness
        Converted_Base_Material.inputs['Opacity'].default_value = Opacity_Value
    elif Render_engine == 'octane':
 
        pass
    
    return Converted_Base_Material   
    
"""
#Debbuging   
mat = bpy.context.object.active_material
c_nodes = mat.node_tree.nodes
Cycles_principleds = [node for node in c_nodes if node.bl_idname.startswith("ShaderNodeBsdfPrincipled")]
for Cycles_principled in Cycles_principleds:
                                     
    Convert_BDSF_node(Cycles_principled,mat)
#"""
    

                    


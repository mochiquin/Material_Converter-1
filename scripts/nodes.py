# scripts/__init__.py
import bpy

def setup_ao_nodes(Render_Engine, nodes, links, diffuse_texture, ao_texture, diffuse_color=None):
    
    if Render_Engine == "octane":
        AO_Type = "OctaneCyclesMixColorNodeWrapper"
        ao_input1 = "A"
        ao_input2 = "B"
    if Render_Engine == "LUXCORE":
        AO_Type = "LuxCoreNodeTexColorMix"
        ao_input1 = "Color 1"
        ao_input2 = "Color 2"
    if Render_Engine == "CYCLES":
        AO_Type = "ShaderNodeMix"
        ao_input1 = 6
        ao_input2 = 7
    if Render_Engine == "VRAY_RENDER_RT":
        AO_Type = "VRayNodeTexMix"
        ao_input1 = 3
        ao_input2 = 4
        
        
    
    ao_node = next((node for node in nodes if node.bl_idname == "AO_Type" and 
                   ("Diffuse AO" in node.label or "COLOR * AO" in node.label)), None)
    
    #Node Setup according to Render Engine
    if not ao_node:
        ao_node = nodes.new(AO_Type)
        ao_node.label = "Diffuse AO"
        if Render_Engine == "octane":
            ao_node.inputs["Blend Type"].default_value = 'Multiply'
        if Render_Engine == "LUXCORE":
            ao_node.mode = 'scale'
        if Render_Engine == "CYCLES":
            ao_node.data_type = 'RGBA'
            ao_node.blend_type = 'MULTIPLY'
        
    links.new(ao_texture.outputs[0], ao_node.inputs[ao_input2])
     
    if diffuse_texture:
        diffuse_texture = diffuse_texture[0]
        links.new(diffuse_texture.outputs[0], ao_node.inputs[ao_input1])
        ao_node.location = (ao_texture.location[0] + 300, ao_texture.location[1])
    else:
        ao_node.location = (ao_texture.location[0] + 300, ao_texture.location[1])
        if diffuse_color:
            ao_node.inputs[1].default_value = diffuse_color[:3]
        else:
            ao_node.inputs[1].default_value = (0.5, 0.5, 0.5)
    return ao_node 

def setup_disp_nodes(preferences, Render_Engine, nodes, links, Displacement_texture, Displacement_node):
    
    
    if Render_Engine == "octane":
        Disp_settings = preferences.octane_preferences
        if Disp_settings.octane_displacement_mode == "TEXTURE":
            Disp_idname = "OctaneTextureDisplacement"
        else:
            Disp_idname = "OctaneVertexDisplacement"
            
        
        
        
        Disp_Input = "Texture"
        
    if Render_Engine == "LUXCORE":
        print("Wszedłem")
        Disp_settings = preferences.luxcore_preferences
        if Disp_settings.luxcore_displacement_node == "Height":
            Disp_idname = "LuxCoreNodeShapeHeightDisplacement"
            Disp_Input = "Height"
        else:
            Disp_idname = "LuxCoreNodeShapeVectorDisplacement"
            Disp_Input = "Vector"

        
        
    if Render_Engine == "CYCLES":

        Disp_idname = "ShaderNodeDisplacement"
        Disp_Input = "Height"
        
    if Render_Engine == "VRAY_RENDER_RT":
        Disp_settings = preferences.vray_preferences
        Ntree_name = bpy.context.active_object.name
        Displacement_group = bpy.data.node_groups.get(Ntree_name)
        
                
        if not Displacement_group:
            bpy.data.node_groups.new(name = Ntree_name, type = "VRayNodeTreeObject")
            bpy.data.objects[Ntree_name].vray.ntree = bpy.data.node_groups[Ntree_name]
            
        Displ_nodes = bpy.data.objects[Ntree_name].vray.ntree.nodes
        Disp_links = bpy.data.objects[Ntree_name].vray.ntree.links
        Object_output = [node for node in Displ_nodes if node.bl_idname.startswith("VRayNodeObjectOutput")]
        Cycles_Displacement = next((node for node in nodes if node.bl_idname.startswith("ShaderNodeTexImage")),None)
        Disp_node = [node for node in Displ_nodes if node.bl_idname.startswith("VRayNodeDisplacement")]
        SBDV_node = [node for node in Displ_nodes if node.bl_idname.startswith("VRayNodeGeomStaticSmoothedMesh")]
        Disp_texture_1 = [node for node in Displ_nodes if node.bl_idname.startswith("VRayNodeMetaImageTexture") and node.label == "Displacement"]
        material_mapping = [node for node in nodes if node.bl_idname.startswith("VRayNodeUVWMapping")]
        Disp_mapping = [node for node in Displ_nodes if node.bl_idname.startswith("VRayNodeUVWMapping")]
        #Disp_Uv = [node for node in Displ_nodes if node.bl_idname.startswith("VRayNodeMetaImageTexture") and node.label == "Displacement"]
        
        
        if Object_output:
            Object_output = Object_output[0]
        else:
            Object_output = Displ_nodes.new("VRayNodeObjectOutput")
        if Disp_node:
            Disp_node = Disp_node[0]
        else:
            Disp_node =  Displ_nodes.new("VRayNodeDisplacement")
        if SBDV_node:
            SBDV_node = SBDV_node[0]
        else:
            SBDV_node = Displ_nodes.new("VRayNodeGeomStaticSmoothedMesh") 
        
        if Disp_texture_1:
            Disp_texture_1 = Disp_texture_1[0]
            
        else:        
            Disp_texture_node = Displacement_texture 
            new_node = Displ_nodes.new("VRayNodeMetaImageTexture") 
            new_node.location = Disp_texture_node.location  
            new_node.label = Disp_texture_node.label 
            
            

            # Set texture to the node 
            if hasattr(Disp_texture_node, "texture") and hasattr(Disp_texture_node.texture, "image"):
                source_image = Disp_texture_node.texture.image
                
                if source_image:
                    new_node.texture.image = source_image
                   
            Disp_texture_1 = [new_node]
            Disp_texture_1 = Disp_texture_1[0]
        if Disp_mapping:
            Disp_mapping = Disp_mapping[0]
        else:
            
            Disp_mapping = Displ_nodes.new("VRayNodeUVWMapping")

           
            if material_mapping:
                material_mapping = material_mapping[0]  
                for attr in dir(material_mapping):
                   
                    if attr.startswith("__") or callable(getattr(material_mapping, attr)):
                        continue

                    try:
                       
                        setattr(Disp_mapping, attr, getattr(material_mapping, attr))
                        
                    except AttributeError:
                        
                        print(f"Couldnt coppy '{attr}' - Only read attribute.")
                
       
        Disp_links.new(Disp_texture_1.outputs["Out Intensity"],Disp_node.inputs["Texture"])
        Disp_node.location = (Disp_texture_1.location[0] + 300, Disp_texture_1.location[1])
        SBDV_node.location = (Disp_node.location[0], Disp_node.location[1] - 200)
        Object_output.location = (Disp_node.location[0] + 300, Disp_node.location[1])
        Disp_links.new(Disp_node.outputs["Displacement"],Object_output.inputs["Displacement"])
        Disp_links.new(SBDV_node.outputs["Geometry"],Object_output.inputs["Subdivision"])
        Disp_links.new(Disp_mapping.outputs["Mapping"],Disp_texture_1.inputs["Mapping"])
        Disp_mapping.location = (Disp_texture_1.location[0] - 300, Disp_texture_1.location[1])
        
        #Setting from Preferences:
        if Disp_settings.use_texture_resolution == True:
            
            Disp_node.inputs[23].value = max(Cycles_Displacement.image.size[0],Cycles_Displacement.image.size[1])
        else:
            Disp_node.inputs[23].value = Disp_settings.vray_disp_txt
        Disp_node.inputs[5].value = Disp_settings.vray_displacement_amount
        
        
        return Disp_node
    if Render_Engine != "VRAY_RENDER_RT":
        if Displacement_node:
            Displacement_node = Displacement_node[0]
        else:
        
            Displacement_node = nodes.new(Disp_idname)
            Displacement_node.label = "Displacement"
        if Render_Engine == "octane":
            Displacement_node.inputs["Mid level"].default_value = Disp_settings.octane_displacement_mid
            Displacement_node.inputs["Height"].default_value = Disp_settings.octane_displacement_height
            if Disp_settings.octane_displacement_mode == "VERTEX":
                Displacement_node.inputs["Subdivision level"].default_value = Disp_settings.octane_displacement_sbdv
                Displacement_node.inputs["Map type"].default_value = Disp_settings.octane_Map_Type
                Displacement_node.inputs["Vector space"].default_value = Disp_settings.octane_Vector_Type
                Displacement_node.inputs["Input axes"].default_value = Disp_settings.octane_axes_Type
            if Disp_settings.octane_displacement_mode == "TEXTURE":
                Displacement_node.inputs["Level of detail"].default_value = Disp_settings.octane_detail_lvl
                Displacement_node.inputs["Displacement direction"].default_value = Disp_settings.octane_Disp_dir
                Displacement_node.inputs["Filter type"].default_value = Disp_settings.octane_Disp_Filter_Type
                Displacement_node.inputs["Filter radius"].default_value = Disp_settings.octane_Filter_radius
        if Render_Engine == "LUXCORE":
            SBDV_node = [node for node in nodes if node.bl_idname.startswith("LuxCoreNodeShapeSubdiv")]
            if SBDV_node:
                SBDV_node = SBDV_node[0]
            else:
                SBDV_node = nodes.new("LuxCoreNodeShapeSubdiv")
                SBDV_node.max_level = Disp_settings.luxcore_subdv
            SBDV_node.location = (Displacement_node.location[0] + 100, Displacement_node.location[1] - 300)
            links.new(SBDV_node.outputs[0], Displacement_node.inputs["Shape"])
            Displacement_node.scale = Disp_settings.luxcore_displacement_scale
            Displacement_node.offset = Disp_settings.luxcore_displacement_mid
            if Disp_settings.luxcore_displacement_node == "Height":
                Displacement_node.inputs['Height'].default_value  = Disp_settings.luxcore_displacement_height
            else:
                Displacement_node.map_chanels = Disp_settings.luxcore_displacement_map
                    
            
            
   
        Displacement_node.location = (Displacement_texture.location[0] + 300, Displacement_texture.location[1])   
        links.new(Displacement_texture.outputs[0], Displacement_node.inputs[Disp_Input])
        
        return Displacement_node
            


def setup_disp_modifier(preferences, Render_Engine, nodes, Displacement_texture, Displacement_node):
    Disp_settings = bpy.context.preferences.addons["Material_Converter 1"].preferences.luxcore_preferences
    
    Modifiers = bpy.context.object.modifiers

    
    Subdivision = next((mod for mod in Modifiers if mod.type == "SUBSURF"), None)
    Displacement = next((mod for mod in Modifiers if mod.type == "DISPLACE"), None)

    # Jeśli modyfikator Subdivision nie istnieje, utwórz go
    if not Subdivision:
        Subdivision = Modifiers.new(name="Subdivision", type="SUBSURF")
        Subdivision.render_levels = Disp_settings.luxcore_subdv
        Subdivision.levels = Disp_settings.luxcore_subdv_lvl

    
    if "Displacement" not in [mod.name for mod in bpy.context.object.modifiers]:
        Displacement = bpy.context.object.modifiers.new(name="Displacement", type='DISPLACE')
        Displacement.texture_coords = 'UV'

        
        if Displacement_texture:
            texture_name = Displacement_texture.image.name

           
            if texture_name not in bpy.data.textures:
                new_texture = bpy.data.textures.new(name=texture_name, type='IMAGE')
                new_texture.image = Displacement_texture.image
            else:
                bpy.data.textures[texture_name].image = Displacement_texture.image

            Displacement.texture = bpy.data.textures[texture_name]





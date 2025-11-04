import bpy


def Convert_image_node(Cycles_Images,mat):
    Render_engine = bpy.context.scene.render.engine
    
    Name_remap = {
        
        "ALPHA": "Opacity",
        "COLOR": "Diffuse",
        "ROUGHNESS": "Roughness",
        "TRANSLUCENCY": "Transmission",
        "NORMAL": "Normal",
        "METALNESS": "Metallic",
        "DISPLACEMENT": "Displacement"
    }
        
    
    if Render_engine == "octane":
        node_image = "OctaneRGBImage"
        nodes = mat.node_tree.nodes
        engine_image_name = "RGB image"
        gamma_input = "Legacy gamma"
        offset_x = 1650
        offset_y = 0
        
    elif Render_engine == "VRAY_RENDER_RT":
        node_image = "VRayNodeMetaImageTexture"
        engine_image_name = "V-Ray Bitmap"
        nodes = mat.node_tree.nodes
        offset_x = 0
        offset_y = -1650
    elif Render_engine == "LUXCORE":
        engine_image_name = "Imagemap"
        node_image = "LuxCoreNodeTexImagemap"
        
        nodes = mat.luxcore.node_tree.nodes
        offset_x = 0
        offset_y = 0 
      
    Engine_image_node = None
    Engine_image_node_name = Cycles_Images.name.replace("Image Texture", engine_image_name)
    print(Engine_image_node_name)
    for n in nodes:
        if n.bl_idname == node_image and n.name == Engine_image_node_name:
            Engine_image_node = n
            break
    if not Engine_image_node:
        
        
        Engine_image_node = nodes.new(node_image)
        Engine_image_node.name = Engine_image_node_name
    Engine_image_node.label = Cycles_Images.label
    Engine_image_node.label = Name_remap.get(Engine_image_node.label, Engine_image_node.label)
    #for label in Engine_image_node.label:
     #   if label in Name_remap:
      #      print("Siema")
        
        
    Engine_image_node.location = (Cycles_Images.location[0] + offset_x, Cycles_Images.location[1] + offset_y)
    Engine_image_node.hide = Cycles_Images.hide
        
    new_texture_name = Cycles_Images.image.name
    new_texture = bpy.data.images.get(new_texture_name) 
    
    if Render_engine == "LUXCORE":
        Engine_image_node.image = Cycles_Images.image
        
        if not "sRGB" in Cycles_Images.image.colorspace_settings.name:
            Engine_image_node.gamma = 1
        else:
            Engine_image_node.gamma = 2.2
    if Render_engine == "octane":
        Engine_image_node.image = Cycles_Images.image
        if not "sRGB" in Cycles_Images.image.colorspace_settings.name:
            Engine_image_node.inputs[gamma_input].default_value = 1.0
            
        else:
            Engine_image_node.inputs[gamma_input].default_value = 2.2
            
    else:
       if new_texture:
           if hasattr(Engine_image_node, 'texture') and Engine_image_node.texture:
               Engine_image_node.texture.image = new_texture
               if not "sRGB" in Cycles_Images.image.colorspace_settings.name:
                   Engine_image_node.BitmapBuffer.transfer_function = '1'
                   Engine_image_node.BitmapBuffer.gamma = 1
               else:
                   Engine_image_node.BitmapBuffer.transfer_function = '1'
                   Engine_image_node.BitmapBuffer.gamma = 2.2  
#"""
mat = bpy.context.object.active_material
c_nodes = mat.node_tree.nodes
Cycles_Images_nodes = [node for node in c_nodes if node.bl_idname == "ShaderNodeTexImage"]
for Cycles_Images in Cycles_Images_nodes:
                                     
   Convert_image_node(Cycles_Images,mat)#"""
    
    
        

                    


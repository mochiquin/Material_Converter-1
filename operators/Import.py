import bpy
import re
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, CollectionProperty
from bpy.types import Operator

# Callback
def my_callback_function():
    print("Operator zakończył pracę!")
    return None  # Timer kończy działanie

class ImportImagesToShaderNodes(Operator, ImportHelper):
    bl_idname = "shader.import_images_to_shadernodes"
    bl_label = "Import Images to Shader Nodes"

    files: CollectionProperty(type=bpy.types.PropertyGroup)
    directory: StringProperty()
        
    
    texture_categories = {
        "Diffuse": ("Albedo", "Diffuse", "BaseColor", "diff"),
        "Reflection": ("Reflection", "Specular", "reflect", "refl", "spec"),
        "Roughness": ("Glossiness", "Roughness", "RGH", "gloss", "rough"),
        "Metal": ("Gold", "Chrome", "Metal", "alum", "brass", "steel", "metallic"),
        "Normal": ("Normal", "nrm", "nor"),
        "Bump": ("Bump", "bump"),
        "Glass": ("glass", "water", "milk", "juice"),
        "Transmission": ("Transmission", "Translucency", "trans", "SubsurfaceColor"),
        "Opacity": ("Opacity", "alpha"),
        "Displacement": ("Displacement", "disp", "Height"),
        "Fabrics": ("wool", "fabric"),
        "IOR": ("IOR", "ior"),
        "AO": ("AO","ambient"),
        "Cavity": ("Cavity", "CAVITY")
    }

    def execute(self, context):
        # Get the active material
        if not self.files or not self.directory:
            return {'RUNNING_MODAL'}
        material = context.object.active_material
        if not material:
            self.report({'ERROR'}, "No active material found on the selected object.")
            return {'CANCELLED'}
            
        # Determine engine and node type
        engine = context.scene.render.engine
        node_type = 'ShaderNodeTexImage'
        Mapping_node = 'ShaderNodeMapping'
        gamma_non_color = "Non-Color"
        gamma_srgb = "sRGB"
        input = 0
        x_offset = 0
        y_offset = 0

        if engine == "LUXCORE":
            material_name = material.name
            
            color = []
            color.append(material.diffuse_color[0])
            color.append(material.diffuse_color[1])
            color.append(material.diffuse_color[2])
            color.append(material.diffuse_color[3])
           
            if not material.luxcore.node_tree:
                material.luxcore.node_tree = bpy.data.node_groups.new(name=material_name, type="luxcore_material_nodes") 
                material.luxcore.use_cycles_nodes = False
                material.luxcore.auto_vp_color = False
                material.diffuse_color = (color[0],color[1],color[2],color[3])
                Mapping_node = material.luxcore.node_tree.nodes.new("LuxCoreNodeTexMapping2D")
                
        else:
            if not material.use_nodes:
                material.use_nodes = True
            

        

        if engine == 'octane':
            input = 5
            gamma_non_color = 1
            gamma_srgb = 2.2
           
            Mapping_node = 'Octane3DTransformation'
            node_type = 'OctaneRGBImage'
            x_offset = 1650
            y_offset = 0
        elif engine == 'LUXCORE':
            Mapping_node= "LuxCoreNodeTexMapping2D"
            gamma_non_color = 1
            gamma_srgb = 2.2
            input = 0
            node_type = 'LuxCoreNodeTexImagemap'
            x_offset = 0
            y_offset = 0
        elif engine == 'VRAY_RENDER_RT':
            input = 0
            Mapping_node = "VRayNodeUVWMapping"
            node_type = 'VRayNodeMetaImageTexture'
            x_offset = 0
            y_offset = 1650
        # Base location for placing nodes
        base_location = 0  # Start Y location
        x_base = -200  # Start X location

        # Access the appropriate node tree
        if engine == 'LUXCORE':
            nodes = material.luxcore.node_tree.nodes
            links = material.luxcore.node_tree.links
            
        else:
            nodes = material.node_tree.nodes
            links = material.node_tree.links

        if not nodes:
            self.report({'ERROR'}, f"No compatible node tree found for the {engine} engine.")
            return {'CANCELLED'}

        # Check for existing Image Texture nodes specific to the engine
        existing_textures = [node for node in nodes if node.bl_idname == node_type]
        existing_Mapping = [node for node in nodes if node.bl_idname == Mapping_node]
        existing_UV = [node for node in nodes if node.bl_idname == "ShaderNodeUVMap"]
        
            
        
        if existing_textures:
            self.report({'INFO'}, f"Material already has texture nodes for the current engine. Skipping ")
        
            return {'CANCELLED'}  
            
        
       
        
        #if engine != 'LUXCORE':
        if existing_Mapping:
            Mapping_node = existing_Mapping[0]
        else: 
            Mapping_node = nodes.new(type=Mapping_node)
            Mapping_node.location = (x_base - 600 + x_offset, base_location - y_offset )
            if engine == "CYCLES":
                if not existing_UV:
                    existing_UV = nodes.new("ShaderNodeUVMap")
                    
                existing_UV.label = "UV Map"
                existing_UV.location = (Mapping_node.location[0] - 300 , Mapping_node.location[1])
                links.new(existing_UV.outputs[0],Mapping_node.inputs[0])

                
        
        

        for i, file in enumerate(self.files):
            # Full path to the image file
            filepath = self.directory + file.name

            # Load the image
            image = bpy.data.images.load(filepath, check_existing=True)

            # Create a new Image Texture node
            image_texture_node = nodes.new(type=node_type)
            
            image_colorspace = gamma_srgb  
            node_label = None
            for category, patterns in self.texture_categories.items():
                if any(re.search(keyword, file.name, re.IGNORECASE) for keyword in patterns):
                    image_colorspace = gamma_non_color if category not in {"Diffuse", "Glass", "Fabrics", "Transmission"} else gamma_srgb
                    node_label = category
                    break
            if engine == 'VRAY_RENDER_RT':
                
                texture_name_Vray = image_texture_node.texture_name 
                
                for tx in bpy.data.textures:
                    if tx.name == texture_name_Vray:  
                        tx.image = image  
                        break  
            else:
                image_texture_node.image = image
                if engine == "CYCLES":
                    image.colorspace_settings.name = image_colorspace

                elif engine == "octane":
                    image_texture_node.inputs[2].default_value = image_colorspace
                    if "gloss" in image_texture_node.image.name.lower():
                        image_texture_node.inputs[3].default_value = True
                elif engine == "LUXCORE":
                    image_texture_node.gamma = image_colorspace
                    
                

            # Set the label to the file name
            image_texture_node.label = node_label if node_label else "Diffuse" 
            #special options: 
            if "Normal" in image_texture_node.label and engine == "LUXCORE":
                image_texture_node.is_normal_map = True
            if "Roughness" in image_texture_node.label and engine == "VRAY_RENDER_RT":
                image_texture_node.TexBitmap['invert']=True
           
                
            
            
                
            
            

            # Adjust node position
            image_texture_node.location = (x_base + x_offset, base_location - y_offset - i * 300)
            
            links.new(Mapping_node.outputs[0],image_texture_node.inputs[input])
            
            

        self.report({'INFO'}, "Images successfully imported.")
        finished = True
        return {'FINISHED'}

# Register the operator
def register():
    bpy.utils.register_class(ImportImagesToShaderNodes)

def unregister():
    bpy.utils.unregister_class(ImportImagesToShaderNodes)

if __name__ == "__main__":
    register()
    execute_operator_with_callback()
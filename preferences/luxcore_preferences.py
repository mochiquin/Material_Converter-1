import bpy
from bpy.props import EnumProperty, FloatProperty, IntProperty, BoolProperty, FloatVectorProperty
from bpy.types import PropertyGroup

class LuxcorePreferences(PropertyGroup):
    # Luxcore material preferences
    active_tab: EnumProperty(
        items=[
            ('BASE_MATERIAL', "Base Material", "Base material settings"),
            ('DISPLACEMENT', "Displacement", "Displacement settings"),
            ('METALLIC_MATERIAL', "Metallic", "Metallic settings"),
            ('TRANS_MATERIAL', "Translucency", "Translucency settings")
        ],
        default='BASE_MATERIAL'
    )
    #Base Material Settings:
    luxcore_base_specular: FloatProperty(
        name="Specular Value",
        description="Set Value for Reflection in Disney Mateiral",
        default=0.5,  
        min=0.0,   
        max=1  
    )
    luxcore_base_roughness: FloatProperty(
        name="Roughness Value",
        description="Set roughness value for Base Material",
        default=0.2,  
        min=0.0,   
        max=1  
    )
    luxcore_albedo_color_addon: FloatVectorProperty(
        name="Albedo Color",
        description="Set Albedo for Luxcore Base Material",
        subtype='COLOR',
        default=(0.8, 0.8, 0.8),
        size = 3,
        min=0.0,
        max=1.0
    )
    
    #Displacement:
    luxcore_displacement: EnumProperty(
        name="Luxcore Type of Displacement",
        description="Select Displacement type for Luxcore",
        items=[
            ('Material', "Material", ""),
            ('Modifier', "Modifier", "")     
                       
        ],
        default='Material'
    )
    luxcore_displacement_node: EnumProperty(
        name="Luxcore node of Displacement",
        description="Select Displacment node for Luxcore",
        items=[
            ('Height', "Height", "Use Height node for presets"),
            ('Vector', "Vector", "Use Vector node for presets")     
                       
        ],
        default='Height'
    )
    luxcore_subdv: bpy.props.IntProperty(
        name="Subdivision level",
        description="Set Subdivision level for Displacement",
        default=1,
        min=1,
        max=20
    )
    luxcore_displacement_mid: FloatProperty(
        name="Displacement Mid Level",
        description="Set mid level of the displacement",
        default=0.5,  
        min=0.0,   
        max=1.0  
    )
    luxcore_subdv_lvl: bpy.props.IntProperty(
        name="Subdivision level for Viewport",
        description="Set Subdivision level for Viewport Displacement",
        default=1,
        min=1,
        max=20
    )
   
    luxcore_displacement_scale: FloatProperty(
        name="Displacement scale",
        description="Set scale of the displacement",
        default=0,  
        min=-10.0,   
        max=10.0  
    )
    luxcore_displacement_height: FloatProperty(
        name="Displacement height",
        description="Set height for Vertex displacement node",
        default=0,  
        min=-10.0,   
        max=10.0  
    )
    luxcore_displacement_map: EnumProperty(
        name="Map Channels for  Displacement",
        description="Select Map Channels for Vertex Displacement node",
        items=[
            ('012', "0, 1, 2 ", ""),
            ('021', "0, 2, 1 (Mudbox)", ""),
            ('102', "1, 0, 2 ", ""), 
            ('120', "1, 2, 0 ", ""), 
            ('201', "2, 0, 1 (Blender) ", ""), 
            ('210', "2, 1, 0 ", ""), 
                       
        ],
        default='201'
    )
    #Metallic Settings:
    use_lux_metallic_material: BoolProperty(
        name="Use Metallic Material instead of Disney Material for Metal Materials ",
        description="It allows you to use Metallic Material instead of Disney Material for Metallic Materials",
        default=False
    )
    
    luxcore_metal_color_addon: FloatVectorProperty(
        name="Base Color",
        description="Set Base Color for Luxcore Metal Material",
        subtype='COLOR',
        default=(0.8, 0.8, 0.8),
        size = 3,
        min=0.0,
        max=1.0
    )
    
    luxcore_metallic_roughness: FloatProperty(
        name="Roughness Value",
        description="Set roughness value for Metallic Material",
        default=0.05,  
        min=0.0,   
        max=1  
    )
    #Trans Settings:
    use_trans_multibounce: BoolProperty(
        name="Multibounce",
        description="Gives material a fuzzy sheen",
        default=False
    )
    use_trans_IOR: BoolProperty(
        name="Use IOR",
        description="Use IOR instead of Specular Color",
        default=False
    )
    use_trans_ar: BoolProperty(
        name="Anisotropic Roughness",
        description="Uses Different Roughness values for directions",
        default=False
    )
    
    luxcore_trans_color_addon: FloatVectorProperty(
        name="Diffuse Color",
        description="Set Diffuse Color for Luxcore Trnslusency Material",
        subtype='COLOR',
        default=(0.185, 0.185, 0.185),
        size = 3,
        min=0.0,
        max=1.0
    )
    luxcore_trans_trans_addon: FloatVectorProperty(
        name="Transmission Color",
        description="Set Transmission Color for Luxcore Trnslusency Material",
        subtype='COLOR',
        default=(0.735, 0.735, 0.735),
        size = 3,
        min=0.0,
        max=1.0
    )
    luxcore_trans_specular_addon: FloatVectorProperty(
        name="Specular Color",
        description="Set Specular Color for Luxcore Trnslusency Material",
        subtype='COLOR',
        default=(0.248, 0.248, 0.248),
        size = 3,
        min=0.0,
        max=1.0
    )
    luxcore_trans_abs_addon: FloatVectorProperty(
        name="Absorption Color",
        description="Set Absorption Color for Luxcore Translucency Material",
        subtype='COLOR',
        default=(0.0, 0.0, 0.0),
        size = 3,
        min=0.0,
        max=1.0
    )
    
    luxcore_trans_roughness: FloatProperty(
        name="Roughness Value Base and U-direction",
        description="Set roughness value for Translucency Material",
        default=0.05,  
        min=0.0,   
        max=1  
    )
    luxcore_trans_roughness_v: FloatProperty(
        name="Roughness Value V-direction",
        description="Set roughness value for Translucency Material",
        default=0.05,  
        min=0.0,   
        max=1  
    )
    luxcore_trans_abs: FloatProperty(
        name="Absorption Depth (nm)",
        description="Set Absorption Depth for Translucency Material",
        default=0.0,  
        min=0.0,   
        max=1000  
    )
    luxcore_trans_IOR: FloatProperty(
        name="IOR",
        description="Set IOR for Translucency Material",
        default=1.5,  
        min=1.0,   
        max=2.0  
    )
    
    def draw_base_material(self, layout):
        """Rysuje zawartość zakładki Base Material"""
        box = layout.box()
        box.prop(self, "luxcore_albedo_color_addon")
        box.prop(self, "luxcore_base_specular")
        box.prop(self, "luxcore_base_roughness")
                
    
    def draw_displacement(self, layout):
        """Rysuje zawartość zakładki Displacement"""
        box = layout.box()
        box.prop(self, "luxcore_displacement")
        displacement_mode = self.luxcore_displacement
        box.prop(self, "luxcore_subdv")
        box.prop(self, "luxcore_displacement_mid")
        box.prop(self, "luxcore_displacement_scale")
        
        if displacement_mode == 'Material':
            
            box.prop(self, "luxcore_displacement_node")
            displacement_mode_lux_node = self.luxcore_displacement_node
            if displacement_mode_lux_node == "Height":
                box.prop(self, "luxcore_displacement_height")
            if displacement_mode_lux_node == "Vector":
                box.prop(self, "luxcore_displacement_map")
        if displacement_mode == "Modifier":
            box.prop(self, "luxcore_subdv_lvl")
    
    def draw_metallic_material(self, layout):
        """Metallic Layout"""
        box = layout.box()
        box.prop(self, "use_lux_metallic_material")
              
        Luxcore_Metallic = self.use_lux_metallic_material
        
        if Luxcore_Metallic == False:
            label = box.label(text="Currently it uses setings from Base Material Tab")  
        else:
            box.prop(self, "luxcore_metal_color_addon")
            box.prop(self, "luxcore_metallic_roughness")
    def draw_trans_material(self, layout):
        """Metallic Layout"""
        box = layout.box()
        box.prop(self, "use_trans_multibounce")
        box.prop(self, "use_trans_IOR")
        box.prop(self, "use_trans_ar")
        
        Lux_Trans_IOR = self.use_trans_IOR
        Lux_Trans_AR = self.use_trans_ar
        
        box.prop(self, "luxcore_trans_color_addon")
        box.prop(self, "luxcore_trans_trans_addon")
                
        if Lux_Trans_IOR == False:
           box.prop(self, "luxcore_trans_specular_addon") 
        else:
            box.prop(self, "luxcore_trans_IOR")
            
        box.prop(self, "luxcore_trans_abs_addon")
        
        box.prop(self, "luxcore_trans_roughness")
        if Lux_Trans_AR == True:
            box.prop(self, "luxcore_trans_roughness_v")
        box.prop(self, "luxcore_trans_abs")
            
                    
                    
    def draw_tabs(self, layout):
        """Rysuje przyciski zakładek w dwóch wierszach"""
        col = layout.column(align=True) 

        row = col.row(align=True)  
        row.prop(self, "active_tab", expand=True, text="Name")

    

    def draw_luxcore_preferences(self, layout):
        """Główna funkcja rysująca UI"""
        # Rysuj zakładki
        self.draw_tabs(layout)
        
        # Rysuj zawartość aktywnej zakładki
        if self.active_tab == 'BASE_MATERIAL':
            self.draw_base_material(layout)
        elif self.active_tab == 'DISPLACEMENT':
            self.draw_displacement(layout)
        elif self.active_tab == 'METALLIC_MATERIAL':
            self.draw_metallic_material(layout)
        elif self.active_tab == 'TRANS_MATERIAL':
            self.draw_trans_material(layout)
        
    
import bpy
from bpy.props import EnumProperty, FloatProperty, IntProperty, BoolProperty, FloatVectorProperty
from bpy.types import PropertyGroup


class VRayPreferences(PropertyGroup):
    # vray material preferences
    
    #Upper Tab
    
    active_tab: EnumProperty(
        items=[
            ('BASE_MATERIAL', "Base Material", "Base material settings"),
            ('DISPLACEMENT', "Displacement", "Displacement settings")
        ],
        default='BASE_MATERIAL'
    )
    
    #Base Material
    vray_base_material: EnumProperty(
        name="Base Material",
        description="Select the base material type for vray",
        items=[
            ('UNIVERSAL', "Universal Material", "Use Universal Material as base"),
            ('STANDARD_SURFACE', "Standard Surface Material", "Use Standard Surface Material as base")
        ],
        default='UNIVERSAL'
    )
    vray_albedo_color_addon: FloatVectorProperty(
        name="Diffuse Color",
        description="Set Diffuse Color for V-ray Material",
        subtype='COLOR',
        default=(0.8, 0.8, 0.8),
        size = 3,
        min=0.0,
        max=1.0
    )
    vray_reflection_color_addon: FloatVectorProperty(
        name="Reflection Color",
        description="Set Reflection Color for V-ray Material",
        subtype='COLOR',
        default=(0.8, 0.8, 0.8),
        size = 3,
        min=0.0,
        max=1.0
    )
    vray_glossiness_amount: FloatProperty(
        name="Glossiness Level",
        description="Set glossiness amount in the new material",
        default=0.65,  
        min=0,   
        max=1  
    )
    vray_Fresnel_amount: FloatProperty(
        name="Fresnel IOR",
        description="Set Fresnel IOR for the new material",
        default=1.6,  
        min=0,   
        max=5  
    )
    
    
    #Displacment:
    vray_displacement_mode: EnumProperty(
        name="Displacement Mode",
        description="Select Displacement Mode for vray",
        items=[
            ('0', "Normal", ""),
            ('1', "2D", ""),
            ('2', "Vector", ""),
            ('3', "Vector (Absolute)", ""),
            ('4', "Vector (Object)", "")
        ],
        default='0'
    )
    vray_disp_txt: EnumProperty(
        name="Displacement Detail Level",
        description="Select the detail level for displacement",
        items=[
            ('256', "256x256", "Set 256x256 resolution for Displacement Detail Level"),
            ('512', "512x512", "Set 512x512 resolution for Displacement Detail Level"),
            ('1024', "1024x1024", "Set 1024x1024 resolution for Displacement Detail Level"),
            ('2048', "2048x2048", "Set 2048x2048 resolution for Displacement Detail Level"),
            ('4096', "4096x4096", "Set 4096x4096 resolution for Displacement Detail Level"),
            ('8192', "8192x8192", "Set 8192x8192 resolution for Displacement Detail Level")            
        ],
        default='256'
    )
    vray_displacement_amount: FloatProperty(
        name="Displacement amount Level",
        description="Set displacement amount for the displacement",
        default=0.5,  
        min=-100.0,   
        max=100.0  
    )
    use_texture_resolution: BoolProperty(
        name="Use Texture Resolution",
        description="Vray Documentation says that it is better to use Input texture resolution for Displacement",
        default=True
    )

   
    def draw_base_material(self, layout):
        """Rysuje zawartość zakładki Base Material"""
        box = layout.box()
        box.prop(self, "vray_albedo_color_addon")
        box.prop(self, "vray_reflection_color_addon")
        box.prop(self, "vray_glossiness_amount")
        box.prop(self, "vray_Fresnel_amount")
            
    def draw_displacement(self, layout):
        """Rysuje zawartość zakładki Displacement"""
        box = layout.box()
        box.prop(self, "vray_displacement_mode")
        box.prop(self, "vray_displacement_amount")
        box.prop(self, "use_texture_resolution")
        Vray_use_Texture_Resolution = self.use_texture_resolution
        
        if Vray_use_Texture_Resolution == False:
            box.prop(self, "vray_disp_txt")
        
        
    def draw_tabs(self, layout):
        """Rysuje przyciski zakładek"""
        row = layout.row()
        row.prop(self, "active_tab", expand=True)

    def draw_vray_preferences(self, layout):
        """Główna funkcja rysująca UI"""
        # Rysuj zakładki
        self.draw_tabs(layout)
        
        # Rysuj zawartość aktywnej zakładki
        if self.active_tab == 'BASE_MATERIAL':
            self.draw_base_material(layout)
        elif self.active_tab == 'DISPLACEMENT':
            self.draw_displacement(layout)
        
    
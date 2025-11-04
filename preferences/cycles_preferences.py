import bpy
from bpy.props import EnumProperty, FloatProperty, IntProperty
from bpy.types import PropertyGroup

class OctanePreferences(PropertyGroup):
    # Octane material preferences
    active_tab: EnumProperty(
        items=[
            ('BASE_MATERIAL', "Base Material", "Base material settings"),
            ('DISPLACEMENT', "Displacement", "Displacement settings")
        ],
        default='BASE_MATERIAL'
    )
    octane_base_material: EnumProperty(
        name="Base Material",
        description="Select the base material type for Octane",
        items=[
            ('UNIVERSAL', "Universal Material", "Use Universal Material as base"),
            ('STANDARD_SURFACE', "Standard Surface Material", "Use Standard Surface Material as base")
        ],
        default='UNIVERSAL'
    )
    octane_BRDF: EnumProperty(
        name="Diffuse BRDF model",
        description="Select BRDF model type for Octane",
        items=[
            ('Octane', "Octane BRDF model", "Use Universal Material as base"),
            ('Lambertian', "Lambertian BRDF model", "Use Standard Surface Material as base"),
            ('Oren-Nayar', "Oren-Nayar BRDF model", "Use Standard Surface Material as base")
        ],
        default='Octane'
    )
    octane_BSDF: EnumProperty(
        name="Diffuse BSDF model",
        description="Select BSDF model type for Octane",
        items=[
            ('Octane', "Octane BSDF model", "Use Universal Material as base"),
            ('Beckmann', "Beckmann BSDF model", "Use Standard Surface Material as base"),
            ('GGX', "GGX BSDF model", "Use Standard Surface Material as base"),
            ('GGX (energy preserving)', "GGX (energy preserving) BSDF model", "Use Standard Surface Material as base"),
            ('STD', "STD BSDF model", "Use Standard Surface Material as base")
        ],
        default='Octane'
    )
    octane_transmission: EnumProperty(
        name="Transmission type",
        description="Select Transmission type",
        items=[
            ('Specular', "Specular type", "Use Universal Material as base"),
            ('Diffuse', "Diffuse type", "Use Standard Surface Material as base"),
            ('Thin wall', "Thin wall", "Use Standard Surface Material as base"),
            ('Thin wall (Diffuse)', "Thin wall (Diffuse)", "Use Standard Surface Material as base")
        ],
        default='Specular'
    )
    
    octane_metallic_type: EnumProperty(
        name="Metallic Reflection mode ",
        description="Select Metallic Reflection mode",
        items=[
            ('Artistic', "Artistic mode", "Use Artistic mode for Metallic Reflection"),
            ('IOR + color', "IOR + color mode", "IOR + color mode for Metallic Reflection"),
            ('RGB IOR', "RGB IOR mode",  "RGB IOR mode for Metallic Reflection")
            
        ],
        default='Artistic'
    )
    octane_Dispersion_mode: EnumProperty(
        name="Dispersion mode ",
        description="Select Dispersion mode",
        items=[
            ('Abbe number', "Abbe number mode", "Use Abbe number mode for Dispersion"),
            ('Cauchy formula', "Cauchy formula mode", "Use Cauchy formula number mode for Dispersion")
            
            
        ],
        default='Abbe number'
    )
    octane_displacement_mode: EnumProperty(
        name="Displacement Type",
        description="Select Displacement Node",
        items=[
            ('TEXTURE', "Texture Displacement Node ", "Use Texture Displacement"),
            ('VERTEX', "Vertex Displacement Node ", "Use Vertex Displacement ")
            
            
        ],
        default='TEXTURE'
    )
    octane_detail_lvl: EnumProperty(
        name="Displacement Detail Level",
        description="Select the detail level for displacement",
        items=[
            ('256x256', "256x256", "Set 256x256 resolution for Displacement Detail Level"),
            ('512x512', "512x512", "Set 512x512 resolution for Displacement Detail Level"),
            ('1024x1024', "1024x1024", "Set 1024x1024 resolution for Displacement Detail Level"),
            ('2048x2048', "2048x2048", "Set 2048x2048 resolution for Displacement Detail Level"),
            ('4096x4096', "4096x4096", "Set 4096x4096 resolution for Displacement Detail Level"),
            ('8192x8192', "8192x8192", "Set 8192x8192 resolution for Displacement Detail Level")            
        ],
        default='1024x1024'
    )
    octane_Disp_dir: EnumProperty(
        name="Displacement Direction",
        description="Select Displacement Direction",
        items=[
            ('Follow vertex normal', "Follow vertex normal", ""),
            ('Follow geometric normal', "Follow geometric normal", ""),
            ('Follow smoothed normal', "Follow smoothed normal", "")
                       
        ],
        default='Follow vertex normal'
    )
    octane_Disp_Filter_Type: EnumProperty(
        name="Displacement Filter Type",
        description="Select Filter Type for Displacement",
        items=[
            ('None', "None", ""),
            ('Box', "Box", ""),
            ('Gaussian', "", "")
                       
        ],
        default='None'
    )
    octane_Filter_radius: bpy.props.IntProperty(
        name="Filter Radius",
        description="Set Filter Radius for Displacement",
        default=1,
        min=1,
        max=20
    )
    octane_displacement_mid: FloatProperty(
        name="Displacement Mid Level",
        description="Set mid level of the displacement",
        default=0.5,  
        min=0.0,   
        max=1.0  
    )
    octane_displacement_height: FloatProperty(
        name="Displacement Height Level",
        description="Set Height of the displacement",
        default=0.2,  
        min=0.0,   
        max=900  
    )
    
    octane_displacement_sbdv: bpy.props.IntProperty(
        name="Displacement Subdivision Level",
        description="Set Subdivision Level for Displacement",
        default=0,
        min=0,
        max=6
    )
    octane_Map_Type: EnumProperty(
        name="Map Type",
        description="Select Map Type for Displacement",
        items=[
            ('Height', "Height", ""),
            ('Vector', "Vector", "")
            
                       
        ],
        default='Height'
    )
    octane_Vector_Type: EnumProperty(
        name="Vector_Space",
        description="Select Vector Space for Displacement",
        items=[
            ('Object', "Object", ""),
            ('Tangent', "Tangent", "")
            
                       
        ],
        default='Object'
    )
    octane_axes_Type: EnumProperty(
        name="Input Axes",
        description="Select Input Axes for Displacement",
        items=[
            ('+X,+Y,+Z', '+X,+Y,+Z', ""),
            ('+X,+Z,+Y', '+X,+Z,+Y', ""),
            ('+X,+Z,-Y', '+X,+Z,-Y', "")
            
                       
        ],
        default='+X,+Y,+Z'
    )
    def draw_base_material(self, layout):
        """Rysuje zawartość zakładki Base Material"""
        box = layout.box()
        box.prop(self, "octane_base_material")
        box.prop(self, "octane_BRDF")
        box.prop(self, "octane_BSDF")
        box.prop(self, "octane_transmission")
        box.prop(self, "octane_metallic_type")
        box.prop(self, "octane_Dispersion_mode")
    
    def draw_displacement(self, layout):
        """Rysuje zawartość zakładki Displacement"""
        box = layout.box()
        box.prop(self, "octane_displacement_mode")
        displacement_mode = self.octane_displacement_mode
        box.prop(self, "octane_displacement_mid")
        box.prop(self, "octane_displacement_height")
        
        if displacement_mode == 'VERTEX':
            box.prop(self, "octane_Map_Type")
            box.prop(self, "octane_Vector_Type")
            box.prop(self, "octane_axes_Type")
            box.prop(self, "octane_displacement_sbdv")
        
        if displacement_mode == 'TEXTURE':
            box.prop(self, "octane_detail_lvl")
            box.prop(self, "octane_Disp_dir")
            box.prop(self, "octane_Disp_Filter_Type")
            box.prop(self, "octane_Filter_radius")
            
    def draw_tabs(self, layout):
        """Rysuje przyciski zakładek"""
        row = layout.row()
        row.prop(self, "active_tab", expand=True)

    def draw_octane_preferences(self, layout):
        """Główna funkcja rysująca UI"""
        # Rysuj zakładki
        self.draw_tabs(layout)
        
        # Rysuj zawartość aktywnej zakładki
        if self.active_tab == 'BASE_MATERIAL':
            self.draw_base_material(layout)
        elif self.active_tab == 'DISPLACEMENT':
            self.draw_displacement(layout)
        
    
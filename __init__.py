bl_info = {
    "name": "Material Converter",
    "author": "Adam Zorian Radziszewski",
    "version": (1, 0, 8),
    "blender": (4, 2, 0),
    "location": "Properties > Material > Material Converter, Node Editor > Sidebar > Material Converter",
    "description": "Converts materials between different render engines",
    "warning": "",
    "doc_url": "",
    "category": "Material",
}

import bpy
import json
import os
import sys
import zipfile
import importlib
import importlib.util
from .operators import register_operators, unregister_operators
from .scripts import *
from bpy.props import StringProperty, EnumProperty, BoolProperty, FloatProperty, IntProperty, FloatVectorProperty
from bpy.types import AddonPreferences, Panel, Operator

from .preferences.luxcore_preferences import LuxcorePreferences
from .preferences.octane_preferences import OctanePreferences
from .preferences.vray_preferences import VRayPreferences

from typing import Dict, Any, Tuple

def get_addon_preferences(addon_name="Material_Converter 1"):
    """Get the addon preferences object."""
    addon = bpy.context.preferences.addons.get(addon_name)
    if addon and addon.preferences:
        return addon.preferences
    return None

def serialize_preferences(prefs) -> Dict[str, Any]:
    """Convert addon preferences to a serializable dictionary."""
    result = {}
    
    # First pass - collect simple properties
    for attr_name in dir(prefs):
        if attr_name.startswith("__") or callable(getattr(prefs, attr_name)) or attr_name.startswith("bl_"):
            continue
            
        try:
            attr_value = getattr(prefs, attr_name)
            
            # Handle simple types that can be directly serialized
            if isinstance(attr_value, (bool, int, float, str)) or attr_value is None:
                result[attr_name] = attr_value
            # Handle vectors, colors, etc.
            elif hasattr(attr_value, "to_list"):
                result[attr_name] = attr_value.to_list()
            # Handle enumerations
            elif isinstance(attr_value, set):
                result[attr_name] = list(attr_value)
            # Handle nested bpy_struct objects as dictionaries
            elif isinstance(attr_value, bpy.types.bpy_struct):
                nested_dict = {}
                for sub_attr_name in dir(attr_value):
                    if sub_attr_name.startswith("__") or callable(getattr(attr_value, sub_attr_name)) or sub_attr_name.startswith("bl_"):
                        continue
                        
                    try:
                        sub_attr_value = getattr(attr_value, sub_attr_name)
                        
                        # Only store simple types for nested structures
                        if isinstance(sub_attr_value, (bool, int, float, str)) or sub_attr_value is None:
                            nested_dict[sub_attr_name] = sub_attr_value
                        elif hasattr(sub_attr_value, "to_list"):
                            nested_dict[sub_attr_name] = sub_attr_value.to_list()
                        else:
                            nested_dict[sub_attr_name] = str(sub_attr_value)
                    except:
                        # Skip properties that can't be accessed
                        continue
                        
                result[attr_name] = nested_dict
            # All other types converted to string
            else:
                result[attr_name] = str(attr_value)
        except:
            # Skip properties that can't be accessed
            continue
            
    return result

def save_addon_preferences_to_json(filepath: str, addon_name="Material_Converter 1") -> Tuple[set, str]:
    """Save addon preferences to a JSON file."""
    prefs = get_addon_preferences(addon_name)
    if not prefs:
        return {'WARNING'}, f"Nie znaleziono preferencji dla dodatku: {addon_name}"
        
    # Get serializable data
    data = serialize_preferences(prefs)
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
        return {'INFO'}, f"Zapisano ustawienia dodatku '{addon_name}' do pliku: {filepath}"
    except Exception as e:
        return {'ERROR'}, f"Błąd zapisywania preferencji: {str(e)}"

def load_addon_preferences_from_json(filepath: str, addon_name="Material_Converter 1") -> Tuple[set, str]:
    """Load addon preferences from a JSON file."""
    prefs = get_addon_preferences(addon_name)
    if not prefs:
        return {'WARNING'}, f"Nie znaleziono preferencji dla dodatku: {addon_name}"
    
    try:
        # Load from file
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Apply settings
        applied_count = 0
        error_count = 0
        
        for key, value in data.items():
            if hasattr(prefs, key):
                try:
                    current_value = getattr(prefs, key)
                    
                    # Handle different types
                    if isinstance(current_value, bpy.types.bpy_struct) and isinstance(value, dict):
                        # Apply nested struct values
                        for sub_key, sub_value in value.items():
                            if hasattr(current_value, sub_key):
                                try:
                                    # Handle color string representation
                                    if isinstance(sub_value, str) and "<Color" in sub_value:
                                        # Extract RGB values using regex
                                        import re
                                        rgb_match = re.search(r'r=(\d+\.\d+),\s*g=(\d+\.\d+),\s*b=(\d+\.\d+)', sub_value)
                                        if rgb_match:
                                            r = float(rgb_match.group(1))
                                            g = float(rgb_match.group(2))
                                            b = float(rgb_match.group(3))
                                            
                                            # Set color values
                                            sub_current = getattr(current_value, sub_key)
                                            if len(sub_current) >= 3:  # Make sure it has at least 3 components
                                                sub_current[0] = r
                                                sub_current[1] = g
                                                sub_current[2] = b
                                                applied_count += 1
                                            else:
                                                error_count += 1
                                        else:
                                            error_count += 1
                                    else:
                                        setattr(current_value, sub_key, sub_value)
                                        applied_count += 1
                                except:
                                    print(f"Nie udało się ustawić {key}.{sub_key} = {sub_value}")
                                    error_count += 1
                    else:
                        # Handle color string in top-level property
                        if isinstance(value, str) and "<Color" in value:
                            # Extract RGB values using regex
                            import re
                            rgb_match = re.search(r'r=(\d+\.\d+),\s*g=(\d+\.\d+),\s*b=(\d+\.\d+)', value)
                            if rgb_match:
                                r = float(rgb_match.group(1))
                                g = float(rgb_match.group(2))
                                b = float(rgb_match.group(3))
                                
                                # Set color values
                                if len(current_value) >= 3:  # Make sure it has at least 3 components
                                    current_value[0] = r
                                    current_value[1] = g
                                    current_value[2] = b
                                    applied_count += 1
                                else:
                                    error_count += 1
                            else:
                                error_count += 1
                        else:
                            # Apply directly
                            setattr(prefs, key, value)
                            applied_count += 1
                except:
                    print(f"Nie udało się ustawić {key} = {value}")
                    error_count += 1
                    
        return {'INFO'}, f"Wczytano {applied_count} ustawień dodatku '{addon_name}' z pliku: {filepath}. Nie udało się wczytać {error_count} ustawień."
    except Exception as e:
        return {'ERROR'}, f"Błąd wczytywania preferencji: {str(e)}"

# Operatory Blender do eksportu/importu preferencji
class MC_OT_ExportPreferences(bpy.types.Operator):
    bl_idname = "mc.export_prefs"
    bl_label = "Export Addon Preferences"
    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH",
        default="mc_settings.json"
    )

    def execute(self, context):
        status, message = save_addon_preferences_to_json(self.filepath)
        self.report(status, message)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.filepath = os.path.join(bpy.path.abspath("//"), "mc_settings.json")
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class MC_OT_ImportPreferences(bpy.types.Operator):
    bl_idname = "mc.import_prefs"
    bl_label = "Import Addon Preferences"
    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH",
        default="mc_settings.json"
    )

    def execute(self, context):
        status, message = load_addon_preferences_from_json(self.filepath)
        self.report(status, message)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# Pomocnicza funkcja do wyświetlenia ustawień dodatku (debugging)
def wypisz_szczegolowe_ustawienia_addonu():
    addon_name = "Material_Converter 1"
    prefs = get_addon_preferences(addon_name)
    if prefs:
        print(f"Ustawienia dodatku: {addon_name}")
        for attr_name in dir(prefs):
            if not attr_name.startswith("__") and not callable(getattr(prefs, attr_name)):
                try:
                    attr_value = getattr(prefs, attr_name)
                    print(f"  {attr_name}: {attr_value}")
                    if isinstance(attr_value, bpy.types.bpy_struct):
                        print(f"    Szczegóły {attr_name}:")
                        for sub_attr_name in dir(attr_value):
                            if not sub_attr_name.startswith("__") and not callable(getattr(attr_value, sub_attr_name)):
                                try:
                                    sub_attr_value = getattr(attr_value, sub_attr_name)
                                    print(f"      {sub_attr_name}: {sub_attr_value}")
                                except:
                                    print(f"      {sub_attr_name}: <nie można odczytać>")
                except:
                    print(f"  {attr_name}: <nie można odczytać>")
    else:
        print(f"Nie znaleziono preferencji dla dodatku: {addon_name}")


def safe_import_module(addon_path, engine_load):
    try:
        module_path = os.path.join(addon_path, engine_load, f"viewport_{engine_load}.py")
        if not os.path.exists(module_path):
            bpy.ops.material.premium_feature_info('INVOKE_DEFAULT', feature_type="Viewport Node Preview", engine=engine_load)
    
            print(f"Module {module_path} does not exist.")
            return None
        
        spec = importlib.util.spec_from_file_location(f"viewport_{engine_load}", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"Unexpected error importing module: {e}")
        return None

class NODE_OT_Viewport(bpy.types.Operator):
    """Set Viewport Preview for nodes"""
    bl_idname = "node.viewport_check"
    bl_label = "Set Viewport Preview for Nodes"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.area.type == 'NODE_EDITOR'
    
    def execute(self, context):
        addon_path = os.path.dirname(os.path.realpath(__file__))
        scene = context.scene
        render_engine = scene.render.engine
        mat = context.object.active_material
        
        if not mat:
            self.report({'WARNING'}, "No active material")
            return {'CANCELLED'}
        
        engine_mapping = {
            "CYCLES": ("Bsdf", "Cycles Output", "cycles"),
            "LUXCORE": ("LuxCoreNodeMat", "LuxCore Output", "luxcore"),
            "octane": ("Material", "Octane Output", "octane"),
            "VRAY_RENDER_RT": ("BRDF", "V-ray Output", "vray")
        }
        
        if render_engine not in engine_mapping:
            self.report({'WARNING'}, f"Unsupported render engine: {render_engine}")
            return {'CANCELLED'}
        
        material_node, output_name, engine_load = engine_mapping[render_engine]
        if render_engine == "LUXCORE":
            nodetree = mat.luxcore.node_tree
        else:
            nodetree = mat.node_tree
        #nodetree = getattr(mat, 'luxcore.node_tree', mat.node_tree) if hasattr(mat, 'luxcore') else mat.node_tree
        
        if not nodetree:
            self.report({'WARNING'}, "No Shader Node Tree")
            return {'CANCELLED'}
        
        material_output = [node for node in nodetree.nodes if node.label.startswith(output_name)]
        active_node = context.space_data.node_tree.nodes.active
        
        if active_node:
            if material_node not in active_node.bl_idname:
                engine_module = safe_import_module(addon_path, engine_load)
                function_name = f"Create_viewport_emission_{engine_load}"
                
                if engine_module and hasattr(engine_module, function_name):
                    func = getattr(engine_module, function_name)
                    status = func(mat, active_node)  # Poprawnie pobieramy wartość zwracaną przez funkcję
                    self.report({'INFO'}, f"Executed {function_name} from {engine_module}")
                    
                    if status == "Success":
                        self.report({'INFO'}, f"Executed {function_name} from {engine_module}")
                    else:
                        self.report({'WARNING'}, status)
                else:
                    
                    #bpy.ops.material.premium_feature_info('INVOKE_DEFAULT', feature_type="Viewport Node Preview", engine=engine_load)
                    self.report({'ERROR'}, f"Function {function_name} not found in {engine_module}")
            else:
                if material_output:
                    nodetree.links.new(active_node.outputs[0], material_output[0].inputs[0])
                
                for n_delete in nodetree.nodes:
                    if "Viewport" in n_delete.label:
                        nodetree.nodes.remove(n_delete)
                
                
                
                self.report({'INFO'}, "Please choose a non-material node type")
        else:
            self.report({'WARNING'}, "No node selection")
        
        return {'FINISHED'}
class NODE_OT_my_search_menu(bpy.types.Operator):
    """Change Node label"""
    bl_idname = "node.my_search_menu"
    bl_label = "Label Change Menu"

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=200)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Change Node Label")

        node = context.active_node

        if node:
            layout.operator("node.change_label", text="Diffuse").label = "Diffuse"
            layout.operator("node.change_label", text="Specular").label = "Specular"
            layout.operator("node.change_label", text="Transmission").label = "Transmission"
            layout.operator("node.change_label", text="IOR").label = "IOR"
            layout.operator("node.change_label", text="Normal").label = "Normal"
            layout.operator("node.change_label", text="Roughness").label = "Roughness"
            layout.operator("node.change_label", text="Displacement").label = "Displacement"
            layout.operator("node.change_label", text="AO").label = "AO"
            layout.operator("node.change_label", text="Bump").label = "Bump"
            layout.operator("node.change_label", text="Opacity").label = "Opacity"
        else:
            layout.label(text="Node has been not selected, Select Node!")

class NODE_OT_change_label(bpy.types.Operator):
    """Change Node Label"""
    bl_idname = "node.change_label"
    bl_label = "Change Label"

    label: bpy.props.StringProperty()

    def execute(self, context):
        node = context.active_node
        if node:
            node.label = self.label
        return {'FINISHED'}

addon_keymaps = []

class MATERIAL_OT_premium_feature(Operator):
    bl_idname = "material.premium_feature_info"
    bl_label = "Premium Feature"
    bl_description = "This is a premium feature"

    feature_type: StringProperty()
    engine: StringProperty()

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.label(text=f"This is a premium feature for {self.engine} converter")
        layout.label(text=f"The {self.feature_type} conversion feature requires additional module")
        layout.operator("wm.url_open", text="Get Premium Features").url = "https://www.patreon.com/c/AdamZorianBlender"

class MATERIAL_OT_install_premium_features(Operator):
    bl_idname = "material.install_premium_features"
    bl_label = "Install Premium Features"
    bl_description = "Install premium converter features"
    
    filepath: StringProperty(subtype='FILE_PATH')
    
    def execute(self, context):
        addon_path = os.path.dirname(os.path.realpath(__file__))
        
        try:
            with zipfile.ZipFile(self.filepath, 'r') as zip_ref:
                # Get list of all files in ZIP
                file_list = zip_ref.namelist()
                
                # Detect which engines are present in the ZIP
                engines_found = set()
                for file_path in file_list:
                    parts = file_path.split('/')
                    if len(parts) > 0:
                        potential_engine = parts[0].upper()
                        if potential_engine in ['OCTANE', 'VRAY', 'LUXCORE', 'CYCLES']:
                            engines_found.add(potential_engine)
                
                # If no recognized engine folders found, assume all files belong to the engine based on ZIP name
                if not engines_found:
                    zip_name = os.path.splitext(os.path.basename(self.filepath))[0].upper()
                    if zip_name in ['OCTANE', 'VRAY', 'LUXCORE', 'CYCLES']:
                        engines_found.add(zip_name)
                        
                        # Create engine directory
                        engine_path = os.path.join(addon_path, zip_name.lower())
                        if not os.path.exists(engine_path):
                            os.makedirs(engine_path)
                            
                        # Extract all files to engine directory
                        zip_ref.extractall(engine_path)
                    else:
                        self.report({'ERROR'}, "No valid engine files found in ZIP")
                        return {'CANCELLED'}
                else:
                    # Extract files for each found engine
                    zip_ref.extractall(addon_path)
                
                # Update preferences for installed engines
                prefs = context.preferences.addons[__package__].preferences
                for engine in engines_found:
                    setattr(prefs, f"{engine.lower()}_installed", True)
                    
                self.report({'INFO'}, f"Successfully installed features for: {', '.join(engines_found)}")
                return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Installation failed: {str(e)}")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class MaterialConverterPreferences(AddonPreferences):
    bl_idname = __package__

    # Installation status properties
    octane_installed: BoolProperty(default=True)
    vray_installed: BoolProperty(default=True)
    luxcore_installed: BoolProperty(default=True)
    cycles_installed: BoolProperty(default=True)

    # Auto-conversion settings
    auto_convert_images: BoolProperty(
        name="Auto-Convert Images",
        description="Automatically convert image texture nodes to render engine format when dragged into shader editor",
        default=False
    )

    octane_preferences: bpy.props.PointerProperty(type=OctanePreferences)
    vray_preferences: bpy.props.PointerProperty(type=VRayPreferences)
    luxcore_preferences: bpy.props.PointerProperty(type=LuxcorePreferences)
     # Zakładki (Octane, V-Ray, LuxCore itp.)
    active_tab: EnumProperty(
        items=[
            ('OCTANE', "Octane", "Octane render settings"),
            ('VRAY', "V-Ray", "V-Ray render settings"),
            ('LUXCORE', "LuxCore", "LuxCore render settings"),
        ],
        default='OCTANE'
    )

    def draw(self, context):
        layout = self.layout
        
        # Installation button
        box = layout.box()
        box.operator("material.install_premium_features", text="Install Premium Features")
        box.operator(MC_OT_ExportPreferences.bl_idname)
        box.operator(MC_OT_ImportPreferences.bl_idname)
        
        # Rysowanie zakładek dla każdego silnika
        row = layout.row()
        row.prop(self, "active_tab", expand=True)

        # Rysowanie preferencji dla aktywnego silnika
        if self.active_tab == 'OCTANE':
            self.octane_preferences.draw_octane_preferences(layout)
        elif self.active_tab == 'VRAY':
            self.vray_preferences.draw_vray_preferences(layout)
        elif self.active_tab == 'LUXCORE':
            self.luxcore_preferences.draw_luxcore_preferences(layout)
        
        
                
                
        
            
            
     
        

class BaseConvertOperator:
    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.active_material

    def get_module_path(self, context, engine):
        addon_path = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(addon_path, engine.lower())

    def load_converter(self, module_path, script_name):
        # Najpierw próbujemy znaleźć plik specyficzny dla silnika
        engine_specific_name = f"{script_name[:-3]}_{self.engine.lower()}.py"
        engine_specific_path = os.path.join(module_path, engine_specific_name)
        
        # Sprawdzamy, który plik istnieje i używamy odpowiedniej ścieżki
        if os.path.exists(engine_specific_path):
            script_path = engine_specific_path
            base_module_name = f"{script_name[:-3]}_{self.engine.lower()}"
        else:
            script_path = os.path.join(module_path, script_name)
            if not os.path.exists(script_path):
                return None
            base_module_name = f"{script_name[:-3]}_{self.engine.lower()}"

        if module_path not in sys.path:
            sys.path.append(module_path)

        try:
            # Reload the module if it already exists
            if base_module_name in sys.modules:
                importlib.reload(sys.modules[base_module_name])
            else:
                # Import the module with the unique name
                spec = importlib.util.spec_from_file_location(base_module_name, script_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                sys.modules[base_module_name] = module

            return sys.modules[base_module_name]
        except Exception as e:
            self.report({'ERROR'}, f"Error loading module: {str(e)}")
            return None

    def is_converter_available(self, context, engine, script_name):
        module_path = self.get_module_path(context, engine)
        engine_specific_name = f"{script_name[:-3]}_{engine.lower()}.py"
        engine_specific_path = os.path.join(module_path, engine_specific_name)
        regular_script_path = os.path.join(module_path, script_name)
        
        return os.path.exists(engine_specific_path) or os.path.exists(regular_script_path)

class MATERIAL_OT_convert(Operator, BaseConvertOperator):
    bl_idname = "material.convert"
    bl_label = "Convert Material"
    bl_description = "Convert materials"

    engine: StringProperty()
    mode: StringProperty()

    def execute(self, context):
        # Sprawdzamy najpierw plik specyficzny dla silnika
        script_base = f"convert_{self.mode}"
        engine_specific_name = f"{script_base}_{self.engine.lower()}.py"
        regular_script_name = f"{script_base}.py"
        
        if not self.is_converter_available(context, self.engine, regular_script_name):
            # Sprawdzamy premium tylko jeśli nie ma żadnego pliku
            bpy.ops.material.premium_feature_info('INVOKE_DEFAULT', 
                feature_type=f"{self.mode} materials", 
                engine=self.engine)
            return {'CANCELLED'}

        module = self.load_converter(self.get_module_path(context, self.engine), regular_script_name)
        if module and hasattr(module, f"convert_{self.mode}"):
            try:
                getattr(module, f"convert_{self.mode}")(context)
                self.report({'INFO'}, "Conversion completed successfully")
            except Exception as e:
                self.report({'ERROR'}, f"Conversion failed: {str(e)}")
        return {'FINISHED'}


def get_active_engine(context):
    """Zwraca nazwę aktywnego silnika renderowania w formacie zgodnym z naszym dodatkiem"""
    engine = context.scene.render.engine
    engine_mapping = {
        'CYCLES': 'CYCLES',
        'LUXCORE': 'LUXCORE',
        'octane': 'OCTANE',
        'VRAY_RENDER_RT': 'VRAY'
    }
    return engine_mapping.get(engine, 'CYCLES')  # Domyślnie zwraca CYCLES

def draw_converter_ui(layout, context):
    preferences = context.preferences.addons[__package__].preferences
    addon_path = os.path.dirname(os.path.realpath(__file__))
    active_engine = get_active_engine(context)

    engines = [
        ('OCTANE', 'Octane Material Converter'),  
        ('VRAY', 'V-Ray Material Converter'),  
        ('LUXCORE', 'LuxCore Material Converter'),
        ('CYCLES', 'Cycles Material Tool')
    ]

    if active_engine == 'CYCLES':
        display_engines = [engine for engine in engines if engine[0] == 'CYCLES']
    else:
        display_engines = [engine for engine in engines if engine[0] == active_engine]

    for engine, engine_display_name in display_engines:
        engine_lower = engine.lower()
        if getattr(preferences, f"{engine_lower}_installed"):
            engine_path = os.path.join(addon_path, engine_lower)
            box = layout.box()
            box.label(text=engine_display_name)
            col = box.column(align=True)

            engine_short_name = engine_display_name.split()[0]

            # Conversion buttons (if not Cycles)
            if engine != 'CYCLES':
                for mode in ["all", "selected", "active"]:
                    script_name = f"convert_{mode}_{engine_lower}.py"
                    script_exists = os.path.exists(os.path.join(engine_path, script_name))

                    row = col.row()
                    if script_exists:
                        if mode == "all":
                            op = row.operator(MATERIAL_OT_convert.bl_idname, 
                                          text=f"Convert all non-{engine_short_name} materials")
                        elif mode == "selected":
                            op = row.operator(MATERIAL_OT_convert.bl_idname, 
                                          text=f"Convert all non-{engine_short_name} materials in selected object")
                        else:
                             op = row.operator(MATERIAL_OT_convert.bl_idname, 
                                          text=f"Convert active material to {engine_short_name} ")
                    else:
                        row.alert = True
                        if mode == "all":
                            op = row.operator(MATERIAL_OT_convert.bl_idname, 
                                          text=f"Convert all non-{engine_short_name} materials")
                        elif mode == "selected":
                            op = row.operator(MATERIAL_OT_convert.bl_idname, 
                                          text=f"Convert all non-{engine_short_name} materials in selected object")
                        else:
                             op = row.operator(MATERIAL_OT_convert.bl_idname, 
                                          text=f"Convert active material to {engine_short_name} ")
                        row.alert = False

                    op.engine = engine
                    op.mode = mode
                
                col.separator()
            #Textures tools:    
            box.label(text="Texture Tools:")
            row = box.row()  # Row for buttons

            # Import Textures Button
            script_name = f"textures_{engine_lower}.py"
            script_exists = os.path.exists(os.path.join(engine_path, script_name))
            
            if script_exists:
                texture_op = row.operator(MATERIAL_OT_import_textures.bl_idname, 
                                          text=f"Import {engine_short_name} Textures")
            else:
                row.alert = True
                texture_op = row.operator(MATERIAL_OT_import_textures.bl_idname, 
                                          text=f"Import {engine_short_name} Textures")
                row.alert = False

            texture_op.engine = engine
            
            #Add Mapping Node
            script_name = f"mapping_{engine_lower}.py"
            script_exists = os.path.exists(os.path.join(engine_path, script_name))
            
            if script_exists:
                mapping_op = row.operator(MATERIAL_OT_add_mapping.bl_idname, 
                                          text=f"Add {engine_short_name} Mapping")
             
            else:
                row.alert = True
                mapping_op = row.operator(MATERIAL_OT_add_mapping.bl_idname, 
                                          text=f"Add {engine_short_name} Mapping")
                row.alert = False

            mapping_op.engine = engine

            # Auto-convert images toggle (only for Octane)
            if engine == 'OCTANE':
                row = box.row()
                row.prop(preferences, "auto_convert_images", text="Auto-Convert Images", toggle=True)
                row.operator(MATERIAL_OT_toggle_auto_convert.bl_idname,
                            text="",
                            icon='FILE_REFRESH')

            # Create Basic Material Button
            script_name = f"basic_{engine_lower}.py"
            script_exists = os.path.exists(os.path.join(engine_path, script_name))
            row = box.row()
            if script_exists:
                basic_op = row.operator(MATERIAL_OT_create_basic.bl_idname, 
                                        text=f"Create Basic {engine_short_name} Material")
            else:
                row.alert = True
                basic_op = row.operator(MATERIAL_OT_create_basic.bl_idname, 
                                        text=f"Create Basic {engine_short_name} Material")
                row.alert = False

            basic_op.engine = engine
            
            #Translucent Material:
            box.label(text="Translucent Materials:")
            row = box.row()  # Row for buttons
            if engine != 'CYCLES':

                # Create Translucent Material Button
                script_name = f"trans_{engine_lower}.py"
                script_exists = os.path.exists(os.path.join(engine_path, script_name))
               
                if script_exists:
                    trans_op = row.operator(MATERIAL_OT_create_trans.bl_idname, 
                                            text=f"Create Translucent {engine_short_name} Material")
                else:
                    row.alert = True 
                    trans_op = row.operator(MATERIAL_OT_create_trans.bl_idname, 
                                            text=f"Create Translucent {engine_short_name} Material")
                    row.alert = False

                trans_op.engine = engine

                # Metallic Materials
                box.label(text="Metallic Materials:")
                row = box.row()  
                script_name = f"metal_{engine_lower}.py"
                script_exists = os.path.exists(os.path.join(engine_path, script_name))
                if script_exists:
                    metal_op = row.operator(MATERIAL_OT_create_metal.bl_idname, 
                                            text=f"Create {engine_short_name} Metallic Material")
                else:
                    row.alert = True 
                    metal_op = row.operator(MATERIAL_OT_create_metal.bl_idname, 
                                            text=f"Create {engine_short_name} Metallic Material")
                    row.alert = False

                metal_op.engine = engine
                # Glass Materials
                box.label(text="Glass Materials:")
                row = box.row()  # Row for buttons
                
                script_name = f"glass_{engine_lower}.py"                                                                            #Standard Glass
                script_exists = os.path.exists(os.path.join(engine_path, script_name))
                if script_exists:
                    glass_op = row.operator(MATERIAL_OT_create_glass.bl_idname, 
                                            text=f"Standard")
                else:
                    row.alert = True 
                    glass_op = row.operator(MATERIAL_OT_create_glass.bl_idname, 
                                            text=f"Standard")
                    row.alert = False

                glass_op.engine = engine
                
                if engine == 'OCTANE':
                    script_name = f"glass_caustics_{engine_lower}.py"                                                                   #Caustics_Glass    
                    script_exists = os.path.exists(os.path.join(engine_path, script_name))
                    if script_exists:
                        caustics_glass_op = row.operator(MATERIAL_OT_create_caustics_glass.bl_idname, 
                                                text=f"Caustic")
                    else:
                        row.alert = True 
                        caustics_glass_op = row.operator(MATERIAL_OT_create_caustics_glass.bl_idname, 
                                                text=f"Caustic")
                        row.alert = False

                    caustics_glass_op.engine = engine
                
                script_name = f"archviz_glass_{engine_lower}.py"                                                                #Archviz Glass    
                script_exists = os.path.exists(os.path.join(engine_path, script_name))
                if script_exists:
                    archviz_glass_op = row.operator(MATERIAL_OT_create_archviz_glass.bl_idname, 
                                            text=f"Thin Glass Material")
                else:
                    row.alert = True 
                    archviz_glass_op = row.operator(MATERIAL_OT_create_archviz_glass.bl_idname,
                                            text=f"Thin Glass Material")
                    row.alert = False

                archviz_glass_op.engine = engine
                
                

                # Shader Tools
                box.label(text="Shader Tools:")
                row = box.row()  # Row for buttons
                script_name = f"remove_{engine_lower}.py" 
                script_exists = os.path.exists(os.path.join(engine_path, script_name))
                if script_exists:
                    remove_op = row.operator(MATERIAL_OT_remove_nodes_confirm.bl_idname, 
                                             text=f"Remove non {engine_short_name} Nodes")
                else:
                    row.alert = True
                    remove_op = row.operator(MATERIAL_OT_remove_nodes_confirm.bl_idname, 
                                             text=f"Remove non {engine_short_name} Nodes")
                    row.alert = False

                remove_op.engine = engine

            
           

class MATERIAL_PT_converter(Panel):
    bl_label = "Material Converter"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    def draw(self, context):
        draw_converter_ui(self.layout, context)

class NODE_PT_converter(Panel):
    bl_label = "Material Converter"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Material Converter"

    #@classmethod
    #def poll(cls, context):
    #    return context.space_data.tree_type in {'ShaderNodeTree', 'luxcore_material_nodes', 'VRayNodeTreeEditor'}

    def draw(self, context):
        draw_converter_ui(self.layout, context)
        
class MATERIAL_OT_remove_nodes_confirm(Operator, BaseConvertOperator):
    bl_idname = "material.remove_nodes_confirm"
    bl_label = "Confirm Node Removal"
    bl_description = "Confirm before removing nodes"
    
    engine: StringProperty()
    
    def execute(self, context):
        #script_name = f"remove_{self.engine.lower()}.py"  # Use engine-specific name
        script_name = f"remove.py"  # Use engine-specific name
        if not self.is_converter_available(context, self.engine, script_name):
            bpy.ops.material.premium_feature_info('INVOKE_DEFAULT', 
                feature_type="remove nodes", 
                engine=self.engine)
            return {'CANCELLED'}

        module = self.load_converter(self.get_module_path(context, self.engine), script_name)
        if module and hasattr(module, "remove_nodes"):
            try:
                module.remove_nodes(context)
                self.report({'INFO'}, "Nodes removed successfully")
            except Exception as e:
                self.report({'ERROR'}, f"Node removal failed: {str(e)}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)
        
    def draw(self, context):
        layout = self.layout
        layout.label(text="This will remove all other engine nodes from all the materials in the Scene.")
        layout.label(text="This operation cannot be undone.")
        
class MATERIAL_OT_create_basic(Operator, BaseConvertOperator):
    bl_idname = "material.create_basic"
    bl_label = "Create Basic Material"
    bl_description = "Create a basic material for the selected engine"

    engine: StringProperty()

    def execute(self, context):
        script_name = "basic.py"
        if not self.is_converter_available(context, self.engine, script_name):
            bpy.ops.material.premium_feature_info('INVOKE_DEFAULT', 
                feature_type="basic material", 
                engine=self.engine)
            return {'CANCELLED'}

        module = self.load_converter(self.get_module_path(context, self.engine), script_name)
        if module and hasattr(module, "create_basic"):
            try:
                module.create_basic(context)
                self.report({'INFO'}, "Basic material created successfully")
            except Exception as e:
                self.report({'ERROR'}, f"Basic material creation failed: {str(e)}")
        return {'FINISHED'}

class MATERIAL_OT_create_trans(Operator, BaseConvertOperator):
    bl_idname = "material.create_trans"
    bl_label = "Create Translucent Material"
    bl_description = "Create a translucent material for the selected engine"

    engine: StringProperty()

    def execute(self, context):
        script_name = "trans.py" 
        if not self.is_converter_available(context, self.engine, script_name):
            bpy.ops.material.premium_feature_info('INVOKE_DEFAULT', 
                feature_type="trans material", 
                engine=self.engine)
            return {'CANCELLED'}

        module = self.load_converter(self.get_module_path(context, self.engine), script_name)
        if module and hasattr(module, "create_trans"):
            try:
                module.create_trans(context)
                self.report({'INFO'}, "Translucent material created successfully")
            except Exception as e:
                self.report({'ERROR'}, f"Translucent material creation failed: {str(e)}")
        return {'FINISHED'}
        
class MATERIAL_OT_create_glass(Operator, BaseConvertOperator):
    bl_idname = "material.create_glass"
    bl_label = "Create Glass Material"
    bl_description = "Create a glass material for the selected engine"

    engine: StringProperty()

    def execute(self, context):
        script_name = "glass.py" 
        if not self.is_converter_available(context, self.engine, script_name):
            bpy.ops.material.premium_feature_info('INVOKE_DEFAULT', 
                feature_type="glass material", 
                engine=self.engine)
            return {'CANCELLED'}

        module = self.load_converter(self.get_module_path(context, self.engine), script_name)
        if module and hasattr(module, "create_glass"):
            try:
                module.create_trans(context)
                self.report({'INFO'}, "Glass material created successfully")
            except Exception as e:
                self.report({'ERROR'}, f"Glass material creation failed: {str(e)}")
        return {'FINISHED'}
        
class MATERIAL_OT_create_caustics_glass(Operator, BaseConvertOperator):
    bl_idname = "material.create_caustics_glass"
    bl_label = "Create Glass Material"
    bl_description = "Create a glass material for the selected engine"

    engine: StringProperty()

    def execute(self, context):
        script_name = "glass_caustics.py" 
        if not self.is_converter_available(context, self.engine, script_name):
            bpy.ops.material.premium_feature_info('INVOKE_DEFAULT', 
                feature_type="caustics glass material", 
                engine=self.engine)
            return {'CANCELLED'}

        module = self.load_converter(self.get_module_path(context, self.engine), script_name)
        if module and hasattr(module, "glass_caustics"):
            try:
                module.create_trans(context)
                self.report({'INFO'}, "Caustics Glass material created successfully")
            except Exception as e:
                self.report({'ERROR'}, f"Caustics Glass material creation failed: {str(e)}")
        return {'FINISHED'}
        
class MATERIAL_OT_create_archviz_glass(Operator, BaseConvertOperator):
    bl_idname = "material.create_archviz_glass"
    bl_label = "Create Archviz Glass Material"
    bl_description = "Create a thin glass material for the selected engine"

    engine: StringProperty()

    def execute(self, context):
        script_name = "archviz_glass.py" 
        if not self.is_converter_available(context, self.engine, script_name):
            bpy.ops.material.premium_feature_info('INVOKE_DEFAULT', 
                feature_type="Thin Glass Material", 
                engine=self.engine)
            return {'CANCELLED'}

        module = self.load_converter(self.get_module_path(context, self.engine), script_name)
        if module and hasattr(module, "create_archviz_glass"):
            try:
                module.create_trans(context)
                self.report({'INFO'}, "Archviz Glass material created successfully")
            except Exception as e:
                self.report({'ERROR'}, f"Archviz Glass material creation failed: {str(e)}")
        return {'FINISHED'}
        
class MATERIAL_OT_create_metal(Operator, BaseConvertOperator):
    bl_idname = "material.create_metal"
    bl_label = "Create Metallic Material"
    bl_description = "Create a metallic material for the selected engine"

    engine: StringProperty()

    def execute(self, context):
        script_name = "metal.py" 
        if not self.is_converter_available(context, self.engine, script_name):
            bpy.ops.material.premium_feature_info('INVOKE_DEFAULT', 
                feature_type="metal material", 
                engine=self.engine)
            return {'CANCELLED'}

        module = self.load_converter(self.get_module_path(context, self.engine), script_name)
        if module and hasattr(module, "create_metal"):
            try:
                module.create_trans(context)
                self.report({'INFO'}, "Metallic material created successfully")
            except Exception as e:
                self.report({'ERROR'}, f"Metallic material creation failed: {str(e)}")
        return {'FINISHED'}

class MATERIAL_OT_import_textures(Operator, BaseConvertOperator):
    bl_idname = "material.import_textures"
    bl_label = "Import textures"
    bl_description = "Import textures for the selected engine"

    engine: StringProperty()

    def execute(self, context):
        script_name = "textures.py"  
        if not self.is_converter_available(context, self.engine, script_name):
            bpy.ops.material.premium_feature_info('INVOKE_DEFAULT', 
                feature_type="import textures", 
                engine=self.engine)
            return {'CANCELLED'}

        module = self.load_converter(self.get_module_path(context, self.engine), script_name)
        if module and hasattr(module, "import_textures"):
            try:
                self.report({'INFO'}, f"Calling import_textures for engine {self.engine}")
                module.import_textures(context)
                self.report({'INFO'}, "Textures imported successfully")
            except Exception as e:
                self.report({'ERROR'}, f"Import textures failed: {str(e)}")
        return {'FINISHED'}

class MATERIAL_OT_add_mapping(Operator, BaseConvertOperator):
    bl_idname = "material.add_mapping"
    bl_label = "Add Mapping"
    bl_description = "Adds Mapping for the selected engine"

    engine: StringProperty()

    def execute(self, context):
        script_name = "mapping.py"
        if not self.is_converter_available(context, self.engine, script_name):
            bpy.ops.material.premium_feature_info('INVOKE_DEFAULT',
                feature_type="Add Mapping",
                engine=self.engine)
            return {'CANCELLED'}

        module = self.load_converter(self.get_module_path(context, self.engine), script_name)
        if module and hasattr(module, "add_mapping"):
            try:
                self.report({'INFO'}, f"Calling add_mapping for engine {self.engine}")
                module.add_mapping(context)
                self.report({'INFO'}, "Mapping added successfully")
            except Exception as e:
                self.report({'ERROR'}, f"Mapping failed: {str(e)}")
        return {'FINISHED'}

class MATERIAL_OT_toggle_auto_convert(Operator):
    bl_idname = "material.toggle_auto_convert"
    bl_label = "Toggle Auto-Convert Images"
    bl_description = "Enable/disable automatic conversion of image texture nodes to render engine format"

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences

        # Import the auto_convert module
        from . import scripts
        auto_convert = importlib.import_module('.scripts.auto_convert_image', package=__package__)

        # Toggle the setting
        prefs.auto_convert_images = not prefs.auto_convert_images

        # Register or unregister based on new setting
        if prefs.auto_convert_images:
            auto_convert.register()
            self.report({'INFO'}, "Auto-convert images: ENABLED")
        else:
            auto_convert.unregister()
            self.report({'INFO'}, "Auto-convert images: DISABLED")

        return {'FINISHED'}

classes = (
    MaterialConverterPreferences,
    NODE_OT_Viewport,
    MATERIAL_OT_create_archviz_glass,
    MATERIAL_OT_create_caustics_glass,
    MATERIAL_OT_create_glass,
    MATERIAL_OT_create_metal,
    MATERIAL_OT_premium_feature,
    MATERIAL_OT_install_premium_features,
    MATERIAL_OT_convert,
    MATERIAL_OT_create_basic,
    MATERIAL_OT_create_trans,
    MATERIAL_OT_import_textures,
    MATERIAL_OT_add_mapping,
    MATERIAL_OT_toggle_auto_convert,
    MATERIAL_PT_converter,
    NODE_PT_converter,
    NODE_OT_my_search_menu,
    NODE_OT_change_label,
    MATERIAL_OT_remove_nodes_confirm,
    MC_OT_ExportPreferences,
    MC_OT_ImportPreferences

)

def register():
    register_operators()

    bpy.utils.register_class(OctanePreferences)
    bpy.utils.register_class(VRayPreferences)
    bpy.utils.register_class(LuxcorePreferences)

    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        kmi = km.keymap_items.new(NODE_OT_my_search_menu.bl_idname, 'E', 'PRESS')
        kmi2 = km.keymap_items.new("node.viewport_check", 'Z', 'PRESS')
        addon_keymaps.append((km, kmi))
        addon_keymaps.append((km, kmi2))

    # Check if auto-convert should be enabled on startup
    try:
        prefs = bpy.context.preferences.addons[__package__].preferences
        if prefs.auto_convert_images:
            auto_convert = importlib.import_module('.scripts.auto_convert_image', package=__package__)
            auto_convert.register()
    except:
        # Preferences not yet available on first install
        pass

def unregister():
    # Unregister auto-convert if it's active
    try:
        auto_convert = importlib.import_module('.scripts.auto_convert_image', package=__package__)
        auto_convert.unregister()
    except:
        pass

    unregister_operators()

    bpy.utils.unregister_class(OctanePreferences)
    bpy.utils.unregister_class(VRayPreferences)
    bpy.utils.unregister_class(LuxcorePreferences)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()
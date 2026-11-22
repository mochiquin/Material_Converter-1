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

import importlib
import importlib.util
import sys
import traceback
import zipfile
from pathlib import Path

try:
    import bpy
    from bpy.props import BoolProperty, EnumProperty, StringProperty
    from bpy.types import AddonPreferences, Operator
except ImportError:  # pragma: no cover - outside Blender runtime (e.g. pytest collection)
    bpy = None

if bpy is not None:
    from .executor.addon_helpers import (
        get_addon_package_name,
        get_addon_preferences,
        load_addon_preferences_from_json,
        save_addon_preferences_to_json,
        serialize_preferences,
    )
    from .operators import register_operators, unregister_operators
    from .preferences.luxcore_preferences import LuxcorePreferences
    from .preferences.octane_preferences import OctanePreferences
    from .preferences.vray_preferences import VRayPreferences
    from .ui_panel import (
        INCREMENTAL_BULK_ENGINES,
        MATERIAL_PT_converter,
        NODE_PT_converter,
        draw_converter_ui,
        get_active_engine,
    )

    __all__ = [
        "INCREMENTAL_BULK_ENGINES",
        "draw_converter_ui",
        "get_active_engine",
        "get_addon_preferences",
        "load_addon_preferences_from_json",
        "register",
        "save_addon_preferences_to_json",
        "serialize_preferences",
        "unregister",
    ]

    class MC_OT_ExportPreferences(Operator):
        bl_idname = "mc.export_prefs"
        bl_label = "Export Addon Preferences"
        filepath: StringProperty(subtype="FILE_PATH", default="mc_settings.json")

        def execute(self, context):
            status, message = save_addon_preferences_to_json(self.filepath)
            self.report(status, message)
            return {"FINISHED"}

        def invoke(self, context, event):
            self.filepath = str(Path(bpy.path.abspath("//")) / "mc_settings.json")
            context.window_manager.fileselect_add(self)
            return {"RUNNING_MODAL"}

    class MC_OT_ImportPreferences(Operator):
        bl_idname = "mc.import_prefs"
        bl_label = "Import Addon Preferences"
        filepath: StringProperty(subtype="FILE_PATH", default="mc_settings.json")

        def execute(self, context):
            status, message = load_addon_preferences_from_json(self.filepath)
            self.report(status, message)
            return {"FINISHED"}

        def invoke(self, context, event):
            context.window_manager.fileselect_add(self)
            return {"RUNNING_MODAL"}

    def safe_import_module(addon_path: Path, engine_load: str):
        try:
            module_path = addon_path / engine_load / f"viewport_{engine_load}.py"
            if not module_path.exists():
                bpy.ops.material.premium_feature_info(
                    "INVOKE_DEFAULT",
                    feature_type="Viewport Node Preview",
                    engine=engine_load,
                )
                print(f"Module {module_path} does not exist.")
                return None

            spec = importlib.util.spec_from_file_location(f"viewport_{engine_load}", module_path)
            if spec is None or spec.loader is None:
                return None
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        except Exception as exc:
            print(f"Unexpected error importing module: {exc}")
            return None

    class NODE_OT_Viewport(Operator):
        """Set Viewport Preview for nodes"""

        bl_idname = "node.viewport_check"
        bl_label = "Set Viewport Preview for Nodes"
        bl_options = {"REGISTER", "UNDO"}

        @classmethod
        def poll(cls, context):
            return context.area.type == "NODE_EDITOR"

        def execute(self, context):
            addon_path = Path(__file__).resolve().parent
            render_engine = context.scene.render.engine
            mat = context.object.active_material

            if not mat:
                self.report({"WARNING"}, "No active material")
                return {"CANCELLED"}

            engine_mapping = {
                "CYCLES": ("Bsdf", "Cycles Output", "cycles"),
                "LUXCORE": ("LuxCoreNodeMat", "LuxCore Output", "luxcore"),
                "octane": ("Material", "Octane Output", "octane"),
                "VRAY_RENDER_RT": ("BRDF", "V-ray Output", "vray"),
            }

            if render_engine not in engine_mapping:
                self.report({"WARNING"}, f"Unsupported render engine: {render_engine}")
                return {"CANCELLED"}

            material_node, output_name, engine_load = engine_mapping[render_engine]
            nodetree = mat.luxcore.node_tree if render_engine == "LUXCORE" else mat.node_tree
            if not nodetree:
                self.report({"WARNING"}, "No Shader Node Tree")
                return {"CANCELLED"}

            material_output = [node for node in nodetree.nodes if node.label.startswith(output_name)]
            active_node = context.space_data.node_tree.nodes.active

            if active_node:
                if material_node not in active_node.bl_idname:
                    engine_module = safe_import_module(addon_path, engine_load)
                    function_name = f"Create_viewport_emission_{engine_load}"
                    if engine_module and hasattr(engine_module, function_name):
                        func = getattr(engine_module, function_name)
                        status = func(mat, active_node)
                        if status == "Success":
                            self.report({"INFO"}, f"Executed {function_name} from {engine_module}")
                        else:
                            self.report({"WARNING"}, str(status))
                    else:
                        self.report({"ERROR"}, f"Function {function_name} not found in {engine_module}")
                else:
                    if material_output:
                        nodetree.links.new(active_node.outputs[0], material_output[0].inputs[0])
                    for n_delete in list(nodetree.nodes):
                        if "Viewport" in n_delete.label:
                            nodetree.nodes.remove(n_delete)
                    self.report({"INFO"}, "Please choose a non-material node type")
            else:
                self.report({"WARNING"}, "No node selection")

            return {"FINISHED"}

    class NODE_OT_my_search_menu(Operator):
        """Change Node label"""

        bl_idname = "node.my_search_menu"
        bl_label = "Label Change Menu"

        def execute(self, context):
            return {"FINISHED"}

        def invoke(self, context, event):
            return context.window_manager.invoke_popup(self, width=200)

        def draw(self, context):
            layout = self.layout
            layout.label(text="Change Node Label")
            node = context.active_node
            if node:
                for label in (
                    "Diffuse",
                    "Specular",
                    "Transmission",
                    "IOR",
                    "Normal",
                    "Roughness",
                    "Displacement",
                    "AO",
                    "Bump",
                    "Opacity",
                ):
                    layout.operator("node.change_label", text=label).label = label
            else:
                layout.label(text="Node has been not selected, Select Node!")

    class NODE_OT_change_label(Operator):
        """Change Node Label"""

        bl_idname = "node.change_label"
        bl_label = "Change Label"

        label: StringProperty()

        def execute(self, context):
            node = context.active_node
            if node:
                node.label = self.label
            return {"FINISHED"}

    addon_keymaps: list[tuple] = []

    class MATERIAL_OT_premium_feature(Operator):
        bl_idname = "material.premium_feature_info"
        bl_label = "Premium Feature"
        bl_description = "This is a premium feature"

        feature_type: StringProperty()
        engine: StringProperty()

        def execute(self, context):
            return {"FINISHED"}

        def invoke(self, context, event):
            return context.window_manager.invoke_props_dialog(self, width=400)

        def draw(self, context):
            layout = self.layout
            layout.label(text=f"This is a premium feature for {self.engine} converter")
            layout.label(text=f"The {self.feature_type} conversion feature requires additional module")
            layout.operator(
                "wm.url_open",
                text="Get Premium Features",
            ).url = "https://www.patreon.com/c/AdamZorianBlender"

    class MATERIAL_OT_install_premium_features(Operator):
        bl_idname = "material.install_premium_features"
        bl_label = "Install Premium Features"
        bl_description = "Install premium converter features"

        filepath: StringProperty(subtype="FILE_PATH")

        def execute(self, context):
            addon_path = Path(__file__).resolve().parent
            zip_path = Path(self.filepath)
            try:
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    file_list = zip_ref.namelist()
                    engines_found: set[str] = set()
                    for file_path in file_list:
                        parts = Path(file_path).parts
                        if parts:
                            potential_engine = parts[0].upper()
                            if potential_engine in {"OCTANE", "VRAY", "LUXCORE", "CYCLES"}:
                                engines_found.add(potential_engine)

                    if not engines_found:
                        zip_name = zip_path.stem.upper()
                        if zip_name in {"OCTANE", "VRAY", "LUXCORE", "CYCLES"}:
                            engines_found.add(zip_name)
                            engine_path = addon_path / zip_name.lower()
                            engine_path.mkdir(parents=True, exist_ok=True)
                            zip_ref.extractall(engine_path)
                        else:
                            self.report({"ERROR"}, "No valid engine files found in ZIP")
                            return {"CANCELLED"}
                    else:
                        zip_ref.extractall(addon_path)

                    prefs = get_addon_preferences(context=context)
                    if prefs is not None:
                        for engine in engines_found:
                            setattr(prefs, f"{engine.lower()}_installed", True)

                    self.report({"INFO"}, f"Successfully installed features for: {', '.join(sorted(engines_found))}")
                    return {"FINISHED"}
            except Exception as exc:
                self.report({"ERROR"}, f"Installation failed: {exc}")
                return {"CANCELLED"}

        def invoke(self, context, event):
            context.window_manager.fileselect_add(self)
            return {"RUNNING_MODAL"}

    class MaterialConverterPreferences(AddonPreferences):
        bl_idname = __package__

        octane_installed: BoolProperty(default=True)
        vray_installed: BoolProperty(default=True)
        luxcore_installed: BoolProperty(default=True)
        cycles_installed: BoolProperty(default=True)

        auto_convert_images: BoolProperty(
            name="Auto-Convert Images",
            description="Automatically convert image texture nodes to render engine format when dragged into shader editor",
            default=False,
        )

        octane_preferences: bpy.props.PointerProperty(type=OctanePreferences)
        vray_preferences: bpy.props.PointerProperty(type=VRayPreferences)
        luxcore_preferences: bpy.props.PointerProperty(type=LuxcorePreferences)

        active_tab: EnumProperty(
            items=[
                ("OCTANE", "Octane", "Octane render settings"),
                ("VRAY", "V-Ray", "V-Ray render settings"),
                ("LUXCORE", "LuxCore", "LuxCore render settings"),
            ],
            default="OCTANE",
        )

        def draw(self, context):
            layout = self.layout
            box = layout.box()
            box.operator("material.install_premium_features", text="Install Premium Features")
            box.operator(MC_OT_ExportPreferences.bl_idname)
            box.operator(MC_OT_ImportPreferences.bl_idname)

            row = layout.row()
            row.prop(self, "active_tab", expand=True)
            if self.active_tab == "OCTANE":
                self.octane_preferences.draw_octane_preferences(layout)
            elif self.active_tab == "VRAY":
                self.vray_preferences.draw_vray_preferences(layout)
            elif self.active_tab == "LUXCORE":
                self.luxcore_preferences.draw_luxcore_preferences(layout)

    class BaseConvertOperator:
        @classmethod
        def poll(cls, context):
            return context.active_object and context.active_object.active_material

        def get_module_path(self, context, engine: str) -> Path:
            addon_path = Path(__file__).resolve().parent
            return addon_path / engine.lower()

        def load_converter(self, module_path: Path, script_name: str):
            stem = Path(script_name).stem
            engine_lower = self.engine.lower()
            engine_specific_path = module_path / f"{stem}_{engine_lower}.py"
            regular_path = module_path / script_name

            if engine_specific_path.exists():
                script_path = engine_specific_path
                module_stem = f"{stem}_{engine_lower}"
            elif regular_path.exists():
                script_path = regular_path
                module_stem = stem
            else:
                return None

            pkg_root = get_addon_package_name()
            qualified_name = f"{pkg_root}.{engine_lower}.{module_stem}"
            try:
                if qualified_name in sys.modules:
                    return importlib.reload(sys.modules[qualified_name])
                if (module_path / "__init__.py").exists():
                    return importlib.import_module(qualified_name)

                if str(module_path) not in sys.path:
                    sys.path.append(str(module_path))
                if module_stem in sys.modules:
                    return importlib.reload(sys.modules[module_stem])
                spec = importlib.util.spec_from_file_location(module_stem, script_path)
                if spec is None or spec.loader is None:
                    return None
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_stem] = module
                spec.loader.exec_module(module)
                return module
            except Exception as exc:
                self.report({"ERROR"}, f"Error loading module: {exc}")
                return None

        def is_converter_available(self, context, engine: str, script_name: str) -> bool:
            module_path = self.get_module_path(context, engine)
            stem = Path(script_name).stem
            engine_specific_path = module_path / f"{stem}_{engine.lower()}.py"
            regular_script_path = module_path / script_name
            return engine_specific_path.exists() or regular_script_path.exists()

    class MATERIAL_OT_convert(Operator, BaseConvertOperator):
        bl_idname = "material.convert"
        bl_label = "Convert Material"
        bl_description = "Convert materials"

        engine: StringProperty()
        mode: StringProperty()

        def execute(self, context):
            regular_script_name = f"convert_{self.mode}.py"
            if not self.is_converter_available(context, self.engine, regular_script_name):
                bpy.ops.material.premium_feature_info(
                    "INVOKE_DEFAULT",
                    feature_type=f"{self.mode} materials",
                    engine=self.engine,
                )
                return {"CANCELLED"}

            module = self.load_converter(self.get_module_path(context, self.engine), regular_script_name)
            fn_name = f"convert_{self.mode}"
            if module and hasattr(module, fn_name):
                try:
                    getattr(module, fn_name)(context)
                    self.report({"INFO"}, "Conversion completed successfully")
                except Exception as exc:
                    self.report({"ERROR"}, f"Conversion failed: {exc}")
            return {"FINISHED"}

    class MATERIAL_OT_convert_all(Operator, BaseConvertOperator):
        """Run bulk material conversion incrementally via modal timer."""

        bl_idname = "material.convert_all"
        bl_label = "Convert All Materials"
        bl_description = "Convert materials (shows progress and stays responsive on large scenes)"

        engine: StringProperty()
        batch_size = 10

        _timer = None
        _materials = None
        _index = 0
        _total = 0
        _module = None
        _convert_fn = None
        _cancelled = False

        def invoke(self, context, event):
            regular_script_name = "convert_all.py"
            if not self.is_converter_available(context, self.engine, regular_script_name):
                bpy.ops.material.premium_feature_info(
                    "INVOKE_DEFAULT",
                    feature_type="all materials",
                    engine=self.engine,
                )
                return {"CANCELLED"}

            module = self.load_converter(self.get_module_path(context, self.engine), regular_script_name)
            convert_fn = getattr(module, f"convert_material_to_{self.engine.lower()}", None) if module else None
            if not module or not hasattr(module, "get_materials_to_convert") or not convert_fn:
                self.report({"ERROR"}, f"{self.engine} does not support progress-tracked bulk conversion yet")
                return {"CANCELLED"}

            self._module = module
            self._convert_fn = convert_fn
            self._materials = module.get_materials_to_convert()
            self._total = len(self._materials)
            self._index = 0
            self._cancelled = False

            if self._total == 0:
                self.report({"INFO"}, "No materials to convert")
                return {"FINISHED"}

            wm = context.window_manager
            wm.progress_begin(0, self._total)
            self._update_status(context)
            self._timer = wm.event_timer_add(0.01, window=context.window)
            wm.modal_handler_add(self)
            return {"RUNNING_MODAL"}

        def modal(self, context, event):
            if event.type == "ESC":
                self._cancelled = True
                self._finish(context)
                return {"CANCELLED"}

            if event.type == "TIMER":
                try:
                    batch_end = min(self._index + self.batch_size, self._total)
                    for i in range(self._index, batch_end):
                        mat = self._materials[i]
                        mat_name = "<unknown>"
                        try:
                            mat_name = mat.name
                            self._convert_fn(mat)
                        except Exception as exc:
                            print(f"[Material Converter] Failed to convert '{mat_name}':")
                            traceback.print_exc()
                            self.report({"WARNING"}, f"Failed to convert '{mat_name}': {exc}")
                    self._index = batch_end
                    context.window_manager.progress_update(self._index)
                    self._update_status(context)
                except Exception as exc:
                    print("[Material Converter] Convert All aborted by an unexpected error:")
                    traceback.print_exc()
                    self.report(
                        {"ERROR"},
                        f"Conversion stopped unexpectedly after {self._index}/{self._total} materials: {exc}",
                    )
                    self._finish(context, report=False)
                    return {"CANCELLED"}

                if self._index >= self._total:
                    self._finish(context)
                    return {"FINISHED"}

            return {"PASS_THROUGH"}

        def _update_status(self, context):
            context.workspace.status_text_set(
                f"Converting materials to {self.engine}: {self._index}/{self._total} (Esc to cancel)"
            )
            screen = getattr(context, "screen", None)
            if screen:
                for area in screen.areas:
                    area.tag_redraw()

        def _finish(self, context, report: bool = True):
            wm = context.window_manager
            try:
                wm.progress_end()
            except Exception:
                pass
            if self._timer:
                wm.event_timer_remove(self._timer)
                self._timer = None
            try:
                context.workspace.status_text_set(None)
            except Exception:
                pass

            if not report:
                return
            if self._cancelled:
                self.report({"WARNING"}, f"Conversion cancelled after {self._index}/{self._total} materials")
            else:
                self.report({"INFO"}, f"Conversion completed: {self._index}/{self._total} materials converted")

    class MATERIAL_OT_remove_nodes_confirm(Operator, BaseConvertOperator):
        bl_idname = "material.remove_nodes_confirm"
        bl_label = "Confirm Node Removal"
        bl_description = "Confirm before removing nodes"

        engine: StringProperty()

        def execute(self, context):
            script_name = "remove.py"
            if not self.is_converter_available(context, self.engine, script_name):
                bpy.ops.material.premium_feature_info(
                    "INVOKE_DEFAULT",
                    feature_type="remove nodes",
                    engine=self.engine,
                )
                return {"CANCELLED"}

            module = self.load_converter(self.get_module_path(context, self.engine), script_name)
            if module and hasattr(module, "remove_nodes"):
                try:
                    module.remove_nodes(context)
                    self.report({"INFO"}, "Nodes removed successfully")
                except Exception as exc:
                    self.report({"ERROR"}, f"Node removal failed: {exc}")
            return {"FINISHED"}

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
                bpy.ops.material.premium_feature_info(
                    "INVOKE_DEFAULT",
                    feature_type="basic material",
                    engine=self.engine,
                )
                return {"CANCELLED"}

            module = self.load_converter(self.get_module_path(context, self.engine), script_name)
            if module and hasattr(module, "create_basic"):
                try:
                    module.create_basic(context)
                    self.report({"INFO"}, "Basic material created successfully")
                except Exception as exc:
                    self.report({"ERROR"}, f"Basic material creation failed: {exc}")
            return {"FINISHED"}

    class MATERIAL_OT_create_trans(Operator, BaseConvertOperator):
        bl_idname = "material.create_trans"
        bl_label = "Create Translucent Material"
        bl_description = "Create a translucent material for the selected engine"

        engine: StringProperty()

        def execute(self, context):
            script_name = "trans.py"
            if not self.is_converter_available(context, self.engine, script_name):
                bpy.ops.material.premium_feature_info(
                    "INVOKE_DEFAULT",
                    feature_type="trans material",
                    engine=self.engine,
                )
                return {"CANCELLED"}

            module = self.load_converter(self.get_module_path(context, self.engine), script_name)
            if module and hasattr(module, "create_trans"):
                try:
                    module.create_trans(context)
                    self.report({"INFO"}, "Translucent material created successfully")
                except Exception as exc:
                    self.report({"ERROR"}, f"Translucent material creation failed: {exc}")
            return {"FINISHED"}

    class MATERIAL_OT_create_glass(Operator, BaseConvertOperator):
        bl_idname = "material.create_glass"
        bl_label = "Create Glass Material"
        bl_description = "Create a glass material for the selected engine"

        engine: StringProperty()

        def execute(self, context):
            script_name = "glass.py"
            if not self.is_converter_available(context, self.engine, script_name):
                bpy.ops.material.premium_feature_info(
                    "INVOKE_DEFAULT",
                    feature_type="glass material",
                    engine=self.engine,
                )
                return {"CANCELLED"}

            module = self.load_converter(self.get_module_path(context, self.engine), script_name)
            if module and hasattr(module, "create_glass"):
                try:
                    module.create_glass(context)
                    self.report({"INFO"}, "Glass material created successfully")
                except Exception as exc:
                    self.report({"ERROR"}, f"Glass material creation failed: {exc}")
            return {"FINISHED"}

    class MATERIAL_OT_create_caustics_glass(Operator, BaseConvertOperator):
        bl_idname = "material.create_caustics_glass"
        bl_label = "Create Glass Material"
        bl_description = "Create a glass material for the selected engine"

        engine: StringProperty()

        def execute(self, context):
            script_name = "glass_caustics.py"
            if not self.is_converter_available(context, self.engine, script_name):
                bpy.ops.material.premium_feature_info(
                    "INVOKE_DEFAULT",
                    feature_type="caustics glass material",
                    engine=self.engine,
                )
                return {"CANCELLED"}

            module = self.load_converter(self.get_module_path(context, self.engine), script_name)
            if module and hasattr(module, "create_caustics_glass"):
                try:
                    module.create_caustics_glass(context)
                    self.report({"INFO"}, "Caustics Glass material created successfully")
                except Exception as exc:
                    self.report({"ERROR"}, f"Caustics Glass material creation failed: {exc}")
            return {"FINISHED"}

    class MATERIAL_OT_create_archviz_glass(Operator, BaseConvertOperator):
        bl_idname = "material.create_archviz_glass"
        bl_label = "Create Archviz Glass Material"
        bl_description = "Create a thin glass material for the selected engine"

        engine: StringProperty()

        def execute(self, context):
            script_name = "archviz_glass.py"
            if not self.is_converter_available(context, self.engine, script_name):
                bpy.ops.material.premium_feature_info(
                    "INVOKE_DEFAULT",
                    feature_type="Thin Glass Material",
                    engine=self.engine,
                )
                return {"CANCELLED"}

            module = self.load_converter(self.get_module_path(context, self.engine), script_name)
            if module and hasattr(module, "create_archviz_glass"):
                try:
                    module.create_archviz_glass(context)
                    self.report({"INFO"}, "Archviz Glass material created successfully")
                except Exception as exc:
                    self.report({"ERROR"}, f"Archviz Glass material creation failed: {exc}")
            return {"FINISHED"}

    class MATERIAL_OT_create_metal(Operator, BaseConvertOperator):
        bl_idname = "material.create_metal"
        bl_label = "Create Metallic Material"
        bl_description = "Create a metallic material for the selected engine"

        engine: StringProperty()

        def execute(self, context):
            script_name = "metal.py"
            if not self.is_converter_available(context, self.engine, script_name):
                bpy.ops.material.premium_feature_info(
                    "INVOKE_DEFAULT",
                    feature_type="metal material",
                    engine=self.engine,
                )
                return {"CANCELLED"}

            module = self.load_converter(self.get_module_path(context, self.engine), script_name)
            if module and hasattr(module, "create_metal"):
                try:
                    module.create_metal(context)
                    self.report({"INFO"}, "Metallic material created successfully")
                except Exception as exc:
                    self.report({"ERROR"}, f"Metallic material creation failed: {exc}")
            return {"FINISHED"}

    class MATERIAL_OT_import_textures(Operator, BaseConvertOperator):
        bl_idname = "material.import_textures"
        bl_label = "Import textures"
        bl_description = "Import textures for the selected engine"

        engine: StringProperty()

        def execute(self, context):
            script_name = "textures.py"
            if not self.is_converter_available(context, self.engine, script_name):
                bpy.ops.material.premium_feature_info(
                    "INVOKE_DEFAULT",
                    feature_type="import textures",
                    engine=self.engine,
                )
                return {"CANCELLED"}

            module = self.load_converter(self.get_module_path(context, self.engine), script_name)
            if module and hasattr(module, "import_textures"):
                try:
                    module.import_textures(context)
                    self.report({"INFO"}, "Textures imported successfully")
                except Exception as exc:
                    self.report({"ERROR"}, f"Import textures failed: {exc}")
            return {"FINISHED"}

    class MATERIAL_OT_add_mapping(Operator, BaseConvertOperator):
        bl_idname = "material.add_mapping"
        bl_label = "Add Mapping"
        bl_description = "Adds Mapping for the selected engine"

        engine: StringProperty()

        def execute(self, context):
            script_name = "mapping.py"
            if not self.is_converter_available(context, self.engine, script_name):
                bpy.ops.material.premium_feature_info(
                    "INVOKE_DEFAULT",
                    feature_type="Add Mapping",
                    engine=self.engine,
                )
                return {"CANCELLED"}

            module = self.load_converter(self.get_module_path(context, self.engine), script_name)
            if module and hasattr(module, "add_mapping"):
                try:
                    module.add_mapping(context)
                    self.report({"INFO"}, "Mapping added successfully")
                except Exception as exc:
                    self.report({"ERROR"}, f"Mapping failed: {exc}")
            return {"FINISHED"}

    class MATERIAL_OT_toggle_auto_convert(Operator):
        bl_idname = "material.toggle_auto_convert"
        bl_label = "Toggle Auto-Convert Images"
        bl_description = "Enable/disable automatic conversion of image texture nodes to render engine format"

        def execute(self, context):
            prefs = get_addon_preferences(context=context)
            auto_convert = importlib.import_module(".scripts.auto_convert_image", package=__package__)
            prefs.auto_convert_images = not prefs.auto_convert_images
            if prefs.auto_convert_images:
                auto_convert.register()
                self.report({"INFO"}, "Auto-convert images: ENABLED")
            else:
                auto_convert.unregister()
                self.report({"INFO"}, "Auto-convert images: DISABLED")
            return {"FINISHED"}

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
        MATERIAL_OT_convert_all,
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
        MC_OT_ImportPreferences,
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
            km = wm.keyconfigs.addon.keymaps.new(name="Node Editor", space_type="NODE_EDITOR")
            kmi = km.keymap_items.new(NODE_OT_my_search_menu.bl_idname, "E", "PRESS")
            kmi2 = km.keymap_items.new("node.viewport_check", "Z", "PRESS")
            addon_keymaps.append((km, kmi))
            addon_keymaps.append((km, kmi2))

        try:
            prefs = get_addon_preferences()
            if prefs and prefs.auto_convert_images:
                auto_convert = importlib.import_module(".scripts.auto_convert_image", package=__package__)
                auto_convert.register()
        except Exception:
            pass

    def unregister():
        try:
            auto_convert = importlib.import_module(".scripts.auto_convert_image", package=__package__)
            auto_convert.unregister()
        except Exception:
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

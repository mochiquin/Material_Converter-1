"""Blender UI Panels for Material Converter."""

from __future__ import annotations

from pathlib import Path

from bpy.types import Panel

from .executor.addon_helpers import get_addon_preferences

INCREMENTAL_BULK_ENGINES = {"OCTANE"}


def get_active_engine(context) -> str:
    """Return active render engine identifier normalized for Material Converter."""
    engine = context.scene.render.engine
    engine_mapping = {
        "CYCLES": "CYCLES",
        "LUXCORE": "LUXCORE",
        "octane": "OCTANE",
        "VRAY_RENDER_RT": "VRAY",
    }
    return engine_mapping.get(engine, "CYCLES")


def draw_converter_ui(layout, context) -> None:
    """Draw Material Converter sidebar/properties UI."""
    preferences = get_addon_preferences(context=context)
    if preferences is None:
        layout.label(text="Material Converter preferences unavailable", icon="ERROR")
        return

    addon_path = Path(__file__).resolve().parent
    active_engine = get_active_engine(context)

    engines = [
        ("OCTANE", "Octane Material Converter"),
        ("VRAY", "V-Ray Material Converter"),
        ("LUXCORE", "LuxCore Material Converter"),
        ("CYCLES", "Cycles Material Tool"),
    ]

    if active_engine == "CYCLES":
        display_engines = [engine for engine in engines if engine[0] == "CYCLES"]
    else:
        display_engines = [engine for engine in engines if engine[0] == active_engine]

    for engine, engine_display_name in display_engines:
        engine_lower = engine.lower()
        if not getattr(preferences, f"{engine_lower}_installed", False):
            continue

        engine_path = addon_path / engine_lower
        box = layout.box()
        box.label(text=engine_display_name)
        col = box.column(align=True)
        engine_short_name = engine_display_name.split()[0]

        if engine != "CYCLES":
            for mode in ("all", "selected", "active"):
                script_exists = (engine_path / f"convert_{mode}_{engine_lower}.py").exists()
                row = col.row()
                if not script_exists:
                    row.alert = True

                if mode == "all" and engine in INCREMENTAL_BULK_ENGINES:
                    op = row.operator(
                        "material.convert_all",
                        text=f"Convert all non-{engine_short_name} materials",
                    )
                    op.engine = engine
                elif mode == "all":
                    op = row.operator(
                        "material.convert",
                        text=f"Convert all non-{engine_short_name} materials",
                    )
                    op.engine = engine
                    op.mode = mode
                elif mode == "selected":
                    op = row.operator(
                        "material.convert",
                        text=f"Convert all non-{engine_short_name} materials in selected object",
                    )
                    op.engine = engine
                    op.mode = mode
                else:
                    op = row.operator(
                        "material.convert",
                        text=f"Convert active material to {engine_short_name} ",
                    )
                    op.engine = engine
                    op.mode = mode

                if not script_exists:
                    row.alert = False
            col.separator()

        box.label(text="Texture Tools:")
        row = box.row()
        if not (engine_path / f"textures_{engine_lower}.py").exists():
            row.alert = True
        texture_op = row.operator("material.import_textures", text=f"Import {engine_short_name} Textures")
        row.alert = False
        texture_op.engine = engine

        if not (engine_path / f"mapping_{engine_lower}.py").exists():
            row.alert = True
        mapping_op = row.operator("material.add_mapping", text=f"Add {engine_short_name} Mapping")
        row.alert = False
        mapping_op.engine = engine

        if engine == "OCTANE":
            row = box.row()
            row.prop(preferences, "auto_convert_images", text="Auto-Convert Images", toggle=True)
            row.operator("material.toggle_auto_convert", text="", icon="FILE_REFRESH")

        row = box.row()
        if not (engine_path / f"basic_{engine_lower}.py").exists():
            row.alert = True
        basic_op = row.operator("material.create_basic", text=f"Create Basic {engine_short_name} Material")
        row.alert = False
        basic_op.engine = engine

        box.label(text="Translucent Materials:")
        row = box.row()
        if engine != "CYCLES":
            if not (engine_path / f"trans_{engine_lower}.py").exists():
                row.alert = True
            trans_op = row.operator(
                "material.create_trans",
                text=f"Create Translucent {engine_short_name} Material",
            )
            row.alert = False
            trans_op.engine = engine

            box.label(text="Metallic Materials:")
            row = box.row()
            if not (engine_path / f"metal_{engine_lower}.py").exists():
                row.alert = True
            metal_op = row.operator(
                "material.create_metal",
                text=f"Create {engine_short_name} Metallic Material",
            )
            row.alert = False
            metal_op.engine = engine

            box.label(text="Glass Materials:")
            row = box.row()
            if not (engine_path / f"glass_{engine_lower}.py").exists():
                row.alert = True
            glass_op = row.operator("material.create_glass", text="Standard")
            row.alert = False
            glass_op.engine = engine

            if engine == "OCTANE":
                if not (engine_path / f"glass_caustics_{engine_lower}.py").exists():
                    row.alert = True
                caustics_glass_op = row.operator("material.create_caustics_glass", text="Caustic")
                row.alert = False
                caustics_glass_op.engine = engine

            if not (engine_path / f"archviz_glass_{engine_lower}.py").exists():
                row.alert = True
            archviz_glass_op = row.operator("material.create_archviz_glass", text="Thin Glass Material")
            row.alert = False
            archviz_glass_op.engine = engine

            box.label(text="Shader Tools:")
            row = box.row()
            if not (engine_path / f"remove_{engine_lower}.py").exists():
                row.alert = True
            remove_op = row.operator(
                "material.remove_nodes_confirm",
                text=f"Remove non {engine_short_name} Nodes",
            )
            row.alert = False
            remove_op.engine = engine


class MATERIAL_PT_converter(Panel):
    bl_label = "Material Converter"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    def draw(self, context) -> None:
        draw_converter_ui(self.layout, context)


class NODE_PT_converter(Panel):
    bl_label = "Material Converter"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Material Converter"

    def draw(self, context) -> None:
        draw_converter_ui(self.layout, context)

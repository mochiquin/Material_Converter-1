"""Operator for bulk importing image textures into shader nodes."""

from __future__ import annotations

from pathlib import Path

import bpy
from bpy.props import CollectionProperty, StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

from ..core.texture_classifier import classify_texture_filename


class ImportImagesToShaderNodes(Operator, ImportHelper):
    bl_idname = "shader.import_images_to_shadernodes"
    bl_label = "Import Images to Shader Nodes"

    files: CollectionProperty(type=bpy.types.PropertyGroup)
    directory: StringProperty()

    def execute(self, context):
        if not self.files or not self.directory:
            return {"RUNNING_MODAL"}
        material = context.object.active_material
        if not material:
            self.report({"ERROR"}, "No active material found on the selected object.")
            return {"CANCELLED"}

        engine = context.scene.render.engine
        node_type = "ShaderNodeTexImage"
        mapping_node_type = "ShaderNodeMapping"
        gamma_non_color: str | float = "Non-Color"
        gamma_srgb: str | float = "sRGB"
        input_idx = 0
        x_offset = 0
        y_offset = 0

        if engine == "LUXCORE":
            material_name = material.name
            color = list(material.diffuse_color[:4])
            if not material.luxcore.node_tree:
                material.luxcore.node_tree = bpy.data.node_groups.new(
                    name=material_name,
                    type="luxcore_material_nodes",
                )
                material.luxcore.use_cycles_nodes = False
                material.luxcore.auto_vp_color = False
                material.diffuse_color = tuple(color)
                material.luxcore.node_tree.nodes.new("LuxCoreNodeTexMapping2D")
        elif not material.use_nodes:
            material.use_nodes = True

        if engine == "octane":
            input_idx = 5
            gamma_non_color = 1
            gamma_srgb = 2.2
            mapping_node_type = "Octane3DTransformation"
            node_type = "OctaneRGBImage"
            x_offset = 1650
        elif engine == "LUXCORE":
            mapping_node_type = "LuxCoreNodeTexMapping2D"
            gamma_non_color = 1
            gamma_srgb = 2.2
            input_idx = 0
            node_type = "LuxCoreNodeTexImagemap"
        elif engine == "VRAY_RENDER_RT":
            input_idx = 0
            mapping_node_type = "VRayNodeUVWMapping"
            node_type = "VRayNodeMetaImageTexture"
            y_offset = 1650

        base_location = 0
        x_base = -200
        node_tree = material.luxcore.node_tree if engine == "LUXCORE" else material.node_tree
        if not node_tree:
            self.report({"ERROR"}, f"No compatible node tree found for the {engine} engine.")
            return {"CANCELLED"}

        nodes = node_tree.nodes
        links = node_tree.links

        existing_textures = [node for node in nodes if node.bl_idname == node_type]
        if existing_textures:
            self.report({"INFO"}, "Material already has texture nodes for the current engine. Skipping")
            return {"CANCELLED"}

        existing_mapping = [node for node in nodes if node.bl_idname == mapping_node_type]
        existing_uv = [node for node in nodes if node.bl_idname == "ShaderNodeUVMap"]

        if existing_mapping:
            mapping_node = existing_mapping[0]
        else:
            mapping_node = nodes.new(type=mapping_node_type)
            mapping_node.location = (x_base - 600 + x_offset, base_location - y_offset)
            if engine == "CYCLES":
                uv_node = existing_uv[0] if existing_uv else nodes.new("ShaderNodeUVMap")
                uv_node.label = "UV Map"
                uv_node.location = (mapping_node.location[0] - 300, mapping_node.location[1])
                links.new(uv_node.outputs[0], mapping_node.inputs[0])

        directory_path = Path(self.directory)
        for i, file in enumerate(self.files):
            filepath = directory_path / file.name
            image = bpy.data.images.load(str(filepath), check_existing=True)
            image_texture_node = nodes.new(type=node_type)

            classification = classify_texture_filename(file.name)
            image_colorspace = gamma_srgb if classification.is_srgb else gamma_non_color
            node_label = classification.category

            if engine == "VRAY_RENDER_RT":
                texture_name_vray = image_texture_node.texture_name
                for tx in bpy.data.textures:
                    if tx.name == texture_name_vray:
                        tx.image = image
                        break
            else:
                image_texture_node.image = image
                if engine == "CYCLES":
                    image.colorspace_settings.name = str(image_colorspace)
                elif engine == "octane":
                    image_texture_node.inputs[2].default_value = float(image_colorspace)
                    if classification.invert_gloss:
                        image_texture_node.inputs[3].default_value = True
                elif engine == "LUXCORE":
                    image_texture_node.gamma = float(image_colorspace)

            image_texture_node.label = node_label if node_label else "Diffuse"
            if "Normal" in image_texture_node.label and engine == "LUXCORE":
                image_texture_node.is_normal_map = True
            if "Roughness" in image_texture_node.label and engine == "VRAY_RENDER_RT":
                image_texture_node.TexBitmap["invert"] = True

            image_texture_node.location = (x_base + x_offset, base_location - y_offset - i * 300)
            links.new(mapping_node.outputs[0], image_texture_node.inputs[input_idx])

        self.report({"INFO"}, "Images successfully imported.")
        return {"FINISHED"}


def register() -> None:
    bpy.utils.register_class(ImportImagesToShaderNodes)


def unregister() -> None:
    bpy.utils.unregister_class(ImportImagesToShaderNodes)

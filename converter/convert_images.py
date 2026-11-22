"""Convert Cycles ShaderNodeTexImage nodes to target render engine image nodes."""

from __future__ import annotations

import bpy

from ..core.texture_classifier import infer_octane_gamma, remap_label


def Convert_image_node(Cycles_Images, mat) -> None:
    """Convert a Cycles ShaderNodeTexImage node into an engine-native image node."""
    render_engine = bpy.context.scene.render.engine

    if render_engine == "octane":
        node_image = "OctaneRGBImage"
        nodes = mat.node_tree.nodes
        engine_image_name = "RGB image"
        gamma_input = "Legacy gamma"
        offset_x, offset_y = 1650, 0
    elif render_engine == "VRAY_RENDER_RT":
        node_image = "VRayNodeMetaImageTexture"
        engine_image_name = "V-Ray Bitmap"
        nodes = mat.node_tree.nodes
        offset_x, offset_y = 0, -1650
    elif render_engine == "LUXCORE":
        engine_image_name = "Imagemap"
        node_image = "LuxCoreNodeTexImagemap"
        nodes = mat.luxcore.node_tree.nodes
        offset_x, offset_y = 0, 0
    else:
        return

    engine_image_node = None
    engine_image_node_name = Cycles_Images.name.replace("Image Texture", engine_image_name)
    for n in nodes:
        if n.bl_idname == node_image and n.name == engine_image_node_name:
            engine_image_node = n
            break
    if not engine_image_node:
        engine_image_node = nodes.new(node_image)
        engine_image_node.name = engine_image_node_name

    engine_image_node.label = remap_label(Cycles_Images.label)
    engine_image_node.location = (Cycles_Images.location[0] + offset_x, Cycles_Images.location[1] + offset_y)
    engine_image_node.hide = Cycles_Images.hide

    if not getattr(Cycles_Images, "image", None):
        return

    colorspace = Cycles_Images.image.colorspace_settings.name
    gamma_val = infer_octane_gamma(colorspace)

    if render_engine == "LUXCORE":
        engine_image_node.image = Cycles_Images.image
        engine_image_node.gamma = int(gamma_val) if gamma_val == 1.0 else gamma_val
    elif render_engine == "octane":
        engine_image_node.image = Cycles_Images.image
        engine_image_node.inputs[gamma_input].default_value = gamma_val
    else:
        new_texture = bpy.data.images.get(Cycles_Images.image.name)
        if new_texture and hasattr(engine_image_node, "texture") and engine_image_node.texture:
            engine_image_node.texture.image = new_texture
            engine_image_node.BitmapBuffer.transfer_function = "1"
            engine_image_node.BitmapBuffer.gamma = 1 if gamma_val == 1.0 else 2.2

"""Auto-convert Image Texture nodes to OctaneRGBImage when dragged into Shader Editor."""

from __future__ import annotations

import bpy
from bpy.app.handlers import persistent

from ..core.texture_classifier import detect_auto_connect_target, infer_octane_gamma

# Track processed nodes to avoid infinite loops
processed_nodes: set[int] = set()


def detect_texture_type(image_name: str | None) -> dict[str, str | int] | None:
    """Detect target Octane Universal Material socket from image filename."""
    if not image_name:
        return None
    target = detect_auto_connect_target(image_name)
    if target is None:
        return None
    input_name, input_index = target
    return {"input_name": input_name, "input_index": input_index}


def auto_connect_to_material(octane_image, node_tree, image_name: str) -> None:
    """Auto-connect Octane image to first Octane material based on filename."""
    texture_type = detect_texture_type(image_name)
    if not texture_type:
        print(f"    -> No keyword found in '{image_name}', skipping auto-connect")
        return

    octane_material = next(
        (
            node
            for node in node_tree.nodes
            if node.bl_idname in ("OctaneUniversalMaterial", "OctaneStandardSurfaceMaterial")
        ),
        None,
    )
    if not octane_material:
        print("    -> No Octane material found, skipping auto-connect")
        return

    try:
        node_tree.links.new(octane_image.outputs[0], octane_material.inputs[texture_type["input_index"]])
        print(f"    Connected: {octane_image.name} -> {octane_material.name}.{texture_type['input_name']}")
    except Exception as exc:
        print(f"    Failed to connect: {exc}")


@persistent
def auto_convert_image_nodes(scene, depsgraph) -> None:
    """Automatically convert ShaderNodeTexImage to OctaneRGBImage on creation."""
    if scene.render.engine != "octane":
        return
    if bpy.app.driver_namespace.get("mc_converting"):
        return

    for material in bpy.data.materials:
        if not material.use_nodes or not material.node_tree:
            continue

        node_tree = material.node_tree
        image_nodes = [node for node in node_tree.nodes if node.bl_idname == "ShaderNodeTexImage"]

        for cycles_image in image_nodes:
            node_id = cycles_image.as_pointer()
            if node_id in processed_nodes:
                continue

            octane_image = node_tree.nodes.new("OctaneRGBImage")
            octane_image.location = (cycles_image.location[0], cycles_image.location[1] - 300)
            octane_image.name = f"{cycles_image.name}_Octane"
            octane_image.label = cycles_image.label

            if getattr(cycles_image, "image", None):
                octane_image.image = cycles_image.image
                octane_image.inputs[2].default_value = infer_octane_gamma(
                    cycles_image.image.colorspace_settings.name,
                    cycles_image.image.name,
                    check_filename_keywords=True,
                )

            for output in cycles_image.outputs:
                if output.is_linked:
                    links_to_recreate = [link.to_socket for link in output.links]
                    for to_socket in links_to_recreate:
                        node_tree.links.remove(output.links[0])
                        if output.name == "Alpha":
                            node_tree.links.new(octane_image.outputs[1], to_socket)
                        else:
                            node_tree.links.new(octane_image.outputs[0], to_socket)

            for input_socket in cycles_image.inputs:
                if input_socket.is_linked:
                    link = input_socket.links[0]
                    from_socket = link.from_socket
                    node_tree.links.remove(link)
                    if input_socket.name == "Vector":
                        node_tree.links.new(from_socket, octane_image.inputs[5])

            processed_nodes.add(node_id)

            if getattr(cycles_image, "image", None):
                auto_connect_to_material(octane_image, node_tree, cycles_image.image.name)


def register() -> None:
    """Register the auto-conversion handler."""
    if auto_convert_image_nodes not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(auto_convert_image_nodes)
    print("Auto-convert image nodes: ENABLED")


def unregister() -> None:
    """Unregister the auto-conversion handler."""
    if auto_convert_image_nodes in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(auto_convert_image_nodes)
    processed_nodes.clear()
    print("Auto-convert image nodes: DISABLED")

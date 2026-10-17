"""
Auto-convert Image Texture nodes to render engine format
Automatically converts ShaderNodeTexImage to OctaneRGBImage when using Octane render engine
Also auto-connects images to material based on filename keywords
"""

import bpy
from bpy.app.handlers import persistent

# Track processed nodes to avoid infinite loops
processed_nodes = set()

# Keyword mapping for auto-connection (KISS principle - simple and direct)
KEYWORD_MAPPING = {
    'diffuse': {'input_name': 'Diffuse', 'input_index': 5},
    'albedo': {'input_name': 'Diffuse', 'input_index': 5},
    'basecolor': {'input_name': 'Diffuse', 'input_index': 5},
    'base': {'input_name': 'Diffuse', 'input_index': 5},
    'color': {'input_name': 'Diffuse', 'input_index': 5},

    'normal': {'input_name': 'Normal', 'input_index': 24},
    'nrm': {'input_name': 'Normal', 'input_index': 24},
    'norm': {'input_name': 'Normal', 'input_index': 24},

    'rough': {'input_name': 'Roughness', 'input_index': 13},
    'roughness': {'input_name': 'Roughness', 'input_index': 13},

    'metal': {'input_name': 'Metallic', 'input_index': 7},
    'metallic': {'input_name': 'Metallic', 'input_index': 7},
    'metalness': {'input_name': 'Metallic', 'input_index': 7},

    'bump': {'input_name': 'Bump', 'input_index': 25},
    'height': {'input_name': 'Bump', 'input_index': 25},

    'opacity': {'input_name': 'Opacity', 'input_index': 43},
    'alpha': {'input_name': 'Opacity', 'input_index': 43},

    'spec': {'input_name': 'Specular', 'input_index': 10},
    'specular': {'input_name': 'Specular', 'input_index': 10},
}

def detect_texture_type(image_name):
    """
    Detect texture type from image filename
    KISS: Simple keyword matching in filename
    """
    if not image_name:
        return None

    name_lower = image_name.lower()

    # Check each keyword - return first match
    for keyword, mapping in KEYWORD_MAPPING.items():
        if keyword in name_lower:
            return mapping

    return None


def auto_connect_to_material(octane_image, node_tree, image_name):
    """
    Auto-connect Octane image to material based on filename
    KISS: Find first Octane material, connect directly (no extra nodes)
    """
    # Detect texture type from filename
    texture_type = detect_texture_type(image_name)
    if not texture_type:
        print(f"    → No keyword found in '{image_name}', skipping auto-connect")
        return

    print(f"    → Detected type: {texture_type['input_name']} from filename '{image_name}'")

    # Find first Octane material node
    octane_material = None
    for node in node_tree.nodes:
        if node.bl_idname in ("OctaneUniversalMaterial", "OctaneStandardSurfaceMaterial"):
            octane_material = node
            break

    if not octane_material:
        print(f"    → No Octane material found, skipping auto-connect")
        return

    print(f"    → Found Octane material: {octane_material.name}")

    # Direct connection: Image → Material (KISS - all textures connect directly)
    try:
        node_tree.links.new(octane_image.outputs[0], octane_material.inputs[texture_type['input_index']])
        print(f"    ✓ Connected: {octane_image.name} → {octane_material.name}.{texture_type['input_name']}")
    except Exception as e:
        print(f"    ✗ Failed to connect: {e}")


@persistent
def auto_convert_image_nodes(scene, depsgraph):
    """
    Automatically convert ShaderNodeTexImage to engine-specific format
    when a new image texture node is added
    """
    # Only run if render engine is Octane
    if scene.render.engine != 'octane':
        return

    # Material conversion in progress: it creates lots of nodes, and this handler
    # would rescan every material after each one (and add duplicate image nodes).
    if bpy.app.driver_namespace.get("mc_converting"):
        return

    # Check all materials for new image texture nodes
    for material in bpy.data.materials:
        if not material.use_nodes or not material.node_tree:
            continue

        node_tree = material.node_tree

        # Find all ShaderNodeTexImage nodes
        image_nodes = [node for node in node_tree.nodes if node.bl_idname == "ShaderNodeTexImage"]

        for cycles_image in image_nodes:
            # Skip if already processed
            node_id = id(cycles_image)
            if node_id in processed_nodes:
                continue

            print(f"=== Auto-converting image node: {cycles_image.name} in material: {material.name} ===")

            # Create Octane RGB Image node
            octane_image = node_tree.nodes.new("OctaneRGBImage")
            octane_image.location = (cycles_image.location[0], cycles_image.location[1] - 300)
            octane_image.name = cycles_image.name + "_Octane"
            octane_image.label = cycles_image.label

            # Copy image reference
            if hasattr(cycles_image, 'image') and cycles_image.image:
                octane_image.image = cycles_image.image

                # Set gamma based on color space
                # Linear images should have gamma = 1.0, sRGB images = 2.2
                keywords = ["normal", "gloss", "reflec", "rough", "opacity", "height", "nrm", "bump", "displacement"]

                if cycles_image.image.colorspace_settings.name == 'Non-Color':
                    octane_image.inputs[2].default_value = 1.0  # Linear gamma
                    print(f"  → Set gamma to 1.0 (Linear) for {cycles_image.image.name}")
                elif any(keyword in cycles_image.image.name.lower() for keyword in keywords):
                    octane_image.inputs[2].default_value = 1.0  # Linear gamma for maps
                    print(f"  → Set gamma to 1.0 (Linear) based on name for {cycles_image.image.name}")
                else:
                    octane_image.inputs[2].default_value = 2.2  # sRGB gamma
                    print(f"  → Set gamma to 2.2 (sRGB) for {cycles_image.image.name}")

            # Redirect all output connections from Cycles to Octane
            for output in cycles_image.outputs:
                if output.is_linked:
                    # Get all connections
                    links_to_recreate = []
                    for link in output.links:
                        links_to_recreate.append((link.to_socket, link.to_node))

                    # Reconnect to Octane node
                    for to_socket, to_node in links_to_recreate:
                        # Remove old link
                        node_tree.links.remove(output.links[0])

                        # Create new link from Octane node
                        if output.name == "Alpha":
                            # Alpha output
                            node_tree.links.new(octane_image.outputs[1], to_socket)
                        else:
                            # Color output (default)
                            node_tree.links.new(octane_image.outputs[0], to_socket)

                    print(f"  → Redirected {len(links_to_recreate)} connections to Octane node")

            # Redirect all input connections from Cycles to Octane
            for i, input_socket in enumerate(cycles_image.inputs):
                if input_socket.is_linked:
                    link = input_socket.links[0]
                    from_socket = link.from_socket

                    # Remove old link
                    node_tree.links.remove(link)

                    # Connect to Octane node (Vector input is index 5)
                    if input_socket.name == "Vector":
                        node_tree.links.new(from_socket, octane_image.inputs[5])
                        print(f"  → Reconnected Vector input to Octane node")

            # Mark as processed
            processed_nodes.add(node_id)

            # Auto-connect to material based on filename (KISS principle)
            if hasattr(cycles_image, 'image') and cycles_image.image:
                print(f"  → Attempting auto-connect for image: {cycles_image.image.name}")
                auto_connect_to_material(octane_image, node_tree, cycles_image.image.name)
            else:
                print(f"  ! No image attached to node, skipping auto-connect")

            # Optionally remove the Cycles image node (or hide it)
            # Uncomment the following line to auto-remove:
            # node_tree.nodes.remove(cycles_image)

            print(f"  ✓ Created Octane image node: {octane_image.name}")


def register():
    """Register the auto-conversion handler"""
    if auto_convert_image_nodes not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(auto_convert_image_nodes)
    print("Auto-convert image nodes: ENABLED")


def unregister():
    """Unregister the auto-conversion handler"""
    if auto_convert_image_nodes in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(auto_convert_image_nodes)
    processed_nodes.clear()
    print("Auto-convert image nodes: DISABLED")


if __name__ == "__main__":
    register()

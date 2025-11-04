import bpy
import math
import sys
import os

# Import
script_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if script_folder not in sys.path:
    sys.path.append(script_folder)


from connect_nodes import (connect_to_closest_luxcore_group_node, label_texture_nodes,Connect_To_Material)
from premade import Add_Mapping_Node

preferences = bpy.context.preferences.addons["Material_Converter 1"].preferences.luxcore_preferences
Render_Engine = bpy.context.scene.render.engine

if not Render_Engine == "LUXCORE":
    bpy.context.scene.view_settings.view_transform = 'AgX'
    bpy.context.scene.view_settings.look = 'None'
    bpy.context.scene.render.engine = "LUXCORE"

    current_workspace = bpy.context.workspace
    for screen in current_workspace.screens:
        for area in screen.areas:
            if area.type == 'NODE_EDITOR' and not area.ui_type in ["GeometryNodeTree", "CompositorNodeTree"]:
                area.ui_type = 'luxcore_material_nodes'


def create_LuxCore_archviz_Glass_material():
    
    def calculate_distance(node_location, material_location):
        return math.sqrt(
            (node_location[0] - material_location[0])**2 +
            (node_location[1] - material_location[1])**2
        )
    
    material_names_to_remove = [
        "LuxCoreNodeMatMatte",
        "LuxCoreNodeMatMix",
        "LuxCoreNodeMatMatteTranslucent",
        "LuxCoreNodeMatMetal",
        "LuxCoreNodeMatDisney",
        
        "LuxCoreNodeMatGlossyTranslucent",
        "LuxCoreNodeMatMirror",
        "LuxCoreNodeMatGlossy2",
        
        "LuxCoreNodeMatGlossyCoating",
        
        "LuxCoreNodeMatNull",
        "LuxCoreNodeMatCarpaint",
        "LuxCoreNodeMatCloth",
        "LuxCoreNodeMatVelvet",
        "LuxCoreNodeMatTwoSided",
        "LuxCoreNodeMatFrontBackOpacity",
    ]
        
    nodes = mat.luxcore.node_tree.nodes
    links = mat.luxcore.node_tree.links
    
    Material_output = [node for node in nodes if node.bl_idname.startswith("LuxCoreNodeMatOutput")]
    material_node = [node for node in nodes if node.bl_idname.startswith("LuxCoreNodeMatGlass")]
    Luxcore_Images_nodes = [node for node in nodes if node.bl_idname.startswith("LuxCoreNodeTexImagemap")]
    Transmission_texture = [node for node in Luxcore_Images_nodes if "Transmission" in node.label]
    Transmission_help = [node for node in nodes if node.bl_idname.startswith("LuxCoreNodeTexHSV") and "Transmission help" in node.label]
    Diffuse_texture = [node for node in Luxcore_Images_nodes if any (z in node.label for z in ["Diffuse", "COL"])]
    AO_texture = [node for node in Luxcore_Images_nodes if "AO" in node.label]
    AO_node = [node for node in nodes if node.bl_idname.startswith("LuxCoreNodeTexColorMix") and "AO" in node.label]
    
    
    Diffuse_color =[]
    Roughness_value = []
    Specular_value = []
    
    Diffues_names = {"Diffuse Color", "Color", "Base Color"}
    Specular_mapping = {"Specular Color", "Wrap Specular Color"}
    for n in nodes:
        if n.bl_idname in material_names_to_remove:
            for input in n.inputs:
                if input.name in Diffues_names: 
            
                    Diffuse_color.append(input.default_value[0])  # R
                    Diffuse_color.append(input.default_value[1])  # G
                    Diffuse_color.append(input.default_value[2])  # B
                elif input.name == 'Roughness':
                    if input.bl_idname != "LuxCoreSocketMatEmission":
                        roughness_value = input.default_value
                        Roughness_value.append(roughness_value)
                elif input.name == "Specular":
                    specular_value = input.default_value
                    Specular_value.append(specular_value)
                elif input.name in Specular_mapping:
                    specular_value = input.default_value[0]
                    Specular_value.append(specular_value)
                  
                
            nodes.remove(n)
    
    texture_node = None 
    for n in nodes:
        if n.bl_idname == ("LuxCoreNodeTexImagemap"):

            texture_node = n
            break
    #Deleting additional nodes:
    for n in nodes:
        if any(z in n.label for z in ["Viewport", "help"]):
            nodes.remove(n)
       
    

    if Material_output:
        Material_output = Material_output[0]
    else:
        Material_output = nodes.new("LuxCoreNodeMatOutput")
        Material_output.label = "LuxCore Output"
    Material = None 

    if material_node:
        Material = material_node[0]
        Material.label = "Material"
        
            
        
    else:
        Material = nodes.new("LuxCoreNodeMatGlass")
        Material.label = "Material"
    Material.architectural = True
    Material.use_thinfilmcoating = False
                
        
    if len(Material.outputs) > 0:
      links.new(Material.outputs[0], Material_output.inputs[0])
    else:
      Material.outputs.new("LuxCoreSocketMaterial", "Material", identifier = "Material")
      links.new(Material.outputs[0], Material_output.inputs[0])
    
    
    
    if Diffuse_color:
        
        Material.inputs["Transmission Color"].default_value = Diffuse_color[:3]
    
    if Roughness_value:
        Material.rough = True
        for input in Material.inputs:
            if input.bl_idname == "LuxCoreSocketRoughness":
                input.default_value = Roughness_value[0]
        Material.rough = False
        
    Material.location = (Material_output.location[0]-250, Material_output.location[1] )
    
    Diffuse_node = min(
        [node for node in nodes if any(z in node.label for z in {"Diffuse", "COL"})],
        key=lambda node: calculate_distance(node.location, Material.location),
        default=None
    )
    
    if Diffuse_node:
        #Diffuse_texture = Diffuse_texture[0]
        links.new(Diffuse_node.outputs[0],Material.inputs[0])
    
    
    if AO_texture:
        AO_texture = AO_texture[0]
        if AO_node:
            AO_node = AO_node[0]
        else:
            AO_node = nodes.new("LuxCoreNodeTexColorMix")
            AO_node.label = "Diffuse AO"
            AO_node.mode = 'scale'
        links.new(AO_texture.outputs[0], AO_node.inputs[2])
        links.new(AO_node.outputs[0], Material.inputs[0])
        if Diffuse_texture:
            links.new(Diffuse_texture[0].outputs[0], AO_node.inputs[1])
            AO_node.location = (AO_texture.location[0] + 300,AO_texture.location[1])
        else:
            AO_node.location = (AO_texture.location[0] + 300,AO_texture.location[1])
            if Diffuse_color:
                    
                AO_node.inputs[1].default_value = Diffuse_color[:3]
            else:
                AO_node.inputs[1].default_value = (0.5, 0.5, 0.5)
    if not AO_texture:
        if AO_node:
            nodes.remove(AO_node[0])
                
def Connect_To_Lux_metal(mat):
    active_mat = mat
    engine = bpy.context.scene.render.engine
    
    node_tree = active_mat.luxcore.node_tree
    
    if node_tree:
        nodes = node_tree.nodes
        links = node_tree.links
        
                
            
        Material_node = next((node for node in nodes if node.bl_idname.startswith("LuxCoreNodeMat") and "Material" in node.label), None)
        other_nodes = [node for node in nodes if node != Material_node and node.bl_idname.startswith("LuxCore")]
        engine_name = "LuxCore"
        prefix_to_input_name = {
            
            ("Specular", "REFL", "REFLECTION"): "Specular",
            
            ("Metallic", "METALNESS", "METAL"): "Metallic",
            ("NRM", "NORMAL", "Normal Map"): "Bump",
            ("GLOSS", "ROUGHNESS", "Invert Gloss", "Roughness"): "Roughness",
            ("Displacement", "DISP", "HEIGHT"): "Displacement",
            ("BUMP",): "Bump",
            ("Opacity", "OPACITY"): "Opacity",
            ("IOR", "ior"): "IOR",
            ("Coat", "COATING"): "Coat Color"
        }
        if bpy.context.preferences.addons["Material_Converter 1"].preferences.luxcore_preferences.use_lux_metallic_material == False:
            prefix_to_input_name[("Diffuse", "COL", "COLOR", "COLOR * AO")]= "Base Color"
        else:
            prefix_to_input_name[("Diffuse", "COL", "COLOR", "COLOR * AO")]= "Color"
            
        if Material_node and Material_node.bl_idname == "LuxCoreNodeMatGlossyTranslucent":
            
            
            for key, value in list(prefix_to_input_name.items()):
                if value == "Specular":
                    prefix_to_input_name[key] = "Specular Color"
                if value == "Base Color":
                    prefix_to_input_name[key] = "Diffuse Color"
            
            
        
            
        if not Material_node:
            print(f"No {engine_name} group node found in material '{active_mat.name}'.")
            return
        
        # Create a dictionary to store inputs of the group node
        group_node_inputs = {input.name: input for input in Material_node.inputs}
        
        # Distance calculation function
        def distance(node):
            return math.sqrt(
                (Material_node.location.x - node.location.x)**2 + 
                (Material_node.location.y - node.location.y)**2
            )
        
        # Sort nodes by distance
        sorted_nodes = sorted(other_nodes, key=distance)
                    
        # Connect nodes to group node inputs
        for node in sorted_nodes:
            
            if node.label:
                node_label_upper = node.label.upper()
                
                # Try to match the node label with our prefix groups
                for prefixes, input_name in prefix_to_input_name.items():
                    if any(prefix.upper() in node_label_upper for prefix in prefixes):
                        if input_name in group_node_inputs:
                            input_socket = group_node_inputs[input_name]
                            
                            if not input_socket.is_linked:
                                if node.outputs:
                                    #current_output = node.outputs[0]
                                    if node.bl_idname == "LuxCoreNodeTexImagemap" and any(x in node.label for x in ["NRM", "NORMAL", "Normal Map"]):
                                        current_output = node.outputs[2]
                                    
                                    elif node.bl_idname == "VRayNodeMetaImageTexture" and any(l in node.label for l in ["GLOSS", "ROUGHNESS", "Metallic", "METALNESS", "METAL"]):
                                        current_output = node.outputs[3]
                                    else:
                                        current_output = node.outputs[0]
                                    if node.bl_idname == "VRayNodeMetaImageTexture" and any(z in node.label for z in ["SSS", "Subsurface"]):
                                        
                                        links.new(node.outputs[0], Material_node.inputs["Fog Color"])
                                        #links.new(node.outputs[0], Material_node.inputs["Refraction Color"])
                                        Material_node.inputs["Refraction Color"].value = (0.248867, 0.248867, 0.248867)
                                        if Material_node.bl_idname == "VRayNodeBRDFVRayMtl":
                                            Material_node.inputs[49].value ="6"
                                    
                                        
                                    links.new(current_output, input_socket)
                                    print(f"Connecting '{node.label}' output to '{Material_node.name}' group's '{input_name}' input")
                                    break
                                    
    
             
    
mat = bpy.context.object.active_material

nodetree = mat.luxcore.node_tree
material_name = mat.name
   
if not mat.luxcore.node_tree:
    color = []
    color.append(mat.diffuse_color[0])
    color.append(mat.diffuse_color[1])
    color.append(mat.diffuse_color[2])
    color.append(mat.diffuse_color[3])
    mat.luxcore.node_tree = bpy.data.node_groups.new(name=material_name, type="luxcore_material_nodes") 
    mat.luxcore.use_cycles_nodes = False
    mat.luxcore.auto_vp_color = False
    mat.diffuse_color = (color[0],color[1],color[2],color[3])
    m = mat.luxcore.node_tree.nodes.new("LuxCoreNodeMatOutput")
    m.label = "LuxCore Output"
        
#Add_Mapping_Node(mat)

if mat:
    label_texture_nodes(mat)
else:
    print("No active material found")
create_LuxCore_archviz_Glass_material()  
Connect_To_Lux_metal(mat)











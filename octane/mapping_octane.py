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

mat = bpy.context.object.active_material
Add_Mapping_Node(mat)
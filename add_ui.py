import bpy
import sys

sys.path.append(bpy.path.abspath("//"))
from add_main import Rig  # noqa


class Panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Loup"
    bl_label = "Main Panel"
    bl_idname = "CCURIG1_PT_panel"

    def draw(self, context):
        self.layout.operator(Rig.bl_idname)

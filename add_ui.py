import bpy
import op


class Panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Astra"
    bl_label = "Main Panel"
    bl_idname = "CCURIG1_PT_panel"

    def draw(self, context):
        self.layout.operator(op.Rig.bl_idname)

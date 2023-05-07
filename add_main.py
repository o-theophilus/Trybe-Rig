import bpy
import os
import ops


class Rig(bpy.types.Operator):
    """Astra Rig for Character Creator and Mixamo"""
    bl_idname = "operator.rig"
    bl_label = "Astra Rig"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        body_name = "body"
        armature_name = "armature"

        script_file = os.path.realpath(__file__)
        script_path = os.path.dirname(script_file)
        ref_path = f"{script_path}\\_"

        res = ops.validate_skin_mesh(self, body_name, ref_path)

        if res == {"FINISHED"}:
            ops.fix_Skin(body_name, ref_path)
            ops.build_rig(body_name, armature_name)
            ops.skin_rig(body_name, armature_name)
            ops.bind_items(body_name, armature_name)

            self.report({'INFO'}, "Rig Done")

        return {'FINISHED'}

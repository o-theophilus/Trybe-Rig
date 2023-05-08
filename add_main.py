import bpy
import sys

sys.path.append(bpy.path.abspath("//"))
import ops  # noqa


class Rig(bpy.types.Operator):
    """Loup Rig for  Mixamo"""
    bl_idname = "operator.rig"
    bl_label = "Rig Skin"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        body_name = "body"
        armature_name = "armature"

        res = ops.validate(body_name)
        if res[0]:
            ops.fix_Skin(body_name)
            ops.build_rig(body_name, armature_name)
            ops.skin_rig(body_name, armature_name)
            ops.bind_items(body_name, armature_name)

            self.report({'INFO'}, "Rig Done")

        return {'FINISHED'}

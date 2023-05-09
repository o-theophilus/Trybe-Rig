import bpy
import sys

sys.path.append(bpy.path.abspath("//"))
import ops  # noqa
import ops_match_rig as omr  # noqa
import tvo  # noqa

bl_info = {
    "name": "Mixa Rig",
    "author": "Theophilus Ogbolu",
    "version": (1, 3),
    "blender": (2, 80, 0),
    "location": "Object Mode -> Object menu, Edit Mode -> Mesh menu, ",
    "description": "Fast and easy 1-click rig",
    "warning": "",
    "wiki_url": "",
    "category": "Object",
}


class RigPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Loup"
    bl_label = "Rig Character"
    bl_idname = "panel.rig"

    def draw(self, context):
        self.layout.prop(context.scene, "rig_body", text="Body")
        self.layout.prop(context.scene, "rig_eye", text="Eyes")
        self.layout.prop(context.scene, "rig_lash", text="Eyelashes")
        self.layout.operator(Rig.bl_idname)


class Rig(bpy.types.Operator):
    """Rig for  Mixamo"""
    bl_idname = "operator.rig"
    bl_label = "Rig Skin"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        body = context.scene.rig_body
        res = ops.validate_skin(body)
        if not res[0]:
            self.report({'INFO'}, res[1])
            return {'FINISHED'}

        ops.fix_transform(body)
        ref_body = ops.get_ref()
        ops.transfer_id(ref_body, body)
        ops.transfer_weight(ref_body, body)
        ops.delete(ref_body)
        armature = ops.build_rig(body)
        ops.bind_to_rig(body, armature)

        eye = context.scene.rig_eye
        if eye:
            ops.fix_transform(eye)
            ops.bind_to_rig(eye, armature, "head")
        lash = context.scene.rig_lash
        if lash:
            ops.fix_transform(lash)
            ops.bind_to_rig(lash, armature, "head")

        self.report({'INFO'}, "Rig Done")
        return {'FINISHED'}


class MatchRigPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Loup"
    bl_label = "Match Rig"
    bl_idname = "panel.match_rig"

    def draw(self, context):
        self.layout.prop(context.scene, "match_rig_main", text="Main Armature")
        self.layout.prop(context.scene, "match_rig_edit", text="Edit Armature")
        self.layout.operator(MatchRig.bl_idname)


class MatchRig(bpy.types.Operator):
    """Match Source Rig to Target Rig"""
    bl_idname = "operator.match_rig"
    bl_label = "Match Rig"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        main = context.scene.match_rig_main
        edit = context.scene.match_rig_edit

        if (
            not main
            or not edit
            or main.type != "ARMATURE"
            or edit.type != "ARMATURE"
        ):
            self.report({'INFO'}, "Select an source and target armature")
            return {'FINISHED'}

        ops.disconnect_armature(edit)
        ops.match_rig(main, edit)
        ops.apply_armature_modifier(edit)
        ops.delete(edit)

        self.report({'INFO'}, "Rig Done")
        return {'FINISHED'}


class AddShapePanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Loup"
    bl_label = "Add Character as Shape"
    bl_idname = "panel.add_shape"

    def draw(self, context):
        self.layout.prop(context.scene, "add_shape_from", text="From")
        self.layout.prop(context.scene, "add_shape_to", text="To")
        self.layout.operator(AddShape.bl_idname)


class AddShape(bpy.types.Operator):
    """Add As Blendshape"""
    bl_idname = "operator.add_shape"
    bl_label = "Add as shape"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from_ = context.scene.add_shape_from
        to_ = context.scene.add_shape_to

        res = ops.validate_vertex_count(from_, to_)
        if not res[0]:
            self.report({'INFO'}, res[1])
            return {'FINISHED'}

        ops.transfer_id(from_, to_)
        ops.transfer_morphs(from_, to_)
        ops.delete(from_)

        self.report({'INFO'}, "Rig Done")
        return {'FINISHED'}


def register():
    bpy.types.Scene.rig_body = bpy.props.PointerProperty(
        type=bpy.types.Object)
    bpy.types.Scene.rig_eye = bpy.props.PointerProperty(
        type=bpy.types.Object)
    bpy.types.Scene.rig_lash = bpy.props.PointerProperty(
        type=bpy.types.Object)
    bpy.types.Scene.match_rig_edit = bpy.props.PointerProperty(
        type=bpy.types.Object)
    bpy.types.Scene.match_rig_main = bpy.props.PointerProperty(
        type=bpy.types.Object)
    bpy.types.Scene.add_shape_from = bpy.props.PointerProperty(
        type=bpy.types.Object)
    bpy.types.Scene.add_shape_to = bpy.props.PointerProperty(
        type=bpy.types.Object)

    bpy.utils.register_class(Rig)
    bpy.utils.register_class(RigPanel)
    bpy.utils.register_class(MatchRig)
    bpy.utils.register_class(MatchRigPanel)
    bpy.utils.register_class(AddShape)
    bpy.utils.register_class(AddShapePanel)
    bpy.utils.register_class(tvo.VOT_OT_TransferVertIdByUV)


def unregister():
    del bpy.types.Scene.rig_body
    del bpy.types.Scene.rig_eye
    del bpy.types.Scene.rig_lash
    del bpy.types.Scene.match_rig_edit
    del bpy.types.Scene.match_rig_main
    del bpy.types.Scene.add_shape_from
    del bpy.types.Scene.add_shape_to

    bpy.utils.unregister_class(Rig)
    bpy.utils.unregister_class(RigPanel)
    bpy.utils.unregister_class(MatchRig)
    bpy.utils.unregister_class(MatchRigPanel)
    bpy.utils.unregister_class(AddShape)
    bpy.utils.unregister_class(AddShapePanel)
    bpy.utils.unregister_class(tvo.VOT_OT_TransferVertIdByUV)


if __name__ == "__main__":
    register()

import bpy
import sys

sys.path.append(bpy.path.abspath("//"))
import ops  # noqa
import tvo  # noqa
import mdt  # noqa

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
        self.layout.prop(context.scene, "rig_body")
        self.layout.prop(context.scene, "rig_eye")
        self.layout.prop(context.scene, "rig_lash")
        self.layout.operator(Rig.bl_idname)


class Rig(bpy.types.Operator):
    """Rig for  Mixamo"""
    bl_idname = "operator.rig"
    bl_label = "Rig Skin"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        body = context.scene["rig_body"]
        res = ops.validate_skin(body)
        if not res[0]:
            self.report({'INFO'}, res[1])
            return {'FINISHED'}

        ops.fix_transform(body)
        ref_body = ops.get_ref()
        ops.transfer_id(ref_body, body)
        ops.transfer_vertex_groups(ref_body, body)
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

        self.report({'INFO'}, "done")
        return {'FINISHED'}


class MatchRigPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Loup"
    bl_label = "Match Rig"
    bl_idname = "panel.match_rig"

    def draw(self, context):
        self.layout.prop(context.scene, "match_rig_main")
        self.layout.prop(context.scene, "match_rig_edit")
        self.layout.operator(MatchRig.bl_idname)


class MatchRig(bpy.types.Operator):
    """Match Source Rig to Target Rig"""
    bl_idname = "operator.match_rig"
    bl_label = "Match Rig"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        main = context.scene["match_rig_main"]
        edit = context.scene["match_rig_edit"]

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

        self.report({'INFO'}, "done")
        return {'FINISHED'}


class AddShapePanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Loup"
    bl_label = "Add Character as Shape"
    bl_idname = "panel.add_shape"

    def draw(self, context):
        self.layout.prop(context.scene, "add_shape_from")
        self.layout.prop(context.scene, "add_shape_to")
        self.layout.operator(AddShape.bl_idname)


class AddShape(bpy.types.Operator):
    """Add As Blendshape"""
    bl_idname = "operator.add_shape"
    bl_label = "Add as shape"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from_ = context.scene["add_shape_from"]
        to_ = context.scene["add_shape_to"]

        res = ops.validate_vertex_count(from_, to_)
        if not res[0]:
            self.report({'INFO'}, res[1])
            return {'FINISHED'}

        ops.transfer_id(from_, to_)
        ops.transfer_morphs(from_, to_)
        ops.delete(from_)

        self.report({'INFO'}, "done")
        return {'FINISHED'}


class RigClothPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Loup"
    bl_label = "Rig Cloth"
    bl_idname = "panel.rig_cloth"

    def draw(self, context):
        self.layout.prop(context.scene, "rig_cloth_armature")
        self.layout.prop(context.scene, "rig_cloth_body")
        self.layout.prop(context.scene, "rig_cloth_cloth")
        self.layout.operator(RigCloth.bl_idname)


class RigCloth(bpy.types.Operator):
    """Rig Cloth"""
    bl_idname = "operator.rig_cloth"
    bl_label = "Rig Cloth"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # armature = context.scene["rig_cloth_armature"]
        body = context.scene["rig_cloth_body"]
        cloth = context.scene["rig_cloth_cloth"]

        res = ops.validate_skin(body)
        if not res[0]:
            self.report({'INFO'}, res[1])
            return {'FINISHED'}

        ops.fix_transform(cloth)
        mdt.transfer_vertex_groups(body, cloth)
        mdt.transfer_shape_keys(body, cloth)

        self.report({'INFO'}, "done")
        return {'FINISHED'}


classes = [
    Rig,
    RigPanel,
    MatchRig,
    MatchRigPanel,
    AddShape,
    AddShapePanel,
    RigCloth,
    RigClothPanel,
    tvo.VOT_OT_TransferVertIdByUV
]

props = [
    "rig_body",
    "rig_eye",
    "rig_lash",
    "match_rig_edit",
    "match_rig_main",
    "add_shape_from",
    "add_shape_to",
    "rig_cloth_armature",
    "rig_cloth_body",
    "rig_cloth_cloth",
]


def register():
    sc = bpy.types.Scene
    prop = bpy.props.PointerProperty
    obj = bpy.types.Object

    sc.rig_body = prop(name="Body", type=obj)
    sc.rig_eye = prop(name="Eyes", type=obj)
    sc.rig_lash = prop(name="Eyelashes", type=obj)
    sc.match_rig_main = prop(name="Main Armature", type=obj)
    sc.match_rig_edit = prop(name="Edit Armature", type=obj)
    sc.add_shape_from = prop(name="From", type=obj)
    sc.add_shape_to = prop(name="To", type=obj)
    sc.rig_cloth_armature = prop(name="Armature", type=obj)
    sc.rig_cloth_body = prop(name="Body", type=obj)
    sc.rig_cloth_cloth = prop(name="Cloth", type=obj)

    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for p in props:
        delattr(bpy.types.Scene, p)
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()

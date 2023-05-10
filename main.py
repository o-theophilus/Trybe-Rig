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


# class MatchRigPanel(bpy.types.Panel):
#     bl_space_type = 'VIEW_3D'
#     bl_region_type = 'UI'
#     bl_category = "Loup"
#     bl_label = "Match Rig"
#     bl_idname = "panel.match_rig"

#     def draw(self, context):
#         self.layout.prop(context.scene, "match_rig_main")
#         self.layout.prop(context.scene, "match_rig_edit")
#         self.layout.operator(MatchRig.bl_idname)


# class MatchRig(bpy.types.Operator):
#     """Match Source Rig to Target Rig"""
#     bl_idname = "operator.match_rig"
#     bl_label = "Match Rig"
#     bl_options = {'REGISTER', 'UNDO'}

#     def execute(self, context):
#         main = context.scene["match_rig_main"]
#         edit = context.scene["match_rig_edit"]

#         if (
#             not main
#             or not edit
#             or main.type != "ARMATURE"
#             or edit.type != "ARMATURE"
#         ):
#             self.report({'INFO'}, "Select an source and target armature")
#             return {'FINISHED'}

#         ops.disconnect_armature(edit)
#         ops.match_rig(main, edit)
#         ops.apply_armature_modifier(edit)
#         ops.delete(edit)

#         self.report({'INFO'}, "done")
#         return {'FINISHED'}


# class AddShapePanel(bpy.types.Panel):
#     bl_space_type = 'VIEW_3D'
#     bl_region_type = 'UI'
#     bl_category = "Loup"
#     bl_label = "Add Character as Shape"
#     bl_idname = "panel.add_shape"

#     def draw(self, context):
#         self.layout.prop(context.scene, "add_shape_from")
#         self.layout.prop(context.scene, "add_shape_to")
#         self.layout.operator(AddShape.bl_idname)


# class AddShape(bpy.types.Operator):
#     """Add As Blendshape"""
#     bl_idname = "operator.add_shape"
#     bl_label = "Add as shape"
#     bl_options = {'REGISTER', 'UNDO'}

#     def execute(self, context):
#         from_ = context.scene["add_shape_from"]
#         to_ = context.scene["add_shape_to"]

#         res = ops.validate_vertex_count(from_, to_)
#         if not res[0]:
#             self.report({'INFO'}, res[1])
#             return {'FINISHED'}

#         ops.transfer_id(from_, to_)
#         ops.transfer_morphs(from_, to_)
#         ops.delete(from_)

#         self.report({'INFO'}, "done")
#         return {'FINISHED'}


class AddBlendshapePanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Loup"
    bl_label = "Add Character as Shape"
    bl_idname = "panel.add_blendshape"

    def draw(self, context):
        self.layout.prop(context.scene, "match_rig_main")
        self.layout.prop(context.scene, "add_shape_from")
        self.layout.prop(context.scene, "add_shape_to")
        self.layout.operator(AddBlendshape.bl_idname)


class AddBlendshape(bpy.types.Operator):
    """Add As Blendshape"""
    bl_idname = "operator.add_blendshape"
    bl_label = "Add as blendshape"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from_ = context.scene["add_shape_from"]
        to_ = context.scene["add_shape_to"]
        amt_1 = context.scene["match_rig_main"]

        res = ops.validate_skin(from_)
        if not res[0]:
            self.report({'INFO'}, res[1])
            return {'FINISHED'}
        res = ops.validate_skin(to_)
        if not res[0]:
            self.report({'INFO'}, res[1])
            return {'FINISHED'}

        res = ops.validate_vertex_count(from_, to_)
        if not res[0]:
            self.report({'INFO'}, res[1])
            return {'FINISHED'}

        if not amt_1 or amt_1.type != "ARMATURE":
            self.report({'INFO'}, "SELECT ARMATURE")
            return {'FINISHED'}

        ops.fix_transform(from_)
        ref_body = ops.get_ref()
        ops.transfer_id(ref_body, from_)
        ops.transfer_vertex_groups(ref_body, from_)
        ops.delete(ref_body)
        amt_2 = ops.build_rig(from_)
        ops.bind_to_rig(from_, amt_2)

        ops.disconnect_armature(amt_2)
        ops.match_rig(amt_1, amt_2)
        ops.apply_armature_modifier(amt_2)
        ops.delete(amt_2)

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
        self.layout.prop(context.scene, "rig_cloth_cloth_1")
        self.layout.prop(context.scene, "rig_cloth_cloth_2")
        self.layout.prop(context.scene, "rig_cloth_cloth_3")
        self.layout.prop(context.scene, "rig_cloth_cloth_4")
        self.layout.prop(context.scene, "rig_cloth_cloth_5")
        self.layout.operator(RigCloth.bl_idname)


class RigCloth(bpy.types.Operator):
    """Rig Cloth"""
    bl_idname = "operator.rig_cloth"
    bl_label = "Rig Cloth"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = context.scene["rig_cloth_armature"]
        body = context.scene["rig_cloth_body"]
        clothes = []
        cloth_1 = context.scene["rig_cloth_cloth_1"]
        if cloth_1:
            clothes.append(cloth_1)
        cloth_2 = context.scene["rig_cloth_cloth_2"]
        if cloth_2:
            clothes.append(cloth_2)
        cloth_3 = context.scene["rig_cloth_cloth_3"]
        if cloth_3:
            clothes.append(cloth_3)
        cloth_4 = context.scene["rig_cloth_cloth_4"]
        if cloth_4:
            clothes.append(cloth_4)
        cloth_5 = context.scene["rig_cloth_cloth_5"]
        if cloth_5:
            clothes.append(cloth_5)

        res = ops.validate_skin(body)
        if not res[0]:
            self.report({'INFO'}, res[1])
            return {'FINISHED'}
        if not armature or armature.type != "ARMATURE":
            self.report({'INFO'}, "SELECT ARMATURE")
            return {'FINISHED'}

        for cloth in clothes:
            ops.fix_transform(cloth)
            mdt.transfer_vertex_groups(body, cloth)
            mdt.transfer_shape_keys(body, cloth)
            ops.bind_to_rig(cloth, armature)

        # ops.delete(body)

        self.report({'INFO'}, "done")
        return {'FINISHED'}


classes = [
    Rig,
    RigPanel,
    # MatchRig,
    # MatchRigPanel,
    # AddShape,
    # AddShapePanel,
    AddBlendshape,
    AddBlendshapePanel,
    RigCloth,
    RigClothPanel,
    tvo.VOT_OT_TransferVertIdByUV
]

props = [
    "rig_body",
    "rig_eye",
    "rig_lash",
    "match_rig_main",
    # "match_rig_edit",
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
    # sc.match_rig_edit = prop(name="Edit Armature", type=obj)
    sc.add_shape_from = prop(name="From", type=obj)
    sc.add_shape_to = prop(name="To", type=obj)
    sc.rig_cloth_armature = prop(name="Armature", type=obj)
    sc.rig_cloth_body = prop(name="Body", type=obj)
    sc.rig_cloth_cloth_1 = prop(name="Cloth 1", type=obj)
    sc.rig_cloth_cloth_2 = prop(name="Cloth 2", type=obj)
    sc.rig_cloth_cloth_3 = prop(name="Cloth 3", type=obj)
    sc.rig_cloth_cloth_4 = prop(name="Cloth 4", type=obj)
    sc.rig_cloth_cloth_5 = prop(name="Cloth 5", type=obj)

    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for p in props:
        delattr(bpy.types.Scene, p)
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()

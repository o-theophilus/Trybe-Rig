import bpy
import sys
import os
# # FOR TESTING IN BLENDER
# sys.path.append(os.path.dirname(bpy.context.space_data.text.filepath))
sys.path.append(os.path.dirname(__file__))
import ops  # noqa
import tvo  # noqa
import mdt  # noqa

bl_info = {
    "name": "Trybe Rig",
    "author": "Theophilus Ogbolu",
    "version": (1, 3),
    "blender": (2, 80, 0),
    "location": "3D Viewport -> Right Panel -> Trybe Rig",
    "description": "Fast and easy 1-click rig",
    "warning": "",
    "wiki_url": "",
    "category": "Object",
}


class RigChatacterPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Trybe"
    bl_label = "Rig Character"
    bl_idname = "PAN3L_PT_rig"

    def draw(self, context):
        self.layout.prop(context.scene, "rig_body")
        self.layout.operator(RigCharacter.bl_idname)


class RigCharacter(bpy.types.Operator):
    """Rig for  Mixamo"""
    bl_idname = "operator.rig"
    bl_label = "Rig Skin"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        body = context.scene["rig_body"]

        if not body or body.type != "MESH":
            self.report({'INFO'}, "select a valid mesh")
            return {'FINISHED'}
        elif ops.count_face(body) != 10306:
            self.report(
                {'INFO'}, "Mesh has different amount of faces / topology")
            return {'FINISHED'}

        ops.fix_transform(body)
        ref_body = ops.get_ref()
        ops.transfer_id(ref_body, body)
        ops.transfer_vertex_groups(ref_body, body)
        ops.delete(ref_body)
        armature = ops.build_rig(body)
        ops.bind_to_rig(body, armature)

        self.report({'INFO'}, "done")
        return {'FINISHED'}


class AddBlendshapePanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Trybe"
    bl_label = "Add Character as Shape"
    bl_idname = "PAN3L_PT_add_blendshape"

    def draw(self, context):
        self.layout.prop(context.scene, "add_shape_from")
        self.layout.prop(context.scene, "add_shape_to")
        self.layout.prop(context.scene, "match_rig_main")
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

        if not from_ or from_.type != "MESH" or not to_ or to_.type != "MESH":
            self.report({'INFO'}, "select a valid mesh")
            return {'FINISHED'}
        elif ops.count_face(from_) != ops.count_face(to_):
            self.report({'INFO'}, "Mesh Topology does not match")
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
    bl_category = "Trybe"
    bl_label = "Rig Cloth"
    bl_idname = "PAN3L_PT_rig_cloth"

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

        if not body or body.type != "MESH":
            self.report({'INFO'}, "select a valid mesh")
            return {'FINISHED'}
        elif ops.count_face(body) != 10306:
            self.report(
                {'INFO'}, "Mesh has different amount of faces / topology")
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
    RigCharacter,
    RigChatacterPanel,
    AddBlendshape,
    AddBlendshapePanel,
    RigCloth,
    RigClothPanel,
    tvo.VOT_OT_TransferVertIdByUV
]

props = [
    "rig_body",
    "match_rig_main",
    "add_shape_from",
    "add_shape_to",
    "rig_cloth_armature",
    "rig_cloth_body",
    "rig_cloth_cloth_1",
    "rig_cloth_cloth_2",
    "rig_cloth_cloth_3",
    "rig_cloth_cloth_4",
    "rig_cloth_cloth_5",
]


def register():
    sc = bpy.types.Scene
    prop = bpy.props.PointerProperty
    obj = bpy.types.Object

    sc.rig_body = prop(name="Body", type=obj)
    sc.add_shape_from = prop(name="From", type=obj)
    sc.add_shape_to = prop(name="To", type=obj)
    sc.match_rig_main = prop(name="Armature", type=obj)
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

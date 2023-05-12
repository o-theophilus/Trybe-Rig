import bpy
import bmesh
import ops_point
import os


def count_face(obj):
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    count = len(bm.faces)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    return count


def fix_transform(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    obj.location = (0, 0, 0)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.select_all(action='DESELECT')


def get_ref():
    with bpy.data.libraries.load(
        f"{os.path.dirname(__file__)}/ops_skin",
            link=False) as (data_from, data_to):
        data_to.objects = [
            name for name in data_from.objects if name == "skin_weight"]
    for obj in data_to.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)

    return bpy.data.objects["skin_weight"]


def transfer_id(from_, to_):
    bpy.ops.object.select_all(action='DESELECT')
    from_.select_set(True)
    to_.select_set(True)
    bpy.context.view_layer.objects.active = from_
    bpy.ops.object.vert_id_transfer_uv()
    bpy.ops.object.select_all(action='DESELECT')


def transfer_vertex_groups(from_, to_, map="TOPOLOGY"):
    bpy.ops.object.select_all(action='DESELECT')
    from_.select_set(True)
    to_.select_set(True)
    bpy.context.view_layer.objects.active = to_
    bpy.ops.object.data_transfer(
        use_reverse_transfer=True,
        data_type='VGROUP_WEIGHTS',
        vert_mapping=map,
        layers_select_src='NAME',
        layers_select_dst='ALL')
    bpy.ops.object.select_all(action='DESELECT')


def delete(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.delete()


def build_rig(body):
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.armature_add()
    armature = bpy.data.objects['Armature']
    armature.name = "armature"
    armature.show_in_front = True
    armature.location = body.location

    amt = armature.data
    amt.name = "armature"
    amt.display_type = "WIRE"

    bpy.ops.object.mode_set(mode='EDIT')

    bone = amt.edit_bones['Bone']
    amt.edit_bones.remove(bone)

    def point(a, b):
        a = body.data.vertices[a].co
        b = body.data.vertices[b].co
        return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)

    def makeBone(bone_name, parent_name, h1, h2, t1, t2, roll, connect=True):
        bone = amt.edit_bones.new(bone_name)

        if h1 and h2:
            bone.head = point(h1, h2)
        bone.tail = point(t1, t2)

        if parent_name:
            bone.parent = amt.edit_bones[parent_name]
            bone.use_connect = connect

        if roll:
            bpy.ops.armature.calculate_roll(type=roll)

    for i in ops_point.points:
        makeBone(i["name"], i["parent"], i["h1"], i["h2"],
                 i["t1"], i["t2"], i["or"], i["conn"])

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    return armature


def bind_to_rig(obj, amt, joint=None):
    bpy.ops.object.select_all(action='DESELECT')

    obj.select_set(True)

    if joint:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        verts = [v.index for v in bm.verts]
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.vertex_groups.new(name="head")
        obj.vertex_groups['head'].add(verts, 1.0, 'REPLACE')

    amt.select_set(True)
    bpy.context.view_layer.objects.active = amt
    bpy.ops.object.parent_set(type='ARMATURE_NAME')
    obj.modifiers["Armature"].use_deform_preserve_volume = True
    bpy.ops.object.select_all(action='DESELECT')


def disconnect_armature(amt):
    bpy.context.view_layer.objects.active = amt
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in amt.data.edit_bones:
        bone.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')


def match_rig(main, edit):
    bpy.context.view_layer.objects.active = edit
    for bone in edit.pose.bones:
        bpy.ops.object.mode_set(mode='POSE')
        bone.matrix = main.pose.bones[bone.name].matrix
        bpy.ops.object.mode_set(mode='OBJECT')


def apply_armature_modifier(amt):
    for o in bpy.data.objects:
        if o.parent == amt and o.type == "MESH":
            for modifier in o.modifiers:
                bpy.ops.object.select_all(action='DESELECT')

                if modifier.type == 'ARMATURE':
                    o.select_set(True)
                    bpy.context.view_layer.objects.active = o
                    bpy.ops.object.modifier_apply(
                        modifier=modifier.name
                    )
                bpy.ops.object.select_all(action='DESELECT')


def transfer_morphs(from_, to_):
    bpy.ops.object.select_all(action='DESELECT')
    from_.select_set(True)
    to_.select_set(True)
    bpy.context.view_layer.objects.active = to_
    bpy.ops.object.join_shapes()
    bpy.ops.object.select_all(action='DESELECT')


####################################

def fix_armature_transform(amt):
    amt.animation_data_clear()
    for bone in amt.pose.bones:
        bone.matrix_basis.identity()

    armature_children = [o for o in bpy.data.objects if o.parent == amt]

    to_select = [amt,  *armature_children]
    for o in to_select:
        o.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.select_all(action='DESELECT')


def fix_namespace(amt):
    bpy.context.view_layer.objects.active = amt
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in amt.data.edit_bones:
        if bone.name.startswith("mixamorig:"):
            bone.name = bone.name.split(":")[1]
    bpy.ops.object.mode_set(mode='OBJECT')


def normalise(obj):
    # obj = bpy.data.objects["Body"]
    for group in obj.vertex_groups:
        bpy.context.object.vertex_groups.active = group
        bpy.ops.object.vertex_group_normalize()

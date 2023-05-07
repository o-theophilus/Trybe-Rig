import bpy
import bmesh
import os
import ops_vid
import ops_point

ref_path = f"{bpy.path.abspath('//')}/_"


def validate(body_name):
    if bpy.context.active_object is not None:
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

    if body_name not in bpy.data.objects:
        return (False, "body mesh not found")

    body = bpy.data.objects[body_name]
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bm = bmesh.from_edit_mesh(body.data)
    bm.faces.ensure_lookup_table()

    if len(bm.faces) != 9452:
        return (False, "Mesh has different amount of faces / topology")

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    if not os.path.exists(ref_path):
        return (False, "skin weight data not found")

    return (True, "done")


def fix_Skin(body_name):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    def get_ref():
        with bpy.data.libraries.load(
                f"{ref_path}", link=False) as (data_from, data_to):
            data_to.objects = [
                name for name in data_from.objects if name == "skin_weight"]
        for obj in data_to.objects:
            if obj is not None:
                bpy.context.collection.objects.link(obj)

    get_ref()

    ref = bpy.data.objects["skin_weight"]
    body = bpy.data.objects[body_name]

    body.location = (0, 0, 0)
    body.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.select_all(action='DESELECT')

    ref.select_set(True)
    bpy.context.view_layer.objects.active = ref
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(ref.data)
    bm.faces.ensure_lookup_table()
    bm.select_history.add(bm.faces[1210])
    bm.select_history.add(bm.faces[1011])

    for x in bm.select_history:
        x.select = True

    ops_vid.CopyVertID().execute()

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')

    def auto_select():
        bm = bmesh.from_edit_mesh(body.data)
        bm.verts.ensure_lookup_table()

        bm.select_history.clear()
        for x in bm.faces:
            x.select = False

        v_i = []
        for x in bm.verts:
            if len(x.link_edges) == 3:
                v_i.append({
                    "vert": x,
                    "x": x.co[0],
                    "y": x.co[1],
                    "z": x.co[2]
                })

        v_i = sorted(v_i, key=lambda k: k['x'])
        v_i = v_i[400:]
        v_i = sorted(v_i, key=lambda k: k['y'])
        v_i = v_i[-300:]
        v_i = sorted(v_i, key=lambda k: k['z'])
        v_i = v_i[-1:]

        vert = v_i[0]["vert"]

        f_i = []
        for i in vert.link_faces:
            f_i.append({
                "face": i,
                "x": i.calc_center_median()[0],
                "y": i.calc_center_median()[1],
                "z": i.calc_center_median()[2]
            })

        f_i = sorted(f_i, key=lambda k: k['z'])[:-1]
        f_i = sorted(f_i, key=lambda k: k['y'])

        for i in f_i:
            face = i["face"]
            bm.select_history.add(face)
            face.select = True

    auto_select()

    ops_vid.PasteVertID().execute()

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    ref.select_set(True)
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.data_transfer(
        use_reverse_transfer=True,
        data_type='VGROUP_WEIGHTS',
        vert_mapping='TOPOLOGY',
        layers_select_src='NAME',
        layers_select_dst='ALL')
    bpy.ops.object.select_all(action='DESELECT')

    ref.select_set(True)
    bpy.ops.object.delete()

    return (True, "done")


def build_rig(body_name, armature_name):
    bpy.ops.object.mode_set(mode='OBJECT')
    body = bpy.data.objects[body_name]

    bpy.ops.object.armature_add()
    armature = bpy.data.objects['Armature']
    armature.name = armature_name
    armature.show_in_front = True
    armature.location = body.location

    amt = armature.data
    amt.name = armature_name
    amt.display_type = "WIRE"

    bpy.ops.object.mode_set(mode='EDIT')

    bone = amt.edit_bones['Bone']
    # bone.name = "root"
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

    return (True, "done")


def skin_rig(body_name, armature_name):
    body = bpy.data.objects[body_name]
    amt = bpy.data.objects[armature_name]

    body.select_set(True)
    amt.select_set(True)
    bpy.context.view_layer.objects.active = amt
    bpy.ops.object.parent_set(type='ARMATURE_NAME')
    body.modifiers["Armature"].use_deform_preserve_volume = True

    bpy.ops.object.select_all(action='DESELECT')

    return (True, "done")


def bind_items(body_name, armature_name):
    amt = bpy.data.objects[armature_name]
    body = bpy.data.objects[body_name]

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    for x in bpy.data.objects:
        if x.type == "MESH":
            if "head" in [x.name.split(".")[0], x.name]:
                x.select_set(True)
                bpy.context.view_layer.objects.active = x
                bpy.ops.object.mode_set(mode='EDIT')

                bm = bmesh.from_edit_mesh(x.data)
                bm.verts.ensure_lookup_table()
                verts = [y.index for y in bm.verts]

                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_all(action='DESELECT')

                x.vertex_groups.new(name="head")
                x.vertex_groups['head'].add(verts, 1.0, 'REPLACE')

                x.select_set(True)
                amt.select_set(True)
                bpy.context.view_layer.objects.active = amt
                bpy.ops.object.parent_set(type='ARMATURE_NAME')

            elif "cloth" in [x.name.split(".")[0], x.name]:
                x.select_set(True)
                body.select_set(True)
                bpy.context.view_layer.objects.active = x
                bpy.ops.object.data_transfer(use_reverse_transfer=True,
                                             data_type='VGROUP_WEIGHTS',
                                             vert_mapping='POLYINTERP_NEAREST',
                                             layers_select_src='NAME',
                                             layers_select_dst='ALL'
                                             )

                bpy.ops.object.select_all(action='DESELECT')

                x.select_set(True)
                amt.select_set(True)
                bpy.context.view_layer.objects.active = amt
                bpy.ops.object.parent_set(type='ARMATURE_NAME')
                x.modifiers["Armature"].use_deform_preserve_volume = True

        bpy.ops.object.select_all(action='DESELECT')

import bpy


def fix_transform(source, target):
    source.animation_data_clear()
    for bone in source.pose.bones:
        bone.matrix_basis.identity()
    target.animation_data_clear()
    for bone in target.pose.bones:
        bone.matrix_basis.identity()

    source_children = [o for o in bpy.data.objects if o.parent == source]
    target_children = [o for o in bpy.data.objects if o.parent == target]

    to_select = [source, target, *source_children, *target_children]
    for o in to_select:
        o.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.select_all(action='DESELECT')


def fix_namespace(armature):
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in armature.data.edit_bones:
        if bone.name.startswith("mixamorig:"):
            bone.name = bone.name.split(":")[1]
    bpy.ops.object.mode_set(mode='OBJECT')


def disconnect(armature):
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in armature.data.edit_bones:
        bone.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')


def match_rig(from_, to_):
    bpy.context.view_layer.objects.active = to_
    for bone in to_.pose.bones:
        bpy.ops.object.mode_set(mode='POSE')
        bone.matrix = from_.pose.bones[bone.name].matrix
        bpy.ops.object.mode_set(mode='OBJECT')


def apply_armature_modifier(armature):
    for o in bpy.data.objects:
        if o.parent == armature and o.type == "MESH":
            for modifier in o.modifiers:
                bpy.ops.object.select_all(action='DESELECT')

                if modifier.type == 'ARMATURE':
                    o.select_set(True)
                    bpy.context.view_layer.objects.active = o
                    bpy.ops.object.modifier_apply(
                        modifier=modifier.name
                    )
                bpy.ops.object.select_all(action='DESELECT')


def fix_vertex_id(mesh_names, armature):
    for m in mesh_names:
        temp = [o for o in bpy.data.objects if o.name.startswith(m)]
        assert len(temp) == 2

        bpy.ops.object.select_all(action='DESELECT')
        for n in temp:
            assert n.type == "MESH"
            n.select_set(True)
            if n.parent == armature:
                bpy.context.view_layer.objects.active = n
        bpy.ops.object.vert_id_transfer_uv()
        bpy.ops.object.select_all(action='DESELECT')


def transfer_morphs_to(mesh_names, armature):
    for m in mesh_names:
        temp = [o for o in bpy.data.objects if o.name.startswith(m)]
        assert len(temp) == 2

        bpy.ops.object.select_all(action='DESELECT')
        for n in temp:
            assert n.type == "MESH"
            n.select_set(True)
            if n.parent == armature:
                bpy.context.view_layer.objects.active = n

        bpy.ops.object.join_shapes()
        bpy.ops.object.select_all(action='DESELECT')


def cleanup(mesh_names, armature):
    children = [o for o in bpy.data.objects if o.parent == armature]
    to_delete = [armature, *children]

    for o in to_delete:
        o.select_set(True)
        bpy.ops.object.delete()


def run():
    source = bpy.context.object
    assert source.type == "ARMATURE"

    all_selected = [o for o in bpy.data.objects if o.select_get()]
    assert len(all_selected) == 2, "select 2 armatures"

    all_selected.remove(source)
    target = all_selected[0]
    assert target.type == "ARMATURE"

    bpy.ops.object.select_all(action='DESELECT')

    fix_transform(source, target)
    fix_namespace(source)
    fix_namespace(target)
    disconnect(target)
    match_rig(source, target)
    apply_armature_modifier(target)
    mesh = ["Body", "Eyes", "Eyelashes"]
    fix_vertex_id(mesh, target)
    transfer_morphs_to(mesh, source)
    cleanup(mesh, target)


run()

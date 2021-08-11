import bpy, bmesh

skinName = "body"
refName = "ref"
refPath = "C:\\Users\\bo2\Desktop\\Theo\\fRig\\ret.blend"
rootName = "root"
amtName = "amt"


def getRef():
    with bpy.data.libraries.load(refPath, link=False) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects if name.startswith(refName)]

    for obj in data_to.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)

    bpy.ops.object.select_all(action='DESELECT')


def fixSkin():
    a = [1879, 3902]
    ref = bpy.data.objects[refName]
    skin = bpy.data.objects[skinName]

    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='DESELECT')
    ref.select_set(True)
    bpy.context.view_layer.objects.active = ref

    for x in ref.data.vertices:
        x.select = False
    for x in ref.data.edges:
        x.select = False
    for x in ref.data.polygons:
        x.select = False


    # ref.data.polygons[a[0]].select = True
    # ref.data.polygons[a[1]].select = True
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.select_mode(type='FACE')
    
    bpy.ops.object.mode_set(mode='EDIT')

    bm = bmesh.from_edit_mesh(ref.data)
    bm.faces.ensure_lookup_table()
    bm.select_history.add(bm.faces[a[0]])
    bm.select_history.add(bm.faces[a[1]])
    
    for x in bm.select_history:
        x.select = True
        
    print(bm.select_history.active.select_set)
    print(dir(bm.select_history.active.select_set))

    bpy.ops.object.copy_vert_id()

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    skin.select_set(True)
    bpy.context.view_layer.objects.active = skin

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')

    bpy.ops.object.paste_vert_id()

    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='DESELECT')
    skin.select_set(True)
    ref.select_set(True)
    bpy.context.view_layer.objects.active = ref
    bpy.ops.object.vertex_group_copy_to_selected()
    bpy.ops.object.select_all(action='DESELECT')
    
    ref.select_set(True)
    bpy.ops.object.delete()


def rig():
    def point(a, b):
        skin = bpy.data.objects[skinName]
        a = skin.data.vertices[a].co
        b = skin.data.vertices[b].co
        return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)


    def makeBone(name, pName, h1, h2, t1, t2, connect=True, roll=None):
        amt = bpy.data.objects[rootName].data
        bone = amt.edit_bones.new(name)
        
        if h1 != None and h2 != None:
            bone.head = point(h1, h2)
        bone.tail = point(t1, t2)
        if pName != None:
            bone.parent = amt.edit_bones[pName]
            bone.use_connect = connect

        if roll != None:
            bpy.ops.armature.calculate_roll(type=roll)

    skin = bpy.data.objects[skinName]
    skin.location = (0, 0, 0)
    bpy.ops.object.select_all(action='DESELECT')
    skin.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    bpy.ops.object.armature_add()
    root = bpy.data.objects['Armature']
    root.name = rootName
    root.location = skin.location

    amt = root.data
    amt.name= amtName
    amt.display_type= "WIRE"

    bpy.ops.object.mode_set(mode='EDIT')
    bone = amt.edit_bones['Bone']
    amt.edit_bones.remove(bone)

    makeBone("pelvis", None, 4559, 2209, 2247, 4387, roll='GLOBAL_NEG_Z')
    makeBone("spine.1", "pelvis", None, None, 4050, 4060, roll="NEG_X")
    makeBone("spine.2", "spine.1", None, None, 3987, 4149, roll="NEG_X")
    makeBone("spine.3", "spine.2", None, None, 9320, 4008, roll="POS_X")
    makeBone("neck.1", "spine.3", None, None, 13106, 11046, roll="POS_X")
    makeBone("neck.2", "neck.1", None, None, 11515, 9515, roll="POS_X")
    makeBone("head", "neck.2", None, None, 11288, 11288, roll="NEG_X")

    makeBone("thigh.L", "pelvis", 2164, 2068, 327, 360, False, roll="GLOBAL_NEG_Y")
    makeBone("thigh.twist.L", "thigh.L", None, None, 15, 481, roll="GLOBAL_NEG_Y")
    makeBone("calf.L", "thigh.twist.L", None, None, 301, 283, roll="GLOBAL_POS_Y")
    makeBone("calf.twist.L", "calf.L", None, None, 858, 825, roll="GLOBAL_POS_Y")
    makeBone("foot.L", "calf.twist.L", None, None, 892, 904, roll="POS_X")
    makeBone("ball.L", "foot.L", None, None, 1161, 1157, roll="GLOBAL_POS_Z")

    makeBone("thigh.R", "pelvis", 4411, 4529, 2663, 2629, False, roll="GLOBAL_NEG_Y")
    makeBone("thigh.twist.R", "thigh.R", None, None, 2322, 2586, roll="GLOBAL_NEG_Y")
    makeBone("calf.R", "thigh.twist.R", None, None, 2596, 2538, roll="GLOBAL_POS_Y")
    makeBone("calf.twist.R", "calf.R", None, None, 3168, 3201, roll="GLOBAL_POS_Y")
    makeBone("foot.R", "calf.twist.R", None, None, 3234, 3246, roll="POS_X")
    makeBone("ball.R", "foot.R", None, None, 3519, 3514, roll="GLOBAL_POS_Z")

    makeBone("clavicle.L", "spine.3", 1780, 1723, 4804, 4774, False, roll="NEG_X")
    makeBone("upperarm.L", "clavicle.L", None, None, 4777, 4799, roll="POS_Z")
    makeBone("upperarm.twist.L", "upperarm.L", None, None, 5078, 5068, roll="NEG_X")
    makeBone("lowerarm.L", "upperarm.twist.L", None, None, 4610, 4614, roll="POS_X")
    makeBone("lowerarm.twist.L", "lowerarm.L", None, None, 6917, 6928, roll="NEG_Z")
    makeBone("hand.L", "lowerarm.twist.L", None, None, 6316, 5454, roll="NEG_Z")

    makeBone("thumb.1.L", "hand.L", 6287, 6770, 6415, 6614, False, roll="GLOBAL_POS_Y")
    makeBone("thumb.2.L", "thumb.1.L", None, None, 6608, 6712, roll="GLOBAL_POS_Y")
    makeBone("thumb.3.L", "thumb.2.L", None, None, 6746, 6673, roll="GLOBAL_POS_Y")
    makeBone("index.1.L", "hand.L", 6486, 6504, 5692, 5749, False, roll="GLOBAL_NEG_Y")
    makeBone("index.2.L", "index.1.L", None, None, 5701, 5753, roll="GLOBAL_NEG_Y")
    makeBone("index.3.L", "index.2.L", None, None, 5796, 5798, roll="GLOBAL_NEG_Y")
    makeBone("middle.1.L", "hand.L", 6525, 6292, 5494, 5551, False, roll="GLOBAL_NEG_Y")
    makeBone("middle.2.L", "middle.1.L", None, None, 5503, 5561, roll="GLOBAL_NEG_Y")
    makeBone("middle.3.L", "middle.2.L", None, None, 5601, 5603, roll="GLOBAL_NEG_Y")
    makeBone("ring.1.L", "hand.L", 6873, 6348, 5984, 5927, False, roll="GLOBAL_NEG_Y")
    makeBone("ring.2.L", "ring.1.L", None, None, 5990, 5937, roll="GLOBAL_NEG_Y")
    makeBone("ring.3.L", "ring.2.L", None, None, 5964, 6062, roll="GLOBAL_NEG_Y")
    makeBone("pinky.1.L", "hand.L", 6519, 6469, 6182, 6120, False, roll="GLOBAL_NEG_Y")
    makeBone("pinky.2.L", "pinky.1.L", None, None, 6188, 6124, roll="GLOBAL_NEG_Y")
    makeBone("pinky.3.L", "pinky.2.L", None, None, 6162, 6262, roll="GLOBAL_NEG_Y")

    makeBone("clavicle.R", "spine.3", 4127, 4154, 7228, 7197, False, roll="POS_X")
    makeBone("upperarm.R", "clavicle.R", None, None, 7160, 7190, roll="NEG_Z")
    makeBone("upperarm.twist.R", "upperarm.R", None, None, 7396, 7469, roll="POS_X")
    makeBone("lowerarm.R", "upperarm.twist.R", None, None, 6968, 6974, roll="NEG_X")
    makeBone("lowerarm.twist.R", "lowerarm.R", None, None, 9230, 8753, roll="POS_Z")
    makeBone("hand.R", "lowerarm.twist.R", None, None, 8735, 7889, roll="POS_Z")

    makeBone("thumb.1.R", "hand.R", 8705, 9027, 8830, 9034, False, roll="GLOBAL_NEG_Y")
    makeBone("thumb.2.R", "thumb.1.R", None, None, 9127, 9030, roll="GLOBAL_NEG_Y")
    makeBone("thumb.3.R", "thumb.2.R", None, None, 9161, 9089, roll="GLOBAL_NEG_Y")
    makeBone("index.1.R", "hand.R", 8898, 8914, 8117, 8176, False, roll="GLOBAL_POS_Y")
    makeBone("index.2.R", "index.1.R", None, None, 8126, 8179, roll="GLOBAL_POS_Y")
    makeBone("index.3.R", "index.2.R", None, None, 8225, 8223, roll="GLOBAL_POS_Y")
    makeBone("middle.1.R", "hand.R", 8935, 8712, 7928, 7982, False, roll="GLOBAL_POS_Y")
    makeBone("middle.2.R", "middle.1.R", None, None, 7936, 7986, roll="GLOBAL_POS_Y")
    makeBone("middle.3.R", "middle.2.R", None, None, 8034, 8032, roll="GLOBAL_POS_Y")
    makeBone("ring.1.R", "hand.R", 8758, 8767, 8407, 8351, False, roll="GLOBAL_POS_Y")
    makeBone("ring.2.R", "ring.1.R", None, None, 8459, 8414, roll="GLOBAL_POS_Y")
    makeBone("ring.3.R", "ring.2.R", None, None, 8486, 8389, roll="GLOBAL_POS_Y")
    makeBone("pinky.1.R", "hand.R", 8879, 8931, 8626, 8544, False, roll="GLOBAL_POS_Y")
    makeBone("pinky.2.R", "pinky.1.R", None, None, 8640, 8547, roll="GLOBAL_POS_Y")
    makeBone("pinky.3.R", "pinky.2.R", None, None, 8684, 8585, roll="GLOBAL_POS_Y")
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')


def skin():
    skin = bpy.data.objects[skinName]
    amt = bpy.data.objects[rootName]
    skin.select_set(True)
    amt.select_set(True)
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    bpy.ops.object.select_all(action='DESELECT')


def bind_items():
    amt = bpy.data.objects[rootName]
    to_head = ["hair", "eyebrow", "eye","teeth",  "tongue"]
    for x in to_head:
        _skin = bpy.data.objects[x]
        
        bpy.ops.object.select_all(action='DESELECT')
        _skin.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(_skin.data)
        print(dir(bm))
        bm.verts.ensure_lookup_table()
        verts = [y.index for y in bm.verts ]
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
            
        _skin.vertex_groups.new(name="head")
        group = _skin.vertex_groups['head']
        group.add(verts, 1.0, 'REPLACE' )
        
        _skin.select_set(True)
        amt.select_set(True)
        bpy.ops.object.parent_set()
        bpy.ops.object.select_all(action='DESELECT')


# bpy.ops.object.mode_set(mode='OBJECT')
# getRef()
# fixSkin()
# rig()
# skin()
bind_items()



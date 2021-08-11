

import bpy, bmesh

skinName = "body"
refName = "ref"
refPath = "C:\\Users\\bo2\Desktop\\Theo\\fRig\\ref.blend"
rootName = "root"
amtName = "amt"


def fix_Skin():
    bpy.ops.object.mode_set(mode='OBJECT')

    # get ref
    with bpy.data.libraries.load(refPath, link=False) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects if name.startswith(refName)]
    for obj in data_to.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)
    bpy.ops.object.select_all(action='DESELECT')
    # get ref
    
    a = [1879, 3902]
    ref = bpy.data.objects[refName]
    skin = bpy.data.objects[skinName]

    bpy.ops.object.select_all(action='DESELECT')
    ref.select_set(True)
    bpy.context.view_layer.objects.active = ref
    
    bpy.ops.object.mode_set(mode='EDIT')

    bm = bmesh.from_edit_mesh(ref.data)
    bm.faces.ensure_lookup_table()
    bm.select_history.add(bm.faces[a[0]])
    bm.select_history.add(bm.faces[a[1]])
    
    for x in bm.select_history:
        x.select = True
        
    print(bm.select_history.active.select_set)
    print(dir(bm.select_history.active.select_set))

    # bpy.ops.object.copy_vert_id()
    CopyVertID().execute()

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    skin.select_set(True)
    bpy.context.view_layer.objects.active = skin

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')

    # bpy.ops.object.paste_vert_id()
    PasteVertID().execute()

    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='DESELECT')
    ref.select_set(True)
    skin.select_set(True)
    bpy.context.view_layer.objects.active = skin
    bpy.ops.object.data_transfer(use_reverse_transfer=True, data_type='VGROUP_WEIGHTS', vert_mapping='TOPOLOGY', layers_select_src='NAME', layers_select_dst='ALL')
    bpy.ops.object.select_all(action='DESELECT')
    
    ref.select_set(True)
    bpy.ops.object.delete()


def build_rig():
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
    # makeBone("foot.L", "calf.twist.L", None, None, 874, 945, roll="POS_X") # fix new pos
    makeBone("ball.L", "foot.L", None, None, 1161, 1157, roll="GLOBAL_POS_Z")

    makeBone("thigh.R", "pelvis", 4411, 4529, 2663, 2629, False, roll="GLOBAL_NEG_Y")
    makeBone("thigh.twist.R", "thigh.R", None, None, 2322, 2586, roll="GLOBAL_NEG_Y")
    makeBone("calf.R", "thigh.twist.R", None, None, 2596, 2538, roll="GLOBAL_POS_Y")
    makeBone("calf.twist.R", "calf.R", None, None, 3168, 3201, roll="GLOBAL_POS_Y")
    makeBone("foot.R", "calf.twist.R", None, None, 3234, 3246, roll="POS_X")
    # makeBone("foot.R", "calf.twist.R", None, None, 3216, 3287, roll="POS_X") # fix new pos
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


def skin_rig():
    skin = bpy.data.objects[skinName]
    amt = bpy.data.objects[rootName]
    skin.select_set(True)
    amt.select_set(True)
    bpy.context.view_layer.objects.active = amt
    # bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    bpy.ops.object.parent_set(type='ARMATURE_NAME')
    bpy.ops.object.select_all(action='DESELECT')


def bind_items():
    amt = bpy.data.objects[rootName]
    to_head = ["hair", "eyebrow", "eye","teeth",  "tongue"]
    for x in to_head:
        item = bpy.data.objects[x]
        
        bpy.ops.object.select_all(action='DESELECT')
        item.select_set(True)
        bpy.context.view_layer.objects.active = item
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(item.data)
        print(dir(bm))
        bm.verts.ensure_lookup_table()
        verts = [y.index for y in bm.verts ]
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
            
        item.vertex_groups.new(name="head")
        group = item.vertex_groups['head']
        group.add(verts, 1.0, 'REPLACE' )
        
        item.select_set(True)
        amt.select_set(True)
        bpy.context.view_layer.objects.active = amt
        bpy.ops.object.parent_set(type='ARMATURE_NAME')
        bpy.ops.object.select_all(action='DESELECT')


#***************************************


from collections import OrderedDict

class CopyIDs():
    def __init__(self):
        self.transuv = ID_DATA()

class ID_DATA():
    face_vert_ids = []
    face_edge_ids = []
    faces_id = []


class CopyVertID():
    def execute(self):
        props = bpy.context.scene.copy_indices.transuv
        active_obj = bpy.context.active_object
        self.obj = active_obj
        bm = bmesh.from_edit_mesh(active_obj.data)
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        props.face_vert_ids.clear()
        props.face_edge_ids.clear()
        props.faces_id.clear()

        # get selected faces
        # active_face = bm.faces.active
        # sel_faces = [face for face in bm.faces if face.select]
        active_face = bm.select_history.active
        sel_faces = [x for x in bm.select_history]
        if len(sel_faces) != 2:
            self.report({'WARNING'}, "Two faces must be selected")
            return {'CANCELLED'}
        if not active_face or active_face not in sel_faces:
            self.report({'WARNING'}, "Two faces must be active")
            return {'CANCELLED'}

        # parse all faces according to selection
        active_face_nor = active_face.normal.copy()
        all_sorted_faces = main_parse(self, sel_faces, active_face, active_face_nor)
        if all_sorted_faces:
            for face, face_data in all_sorted_faces.items():
                verts = face_data[0]
                edges = face_data[1]
                props.face_vert_ids.append([vert.index for vert in verts])
                props.face_edge_ids.append([e.index for e in edges])
                props.faces_id.append(face.index)

        bmesh.update_edit_mesh(active_obj.data)


class PasteVertID():
    # invert_normals: bpy.props.BoolProperty(name="Invert Normals", description="Invert Normals", default=False)

    @staticmethod
    def sortOtherVerts(processedVertsIdDict, preocessedEdgesIsDict, preocessedFaceIsDict, bm):
        """Prevet verts on other islands from being all shuffled"""
        # dicts instead of lists - faster search 4x?
        if len(bm.verts) == len(processedVertsIdDict) and len(bm.faces) == len(preocessedFaceIsDict): 
            return #all verts, and faces were processed - > no other Islands -> quit

        def fix_islands(processed_items, bm_element): #face, verts, or edges
            processedItems = {item: id for (item, id) in processed_items.items()}  # dicts instead of lists
            processedIDs = {id: 1 for (item, id) in processed_items.items()}  # dicts instead of lists

            notProcessedItemsIds = {ele.index: 1 for ele in bm_element if ele not in processedItems}  # it will have duplicated ids from processedIDs that have to be

            spareIDS = [i for i in range(len(bm_element)) if (i not in processedIDs and i not in notProcessedItemsIds)]

            notProcessedElements = [item for item in bm_element if item not in processedItems]
            for item in notProcessedElements:
                if item.index in processedIDs:  # if duplicated id found in not processed verts
                    item.index = spareIDS.pop(0)  # what if list is empty??

        fix_islands(processedVertsIdDict, bm.verts)
        fix_islands(preocessedEdgesIsDict, bm.edges)
        fix_islands(preocessedFaceIsDict, bm.faces)


    def execute(self):
        props = bpy.context.scene.copy_indices.transuv
        active_obj = bpy.context.active_object
        bm = bmesh.from_edit_mesh(active_obj.data)
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        # get selection history
        all_sel_faces = [
            e for e in bm.select_history
            if isinstance(e, bmesh.types.BMFace) and e.select]
        if len(all_sel_faces) % 2 != 0:
            self.report({'WARNING'}, "Two faces must be selected")
            return {'CANCELLED'}

        # parse selection history
        vertID_dict = {}
        edgeID_dict = {}
        faceID_dict = {}
        for i, _ in enumerate(all_sel_faces):
            if (i == 0) or (i % 2 == 0):
                continue
            sel_faces = [all_sel_faces[i - 1], all_sel_faces[i]]
            active_face = all_sel_faces[i]

            # parse all faces according to selection history
            active_face_nor = active_face.normal.copy()
            # if self.invert_normals:
            #     active_face_nor.negate()
            all_sorted_faces = main_parse(self, sel_faces, active_face, active_face_nor)
            # ipdb.set_trace()
            if all_sorted_faces:
                # check amount of copied/pasted faces
                if len(all_sorted_faces) != len(props.face_vert_ids):
                    self.report(
                        {'WARNING'},
                        "Mesh has different amount of faces"
                    )
                    return {'FINISHED'}

                for j,(face, face_data) in enumerate(all_sorted_faces.items()):
                    vert_ids_cache = props.face_vert_ids[j]
                    edge_ids_cache = props.face_edge_ids[j]
                    face_id_cache = props.faces_id[j]

                    # check amount of copied/pasted verts
                    if len(vert_ids_cache) != len(face_data[0]):
                        bpy.ops.mesh.select_all(action='DESELECT')
                        # select problematic face
                        list(all_sorted_faces.keys())[j].select = True
                        self.report(
                            {'WARNING'},
                            "Face have different amount of vertices"
                        )
                        return {'FINISHED'}


                    for k, vert in enumerate(face_data[0]):
                        vert.index = vert_ids_cache[k]  #index
                        vertID_dict[vert] = vert.index
                    face.index = face_id_cache
                    faceID_dict[face] = face_id_cache
                    for k, edge in enumerate(face_data[1]): #edges
                        edge.index = edge_ids_cache[k]  # index
                        edgeID_dict[edge] = edge.index
        self.sortOtherVerts(vertID_dict, edgeID_dict, faceID_dict, bm)
        bm.verts.sort()
        bm.edges.sort()
        bm.faces.sort()
        bmesh.update_edit_mesh(active_obj.data)


def main_parse(self, sel_faces, active_face, active_face_nor):
    all_sorted_faces = OrderedDict()  # This is the main stuff

    used_verts = set()
    used_edges = set()

    faces_to_parse = []

    # get shared edge of two faces
    cross_edges = []
    for edge in active_face.edges:
        if edge in sel_faces[0].edges and edge in sel_faces[1].edges:
            cross_edges.append(edge)

    # parse two selected faces
    if cross_edges and len(cross_edges) == 1:
        shared_edge = cross_edges[0]
        vert1 = None
        vert2 = None

        dot_n = active_face_nor.normalized()
        edge_vec_1 = (shared_edge.verts[1].co - shared_edge.verts[0].co)
        edge_vec_len = edge_vec_1.length
        edge_vec_1 = edge_vec_1.normalized()

        af_center = active_face.calc_center_median()
        af_vec = shared_edge.verts[0].co + (edge_vec_1 * (edge_vec_len * 0.5))
        af_vec = (af_vec - af_center).normalized()

        if af_vec.cross(edge_vec_1).dot(dot_n) > 0:
            vert1 = shared_edge.verts[0]
            vert2 = shared_edge.verts[1]
        else:
            vert1 = shared_edge.verts[1]
            vert2 = shared_edge.verts[0]

        # get active face stuff and uvs
        # ipdb.set_trace()
        face_stuff = get_other_verts_edges(active_face, vert1, vert2, shared_edge)
        all_sorted_faces[active_face] = face_stuff
        used_verts.update(active_face.verts)
        used_edges.update(active_face.edges)

        # get first selected face stuff and uvs as they share shared_edge
        second_face = sel_faces[0]
        if second_face is active_face:
            second_face = sel_faces[1]
        face_stuff = get_other_verts_edges(second_face, vert1, vert2, shared_edge)
        all_sorted_faces[second_face] = face_stuff
        used_verts.update(second_face.verts)
        used_edges.update(second_face.edges)

        # first Grow
        faces_to_parse.append(active_face)
        faces_to_parse.append(second_face)

    else:
        self.report({'WARNING'}, "Two faces should share one edge")
        return None

    # parse all faces
    while True:
        new_parsed_faces = []

        if not faces_to_parse:
            break
        for face in faces_to_parse:
            face_stuff = all_sorted_faces.get(face)
            new_faces = parse_faces(face, face_stuff, used_verts, used_edges, all_sorted_faces)
            if new_faces == 'CANCELLED':
                self.report({'WARNING'}, "More than 2 faces share edge")
                return None

            new_parsed_faces += new_faces
        faces_to_parse = new_parsed_faces

    return all_sorted_faces


def parse_faces(check_face, face_stuff, used_verts, used_edges, all_sorted_faces):
    """recurse faces around the new_grow only"""

    new_shared_faces = []
    for sorted_edge in face_stuff[1]:
        shared_faces = sorted_edge.link_faces
        if shared_faces:
            if len(shared_faces) > 2:
                bpy.ops.mesh.select_all(action='DESELECT')
                for face_sel in shared_faces:
                    face_sel.select = True
                shared_faces = []
                return 'CANCELLED'

            clear_shared_faces = get_new_shared_faces(check_face, sorted_edge, shared_faces, all_sorted_faces.keys())
            if clear_shared_faces:
                shared_face = clear_shared_faces[0]
                # get vertices of the edge
                vert1 = sorted_edge.verts[0]
                vert2 = sorted_edge.verts[1]

                if face_stuff[0].index(vert1) > face_stuff[0].index(vert2):
                    vert1 = sorted_edge.verts[1]
                    vert2 = sorted_edge.verts[0]

                new_face_stuff = get_other_verts_edges(shared_face, vert1, vert2, sorted_edge)
                all_sorted_faces[shared_face] = new_face_stuff
                used_verts.update(shared_face.verts)
                used_edges.update(shared_face.edges)

                new_shared_faces.append(shared_face)

    return new_shared_faces


def get_new_shared_faces(orig_face, shared_edge, check_faces, used_faces):
    shared_faces = []

    for face in check_faces:
        is_shared_edge = shared_edge in face.edges
        not_used = face not in used_faces
        not_orig = face is not orig_face
        not_hide = face.hide is False
        if is_shared_edge and not_used and not_orig and not_hide:
            shared_faces.append(face)

    return shared_faces


def get_other_verts_edges(face, vert1, vert2, first_edge):
    face_edges = [first_edge]
    face_verts = [vert1, vert2]

    other_edges = [edge for edge in face.edges if edge not in face_edges]

    for _ in range(len(other_edges)):
        found_edge = None
        # get sorted verts and edges
        for edge in other_edges:
            if face_verts[-1] in edge.verts:
                other_vert = edge.other_vert(face_verts[-1])

                if other_vert not in face_verts:
                    face_verts.append(other_vert)

                found_edge = edge
                if found_edge not in face_edges:
                    face_edges.append(edge)
                break

        other_edges.remove(found_edge)

    return [face_verts, face_edges]




#***************************************


bl_info = {
    "name": "fRig",
    "blender": (2, 80, 0),
    "category": "Object",
}

class Rig(bpy.types.Operator):
    """Auto rig"""      # Use this as a tooltip for menu items and buttons.
    bl_idname = "object.f_rig"        # Unique identifier for buttons and menu items to reference.
    bl_label = "fRig"         # Display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.

    def execute(self, context):        # execute() is called when running the operator.
        fix_Skin()
        build_rig()
        skin_rig()
        bind_items()

        return {'FINISHED'}            # Lets Blender know the operator finished successfully.

def menu_func(self, context):
    self.layout.operator(Rig.bl_idname)

def register():
    bpy.utils.register_class(Rig)
    bpy.types.VIEW3D_MT_object.append(menu_func)  # Adds the new operator to an existing menu.

def unregister():
    bpy.utils.unregister_class(Rig)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
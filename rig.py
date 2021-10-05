# ##### LICENSE BLOCK #####
#
#  Not to be used in Production
#
# ##### LICENSE BLOCK #####


import bpy, bmesh
import os


#***************************************
#***************************************
#***************************************


from collections import OrderedDict

class ID_DATA():
    face_vert_ids = []
    face_edge_ids = []
    faces_id = []


class CopyVertID():
    def execute(self):
        props = ID_DATA()
        active_obj = bpy.context.active_object
        self.obj = active_obj
        bm = bmesh.from_edit_mesh(active_obj.data)
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        props.face_vert_ids.clear()
        props.face_edge_ids.clear()
        props.faces_id.clear()

        active_face = bm.select_history.active
        sel_faces = [x for x in bm.select_history]
        if len(sel_faces) != 2:
            self.report({'WARNING'}, "Two faces must be selected")
            return {'CANCELLED'}
        if not active_face or active_face not in sel_faces:
            self.report({'WARNING'}, "Two faces must be active")
            return {'CANCELLED'}

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
        props = ID_DATA()
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
#***************************************
#***************************************

bone_strct_cc = [
    {"name":"pelvis", "parent": None, "h1": 4559, "h2":2209, "t1": 2247, "t2": 4387, "or":"GLOBAL_NEG_Z", "conn":True},
    {"name":"spine.1", "parent": "pelvis", "h1": None, "h2": None, "t1": 4050, "t2": 4060, "or":"NEG_X", "conn":True},
    {"name":"spine.2", "parent": "spine.1", "h1": None, "h2":None, "t1": 3987, "t2":4149, "or":"NEG_X", "conn":True},
    {"name":"spine.3", "parent": "spine.2", "h1": None, "h2": None, "t1": 9320, "t2":4008, "or":"POS_X", "conn":True},
    {"name":"neck.1", "parent": "spine.3", "h1": None, "h2":None, "t1": 13106, "t2":11046, "or":"POS_X", "conn":True},
    {"name":"neck.2", "parent": "neck.1", "h1": None, "h2": None, "t1": 11515, "t2": 9515, "or":"POS_X", "conn":True},
    {"name":"head", "parent": "neck.2", "h1": None, "h2": None, "t1": 11288, "t2":11288, "or":"NEG_X", "conn":True},

    {"name":"thigh.L", "parent": "pelvis", "h1": 2164, "h2": 2068, "t1": 15, "t2":481, "or":"GLOBAL_NEG_Y", "conn":False},
    {"name":"thigh.twist.L", "parent": "pelvis", "h1":2164, "h2": 2068, "t1": 327, "t2": 360, "or":"GLOBAL_NEG_Y", "conn":False},
    {"name":"calf.L", "parent": "thigh.L", "h1": None, "h2": None, "t1": 858, "t2": 825, "or":"GLOBAL_POS_Y", "conn":True},
    {"name":"calf.twist.L", "parent": "thigh.L", "h1":None, "h2": None, "t1": 301, "t2": 283, "or":"GLOBAL_POS_Y", "conn":True},
    {"name":"foot.L", "parent": "calf.L", "h1": None, "h2": None, "t1": 874, "t2": 945, "or":"POS_X", "conn":True},
    {"name":"ball.L", "parent": "foot.L", "h1": None, "h2": None, "t1": 1161, "t2": 1157, "or":"GLOBAL_POS_Z", "conn":True},

    {"name":"thigh.R", "parent": "pelvis", "h1": 4411, "h2": 4529, "t1":2322, "t2": 2586, "or":"GLOBAL_NEG_Y", "conn":False},
    {"name":"thigh.twist.R", "parent": "pelvis", "h1":4411, "h2":4529, "t1": 2663, "t2":2629, "or":"GLOBAL_NEG_Y", "conn":False},
    {"name":"calf.R", "parent": "thigh.R", "h1": None, "h2": None, "t1":3168, "t2": 3201, "or":"GLOBAL_POS_Y", "conn":True},
    {"name":"calf.twist.R", "parent": "thigh.R", "h1": None, "h2": None, "t1":2596, "t2": 2538, "or":"GLOBAL_POS_Y", "conn":True},
    {"name":"foot.R", "parent": "calf.R", "h1": None, "h2":None, "t1": 3216, "t2": 3287, "or":"POS_X", "conn":True},
    {"name":"ball.R", "parent": "foot.R", "h1": None, "h2": None, "t1": 3519, "t2": 3514, "or":"GLOBAL_POS_Z", "conn":True},

    {"name":"clavicle.L", "parent": "spine.3", "h1": 1780, "h2": 1723, "t1": 4804, "t2": 4774, "or":"NEG_X", "conn":False},
    {"name":"upperarm.L", "parent": "clavicle.L", "h1":None, "h2": None, "t1": 5078, "t2": 5068, "or":"GLOBAL_NEG_Z", "conn":True},
    {"name":"upperarm.twist.L", "parent": "clavicle.L", "h1": None, "h2":None, "t1": 4777, "t2": 4799, "or":"NEG_X", "conn":True},
    {"name":"lowerarm.L", "parent": "upperarm.L", "h1": None, "h2": None, "t1": 6917, "t2": 6928, "or":"GLOBAL_POS_X", "conn":True},
    {"name":"lowerarm.twist.L", "parent": "upperarm.L", "h1": None, "h2": None, "t1": 4610, "t2": 4614, "or":"NEG_Z", "conn":True},
    {"name":"hand.L", "parent": "lowerarm.L", "h1": None, "h2": None, "t1":6316, "t2":5454, "or":"GLOBAL_NEG_Z", "conn":True},

    {"name":"clavicle.R", "parent": "spine.3", "h1": 4127, "h2": 4154, "t1": 7228, "t2": 7197, "or":"POS_X", "conn":False},
    {"name":"upperarm.R", "parent": "clavicle.R", "h1": None, "h2": None, "t1": 7396, "t2":7469, "or":"GLOBAL_NEG_Z", "conn":True},
    {"name":"upperarm.twist.R", "parent": "clavicle.R", "h1": None, "h2": None, "t1": 7160, "t2": 7190, "or":"POS_X", "conn":True},
    {"name":"lowerarm.R", "parent": "upperarm.R", "h1": None, "h2": None, "t1": 9230, "t2": 8753, "or":"GLOBAL_NEG_X", "conn":True},
    {"name":"lowerarm.twist.R", "parent": "upperarm.R", "h1": None, "h2":None, "t1": 6968, "t2":6974, "or":"POS_Z", "conn":True},
    {"name":"hand.R", "parent": "lowerarm.R", "h1": None, "h2": None, "t1": 8735, "t2": 7889, "or":"GLOBAL_POS_Z", "conn":True},

    {"name":"thumb.1.L", "parent": "hand.L", "h1":6287, "h2": 6770, "t1": 6415, "t2": 6614, "or":"GLOBAL_POS_Y", "conn":False},
    {"name":"thumb.2.L", "parent": "thumb.1.L", "h1": None, "h2": None, "t1": 6608, "t2":6712, "or":"GLOBAL_POS_Y", "conn":True},
    {"name":"thumb.3.L", "parent": "thumb.2.L", "h1": None, "h2":None, "t1":6746, "t2":6673, "or":"GLOBAL_POS_Y", "conn":True},
    {"name":"index.1.L", "parent": "hand.L", "h1": 6486, "h2": 6504, "t1": 5692, "t2":5749, "or":"GLOBAL_NEG_Z", "conn":False},
    {"name":"index.2.L", "parent": "index.1.L", "h1": None, "h2":None, "t1":5701, "t2":5753, "or":"GLOBAL_NEG_Z", "conn":True},
    {"name":"index.3.L", "parent": "index.2.L", "h1": None, "h2":None, "t1": 5796, "t2":5798, "or":"GLOBAL_NEG_Z", "conn":True},
    {"name":"middle.1.L", "parent": "hand.L", "h1": 6525, "h2": 6292, "t1": 5494, "t2": 5551, "or":"GLOBAL_NEG_Z", "conn":False},
    {"name":"middle.2.L", "parent": "middle.1.L", "h1": None, "h2": None, "t1": 5503, "t2": 5561, "or":"GLOBAL_NEG_Z", "conn":True},
    {"name":"middle.3.L", "parent": "middle.2.L", "h1":None, "h2": None, "t1": 5601, "t2": 5603, "or":"GLOBAL_NEG_Z", "conn":True},
    {"name":"ring.1.L", "parent": "hand.L", "h1": 6873, "h2": 6348, "t1": 5984, "t2": 5927, "or":"GLOBAL_NEG_Z", "conn":False},
    {"name":"ring.2.L", "parent": "ring.1.L", "h1": None, "h2": None, "t1": 5990, "t2": 5937, "or":"GLOBAL_NEG_Z", "conn":True},
    {"name":"ring.3.L", "parent":"ring.2.L", "h1": None, "h2": None, "t1": 5964, "t2": 6062, "or":"GLOBAL_NEG_Z", "conn":True},
    {"name":"pinky.1.L", "parent": "hand.L", "h1": 6519, "h2":6469, "t1": 6182, "t2": 6120, "or":"GLOBAL_NEG_Z", "conn":False},
    {"name":"pinky.2.L", "parent": "pinky.1.L", "h1": None, "h2": None, "t1": 6188, "t2": 6124, "or":"GLOBAL_NEG_Z", "conn":True},
    {"name":"pinky.3.L", "parent": "pinky.2.L", "h1": None, "h2": None, "t1": 6162, "t2":6262, "or":"GLOBAL_NEG_Z", "conn":True},

    {"name":"thumb.1.R", "parent": "hand.R", "h1": 8705, "h2": 9027, "t1": 8830, "t2":9034, "or":"GLOBAL_NEG_Y", "conn":False},
    {"name":"thumb.2.R", "parent": "thumb.1.R", "h1": None, "h2": None, "t1": 9127, "t2": 9030, "or":"GLOBAL_NEG_Y", "conn":True},
    {"name":"thumb.3.R", "parent": "thumb.2.R", "h1": None, "h2":None, "t1": 9161, "t2":9089, "or":"GLOBAL_NEG_Y", "conn":True},
    {"name":"index.1.R", "parent": "hand.R", "h1": 8898, "h2": 8914, "t1": 8117, "t2": 8176, "or":"GLOBAL_POS_Z", "conn":False},
    {"name":"index.2.R", "parent": "index.1.R", "h1": None, "h2": None, "t1": 8126, "t2":8179, "or":"GLOBAL_POS_Z", "conn":True},
    {"name":"index.3.R", "parent": "index.2.R", "h1": None, "h2": None, "t1": 8225, "t2": 8223, "or":"GLOBAL_POS_Z", "conn":True},
    {"name":"middle.1.R", "parent": "hand.R", "h1": 8935, "h2": 8712, "t1":7928, "t2": 7982, "or":"GLOBAL_POS_Z", "conn":False},
    {"name":"middle.2.R", "parent": "middle.1.R", "h1": None, "h2": None, "t1": 7936, "t2": 7986, "or":"GLOBAL_POS_Z", "conn":True},
    {"name":"middle.3.R", "parent": "middle.2.R", "h1": None, "h2": None, "t1": 8034, "t2":8032, "or":"GLOBAL_POS_Z", "conn":True},
    {"name":"ring.1.R", "parent": "hand.R", "h1": 8758, "h2": 8767, "t1":8407, "t2": 8351, "or":"GLOBAL_POS_Z", "conn":False},
    {"name":"ring.2.R", "parent": "ring.1.R", "h1":None, "h2":None, "t1": 8459, "t2": 8414, "or":"GLOBAL_POS_Z", "conn":True},
    {"name":"ring.3.R", "parent": "ring.2.R", "h1":None, "h2": None, "t1": 8486, "t2": 8389, "or":"GLOBAL_POS_Z", "conn":True},
    {"name":"pinky.1.R", "parent": "hand.R", "h1": 8879, "h2": 8931, "t1": 8626, "t2": 8544, "or":"GLOBAL_POS_Z", "conn":False},
    {"name":"pinky.2.R", "parent": "pinky.1.R", "h1": None, "h2": None, "t1": 8640, "t2": 8547, "or":"GLOBAL_POS_Z", "conn":True},
    {"name":"pinky.3.R", "parent": "pinky.2.R", "h1": None, "h2": None, "t1": 8684, "t2": 8585, "or":"GLOBAL_POS_Z", "conn":True},
]

bone_strct_mix =[
    {"name":"pelvis","parent": None, "h1":4952, "h2": 5005, "t1":5513, "t2":4853, "or":'GLOBAL_NEG_Z', "conn":True},
    {"name":"spine.1", "parent":"pelvis", "h1": None, "h2":None, "t1":5493, "t2":4829, "or":"NEG_X", "conn":True},
    {"name":"spine.2", "parent":"spine.1", "h1": None,"h2": None, "t1":5263,"t2": 5087,"or": "NEG_X", "conn":True},
    {"name":"spine.3","parent": "spine.2", "h1": None,"h2": None,"t1": 757, "t2":478,"or": "POS_X", "conn":True},
    {"name":"neck.1", "parent":"spine.3", "h1": None, "h2":None,"t1": 1527,"t2": 18,"or": "POS_X", "conn":True},
    {"name":"neck.2","parent": "neck.1", "h1": None,"h2": None,"t1": 2592,"t2": 1125, "or":"POS_X", "conn":True},
    {"name":"head","parent": "neck.2", "h1": None,"h2": None,"t1": 31, "t2":31,"or": "NEG_X", "conn":True},

    {"name":"thigh.L","parent": "pelvis", "h1": 4887,"h2": 4918, "t1":7214, "t2":7251, "or":"GLOBAL_NEG_Y", "conn":False},
    {"name":"thigh.twist.L","parent": "thigh.L", "h1": None,"h2": None,"t1": 7040,"t2": 7006, "or":"GLOBAL_NEG_Y", "conn":True},
    {"name":"calf.L","parent": "thigh.twist.L", "h1": None, "h2":None,"t1": 6964, "t2":6936,"or": "GLOBAL_POS_Y", "conn":True},
    {"name":"calf.twist.L","parent": "calf.L", "h1": None,"h2": None, "t1":7086, "t2":7158,"or": "GLOBAL_POS_Y", "conn":True},
    {"name":"foot.L","parent": "calf.twist.L", "h1":None, "h2":None,"t1": 7593,"t2": 7604,"or": "POS_X", "conn":True},
    {"name":"ball.L", "parent":"foot.L", "h1": None, "h2":None, "t1":7349,"t2": 7372,"or": "GLOBAL_POS_Z", "conn":True},

    {"name":"thigh.R","parent": "pelvis", "h1":5571,"h2": 5546,"t1": 8882,"t2": 8845,"or": "GLOBAL_NEG_Y", "conn":False},
    {"name":"thigh.twist.R","parent": "thigh.R", "h1": None,"h2": None,"t1": 8637,"t2": 8671,"or": "GLOBAL_NEG_Y", "conn":True},
    {"name":"calf.R", "parent":"thigh.twist.R", "h1": None,"h2": None,"t1": 8564,"t2": 8592,"or": "GLOBAL_POS_Y", "conn":True},
    {"name":"calf.twist.R","parent": "calf.R", "h1": None, "h2":None,"t1": 8788,"t2": 8716,"or": "GLOBAL_POS_Y", "conn":True},
    {"name":"foot.R","parent": "calf.twist.R", "h1":None,"h2": None, "t1":9224,"t2": 9234,"or": "POS_X", "conn":True},
    {"name":"ball.R", "parent":"foot.R", "h1": None,"h2": None, "t1":9000,"t2": 8979,"or": "GLOBAL_POS_Z", "conn":True},

    {"name":"clavicle.L","parent": "spine.3", "h1": 477,"h2": 712, "t1":5070,"t2": 5096,"or": "NEG_X", "conn":False},
    {"name":"upperarm.L", "parent":"clavicle.L", "h1": None,"h2": None,"t1": 6824,"t2": 6816, "or":"GLOBAL_NEG_Z", "conn":True},
    {"name":"upperarm.twist.L","parent": "upperarm.L", "h1": None, "h2":None, "t1":6244,"t2": 6223, "or":"NEG_X", "conn":True},
    {"name":"lowerarm.L","parent": "upperarm.twist.L", "h1": None, "h2":None, "t1":6283,"t2": 6287,"or": "GLOBAL_POS_X", "conn":True},
    {"name":"lowerarm.twist.L","parent": "lowerarm.L", "h1":None,"h2": None, "t1":6324, "t2":6333,"or": "NEG_Z", "conn":True},
    {"name":"hand.L","parent": "lowerarm.twist.L", "h1": None,"h2": None, "t1":6891, "t2":6837,"or": "GLOBAL_NEG_Z", "conn":True},

    {"name":"clavicle.R","parent": "spine.3", "h1": 1964,"h2": 2184,"t1": 5697,"t2": 5722,"or": "POS_X", "conn":False},
    {"name":"upperarm.R","parent": "clavicle.R", "h1": None,"h2": None, "t1":8456,"t2": 8446, "or":"GLOBAL_NEG_Z", "conn":True},
    {"name":"upperarm.twist.R","parent": "upperarm.R", "h1": None,"h2": None,"t1": 7874,"t2": 7853,"or": "POS_X", "conn":True},
    {"name":"lowerarm.R","parent": "upperarm.twist.R", "h1": None, "h2":None,"t1": 7913,"t2": 7917, "or":"GLOBAL_NEG_X", "conn":True},
    {"name":"lowerarm.twist.R","parent": "lowerarm.R", "h1":None, "h2":None, "t1":7954,"t2": 7657,"or": "POS_Z", "conn":True},
    {"name":"hand.R", "parent":"lowerarm.twist.R", "h1":None,"h2": None,"t1": 8521, "t2":8467,"or": "GLOBAL_POS_Z", "conn":True},

    {"name":"thumb.1.L","parent": "hand.L", "h1": 6840,"h2": 6713,"t1": 6084, "t2":6077, "or":"GLOBAL_POS_Y", "conn":False},
    {"name":"thumb.2.L", "parent":"thumb.1.L", "h1": None, "h2":None,"t1": 6683, "t2":6691,"or": "GLOBAL_POS_Y", "conn":True},
    {"name":"thumb.3.L", "parent":"thumb.2.L", "h1": None,"h2": None,"t1": 6088, "t2":6088, "or":"GLOBAL_POS_Y", "conn":True},
    {"name":"index.1.L","parent": "hand.L", "h1": 6068,"h2": 6719,"t1": 6601, "t2":6605, "or":"GLOBAL_NEG_Z", "conn":False},
    {"name":"index.2.L","parent": "index.1.L", "h1": None,"h2": None,"t1": 6442,"t2": 6434,"or": "GLOBAL_NEG_Z", "conn":True},
    {"name":"index.3.L","parent": "index.2.L", "h1": None,"h2": None, "t1":6096,"t2": 6096, "or":"GLOBAL_NEG_Z", "conn":True},
    {"name":"middle.1.L","parent": "hand.L", "h1": 6064,"h2": 6724,"t1": 6448,"t2": 6455, "or":"GLOBAL_NEG_Z", "conn":False},
    {"name":"middle.2.L","parent": "middle.1.L", "h1": None,"h2": None,"t1": 6466,"t2": 6474,"or": "GLOBAL_NEG_Z", "conn":True},
    {"name":"middle.3.L","parent": "middle.2.L", "h1": None,"h2": None,"t1": 6103, "t2":6103, "or":"GLOBAL_NEG_Z", "conn":True},
    {"name":"ring.1.L","parent": "hand.L", "h1": 6060,"h2": 6739,"t1": 6480,"t2": 6487, "or":"GLOBAL_NEG_Z", "conn":False},
    {"name":"ring.2.L","parent": "ring.1.L", "h1": None,"h2": None, "t1":6498,"t2": 6506,"or": "GLOBAL_NEG_Z", "conn":True},
    {"name":"ring.3.L","parent": "ring.2.L", "h1": None,"h2": None, "t1":6106,"t2": 6106,"or": "GLOBAL_NEG_Z", "conn":True},
    {"name":"pinky.1.L", "parent":"hand.L", "h1": 6745,"h2": 6740,"t1": 6610,"t2": 6614,"or": "GLOBAL_NEG_Z", "conn":False},
    {"name":"pinky.2.L","parent": "pinky.1.L", "h1": None, "h2":None,"t1": 6530,"t2": 6538,"or": "GLOBAL_NEG_Z", "conn":True},
    {"name":"pinky.3.L","parent": "pinky.2.L", "h1": None, "h2":None, "t1":6095, "t2":6095,"or": "GLOBAL_NEG_Z", "conn":True},

    {"name":"thumb.1.R","parent": "hand.R", "h1": 8343, "h2":8470, "t1":7709, "t2":7714, "or":"GLOBAL_NEG_Y", "conn":False},
    {"name":"thumb.2.R","parent": "thumb.1.R", "h1": None,"h2": None,"t1": 8320,"t2": 8312, "or":"GLOBAL_NEG_Y", "conn":True},
    {"name":"thumb.3.R", "parent":"thumb.2.R", "h1": None, "h2":None, "t1":7718, "t2":7718, "or":"GLOBAL_NEG_Y", "conn":True},
    {"name":"index.1.R", "parent":"hand.R" ,"h1": 7698,"h2": 8349, "t1":8231,"t2": 8235, "or":"GLOBAL_POS_Z", "conn":False},
    {"name":"index.2.R", "parent":"index.1.R", "h1": None, "h2":None,"t1": 8072,"t2": 8063, "or":"GLOBAL_POS_Z", "conn":True},
    {"name":"index.3.R","parent": "index.2.R", "h1": None,"h2": None,"t1": 7726, "t2":7726, "or":"GLOBAL_POS_Z", "conn":True},
    {"name":"middle.1.R","parent": "hand.R", "h1": 8354,"h2": 7694,"t1": 8085,"t2": 8080, "or":"GLOBAL_POS_Z", "conn":False},
    {"name":"middle.2.R","parent": "middle.1.R", "h1": None,"h2": None,"t1": 8104,"t2": 8095, "or":"GLOBAL_POS_Z", "conn":True},
    {"name":"middle.3.R","parent": "middle.2.R", "h1": None,"h2": None,"t1": 7731,"t2": 7731, "or":"GLOBAL_POS_Z", "conn":True},
    {"name":"ring.1.R","parent": "hand.R", "h1": 8369,"h2": 7690,"t1": 8117, "t2":8112, "or":"GLOBAL_POS_Z", "conn":False},
    {"name":"ring.2.R","parent": "ring.1.R", "h1": None, "h2":None, "t1":8136,"t2": 8127, "or":"GLOBAL_POS_Z", "conn":True},
    {"name":"ring.3.R", "parent":"ring.2.R", "h1": None,"h2": None, "t1":7736,"t2": 7736, "or":"GLOBAL_POS_Z", "conn":True},
    {"name":"pinky.1.R","parent": "hand.R", "h1": 8371,"h2": 8375, "t1":8244,"t2": 8240, "or":"GLOBAL_POS_Z", "conn":False},
    {"name":"pinky.2.R","parent": "pinky.1.R", "h1": None, "h2":None,"t1": 8168,"t2": 8159, "or":"GLOBAL_POS_Z", "conn":True},
    {"name":"pinky.3.R","parent": "pinky.2.R", "h1": None,"h2": None, "t1":7723,"t2": 7723, "or":"GLOBAL_POS_Z", "conn":True},
]

ref_faces_auto_cc = [2197, 2199]
ref_faces_cc = [1879, 3902]
ref_faces_auto_mix = [1210, 1011]
ref_faces_mix = [684, 685]

base_model = ""
ref_faces = []
bone_strct = []


body_name = "body"
root_name = "root"
ref_path="C:\\cc_u_rig\\_"

auto_select_faces = True


def validate_skin_mesh(self, body_name, ref_path):

    bpy.ops.object.mode_set(mode='OBJECT')

    if body_name not in bpy.data.objects:
        self.report({'ERROR'}, "body mesh not found")
        return {'CANCELLED'}
    
    bpy.ops.object.select_all(action='DESELECT')
    body = bpy.data.objects[body_name]
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bm = bmesh.from_edit_mesh(body.data)
    bm.faces.ensure_lookup_table()

    if len(bm.faces) != 14046 and len(bm.faces) != 9452:
        self.report({'ERROR'}, "Mesh has different amount of faces / topology")
        return {'CANCELLED'}
    
    global base_model
    global ref_faces
    global bone_strct
    if len(bm.faces) == 14046:
        base_model = "cc"
        ref_faces = ref_faces_auto_cc if auto_select_faces else ref_faces_cc
        bone_strct = bone_strct_cc
    elif len(bm.faces) == 9452:
        base_model = "mix"
        ref_faces = ref_faces_auto_mix if auto_select_faces else ref_faces_mix
        bone_strct = bone_strct_mix

    if not auto_select_faces:
        if len(bm.select_history) != 2:
            self.report({'ERROR'}, "Two specific faces must be selected")
            return {'CANCELLED'}

        face_verts_1 =[x.index for x in bm.select_history[0].verts]
        face_verts_2 =[x.index for x in bm.select_history[1].verts]
        common_verts = list(set(face_verts_1) & set(face_verts_2))

        if len(common_verts) != 2:
            self.report({'ERROR'}, "Two adjacent faces must be selected")
            return {'CANCELLED'}

    bpy.ops.object.mode_set(mode='OBJECT')

    if not os.path.exists(ref_path):
        self.report({'ERROR'}, f"{ref_path} not found")
        return {'CANCELLED'}

    return {'FINISHED'}
  

def fix_Skin(body_name, f_, ref_path):
    bpy.ops.object.mode_set(mode='OBJECT')

    # get ref
    with bpy.data.libraries.load(f"{ref_path}", link=False) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects if name.startswith(base_model)]
    for obj in data_to.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)
    bpy.ops.object.select_all(action='DESELECT')
    # get ref
    
    ref = bpy.data.objects[base_model]
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
    bm.select_history.add(bm.faces[f_[0]])
    bm.select_history.add(bm.faces[f_[1]])
    
    for x in bm.select_history:
        x.select = True

    CopyVertID().execute()

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')

    def manual_select():
        # face selection order fix
        bm = bmesh.from_edit_mesh(body.data)
        bm.faces.ensure_lookup_table()

        left_face = bm.select_history[0]
        right_face = bm.select_history[1]

        face1_x_pos = bm.select_history[0].calc_center_median()[0]
        face2_x_pos = bm.select_history[1].calc_center_median()[0]
        
        if face1_x_pos > face2_x_pos:
            left_face = bm.select_history[1]
            right_face = bm.select_history[0]

        bm.select_history.clear()
        for x in bm.select_history:
            x.select = False
        
        bm.select_history.add(left_face)
        bm.select_history.add(right_face)
        for x in bm.select_history:
            x.select = True

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
                    "vert":x,
                    "x":x.co[0],
                    "y":x.co[1],
                    "z":x.co[2]
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
                "face":i,
                "x":i.calc_center_median()[0],
                "y":i.calc_center_median()[1],
                "z":i.calc_center_median()[2]
            })
            

        f_i = sorted(f_i, key=lambda k: k['z'])[:-1]
        f_i = sorted(f_i, key=lambda k: k['y']) 


        for i in f_i:
            face = i["face"]
            bm.select_history.add(face)
            face.select = True



    auto_select() if auto_select_faces else manual_select()

    PasteVertID().execute()

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    
    ref.select_set(True)
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.data_transfer(use_reverse_transfer=True, data_type='VGROUP_WEIGHTS', vert_mapping='TOPOLOGY', layers_select_src='NAME', layers_select_dst='ALL')
    bpy.ops.object.select_all(action='DESELECT')
    
    ref.select_set(True)
    bpy.ops.object.delete()


def build_rig(body_name, root_name):
    bpy.ops.object.mode_set(mode='OBJECT')
    body = bpy.data.objects[body_name]

    bpy.ops.object.armature_add()
    root = bpy.data.objects['Armature']
    root.name = root_name
    root.show_in_front = True
    root.location = body.location

    amt = root.data
    amt.name= "amt"
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
        
        if h1 and h2: bone.head = point(h1, h2)
        bone.tail = point(t1, t2)

        if parent_name:
            bone.parent = amt.edit_bones[parent_name]
            bone.use_connect = connect

        if roll: bpy.ops.armature.calculate_roll(type=roll)


    for i in bone_strct:
        makeBone(i["name"], i["parent"], i["h1"], i["h2"], i["t1"], i["t2"], i["or"], i["conn"])

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')


def skin_rig(body_name, root_name):
    body = bpy.data.objects[body_name]
    amt = bpy.data.objects[root_name]

    body.select_set(True)
    amt.select_set(True)
    bpy.context.view_layer.objects.active = amt
    bpy.ops.object.parent_set(type='ARMATURE_NAME')
    body.modifiers["Armature"].use_deform_preserve_volume = True

    bpy.ops.object.select_all(action='DESELECT')


def bind_items(body_name, root_name):
    amt = bpy.data.objects[root_name]
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
                verts = [ y.index for y in bm.verts ]

                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_all(action='DESELECT')
                    
                x.vertex_groups.new(name="head")
                x.vertex_groups['head'].add(verts, 1.0, 'REPLACE' )
                
                x.select_set(True)
                amt.select_set(True)
                bpy.context.view_layer.objects.active = amt
                bpy.ops.object.parent_set(type='ARMATURE_NAME')
            
            
            elif "cloth" in [x.name.split(".")[0], x.name]:
                x.select_set(True)
                body.select_set(True)
                bpy.context.view_layer.objects.active = x            
                bpy.ops.object.data_transfer(use_reverse_transfer=True, data_type='VGROUP_WEIGHTS', vert_mapping='POLYINTERP_NEAREST', layers_select_src='NAME', layers_select_dst='ALL')

                bpy.ops.object.select_all(action='DESELECT')
                
                x.select_set(True)
                amt.select_set(True)
                bpy.context.view_layer.objects.active = amt
                bpy.ops.object.parent_set(type='ARMATURE_NAME')
                x.modifiers["Armature"].use_deform_preserve_volume = True

        bpy.ops.object.select_all(action='DESELECT')


bl_info = {
    "name": "Auto Rig for Mixamo and Character Creator",
    "author": "Theophilus",
    "version": (1, 1),
    "blender": (2, 80, 0),
    "location": "Object Mode -> Object menu, Edit Mode -> Mesh menu, ",
    "description": "Fast and easy 1-click rig",
    "warning": "",
    "wiki_url": "",
    "category": "Object",
}

class Rig(bpy.types.Operator):
    """Auto Rig for Mixamo and Character Creator"""
    bl_idname = "operator.rig"
    bl_label = "Rig"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        res = validate_skin_mesh(self, body_name, ref_path)

        if res == {"FINISHED"}:
            fix_Skin(body_name, ref_faces, ref_path)
            build_rig(body_name, root_name)
            skin_rig(body_name, root_name)
            bind_items(body_name, root_name)

            self.report({'INFO'}, "Rig Done")

        return {'FINISHED'}


class Panel(bpy.types.Panel):
    bl_label = "Main Panel"
    bl_idname = "CCURIG1_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rig"
 
    def draw(self, context):
        self.layout.operator(Rig.bl_idname)
 
 
def menu_func(self, context):
    self.layout.operator(Rig.bl_idname)

def register():
    bpy.utils.register_class(Rig)
    bpy.utils.register_class(Panel)

    bpy.types.VIEW3D_MT_object.append(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh.append(menu_func)

def unregister():
    bpy.utils.unregister_class(Rig)
    bpy.utils.unregister_class(Panel)


if __name__ == "__main__":
    register()
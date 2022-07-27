# ##### LICENSE BLOCK #####
#
#  Not to be used in Production
#
# ##### LICENSE BLOCK #####


import bpy, bmesh
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

import sys
import bpy
from importlib import reload

sys.path.append(bpy.path.abspath("//"))

# import transfer_vertex_order  # noqa
import ops  # noqa
if "ops" in locals():
    reload(ops)
# if "ops" in locals():
#     reload(transfer_vertex_order)

# transfer_vertex_order.register()

skin = "Body"
arm = "armature"


sourceObj = bpy.context.active_object
TargetObjs = [obj for obj in bpy.context.selected_objects if obj !=
              sourceObj and obj.type == 'MESH']

# lll = transfer_vertex_order.VOT_OT_TransferVertIdByUV
# lll.execute(sourceObj=sourceObj, TargetObjs=TargetObjs)

# res = ops.validate(skin)
res = ops.fix_Skin(skin)
# res = ops.build_rig(skin, arm)
# res = ops.skin_rig(skin, arm)

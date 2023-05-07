import sys
import bpy
from importlib import reload

sys.path.append(bpy.path.abspath("//"))
import ops  # noqa
if "ops" in locals():
    reload(ops)

skin = "Body"
arm = "armature"
res = ops.validate(skin)
res = ops.fix_Skin(skin)
res = ops.build_rig(skin, arm)
res = ops.skin_rig(skin, arm)

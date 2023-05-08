import bpy
import sys

sys.path.append(bpy.path.abspath("//"))
from add_main import Rig  # noqa
from add_ui import Panel  # noqa


bl_info = {
    "name": "Mixa Rig",
    "author": "Theophilus Ogbolu",
    "version": (1, 3),
    "blender": (2, 80, 0),
    "location": "Object Mode -> Object menu, Edit Mode -> Mesh menu, ",
    "description": "Fast and easy 1-click rig",
    "warning": "",
    "wiki_url": "",
    "category": "Object",
}


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

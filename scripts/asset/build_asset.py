import bpy
import sys
import os
import json
from pathlib import Path
import bmesh

# fix for python being annoying about imports, maybe not good practice
# basically adds the root bmubin directory to path
sys.path.append('.')

# local script imports
# auto formatting this file will move these above sys.path.append, breaking the script
from scripts.asset import shader_fixer
from scripts.asset import dae_fixer

with open("mbconfig.json", "r") as f:
    config = json.load(f)


base_path = os.path.abspath("asset_library\\assets")
import_path = os.path.abspath(config["colladaPath"])


def save(path):
    print(f'saving to {path}')
    try:
        bpy.ops.wm.save_as_mainfile(filepath=path)
    except:
        print(f'save failed for {path}')


def import_dae(path: str):
    print('importing dae')
    # Import DAE
    bpy.ops.wm.collada_import(filepath=path)
    bpy.ops.object.select_all(action='DESELECT')


def clean_file():
    print('clean file')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()


# this makes the layout viewport show the image textures
def set_shading_type():
    print('set shading type')
    layout = bpy.data.screens.get('Layout')
    if not layout:
        print('Default layout window not found, cannot set shading type')
        return
    for area in layout.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    # bpy.ops.view3d.view_all(center=True)
                    space.shading.color_type = 'TEXTURE'
        if area.type == 'OUTLINER':
            space = area.spaces[0]
            space.show_restrict_column_viewport = True


# yes is true, no is false
def yes_or_no(default):
    user_choice = input()
    user_choice = str.lower(str.strip(user_choice))
    if len(user_choice) == 0:
        return default
    choices = ['y', 'n']
    if user_choice not in choices:
        print('Choice not recognized, try again')
        return yes_or_no()
    elif user_choice == 'y':
        return True
    elif user_choice == 'n':
        return False
    else:
        return default


def bmesh_cleanup():
    for object in bpy.data.objects:
        if object.type != 'MESH':
            continue
        object_data = object.data
        bm = bmesh.new()
        bm.from_mesh(object_data)
        # remove duplicate vertices
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=.005)
        bm.to_mesh(object_data)
        # remove all loose vertices
        loose_verts = [v for v in bm.verts if not v.link_faces]
        for v in loose_verts:
            bm.verts.remove(v)


def main():
    argv = sys.argv
    try:
        index = argv.index("--") + 1
    except ValueError:
        index = len(argv)
    argv = argv[index:]
    # example arg
    # TwnObj_Village_Hateno_A-51\TwnObj_Village_HatenoHouse_A_L_02.dae
    if argv and argv[0]:
        asset_path = argv[0]
        dae_name = Path(asset_path).stem
        save_path = base_path+'\\'+dae_name+'.blend'
        if os.path.isfile(save_path):
            print(f'{dae_name} already built')
            return
        clean_file()

        new_dae_file_path = dae_fixer.get_new_dae_path(asset_path)

        if not new_dae_file_path.is_file():
            new_dae_file_path = dae_fixer.fix_dae(asset_path)
        # new_dae_file_path = dae_fixer.fix_dae(asset_path)
        default_collection = bpy.data.collections.get('Collection')
        if not default_collection:
            default_collection = bpy.data.collections.new('Collection')
            bpy.context.scene.collection.children.link(default_collection)
            vl_collections = bpy.context.scene.view_layers["ViewLayer"].layer_collection
            default_layer_collection = vl_collections.children.get('Collection')
            bpy.context.view_layer.active_layer_collection = default_layer_collection

        import_dae(str(new_dae_file_path))
        shader_fixer.fix_shaders(dae_name)
        set_shading_type()
        bmesh_cleanup()
        armature = bpy.data.objects["Armature"]
        armature.name = dae_name
        root_bone = armature.pose.bones.get("Root")
        if root_bone:
            root_bone.rotation_mode = 'XYZ'
        if default_collection:
            default_collection.name = dae_name
        else:
            print('Default collection not found, cannot rename')
        print(dae_name)
        save(save_path)
    else:
        print('build_asset cannot build_asset without an asset to build')
    return


if __name__ == "__main__":
    print(f"{__file__} is being run directly")
    main()
else:
    print(f"{__file__} is being imported")

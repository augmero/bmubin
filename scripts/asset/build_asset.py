import bpy
import sys
import os
import json
from pathlib import Path

# fix for python being annoying about imports, maybe not good practice
# basically adds the root bmubin directory to path
sys.path.append('.')

# local script imports
from scripts.asset import dae_texture_directory as dtd
from scripts.asset import shader_fixer

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


def import_dae(path):
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
    for area in bpy.data.screens["Layout"].areas:
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

# check if the collada file references the correct relative path for the textures


def correct_texture_directory(path, ask):
    # import dae_texture_directory as dtd
    # from dae_texture_directory import has_fixed_texture_dir
    # from dae_texture_directory import find_replace_image_dir
    print('after import')
    if not dtd.has_fixed_texture_dir(path):
        if not ask:
            dtd.find_replace_image_dir(path)
            return True
        else:
            print('Fix texture reference in collada? Y/n')
            user_choice = yes_or_no(True)
            if user_choice:
                dtd.find_replace_image_dir(path)
                return True
    return False


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
        print(argv)
        print(len(argv))
        asset_path = argv[0]
        dae_name = Path(asset_path).stem
        save_path = base_path+'\\'+dae_name+'.blend'
        if os.path.isfile(save_path):
            print(f'{dae_name} already built')
            return
        clean_file()

        fix_texture_dir = len(argv) > 1 and argv[1] == '--fix_texture_dir'
        if fix_texture_dir:
            print('fix texture dir')
            ask_fix_texture_dir = len(argv) > 2 and argv[2] == '--ask_fix_texture_dir'
            correct_texture_directory(asset_path, ask_fix_texture_dir)

        import_dae(asset_path)
        shader_fixer.fix_shaders()
        set_shading_type()
        armature = bpy.data.objects["Armature"]
        armature.name = dae_name
        root_bone = armature.pose.bones.get("Root")
        if root_bone:
            root_bone.rotation_mode = 'XYZ'
        bpy.data.collections['Collection'].name = dae_name
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

import shutil
from pathlib import Path
import re
import json

texture_directory_relative = '..\\..\\textures\\'
parsed_collada_directory = 'collada_parsed\\'


# make a copy of the dae file
# set the relative texture directory
# simplify all the texcoord names to make it easier for the native blender importer
#   the dae files exported from programs like switch toolbox are valid as far as I can tell
#   blender for some reason fails to import random uv maps unless I change the name
# record extra shader information for the shader fixer

def get_new_dae_path(dae_file_path) -> Path:
    dae_file_path_parent = Path(dae_file_path).parent.stem
    parent_directory = Path(f'{parsed_collada_directory}{dae_file_path_parent}').absolute()
    new_dae_file_path = Path(
        str(parent_directory) + '\\' +
        str(Path(dae_file_path).stem) + '.dae'
    ).absolute()
    return new_dae_file_path


def fix_dae(dae_file_path):
    # copy file
    dae_file_path_parent = Path(dae_file_path).parent.stem
    parent_directory = Path(f'{parsed_collada_directory}{dae_file_path_parent}').absolute()
    if not parent_directory.is_dir():
        parent_directory.mkdir()
    new_dae_file_path = Path(
        str(parent_directory) + '\\' +
        str(Path(dae_file_path).stem) + '.dae'
    ).absolute()
    print(new_dae_file_path)
    shutil.copyfile(dae_file_path, new_dae_file_path)
    # fix_texture_dir(new_dae_file_path)
    open_and_fix_problems(new_dae_file_path)
    return new_dae_file_path


def open_and_fix_problems(dae_file_path):
    lines_to_write = []
    with open(dae_file_path, 'r') as file:
        lines_to_write = file.readlines()
        lines_to_write = fix_texture_dir(lines_to_write)
        lines_to_write = simplify_names(lines_to_write)
    with open(dae_file_path, 'w') as file:
        file.writelines(lines_to_write)


# Makes the dae file much less human readable but fixes blender import issues
def simplify_names(lines: list[str]):
    name_cache = {}
    sequential_number = 0
    # first pass build name cache
    for line in lines:
        # TEXCOORD
        regex_match = re.search('source=".*-texcoord', line)
        if regex_match:
            matched_name = regex_match.group()[9:]
            if matched_name in name_cache:
                continue
            number_zfill = str(sequential_number).zfill(5)
            matched_name_value = f'bmubin_fixed_{number_zfill}-texcoord'
            name_cache[matched_name] = matched_name_value
            sequential_number += 1
        regex_match = re.search('source=".*-color', line)
        # VCOLOR
        if regex_match:
            matched_name = regex_match.group()[9:]
            if matched_name in name_cache:
                continue
            number_zfill = str(sequential_number).zfill(5)
            matched_name_value = f'bmubin_fixed_{number_zfill}-color'
            name_cache[matched_name] = matched_name_value
            sequential_number += 1
    print(json.dumps(name_cache, indent=4))
    # now rename
    lines_to_write = lines
    for key, value in name_cache.items():
        lines_to_write = [re.sub(key, value, x) for x in lines_to_write]
    return lines_to_write


def fix_texture_dir(lines: list[str]):
    linesToWrite = []
    for line in lines:
        if 'png' in line:
            line = line.replace("<init_from>", "<init_from>"+texture_directory_relative)
        linesToWrite += [line]
    return linesToWrite


if __name__ == "__main__":
    print(f"{__file__} is being run directly")
else:
    print(f"{__file__} is being imported")

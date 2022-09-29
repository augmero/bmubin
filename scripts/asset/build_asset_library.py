from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
import time
import subprocess
import json
import os
import sys
from pathlib import Path
from tqdm import tqdm

with open("mbconfig.json", "r") as f:
    config = json.load(f)

executor = ThreadPoolExecutor()


class textures:
    normals = {}
    masks = {}
    trs = {}


def walk_textures():
    tx = textures()
    for dirpath, dirnames, files in os.walk(config['texturesPath']):
        for name in files:
            if 'Nrm' in name:
                base_color_name = name.split('Nrm')[0]
                tx.normals[base_color_name] = True
            if 'Trs' in name:
                base_color_name = name.split('Trs')[0]
                tx.trs[base_color_name] = True
            if 'Msk' in name:
                base_color_name = name.split('Msk')[0]
                tx.masks[base_color_name] = True
    return tx


def cache_textures():
    tx: textures = walk_textures()
    Path(f'linked_resources\\json\\generated\\normals.json').write_text(json.dumps(tx.normals, indent=4))
    Path(f'linked_resources\\json\\generated\\masks.json').write_text(json.dumps(tx.masks, indent=4))
    Path(f'linked_resources\\json\\generated\\trs.json').write_text(json.dumps(tx.trs, indent=4))


def build_asset(dae_path, quiet=True, background=True, timeout_s=30):
    ask_fix_texture_dir = '--ask_fix_texture_dir'
    bg = None
    if quiet:
        ask_fix_texture_dir = ''
    if background:
        bg = '--background'
    launch_file = os.path.abspath('starting_scene\\starting_scene.blend')
    if not os.path.isfile(launch_file):
        launch_file = None
    args = (
        config["blenderPath"],
        launch_file,
        bg,
        "--python",
        "scripts\\asset\\build_asset.py",
        "--factory-startup",
        "--", 
        str(dae_path), 
        "--fix_texture_dir", 
        ask_fix_texture_dir
    )
    # kinda stinky way to remove any None from the tuple
    args = tuple(x for x in args if x is not None)

    popen_args = {
        'stdout': subprocess.PIPE,
        'universal_newlines': True
    }
    if quiet:
        popen_args['stdout'] = subprocess.DEVNULL
        popen_args['stderr'] = subprocess.DEVNULL
    try:
        sprocess = subprocess.Popen(args, **popen_args)
        if not quiet:
            for line in sprocess.stdout:
                print(line.strip())
        sprocess.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        print(f'Timeout for {args} ({timeout_s}s) expired', file=sys.stderr)
        sprocess.terminate()
        return 'timeout'
    return 'complete'


def assets_to_build_flawed():
    built_assets = []
    for dirpath, dirnames, files in os.walk('asset_library\\assets'):
        for name in files:
            if '.blend' in name:
                built_assets += [name[:-6]]

    unbuilt_assets = []
    for dirpath, dirnames, files in os.walk(config["colladaPath"]):
        local_path = dirpath.split('collada')[1][1:]
        for name in files:
            if '.dae' in name:
                if name[:-4] not in built_assets:
                    dae_file_path = os.path.abspath(os.path.join(dirpath, name))
                    unbuilt_assets += [dae_file_path]
                    print(f"{name} not built")
    return unbuilt_assets


def all_dae_files():
    unbuilt_assets = []
    for dirpath, dirnames, files in os.walk(config["colladaPath"]):
        local_path = dirpath.split('collada')[1][1:]
        for name in files:
            if '.dae' in name:
                dae_file_path = os.path.join(local_path, name)
                unbuilt_assets += [dae_file_path]
    return unbuilt_assets


def build_asset_library(quiet=True, timeout=60):
    start_time = time.time()
    print("Building asset library")
    cache_textures()
    assets_to_build = assets_to_build_flawed()
    # quiet = False
    # assets_to_build = assets_to_build[:1]

    with open("missing_shaders.txt", "w") as f:
        missing_shaders = {
            "fileInfo": "This file was auto generated, below is a list of assets and materials that are broken"
        }
        json.dump(missing_shaders, f, indent=4)
        f.close()

    futures = [executor.submit(build_asset, x, quiet, True, timeout) for x in assets_to_build]
    num_completed = 0
    num_timeout = 0

    tqdm_args = {
        'total': len(assets_to_build),
        'leave': False,
        'dynamic_ncols': True,
        'colour': 'green',
        'desc': 'Assets Built'
    }

    # for future in as_completed(futures):
    for future in tqdm(as_completed(futures), **tqdm_args):
        # retrieve the result
        res = future.result()
        if res == 'complete':
            num_completed += 1
        else:
            num_timeout += 1
    print(f'\nTotal number of threads completed: {num_completed}')
    print(f'Total number of threads timed out: {num_timeout}')
    end_time = time.time()
    sec = end_time - start_time
    print(f'\nCompleted in {sec} seconds.\n')


def build_test_asset():
    print("building test asset")
    futures = [executor.submit(build_asset, "TwnObj_Village_Hateno_A-51\TwnObj_Village_HatenoHouse_A_L_02.dae")]
    for future in as_completed(futures):
        # retrieve the result
        future.result()


def main():
    build_asset_library()


if __name__ == "__main__":
    print(f"{__file__} is being run directly")
else:
    print(f"{__file__} is being imported")

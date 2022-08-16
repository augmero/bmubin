import os
import subprocess
import json
from pathlib import Path
from scripts.asset.build_asset_library import build_asset_library
from scripts.asset.build_asset_library import build_asset
from scripts.mubin.get_stats import mubin_stats
from scripts.mubin.parser import parse_mubin
from scripts.classes.instance_cache import instance_cache
import tkinter as tk
from tkinter import filedialog
import sys
from tqdm import tqdm
import ujson
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed


with open("mbconfig.json", "r") as config_load:
    config = json.load(config_load)
    config_load.close()

tk_obj = tk.Tk()

executor = ThreadPoolExecutor()


def install_dependencies():
    # Set app data information
    print('Setting up...')

    # Write cache file
    if not Path(f'{config["dataDir"]}').is_dir():
        Path(f'{config["dataDir"]}').mkdir()
    if not Path(f'{config["dataDir"]}\\cache').is_dir():
        Path(f'{config["dataDir"]}\\cache').mkdir()
    Path(f'{config["dataDir"]}\\cache.json').write_text(json.dumps({}))

    needed_folders = [
        'asset_library',
        'asset_library\\assets',
        'asset_library\\mubins_by_prefix',
        'linked_resources',
        'linked_resources\\json',
        'linked_resources\\json\\generated',
        'linked_resources\\json\\generated\\instance_caches',
        'collada',
        'collada_parsed',
        'textures',
        'starting_scene',
    ]
    # set up needed folders
    for folder in needed_folders:
        if not Path(folder).is_dir():
            Path(folder).mkdir()

    config["depsInstalled"] = True
    with open("mbconfig.json", "w") as config_load:
        json.dump(config, config_load, indent=4)
        config_load.close()
    print('Install Complete!')

    return {'FINISHED'}


def init_tk():
    # tk_obj = tk.Tk()
    tk_obj.geometry('0x0')
    tk_obj.title('tk is only used for file dialog this window should dissapear immediately')
    tk_obj.lower()
    tk_obj.withdraw()


def get_blender_path():
    if "blenderPath" not in config:
        print('Blender required to run this script, please select the executable')
        exe_filetypes = [('exe', '*.exe'), ('all', '*.*')]
        blender_executable = filedialog.askopenfilename(filetypes=exe_filetypes)
        if not blender_executable:
            print('Blender executable not found, returning to main menu')
            return
        config["blenderPath"] = blender_executable
        with open("mbconfig.json", "w") as write_config:
            json.dump(config, write_config, indent=4)


def check_texture_atlas():
    print('checking for texture atlas')
    texture_atlases = ['MaterialAlb', 'MaterialCmb']
    for atlas in texture_atlases:
        atlas_path = f'linked_resources\\{atlas}_TextureAtlas.png'
        if not Path(atlas_path).is_file():
            print(f'{atlas} atlas not found, building')
            from scripts.asset.build_texture_atlas import build_texture_atlas
            built = build_texture_atlas(atlas)
            if not built:
                return False
        else:
            print(f'{atlas} atlas found! Continuing')
    return True


def new_stats():
    print('new stats')
    from scripts.classes.stats import stats
    s_cache = stats()
    for dirpath, dirnames, files in os.walk('asset_library\\assets'):
        for name in files:
            if '.blend' in name:
                s_cache.built_assets[name[:-6]] = True
    return s_cache


def json_pretty_print(ugly):
    print(json.dumps(ugly, sort_keys=True, indent=4))


def get_stats(mubin_paths):
    stats = new_stats()
    for i in tqdm(
            range(len(mubin_paths)),
            leave=False, dynamic_ncols=True, colour='cyan', position=1, desc='mubin paths'):
        # for i in range(len(mubin_paths)):
        mubin_path = mubin_paths[i]
        mubin_stats(Path(mubin_path), True, stats)
    print('_____________________________________')
    print('\n')
    print('Assets ready to import:')
    print('\n')
    print('name: count')
    json_pretty_print(stats.assets_ready)

    print('_____________________________________')
    print('\n')
    print('Assets not found:')
    print('\n')
    print('name: count')
    json_pretty_print(stats.assets_not_found)

    print('_____________________________________')
    all_assets = dict()
    all_assets.update(stats.assets_ready)
    all_assets.update(stats.assets_not_found)
    all_assets_list = sorted(all_assets, key=all_assets.get)
    print('\n')
    print('Top 10 common assets')
    print('\n')
    i = 0
    while i < 10:
        asset = all_assets_list.pop()
        print(asset, all_assets[asset])
        i += 1

    print('_____________________________________')
    print('\n')
    print(f'Unique assets: {len(all_assets)}')
    print(f'Missing unique assets: {len(stats.assets_not_found)}')
    print(f'Total assets: {sum(all_assets.values())}')
    print(f'Total missing assets: {sum(stats.assets_not_found.values())}')
    print('\n')


def open_helper(func_to_run: str, arg_list: list = [], timeout_s=60, background=True, quiet=True):
    if not func_to_run:
        return 'func_to_run param missing'
    bg = None
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
        "helper.py",
        "--factory-startup",
        "-y",
        "--",
        func_to_run
    )
    # kinda stinky way to remove any None from the tuple
    args = tuple(x for x in args if x is not None)
    arg_list_tuple = tuple(x for x in arg_list)
    args = args + arg_list_tuple

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
                line = line.strip()
                if len(line) > 0 and not 'WARN' in line:
                    print(line)
        sprocess.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        print(f'Timeout for {args} ({timeout_s}s) expired', file=sys.stderr)
        sprocess.terminate()
        return 'timeout'
    return 'complete'


def mubins_in_directory(path):
    ret = []
    for dirpath, dirnames, files in os.walk(Path(path)):
        for name in files:
            if '.smubin' in name:
                file_path = os.path.abspath(os.path.join(dirpath, name))
                ret.append(file_path)
    return ret


def organize_paths_by_prefix(paths: list):
    prefix_cache = {}
    for path in paths:
        stem = Path(path).stem
        prefix = stem[:3]
        if prefix not in prefix_cache:
            prefix_cache[prefix] = []
        prefix_cache[prefix].append(path)
    return prefix_cache


def build_mubin_library(directory, quiet=True, timeout=60):
    start_time = time.time()
    print("Building asset library")

    mubins_found = mubins_in_directory(directory)

    # multithreaded caching
    paths_by_prefix = organize_paths_by_prefix(mubins_found)
    futures_prefix = [executor.submit(cache_mubins, x, True) for x in paths_by_prefix.values()]
    for future in as_completed(futures_prefix):
        res = future.result()

    # multithreaded mubin instancing
    print(paths_by_prefix.keys())
    futures_helper = [executor.submit(open_helper, 'import_mubin', [x], timeout, quiet, quiet)
                      for x in paths_by_prefix.keys()]
    num_completed = 0
    num_timeout = 0
    tqdm_args = {
        'total': len(paths_by_prefix.keys()),
        'leave': False,
        'dynamic_ncols': True,
        'colour': 'green',
        'desc': 'Grouped mubins imported'
    }
    for future in tqdm(as_completed(futures_helper), **tqdm_args):
        # for future in as_completed(futures_helper):
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


def cache_mubins(mubin_paths: list, by_prefix=True):
    p_caches = {}
    for mubin_path in mubin_paths:
        p_cache = instance_cache()
        stem = Path(mubin_path).stem
        parse_mubin(Path(mubin_path), True, p_cache)
        if by_prefix:
            prefix = stem[:3]
            if prefix not in p_caches:
                p_caches[prefix] = {}
            p_caches[prefix][stem] = p_cache
        else:
            p_caches[stem] = p_cache

    if by_prefix:
        for prefix, mubins in p_caches.items():
            dumpJson = json.loads(json.dumps(mubins, default=lambda o: o.__dict__))
            with open(f"linked_resources\\json\\generated\\instance_caches\\{prefix}_instance_cache.json", "w") as write_instance_cache:
                # this can be a very big json (20mb) so using ujson
                ujson.dump(dumpJson, write_instance_cache)
                write_instance_cache.close()
        return p_caches.keys()
    else:
        dumpJson = json.loads(json.dumps(p_caches, default=lambda o: o.__dict__))
        with open(f"linked_resources\\json\\generated\\instance_caches\\_instance_cache.json", "w") as write_instance_cache:
            # this can be a very big json (20mb) so using ujson
            ujson.dump(dumpJson, write_instance_cache)
            write_instance_cache.close()


task_list = {
    'extra info about these scripts': 'Just prints some extra info',
    'build asset library': 'Builds asset blend files for each dae file present in .collada\\ \n(multithreaded)',
    'build single asset': 'Builds an asset blend file in .asset_library\\ for a selected dae file',
    'build mubin library from directory':
    'Builds a blend file out of instanced assets for every smubin found in the directory selected \n(multithreaded)',
    'import mubin(s)': 'Builds a blend file out of instanced assets for selected mubins',
    'mubin(s) stats': 'Prints out some useful stats about selected mubin(s)',
    'combine mubin blend libraries':
    'Creates .asset_library\\combined_blends.blend by including instances of the selected blend files by prefix (ex I-7)' + \
    '\nMap: https://objmap.zeldamods.org Enable "show map unit grid" under filter on this site to see the meaning of these prefixes' + \
    '\nWarning, many of these in one file will have worse performance and higher ram usage'
}


def print_task_list_info():
    print('\n')
    print('____________________________________')
    print('Currently available utilities:')
    print('\n')
    for i in range(len(task_list.keys())):
        print(f'{i+1}: {list(task_list.keys())[i]}')
        print(list(task_list.values())[i])
        print('\n')


def run_task(task_input):
    print(f'running task {task_input}')
    task_input = str.strip(str(task_input))
    if 'x' in task_input:
        return 'quit'
    task_index = int(task_input)
    if not task_index or task_index < 1:
        return 'quit'
    task_index -= 1
    task = list(task_list.keys())[task_index]

    if 'extra info about' in task:
        print_task_list_info()
        select_task()
    elif 'build asset library' in task:
        # If lots of threads are timing out try raising this timeout value it's in seconds
        # Possibly test one of the larger files to see how long it takes
        #  (DgnObj_DLC_IbutsuEx_BossBattleRoom_A_01)
        build_asset_library(quiet=True, timeout=60)
    elif 'build single asset' in task:
        dae_filetypes = [('collada', '*.dae'), ('all', '*.*')]
        dae_file = filedialog.askopenfilename(filetypes=dae_filetypes)
        if not dae_file:
            return ('not selected', 'No file')
        build_asset(dae_file, quiet=False, timeout_s=60)
    elif 'build mubin library' in task:
        print('Please open directory with all the mubins in it')
        print('for example, look for \\content\\0010\\Map\\MainField')
        mubin_directory = filedialog.askdirectory()
        if not mubin_directory:
            return ('not selected', 'No directory')
        build_mubin_library(mubin_directory)
    elif 'import mubin' in task or 'mubin(s) stats' in task:
        mubin_filetypes = [('mubin', '*.smubin'), ('all', '*.*')]
        mubin_paths = filedialog.askopenfilenames(filetypes=mubin_filetypes)
        if not mubin_paths:
            return ('not selected', 'No paths')
        if not isinstance(mubin_paths, list):
            mubin_paths = list(mubin_paths)
        print(mubin_paths)
        if 'import mubin' in task:
            cache_mubins(mubin_paths, by_prefix=False)
            open_helper('import_mubin', timeout_s=60, background=True, quiet=False)
        elif 'mubin(s) stats' in task:
            get_stats(mubin_paths)
    elif 'combine mubin blend libraries' in task:
        blend_filetypes = [('blend', '*.blend'), ('all', '*.*')]
        initial_dir = 'asset_library\\mubins_by_prefix'
        blend_paths = filedialog.askopenfilenames(filetypes=blend_filetypes, initialdir=initial_dir)
        if not blend_paths:
            return ('not selected', 'No paths')
        if not isinstance(blend_paths, list):
            blend_paths = list(blend_paths)
        open_helper('combine_blends', arg_list=blend_paths, timeout_s=500, background=True, quiet=False)
    else:
        print('Command not recognized, back to main menu')
        select_task()


def select_task():
    print('\nWelcome to the mubin_to_blender script task selection system')
    for i in range(len(task_list.keys())):
        print(f'{i+1}: {list(task_list.keys())[i]}')
    print('x: exit')
    selected_task = 'x'
    try:
        selected_task = input("Choose something to do: ")
    except KeyboardInterrupt:
        print('keyboard interrupt')
    result = run_task(selected_task)
    if type(result) is tuple:
        result: tuple = result
        if result[0] == 'not selected':
            print(f'{result[1]} selected, back to main menu')
            select_task()


def main():
    init_tk()
    config["dataDir"] = os.path.abspath('data_dir')
    get_blender_path()
    if not config["depsInstalled"]:
        try:
            install_dependencies()
        except:
            print('Dependencies not installed, please try again')
            return
    if not check_texture_atlas():
        return

    select_task()


if __name__ == "__main__":
    print(f"{__file__} is being run directly")
    main()
else:
    print(f"{__file__} is being imported")
    main()

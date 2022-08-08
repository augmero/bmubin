import os
import subprocess
import json
from pathlib import Path
from scripts.asset.build_asset_library import build_asset_library
from scripts.asset.build_asset_library import build_asset
from scripts.mubin.get_stats import mubin_stats
import tkinter as tk
from tkinter import filedialog

with open("mbconfig.json", "r") as config_load:
    config = json.load(config_load)
    config_load.close()

tk_obj = tk.Tk()


def install_dependencies():
    # Set app data information
    print('Setting up...')

    # Write cache file
    if not Path(f'{config["dataDir"]}').is_dir():
        Path(f'{config["dataDir"]}').mkdir()
    if not Path(f'{config["dataDir"]}\\cache').is_dir():
        Path(f'{config["dataDir"]}\\cache').mkdir()
    Path(f'{config["dataDir"]}\\cache.json').write_text(json.dumps({}))

    # set up needed folders
    if not Path('asset_library').is_dir():
        Path('asset_library').mkdir()
    if not Path('asset_library\\assets').is_dir():
        Path('asset_library\\assets').mkdir()
    if not Path('collada').is_dir():
        Path('collada').mkdir()
    if not Path('collada_parsed').is_dir():
        Path('collada_parsed').mkdir()
    if not Path('textures').is_dir():
        Path('textures').mkdir()
    if not Path('starting_scene').is_dir():
        Path('starting_scene').mkdir()

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
    while len(mubin_paths) > 0:
        mubin_path = mubin_paths.pop()
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


def open_helper(func_to_run: str, background=True, arg_list: list = []):
    print('open_helper')
    bg = None
    if background:
        bg = '--background'
    launch_file = os.path.abspath('starting_scene\\starting_scene.blend')
    if not os.path.isfile(launch_file):
        launch_file = None
    # log_level = 0
    # log_level_string = f'--log-level {log_level}'
    args = (config["blenderPath"], launch_file, bg, "--python",
            "helper.py", "--factory-startup", "-y", "--", func_to_run)
    print(args)
    # kinda stinky way to remove any None from the tuple
    args = tuple(x for x in args if x is not None)
    arg_list_tuple = tuple(x for x in arg_list)
    args = args + arg_list_tuple
    print(args)

    sprocess = subprocess.Popen(args, stdout=subprocess.PIPE, universal_newlines=True)
    for line in sprocess.stdout:
        print(line.strip())
    sprocess.wait()
    return


def run_task(task):
    print(f'running task {task}')
    task = str.strip(str(task))
    if '1' in task:
        # If lots of threads are timing out try raising this timeout value it's in seconds
        # Possibly test one of the larger files to see how long it takes
        #  (DgnObj_DLC_IbutsuEx_BossBattleRoom_A_01)
        build_asset_library(quiet=True, timeout=60)
    elif '2' in task:
        dae_filetypes = [('collada', '*.dae'), ('all', '*.*')]
        dae_file = filedialog.askopenfilename(filetypes=dae_filetypes)
        if not dae_file:
            print('No file selected, back to main menu')
            select_task()
            return
        build_asset(dae_file, quiet=False, timeout_s=60)
    elif '3' in task or '4' in task:
        mubin_filetypes = [('mubin', '*.smubin'), ('all', '*.*')]
        mubin_paths = filedialog.askopenfilenames(filetypes=mubin_filetypes)
        if not mubin_paths:
            print('No paths selected, back to main menu')
            select_task()
            return
        if not isinstance(mubin_paths, list):
            mubin_paths = list(mubin_paths)
        print(mubin_paths)
        if '3' in task:
            open_helper('import_mubin', True, mubin_paths)
        elif '4' in task:
            get_stats(mubin_paths)
    elif 'x' in task:
        return
    else:
        print('Command not recognized, back to main menu')
        select_task()


def select_task():
    print('\nWelcome to the mubin_to_blender script task selection system')
    print('1: build asset library')
    print('2: build single asset')
    print('3: import mubin(s)')
    print('4: mubin(s) stats')
    print('x: exit')
    selected_task = 'x'
    try:
        selected_task = input("Choose something to do: ")
    except KeyboardInterrupt:
        print('keyboard interrupt')
    run_task(selected_task)


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

    # open_helper('gen_slice_nodes', False)


if __name__ == "__main__":
    print(f"{__file__} is being run directly")
    main()
else:
    print(f"{__file__} is being imported")
    main()

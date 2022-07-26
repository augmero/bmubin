from pathlib import Path
import sys
import json
import os
import bpy


with open("mbconfig.json", "r") as f:
    config = json.load(f)


def save(path):
    path = os.path.abspath(path)
    try:
        bpy.ops.wm.save_as_mainfile(filepath=path)
    except:
        print(f'save failed for {path}')

def new_session_cache():
    print('new session cache')
    from scripts.classes.session_cache import session_cache
    s_cache = session_cache()
    for dirpath, dirnames, files in os.walk('asset_library\\assets'):
        for name in files:
            if '.blend' in name:
                s_cache.built_assets[name[:-6]] = True
    return s_cache


def main():
    print('main')
    # first arg should be the function to run
    # additional args are for said function
    argv = sys.argv
    try:
        index = argv.index("--") + 1
    except ValueError:
        index = len(argv)
    argv = argv[index:]
    # example arg
    # TwnObj_Village_Hateno_A-51\TwnObj_Village_HatenoHouse_A_L_02.dae
    save_path = 'asset_library\\'
    if argv and argv[0]:
        func_to_run = argv[0]
        if func_to_run == 'import_mubin':
            from scripts.mubin import importer
            if len(argv) > 1:
                save_path += Path(argv[1]).stem[:3]
                mubin_paths = argv[1:]
                print(f'mubin_paths: {mubin_paths}')
                session_cache = new_session_cache()
                while len(mubin_paths) > 0:
                    mubin_path = mubin_paths.pop()
                    importer.import_mubin(Path(mubin_path), False,  session_cache)
                importer.include_all_collections()
            else:
                print("import_mubin requires path(s)")
            save(f'{save_path}.blend')
        elif func_to_run == 'gen_slice_nodes':
            from scripts.asset import gen_slice_nodes
            gen_slice_nodes.main()
    else:
        print('Try calling one of the available functions')
    return


if __name__ == "__main__":
    print(f"{__file__} is being run directly")
    sys.path.append(os.path.abspath("."))
    main()
else:
    print(f"{__file__} is being imported")
    print("don't do this")

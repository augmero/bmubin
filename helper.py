from pathlib import Path
import sys
import json
import os
import bpy
import sys
import contextlib
try:
    from tqdm import tqdm
except:
    # installs progress bar in bpython
    from pip._internal import main
    main(['install', 'tqdm'])
from tqdm import tqdm

with open("mbconfig.json", "r") as f:
    config = json.load(f)


class DummyFile(object):
    # https://stackoverflow.com/questions/36986929/redirect-print-command-in-python-script-through-tqdm-write/37243211#37243211
    file = None

    def __init__(self, file):
        self.file = file

    def write(self, x):
        # Avoid print() second call (useless \n)
        if len(x.strip()) > 0:
            tqdm.write(x, file=self.file)

    def flush(self): pass


@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = DummyFile(sys.stdout)
    yield
    sys.stdout = save_stdout


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


def load_override_script():
    print('loading script')
    text = bpy.data.texts.load(str(Path("scripts\\asset\\override_keep_transforms.py").absolute()))


def import_mubin(argv):
    from scripts.mubin import importer
    mubin_paths = argv[1:]
    print(f'mubin_paths: {mubin_paths}')
    session_cache = new_session_cache()
    tqdm_args = {
        'leave': False,
        'dynamic_ncols': True,
        'ascii': True,
        'colour': 'cyan',
        'position': 1,
        'desc': 'Mubin Paths',
        'file': sys.stdout
    }
    # for i in range(len(mubin_paths)):
    for mubin_path in tqdm(mubin_paths, **tqdm_args):
        with nostdout():
            importer.import_mubin(Path(mubin_path), False, session_cache)


def run_importer(prefix):
    from scripts.mubin import importer
    importer.import_all_mubins(prefix)


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
            prefix = ''
            if len(argv) > 1:
                # import_mubin(argv)
                # save_path += Path(argv[1]).stem[:3]
                prefix = argv[1][:3]
                save_path += f'mubins_by_prefix\\{prefix}'
            else:
                save_path += 'selected_mubins'

            print('running importer')
            run_importer(prefix)
            load_override_script()
            save(f'{save_path}.blend')
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

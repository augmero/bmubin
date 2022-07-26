import bpy
import traceback
import time
from pathlib import Path
import json

with open("mbconfig.json", "r") as f:
    config = json.load(f)

# lightweight version of import.py designed to just retrieve statistics on assets and asset availability

def import_actor(actor: dict, mod_folder: str, cache={}, exported={}, data_dir='', stats={}):
    # print('fake import actor')
    from .io.data import Data
    """Imports a mubin actor entry using the cached models and relative sbfres files."""

    name = actor['UnitConfigName']
    dae_file = ''

    # Vanilla actor
    if name in exported:
        dae_file = f'{data_dir}\\collada\\{exported[name]["BfresName"]}\\{exported[name]["ModelName"]}.dae'

    # Custom actor already cached
    elif name in cache:
        dae_file = f'{data_dir}\\cache\\{cache[name]["BfresName"]}\\{cache[name]["ModelName"]}.dae'

    # Custom actor
    elif Path(f'{mod_folder}\\content\\Actor\\Pack\\{name}.sbactorpack').is_file():
        Data.cache_actor(Path(f'{mod_folder}\\content\\Actor\\Pack\\{name}.sbactorpack'))
        dae_file = f'{data_dir}\\bin\\{cache[name]["BfresName"]}\\{cache[name]["ModelName"]}.dae'

    # Actor not found
    else:
        print(f'A model for {name}: {actor["HashId"]} could not be found.')
        return

    model_name = Path(dae_file).stem

    if not stats.built_assets.get(model_name):
        if not stats.assets_not_found.get(model_name):
            stats.assets_not_found[model_name] = 1
        else:
            stats.assets_not_found[model_name] += 1
        return

    if not stats.assets_ready.get(model_name):
        stats.assets_ready[model_name] = 1
    else:
        stats.assets_ready[model_name] += 1
    return


def mubin_stats(mubin: Path, import_far, stats):
    from .io.open_oead import OpenOead
    from .io.data import Data
    context = bpy.context
    Data.init()
    data_dir = config["dataDir"]
    cache = Data.cache
    exported = Data.exported
    data = OpenOead.from_path(mubin)
    
    content = ''
    num = range(0)
    # find the content directory which should be part of the mubin's path
    for i in num:
        if Path(f'{mubin}{".//" * (i + 1)}/content').is_dir():
            content = f'{mubin}{"..//" * (i + 1)}/content'
            break
        num = range(i + 1)

    if data.type == 'BYML' and data.sub_type == 'MUBIN':
        start_time = time.time()
        for actor in data.content['Objs']:
            print(f'name:{actor["UnitConfigName"]} hashid:{actor["HashId"]}')
            try:
                if str(actor["UnitConfigName"]).endswith('_Far'):
                    if import_far:
                        import_actor(actor, f'{content}..\\', cache=cache, exported=exported, data_dir=data_dir, stats=stats)
                else:
                    import_actor(actor, f'{content}..\\', cache=cache, exported=exported, data_dir=data_dir, stats=stats)
            except:
                print(f'Could not import {actor["UnitConfigName"]}\n{traceback.format_exc()}')

                error = ''
                if Path(f'{data_dir}\\error.txt').is_file():
                    error = Path(f'{data_dir}\\error.txt').read_text()

                Path(f'{data_dir}\\error.txt').write_text(
                    f'{error}Could not import {actor["UnitConfigName"]}\n{traceback.format_exc()}{"- " * 30}\n')


        end_time = time.time()
        sec = end_time - start_time
        print(f'\nCompleted in {sec} seconds.')
    return


def main():
    print('try calling mubin_stats with a path')
    return

if __name__ == "__main__":
    print(f"{__file__} is being run directly")
    main()
else:
    print(f"{__file__} is being imported")


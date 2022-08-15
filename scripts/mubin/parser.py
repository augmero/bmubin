import traceback
import time
from pathlib import Path
import json
from scripts.classes.instance_cache import instance_cache

with open("mbconfig.json", "r") as f:
    config = json.load(f)


def parse_actor(actor: dict, mod_folder: str, cache={}, exported={}, data_dir='', p_cache: instance_cache = {}):
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
        # print(f'A model for {name}: {actor["HashId"]} could not be found.')
        return

    model_name = Path(dae_file).stem

    # Set the transform
    location = actor['Translate']
    rotate = [0, 0, 0]
    scale = [1, 1, 1]

    # Get rotation
    if 'Rotate' in actor:
        try:
            rotate = [
                actor['Rotate'][0],
                actor['Rotate'][1],
                actor['Rotate'][2],
            ]
        except:
            rotate = [
                0.0,
                actor['Rotate'],
                0.0,
            ]

    # Get scale
    if 'Scale' in actor:
        try:
            scale = [
                actor['Scale'][0],
                actor['Scale'][2],
                actor['Scale'][1],
            ]
        except:
            scale = [
                actor['Scale'],
                actor['Scale'],
                actor['Scale'],
            ]

    location = [float(l) for l in location]
    rotate = [float(r) for r in rotate]
    scale = [float(s) for s in scale]

    model_position = instance_cache.position(location, rotate, scale)

    if p_cache.models.get(model_name):
        p_cache.models[model_name].positions.append(model_position)
    else:
        # cache by model name
        p_cache.models[model_name] = instance_cache.model([model_position])

    # print(f'cached {name}: {actor["HashId"]} successfully.\n')
    return


def parse_mubin(mubin: Path, import_far: bool, p_cache: instance_cache):
    print(f'parse_mubin {mubin}')
    from .io.open_oead import OpenOead
    from .io.data import Data
    Data.init()
    data_dir = config["dataDir"]
    cache = Data.cache
    exported = Data.exported
    data = OpenOead.from_path(mubin)

    if not p_cache:
        print('no parse cache?')
        return

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
            # print(f'name:{actor["UnitConfigName"]} hashid:{actor["HashId"]}')
            try:
                if str(actor["UnitConfigName"]).endswith('_Far') and import_far:
                    # Import actor
                    parse_actor(actor, f'{content}..\\', cache=cache, exported=exported,
                                 data_dir=data_dir, p_cache=p_cache)
                else:
                    # Import actor
                    parse_actor(actor, f'{content}..\\', cache=cache, exported=exported,
                                 data_dir=data_dir, p_cache=p_cache)
            except:
                # print(f'Could not cache {actor["UnitConfigName"]}\n{traceback.format_exc()}')

                error = ''
                if Path(f'{data_dir}\\error.txt').is_file():
                    error = Path(f'{data_dir}\\error.txt').read_text()

                Path(f'{data_dir}\\error.txt').write_text(
                    f'{error}Could not cache {actor["UnitConfigName"]}\n{traceback.format_exc()}{"- " * 30}\n')

        end_time = time.time()
        sec = end_time - start_time
        print(f'\nCompleted in {sec} seconds.')
    return


def main():
    print('importer main')
    return


if __name__ == "__main__":
    print(f"{__file__} is being run directly")
    main()
else:
    print(f"{__file__} is being imported")

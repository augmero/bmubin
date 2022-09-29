from oead import Sarc, yaz0
from pathlib import Path
import os
from tqdm import tqdm
import time


def __check_dirs():
    needed_folders = [
        'map_data',
        'map_data\\terrain',
        'map_data\\mate',
        'map_data\\grass',
        'map_data\\water',
    ]
    # set up needed folders
    for folder in needed_folders:
        if not Path(folder).is_dir():
            Path(folder).mkdir()


def unpack_path(path: str):
    start_time = time.time()
    __check_dirs()
    if not Path(path).is_dir():
        print('Path not found')
        return False

    number_of_files = sum([len(files) for _,_,files in os.walk(path)])
    print(f'number of files {number_of_files}')
    tqdm_args = {
        'total': number_of_files,
        'leave': False,
        'dynamic_ncols': True,
        'colour': 'green',
        'desc': 'Files decompressed and extracted'
    }
    with tqdm(**tqdm_args) as pgbar:
        for dirpath, dirnames, files in os.walk(path):
            for name in files:
                if 'sstera' in name:
                    file_path = os.path.abspath(os.path.join(dirpath, name))
                    unpack_file(file_path)
                    pgbar.update(1)
    
    end_time = time.time()
    sec = end_time - start_time
    print(f'\nCompleted in {sec} seconds.\n')


def unpack_file(path: str):
    # path = '580000C000.hght.sstera'
    base_path = 'map_data\\'
    if 'hght' in path:
        base_path += 'terrain\\'
    elif 'mate' in path:
        base_path += 'mate\\'
    elif 'grass' in path:
        base_path += 'grass\\'
    elif 'water' in path:
        base_path += 'water\\'

    data = Path(path).read_bytes()

    if data[:4] == b'Yaz0':
        data = yaz0.decompress(data)
    else:
        print('not yaz0')
        return False

    if data[:4] == b'SARC':
        data = Sarc(data)
    else:
        print('not sarc')
        return False

    for file in data.get_files():
        write_path = base_path + file.name
        file_data = bytes(file.data)
        with open(write_path, "wb") as f:
            f.write(file_data)
            f.close()

    return

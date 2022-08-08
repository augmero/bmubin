import json
import os
from PIL import Image
from pathlib import Path

with open("mbconfig.json", "r") as f:
    config = json.load(f)

textures_path = config['texturesPath']
textures_path_abs = os.path.abspath(textures_path)


def build_texture_atlas(atlas_name):
    count = 0
    img0_path = f'{textures_path}\\{atlas_name}_Slice_0_.png'
    if not Path(img0_path).is_file():
        print('first slice not found, building texture atlas failed')
        return False
    for dirpath, dirnames, files in os.walk(config['texturesPath']):
        for name in files:
            if atlas_name in name:
                count += 1
    print(count)
    img0 = Image.open(img0_path)
    size = img0.size
    print(size)
    print(size[0])
    # atlas = Image.new()
    atlas = Image.new("RGBA", (size[0]*count, size[0]))
    for i in range(count):
        print(f'adding slice {i}')
        slice_path = f'{textures_path}\\{atlas_name}_Slice_{i}_.png'
        slice_image = Image.open(slice_path)
        x_loc = size[0]*i
        atlas.paste(slice_image, (x_loc, 0))
    print(f'saving {atlas_name}...')
    atlas.save(f'linked_resources\\{atlas_name}_TextureAtlas.png')
    print(f'atlas {atlas_name} saved!')
    return True

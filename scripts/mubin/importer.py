# THIS SCRIPT RUNS WITHIN BLENDER
import bpy
from pathlib import Path
import json
from scripts.classes.instance_cache import instance_cache
import sys
import contextlib
from tqdm import tqdm
import math
import mathutils
import time

with open("mbconfig.json", "r") as f:
    config = json.load(f)


class DummyFile(object):
    # https://stackoverflow.com/questions/36986929/redirect-print-command-in-python-script-through-tqdm-write/37243211#37243211
    file = None

    def __init__(self, file):
        self.file = file

    def write(self, x): pass
    # Avoid print() second call (useless \n)
    # if len(x.rstrip()) > 0:
    #     tqdm.write(x, file=self.file)

    def flush(self): pass


@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = DummyFile(sys.stdout)
    yield
    sys.stdout = save_stdout


vl_collections = bpy.context.scene.view_layers["ViewLayer"].layer_collection
layer_collection_cache = {}
model_instance_counter = {}


def include_all_collections():
    exclude_all_collection_view_layer(vl_collections, False)


def exclude_all_collection_view_layer(p_collection, exclude):
    for collection in p_collection.children:
        collection.exclude = exclude
        if collection.children:
            exclude_all_collection_view_layer(collection, exclude)


def retrieve_layer_collection_BFS(layer_collection, collection_name):
    layers = [l for l in layer_collection.children]
    while len(layers) > 0:
        layer = layers.pop(0)
        if layer.name == collection_name:
            # print(f'BFS FOUND {collection_name}\n')
            return layer
        if layer.children and len(layer.children) > 0:
            layers += layer.children
    print(f'BFS DID NOT FIND {collection_name}\n')
    return None


def exclude_collection(layer_collection_name, exclude=True):
    layer_collection_cache[layer_collection_name].exclude = exclude


def add_collection(name, parent=bpy.context.scene.collection):
    # print(f'{name}, {parent}')
    context = bpy.context
    if name not in context.blend_data.collections:
        # print(f'adding collection {name}')
        # if parent is a layer collection get the collection it wraps
        if hasattr(parent, 'collection'):
            parent = parent.collection
        collection = context.blend_data.collections.new(name)
        parent.children.link(collection)
        layer_collection = retrieve_layer_collection_BFS(vl_collections, name)
        layer_collection_cache[name] = layer_collection
    return set_active_collection(name)


def set_active_collection(name):
    context = bpy.context
    context.view_layer.active_layer_collection = layer_collection_cache[name]
    return layer_collection_cache[name]

    # scene collection data structure will look like
    # mn - mubin_name
    # mn (first 3 chars)
    # |_
    #     mn
    #     |_
    #         mn_linked
    #         |_
    #             mn_{model_name}_linked collection
    #             |_
    #                 {model_name} (collection)
    #                 |_
    #                     {model_name}.002 (armature)
    #         mn_linked_Far
    #         |_
    #             mn_{model_name}_Instancer collection
    #             |_
    #                 mn_{model_name}_Instancer (object)
    #                 |_
    #                     {model_name} (linked collection object)

    # Assets to Instance
    # |_
    #   Assets to Instance.001
    #   |_
    #       {model_name}_Asset collection
    #       |_
    #           {model_name} (linked collection object)


def import_all_mubins(prefix: str = ''):
    print('import_all_mubins')
    start_time = time.time()

    # Add collections for the asset imports
    col_assets_to_instance = add_collection('Assets')
    # layer_collection_cache['Assets to Instance'].collection.hide_render = True
    add_collection('Assets.001', col_assets_to_instance.collection)

    tqdm_args = {
        'leave': False,
        'dynamic_ncols': True,
        'ascii': True,
        'colour': 'cyan',
        'desc': 'Mubin',
        'position': 0
    }
    # for mubin, mubin_data in all_caches.items():
    with open(f"linked_resources\\json\\generated\\instance_caches\\{prefix}_instance_cache.json", "r") as f:
        all_caches: dict = json.load(f)
    for mubin, mubin_data in tqdm(all_caches.items(), **tqdm_args):
        mubin_prefix = mubin[:3]
        coll_mn_prefix = add_collection(mubin_prefix)
        coll_mn = add_collection(mubin, coll_mn_prefix)

        models: dict = mubin_data['models']
        # for key, val in models.items():
        tqdm_args['position'] = 1
        tqdm_args['colour'] = 'green'
        tqdm_args['desc'] = 'Models Instanced'
        for key, val in tqdm(models.items(), **tqdm_args):
            key: str = key
            val: instance_cache.model = val
            parent_collection = add_collection(f'{mubin}_Instances', coll_mn)
            if key.endswith('_Far'):
                parent_collection = add_collection(f'{mubin}_Instances_Far', coll_mn)
            instantiate_assets(mubin, key, val['positions'], parent_collection)

    # include_all_collections()
    # include only far lod for intially lightweight viewport, make it one-click easy to enable detailed
    for cname in layer_collection_cache.keys():
        if 'Instances' in cname:
            exclude_collection(cname, False)
        if 'Instances' in cname and 'Instances_Far' not in cname:
            exclude_collection(cname)

    end_time = time.time()
    sec = end_time - start_time
    print(f'\nCompleted in {sec} seconds.')


def instantiate_assets(mubin_name, model_name, positions, parent_collection):
    link_success = link_asset(model_name)
    if not link_success:
        return

    model_asset = bpy.data.objects.get(model_name)
    if not model_asset:
        print(f'WARNING: {model_asset} not found')
        return

    new_collection_name = f'{mubin_name}_{model_name}'
    link_to_this_coll: bpy.types.Collection = add_collection(new_collection_name, parent_collection).collection

    for pos in positions:
        # print(model_instance_counter)
        location = pos['location']
        rotate = pos['rotate']
        scale = pos['scale']

        model_copy: bpy.types.Object = model_asset.copy()

        link_to_this_coll.objects.link(model_copy)

        # this is a bit complicated, but it works
        # useful link for explaining order of matrix operations
        # https://blender.stackexchange.com/questions/44760/rotate-objects-around-their-origin-along-a-global-axis-scripted-without-bpy-op
        r_m0 = mathutils.Matrix.Rotation(math.radians(-90), 4, 'X')
        t_m = mathutils.Matrix.Translation(location)
        r_m1 = mathutils.Matrix.Rotation(math.radians(90), 4, 'X')
        r_m2 = mathutils.Euler(rotate).to_matrix().to_4x4()

        model_copy.matrix_world = r_m1 @ t_m @ r_m2 @ r_m0
        model_copy.scale = scale

        model_instance_counter[model_name] += 1
        # if model_instance_counter[model_name] > 5:
        #     break

    # exclude collection for performance
    exclude_collection(f'{model_name}_Asset')
    exclude_collection(new_collection_name)


def link_asset(model_name):
    asset_collection_name = f'{model_name}_Asset'

    # asset is likely already imported
    if model_name not in bpy.data.objects:
        append_directory = Path(f"asset_library\\assets\\{model_name}.blend").absolute()
        # make sure there's an asset to append
        if not append_directory.is_file():
            print(f'asset file for {model_name} not found')
            print(f'path: {append_directory}')
            return 'append failed'

        # make sure we're in the correct collection
        add_collection(asset_collection_name, layer_collection_cache['Assets.001'])
        append_directory = f'{str(append_directory)}\\Collection\\'
        files = [{'name': model_name}]

        # link haha
        try:
            bpy.ops.wm.append(directory=append_directory, files=files, link=True, instance_collections=True)
            model_instance_counter[model_name] = 0
        except:
            print('append failed')
            return 'append failed'
        bpy.ops.object.select_all(action='DESELECT')
    else:
        exclude_collection(asset_collection_name, False)
    return True


def setupLayout():
    """this makes the layout viewport show the image textures and extends clipping distance"""
    for area in bpy.data.screens["Layout"].areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    # bpy.ops.view3d.view_all(center=True)
                    space.shading.color_type = 'TEXTURE'
                    space.clip_end = 100000
        if area.type == 'OUTLINER':
            space = area.spaces[0]
            space.show_restrict_column_viewport = True


def main():
    print('importer main')
    return


if __name__ == "__main__":
    print(f"{__file__} is being run directly")
    main()
else:
    print(f"{__file__} is being imported")

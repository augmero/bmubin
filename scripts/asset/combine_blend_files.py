import bpy
import os
from pathlib import Path


layer_collection_cache = {}
vl_collections = bpy.context.scene.view_layers["ViewLayer"].layer_collection


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


def set_active_collection(name):
    context = bpy.context
    context.view_layer.active_layer_collection = layer_collection_cache[name]
    return layer_collection_cache[name]


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


def combine_mubins(paths: list = []):
    for path in paths:
        path = Path(path)
        prefix = path.stem
        link_mubin(path)
        exclude_collection(prefix, False)
    bpy.ops.object.select_all(action='DESELECT')


def link_mubin(append_directory: Path):
    stem = Path(append_directory).stem
    print(f'\n\n{stem}\n\n')

    add_collection(stem)

    append_directory = f'{str(append_directory)}\\Collection\\'
    files = [{'name': stem}]
    try:
        bpy.ops.wm.append(directory=append_directory, files=files, link=True, instance_collections=True)
    except:
        print('append failed')
        return 'append failed'

    exclude_collection(stem)


def blends_in_directory(path):
    # directory = 'asset_library\\mubins_by_prefix'
    # print(f'combining all files from {directory}')
    ret = []
    for dirpath, dirnames, files in os.walk(Path(path)):
        for name in files:
            if '.blend' in name:
                file_path = os.path.abspath(os.path.join(dirpath, name))
                ret.append(file_path)
    return ret

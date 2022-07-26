import bpy
import traceback
import time
from pathlib import Path
import json
from scripts.classes.session_cache import session_cache

with open("mbconfig.json", "r") as f:
    config = json.load(f)

# THIS SCRIPT RUNS WITHIN BLENDER

vl_collections = bpy.context.scene.view_layers["ViewLayer"].layer_collection

def include_all_collections():
    exclude_all_collection_view_layer(vl_collections, False)

def exclude_all_collection_view_layer(p_collection, exclude):
    for collection in p_collection.children:
        collection.exclude = exclude
        if collection.children:
            exclude_all_collection_view_layer(collection, exclude)

def retrieve_layer_collection_BFS(layer_collection, collection_name):
    layers = [l for l in layer_collection.children]
    while len(layers)>0:
        layer = layers.pop(0)
        if layer.name == collection_name:
            return layer
        if layer.children and len(layer.children)>0:
            layers += layer.children

def import_actor(actor: dict, mod_folder: str, cache={}, exported={}, data_dir='', session_cache:session_cache={}):
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

    if not session_cache.built_assets.get(model_name):
        print(f'{model_name} NOT FOUND IN ASSET LIBRARY, SKIPPING')
        return

    armature = None
    # TODO: fix this
    append_directory = Path(f"asset_library\\assets\\{model_name}.blend").absolute()
    append_directory = f'{str(append_directory)}\\Collection\\'
    print(append_directory)
    files = [{'name': model_name}]
    if session_cache.imported_assets.get(model_name):
        # print(f'EXISTING IMPORT: model {model_name} already imported, importing again')

        layer_collection = session_cache.layer_collection_tracker[model_name]['layer_collection']
        bpy.context.view_layer.active_layer_collection = layer_collection

        session_cache.layer_collection_tracker[model_name]['count'] += 1

        bpy.ops.wm.append(directory=append_directory, files=files, link=True, instance_collections=True, do_reuse_local_id=True)
        bpy.ops.object.make_override_library()
        
        suffix = '.'+str(session_cache.layer_collection_tracker[model_name]['count']).zfill(3)
        armature = bpy.data.objects[model_name+suffix]

        # deselect all
        bpy.ops.object.select_all(action='DESELECT')

    else:
        # print(f'NEW IMPORT: model {model_name}')
        bpy.ops.object.select_all(action='DESELECT')

        # structure will be like
        # actors (or far LOD)
        # |_
        #   model_name collection
        #   |_
        #       model_name
        #       |_
        #           armature (also named model_name but with some number .001 etc)

        # Create model name collection collection (not a typo)
        model_name_collection_name = f'{model_name} collection'
        collection = bpy.context.blend_data.collections.new(model_name_collection_name)
        bpy.data.collections['Actors'].children.link(collection)
        layer_collection = retrieve_layer_collection_BFS(vl_collections, model_name_collection_name)
        bpy.context.view_layer.active_layer_collection = layer_collection

        # cache this collection by model name so it's easier to find when we're duplicating stuff
        session_cache.layer_collection_tracker[model_name] = {'layer_collection': layer_collection, 'count': 1}

        # link override so we can pose the armature
        # this is way better than appending for file size and allows for the user to make the data local as needed
        # link haha
        bpy.ops.wm.append(directory=append_directory, files=files, link=True, instance_collections=True)
        bpy.ops.object.make_override_library()


        # for some reason override libraries makes the armature .001
        armature = bpy.data.objects[model_name+'.001']
        session_cache.imported_assets[model_name] = True
        bpy.ops.object.select_all(action='DESELECT')

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

    # Set transforms
    bone = None
    if armature.type == 'ARMATURE':
        for child_bone in armature.pose.bones:
            if child_bone.name == 'Root':
                bone = child_bone
                break
            elif child_bone.name == 'Model':
                bone = child_bone
                break
            else:
                bone = child_bone
                break

        bone.rotation_mode = 'XYZ'
        if bone is not None:
            bone.location = location
            bone.scale = scale
            bone.rotation_euler = rotate
        else:
            print('Root bone could not be found!')
    else:
        print('Imported armature could not be found!')

    # Rename armature
    # armature.name = f"{name} ({actor['HashId']})"

    # exclude collection for performance
    exclude_layer_collection = session_cache.layer_collection_tracker[model_name]['layer_collection'].children[-1]
    exclude_layer_collection.exclude = True
    # deselect all
    bpy.ops.object.select_all(action='DESELECT')
    print(f'Imported {name}: {actor["HashId"]} successfully.\n')
    return


def import_mubin(mubin: Path, import_far, session_cache: session_cache):
    print(f'import_mubin {mubin}')
    from .io.open_oead import OpenOead
    from .io.data import Data
    context = bpy.context
    Data.init()
    data_dir = config["dataDir"]
    cache = Data.cache
    exported = Data.exported
    data = OpenOead.from_path(mubin)
    if not session_cache:
        print('no session cache?')
        return
    
    # bpy.data.collections['Collection'].name = mubin.stem

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
                        # Create Far LOD collection
                        if 'Far LOD' not in context.blend_data.collections:
                            collection = context.blend_data.collections.new("Far LOD")
                            context.scene.collection.children.link(collection)

                        # Set context
                        print(context.view_layer.layer_collection.children)
                        context.view_layer.active_layer_collection = context.view_layer.layer_collection.children["Far LOD"]

                        # Import actor
                        import_actor(actor, f'{content}..\\', cache=cache, exported=exported, data_dir=data_dir, session_cache=session_cache)
                else:
                    # Create Actors collection
                    if 'Actors' not in context.blend_data.collections:
                        collection = context.blend_data.collections.new("Actors")
                        context.scene.collection.children.link(collection)

                    # Set context
                    context.view_layer.active_layer_collection = context.view_layer.layer_collection.children["Actors"]

                    # Import actor
                    import_actor(actor, f'{content}..\\', cache=cache, exported=exported, data_dir=data_dir, session_cache=session_cache)
            except:
                print(f'Could not import {actor["UnitConfigName"]}\n{traceback.format_exc()}')

                error = ''
                if Path(f'{data_dir}\\error.txt').is_file():
                    error = Path(f'{data_dir}\\error.txt').read_text()

                Path(f'{data_dir}\\error.txt').write_text(
                    f'{error}Could not import {actor["UnitConfigName"]}\n{traceback.format_exc()}{"- " * 30}\n')

        
        setupLayout()

        end_time = time.time()
        sec = end_time - start_time
        print(f'\nCompleted in {sec} seconds.')
    return

# this makes the layout viewport show the image textures and extends clipping distance
def setupLayout():
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


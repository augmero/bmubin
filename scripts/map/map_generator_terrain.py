from collections import Counter
import math
import os
import struct
import bpy
import bmesh
from pathlib import Path
try:
    from tqdm import tqdm
except:
    # installs progress bar in bpython
    from pip._internal import main
    main(['install', 'tqdm'])
from tqdm import tqdm
import sys
import json

with open("scripts\\map\\index_mapping.json", "r") as f:
    index_mapping = json.load(f)
    index_mapping = index_mapping['index_mapping']
    f.close()


bm: bmesh.types.BMesh = bmesh.new()


bvert_material_table = {}
color_layer = bm.loops.layers.float_color.new("material_data")
uv_lay0 = bm.loops.layers.uv.new("material0")
uv_lay1 = bm.loops.layers.uv.new("material1")
blocks = []
bvert_location_cache = {}

# block
# {
#   right: [bverts]
#   bottom: [bverts]
# }

# Store the internal edges of all LODs by location, for use in combining LODs
# lod_inside_edge_by_location
lod_borders = [None, {}, {}, {}, {}, {}, {}, {}, {}, None]
lod_current = -1
lod_current_verts = []
target = "A-1"


def clean_up_memory():
    global lod_borders, lod_current_verts, bvert_material_table, color_layer, uv_lay0, uv_lay1, blocks, bvert_location_cache
    lod_borders = None
    lod_current_verts = None
    bvert_material_table = None
    color_layer = None
    uv_lay0 = None
    uv_lay1 = None
    blocks = None
    bvert_location_cache = None


def blocks_add_entry(entry):
    blocks[-1].append(entry)


def blocks_new_row():
    # print('blocks_new_row')
    # print(len(blocks))
    if len(blocks) > 1:
        merge_blocks()
    blocks.append([])


def vert_dist(lod):
    return float(scale_multiplier[lod])


x_dist = float(1/83)
vadd_viewport = [
    (0, 0),
    (0, 1),
    (x_dist, 1),
    (x_dist, 0),
]
vadd = [
    (0, 0),
    (0, 1),
    (0, 1),
    (0, 0),
]


def make_a_face(face_verts):
    if None in face_verts:
        return None
    new_face = None
    try:
        new_face = bm.faces.new(face_verts)
    except:
        pass
    if not new_face:
        return None

    face_mats0 = []
    face_mats1 = []
    for loop in new_face.loops:
        face_mats0.append(bvert_material_table[loop.vert][0])
        face_mats1.append(bvert_material_table[loop.vert][1])

    def get_most_common(lst: list):
        return Counter(lst).most_common(1)[0][0]

    face_mat0 = get_most_common(face_mats0)
    face_mat1 = get_most_common(face_mats1)

    for index, loop in enumerate(new_face.loops):
        # rgba
        make_color = [
            bvert_material_table[loop.vert][0],
            bvert_material_table[loop.vert][1],
            bvert_material_table[loop.vert][2],
            1
        ]
        loop[color_layer] = make_color
        m0uv = (face_mat0 + vadd[index][0], vadd[index][1])
        m1uv = (face_mat1 + vadd[index][0], vadd[index][1])
        loop[uv_lay0].uv = m0uv
        loop[uv_lay1].uv = m1uv


def connect_lod_borders(lod):
    border_1 = lod_borders[lod]
    border_2 = lod_borders[lod+1]
    border_3 = None
    if lod+2 < 9:
        if len(lod_borders[lod+2]) > 0:
            border_3 = lod_borders[lod+2]
    if not border_2 or not border_1:
        print(f"connect_lod_borders {lod} input sanitization did not pass")
        return
    dist_1 = vert_dist(lod)
    # dist_2 = vert_dist(lod+1)
    for bvert in border_1.values():
        bverts = get_face_verts_2_to_3(dist_1, bvert, border_1, border_2)
        if len(bverts) < 5 and border_3:
            # print(f'2 to 5, lod {lod}')
            bverts = get_face_verts_2_to_5(dist_1, bvert, border_1, border_3)

        faces = None
        if len(bverts) == 5:
            faces = pair_face_verts_2_to_3(bverts)
        if len(bverts) == 7:
            faces = pair_face_verts_2_to_5(bverts)

        if not faces:
            continue
        for face_verts in faces:
            make_a_face(face_verts)


def cache_border_verts():
    global lod_current
    global lod_borders
    global lod_current_verts
    for bvert in lod_current_verts:
        if len(bvert.link_edges) > 3:
            continue
        bvert: bmesh.types.BMVert = bvert
        bv_location = str(bvert.co.x) + str(bvert.co.y)
        lod_borders[lod_current][bv_location] = bvert


def merge_blocks():
    # print('merge_blocks')

    # function to connect the faces of adjacent blocks
    block_row_len = len(blocks[0])
    for block_index in range(block_row_len):
        # print(f'block_index {block_index}')
        block = blocks[0][block_index]
        if not block:
            continue

        block_below = None
        if len(blocks) > 1 and len(blocks[1]) == len(blocks[0]):
            block_below = blocks[1][block_index]
        # print(f'block_below {bool(block_below)}')
        if block_below:
            # print(len(block[0]))
            # print(len(block[-1]))
            max_range = min(len(block[-1])-1, len(block_below[0])-1)
            for bvert_index in range(max_range):
                face_verts = [
                    block[-1][bvert_index],
                    block[-1][bvert_index+1],
                    block_below[0][bvert_index+1],
                    block_below[0][bvert_index],
                ]
                if None in face_verts:
                    continue
                make_a_face(face_verts)

        block_right = None
        if block_index < block_row_len-1:
            block_right = blocks[0][block_index+1]
        # print(f'block_right {bool(block_right)}')
        if block_right:
            for bvert_index in range(len(block)-1):
                face_verts = [
                    block[bvert_index][-1],
                    block_right[bvert_index][0],
                    block_right[bvert_index+1][0],
                    block[bvert_index+1][-1],
                ]
                if None in face_verts:
                    continue
                make_a_face(face_verts)

        # handle corner face
        block_diagonal = None
        if block_below and block_index < block_row_len-1:
            block_diagonal = blocks[1][block_index+1]
        if block_right and block_below and block_diagonal:
            face_verts = [
                block[-1][-1],
                block_right[-1][0],
                block_diagonal[0][0],
                block_below[0][-1],
            ]
            if None not in face_verts:
                make_a_face(face_verts)

    blocks.pop(0)


def build_block(grid_tl, grid_xy, detail, mdb):
    grid_x = (grid_xy[0] - grid_tl[0])
    grid_y = (grid_xy[1] - grid_tl[1])

    # handle LOD focus, ignore if far away
    if lod_ignore(target, detail, (grid_x, grid_y)):
        blocks_add_entry(None)
        return

    # if detail>1:
    #     blocks_add_entry(None)
    #     return

    name = '5' + str(detail)
    grid_z = z_from_xy(grid_xy, mdb)

    name += format(grid_z, '0>8X')
    hfile = None
    mfile = None

    # https://zeldamods.org/wiki/Water.extm
    # https://zeldamods.org/wiki/MATE
    byte_structure_mate = '<BBBB'
    byte_entry_size_mate = 4
    file_name_mate = 'map_data/mate/' + name + '.mate'
    # https://zeldamods.org/wiki/HGHT
    byte_structure_hght = '<H'
    byte_entry_size_hght = 2
    file_name_hght = 'map_data/terrain/' + name + '.hght'
    # https://zeldamods.org/wiki/Grass.extm

    if os.path.isfile(file_name_hght):
        try:
            hfile = open(file_name_hght, 'rb')
            mfile = open(file_name_mate, 'rb')
        except:
            print(f'open {file_name_hght} failed')
            blocks_add_entry(None)
            return
    else:
        # print(f'{file_name} does not exist')
        blocks_add_entry(None)
        return

    # https://docs.python.org/3/library/struct.html
    h_data = struct.unpack(byte_structure_hght, hfile.read(byte_entry_size_hght))
    m_data = struct.unpack(byte_structure_mate, mfile.read(byte_entry_size_mate))
    heights = []
    material0 = []
    material1 = []
    blend_weight = []
    while h_data:
        heights.append(h_data[0])
        material0.append(m_data[0])
        material1.append(m_data[1])
        blend_weight.append(m_data[2])
        try:
            h_data = struct.unpack(byte_structure_hght, hfile.read(byte_entry_size_hght))
            m_data = struct.unpack(byte_structure_mate, mfile.read(byte_entry_size_mate))
        except:
            h_data = None
            m_data = None

    if len(heights) != 65536:
        print('not enough heights?')
        return

    if len(heights) != len(material0):
        print('height and material mismatch')
        print(len(heights))
        print(len(material0))
        return

    # raise 'stop'

    grid_rel_x = 256*grid_x
    grid_rel_y = 256*grid_y

    vertex_x = 0
    vertex_y = 0
    # make verts
    rows = []
    row = []

    for index in range(len(heights)):
        height = heights[index]
        if vertex_x > 255:
            vertex_x = 0
            vertex_y += 1
            rows.append(row)
            row = []
        if vertex_y > 255:
            print("this shouldn't happen")
            vertex_y = 0

        mult_loc = float(scale_multiplier[detail])
        x_loc = mult_loc * (grid_rel_x + vertex_x)
        y_loc = mult_loc * (grid_rel_y + vertex_y)
        location_cache_key = str(x_loc) + str(y_loc)
        vertex_x += 1
        if location_cache_key in bvert_location_cache:
            if bvert_location_cache[location_cache_key] == False:
                bvert_location_cache[location_cache_key] = True
            else:
                row.append(None)
                continue
        else:
            bvert_location_cache[location_cache_key] = True

        bvert = bm.verts.new((
            x_loc,
            y_loc,
            height
        ))
        global lod_current_verts
        lod_current_verts.append(bvert)
        row.append(bvert)

        mat0 = index_mapping[material0[index]]
        mat1 = index_mapping[material1[index]]
        blen = blend_weight[index]
        bvert_material_table[bvert] = [
            float(mat0)/83,
            float(mat1)/83,
            blen
        ]
        # bvert_material_table[bvert] = [
        #     0,
        #     0,
        #     0
        # ]

    rows.append(row)
    blocks_add_entry(rows)

    previous_row = rows[0]
    for row in rows[1:]:
        for bvert_index in range(len(row)-1):
            face_verts = [
                previous_row[bvert_index],
                previous_row[bvert_index+1],
                row[bvert_index+1],
                row[bvert_index],
            ]
            if None in face_verts:
                continue
            make_a_face(face_verts)

        previous_row = row

    hfile.close()
    mfile.close()


def build_blocks_lod(detail):
    """tl - top left, br - bottom right"""
    tl, br = (0, 0), (1, 1)
    grid_size = 2**detail
    mdb = generate_mdb(grid_size)
    grid_tl = tuple([int(x*grid_size) for x in tl])
    grid_br = tuple([math.ceil(x*grid_size) - 1 for x in br])
    tqdm_args = {
        'leave': False,
        'ascii': True,
        'dynamic_ncols': True,
        'colour': 'green',
        'desc': 'blocks'
    }
    # length_y = grid_br[1] + 1 - grid_tl[1]
    # length_x = grid_br[0] + 1 - grid_tl[0]
    # print(f'length_y {length_y}')
    # print(f'length_x {length_x}')
    for y in tqdm(range(grid_tl[1], grid_br[1] + 1), **tqdm_args):
        blocks_new_row()
        for x in range(grid_tl[0], grid_br[0] + 1):
            build_block(grid_tl, (x, y), detail, mdb)
    blocks_new_row()
    blocks_new_row()


def reset_globals():
    global bm, bvert_material_table, color_layer, blocks, lod_current_verts
    # bm = bmesh.new()
    # bvert_material_table = {}
    # color_layer = bm.loops.layers.float_color.new("water_data")
    blocks = []
    lod_current_verts = []


grid_rows_cols = [0, 2, 4, 8, 16, 32, 64, 128, 256]


def build_map():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    for area in bpy.data.screens["Layout"].areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.color_type = 'TEXTURE'
                    space.clip_end = 100000
        if area.type == 'OUTLINER':
            space = area.spaces[0]
            space.show_restrict_column_viewport = True

    print('\n\n')

    # for detail in range(4, 5):
    for detail in range(8, 0, -1):
        global lod_current
        lod_current = detail
        print(f'detail level {detail}')
        build_blocks_lod(detail)
        cache_border_verts()
        reset_globals()
        connect_lod_borders(detail)

    clean_up_memory()

    print('\n')


def apply_terrain_mat(object: bpy.types.Object):
    terrain_mat_name = 'BotW_Terrain_Map2'
    terrain_mat = bpy.data.materials.get(terrain_mat_name)
    if not terrain_mat:
        # import the actor terrain material from linked_map.blend
        append_directory = Path(f"linked_resources\\linked_map.blend").absolute()
        append_directory = f'{str(append_directory)}\\Material\\'
        files = [{'name': terrain_mat_name}]
        bpy.ops.wm.append(directory=append_directory, files=files, link=True, instance_collections=True)
        terrain_mat = bpy.data.materials.get(terrain_mat_name)
    object.active_material = terrain_mat


def main():
    if not os.path.isdir('map_data'):
        print('No map_data found')
        return

    global target
    # target = "b-7"
    target = (4, 11)

    build_map()
    map_name = f'terrain_map {target}'
    map_object = add_map_to_scene(map_name, bm)
    apply_terrain_mat(map_object)
    save_path = Path(f"asset_library\\{map_name}.blend").absolute()
    bpy.ops.wm.save_as_mainfile(filepath=str(save_path))


if __name__ == "__main__":
    # print(f"{__file__} is being run directly")
    sys.path.append(os.path.abspath("."))
    from scripts.map.map_generator_shared import *
    main()
else:
    # print(f"{__file__} is being imported")
    sys.path.append(os.path.abspath("."))
    from scripts.map.map_generator_shared import *

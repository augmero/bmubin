import math
import bpy


def generate_mdb(n):
    mdb = []
    i = 0
    while len(mdb) < n:
        if i & 0x55555555 == i:
            mdb.append(i)
        i += 1
    return mdb


def z_from_xy(xy, mdb):
    return mdb[xy[0]] + 2*mdb[xy[1]]


scale_multiplier = {
    1: 8,
    2: 4,
    3: 2,
    4: 1,
    5: .5,
    6: .25,
    7: .125,
    8: .0625
}

scale_multiplier_water = {
    key: value * 4 for key, value in scale_multiplier.items()
}


def sanitize_face_verts(bverts, border):
    for index in range(len(bverts)):
        bvert = bverts[index]
        if type(bvert) == str:
            bverts[index] = border.get(bvert)
    return bverts


def pair_face_verts_2_to_3(bverts: list):
    """returns groups of verts to make triangle faces"""
    if len(bverts) < 5:
        return None
    return [
        [
            bverts[0],
            bverts[1],
            bverts[2],
        ],
        [
            bverts[0],
            bverts[2],
            bverts[4],
        ],
        [
            bverts[2],
            bverts[3],
            bverts[4],
        ]
    ]


def get_face_verts_2_to_3(dist_1, bvert, border_1, border_2):
    dist_2 = dist_1/2

    connected_right_loc = str(dist_1 + bvert.co.x) + str(bvert.co.y)
    # connected_left_loc = str(-dist_1 + bvert.co.x) + str(bvert.co.y)
    # connected_top_loc = str(bvert.co.x) + str(-dist_1 + bvert.co.y)
    connected_below_loc = str(bvert.co.x) + str(dist_1 + bvert.co.y)

    bverts = [bvert]

    c_r = str(dist_1 + bvert.co.x) + str(bvert.co.y)  # right
    c_l = str(-dist_2 + bvert.co.x) + str(bvert.co.y)  # left
    c_d = str(bvert.co.x) + str(dist_1 + bvert.co.y)  # down
    c_u = str(bvert.co.x) + str(-dist_2 + bvert.co.y)  # up
    if bool(border_2.get(c_r)):  # right
        bverts += [
            str(dist_1 + bvert.co.x) + str(bvert.co.y),
            str(dist_1 + bvert.co.x) + str(dist_2 + bvert.co.y),
            str(dist_1 + bvert.co.x) + str(dist_1 + bvert.co.y),
            border_1.get(connected_below_loc)
        ]
    elif bool(border_2.get(c_l)):  # left
        bverts += [
            str(-dist_2 + bvert.co.x) + str(bvert.co.y),
            str(-dist_2 + bvert.co.x) + str(dist_2 + bvert.co.y),
            str(-dist_2 + bvert.co.x) + str(dist_1 + bvert.co.y),
            border_1.get(connected_below_loc)
        ]
    elif bool(border_2.get(c_d)):  # down
        bverts += [
            str(bvert.co.x) + str(dist_1 + bvert.co.y),
            str(dist_2 + bvert.co.x) + str(dist_1 + bvert.co.y),
            str(dist_1 + bvert.co.x) + str(dist_1 + bvert.co.y),
            border_1.get(connected_right_loc)
        ]
    elif bool(border_2.get(c_u)):  # up
        bverts += [
            str(bvert.co.x) + str(-dist_2 + bvert.co.y),
            str(dist_2 + bvert.co.x) + str(-dist_2 + bvert.co.y),
            str(dist_1 + bvert.co.x) + str(-dist_2 + bvert.co.y),
            border_1.get(connected_right_loc)
        ]
    bverts = sanitize_face_verts(bverts, border_2)
    return bverts


def pair_face_verts_2_to_5(bverts: list):
    """returns groups of verts to make triangle faces"""
    if len(bverts) < 7:
        return None
    return [
        [
            bverts[0],
            bverts[1],
            bverts[2],
        ],
        [
            bverts[0],
            bverts[2],
            bverts[3],
        ],
        [
            bverts[0],
            bverts[3],
            bverts[6],
        ],
        [
            bverts[3],
            bverts[4],
            bverts[6],
        ],
        [
            bverts[4],
            bverts[5],
            bverts[6],
        ],
    ]


def get_face_verts_2_to_5(dist_1, bvert, border_1, border_2):
    dist_2 = dist_1/4

    connected_right_loc = str(dist_1 + bvert.co.x) + str(bvert.co.y)
    connected_below_loc = str(bvert.co.x) + str(dist_1 + bvert.co.y)

    bverts = [bvert]

    c_r = str(dist_1 + bvert.co.x) + str(bvert.co.y)  # right
    c_l = str(-dist_2 + bvert.co.x) + str(bvert.co.y)  # left
    c_d = str(bvert.co.x) + str(dist_1 + bvert.co.y)  # down
    c_u = str(bvert.co.x) + str(-dist_2 + bvert.co.y)  # up
    if bool(border_2.get(c_r)):  # right
        bverts += [
            str(dist_1 + bvert.co.x) + str(bvert.co.y),
            str(dist_1 + bvert.co.x) + str(dist_2 + bvert.co.y),
            str(dist_1 + bvert.co.x) + str(2*dist_2 + bvert.co.y),
            str(dist_1 + bvert.co.x) + str(3*dist_2 + bvert.co.y),
            str(dist_1 + bvert.co.x) + str(dist_1 + bvert.co.y),
            border_1.get(connected_below_loc)
        ]
    elif bool(border_2.get(c_l)):  # left
        bverts += [
            str(-dist_2 + bvert.co.x) + str(bvert.co.y),
            str(-dist_2 + bvert.co.x) + str(dist_2 + bvert.co.y),
            str(-dist_2 + bvert.co.x) + str(2*dist_2 + bvert.co.y),
            str(-dist_2 + bvert.co.x) + str(2*dist_2 + bvert.co.y),
            str(-dist_2 + bvert.co.x) + str(dist_1 + bvert.co.y),
            border_1.get(connected_below_loc)
        ]
    elif bool(border_2.get(c_d)):  # down
        bverts += [
            str(bvert.co.x) + str(dist_1 + bvert.co.y),
            str(dist_2 + bvert.co.x) + str(dist_1 + bvert.co.y),
            str(2*dist_2 + bvert.co.x) + str(dist_1 + bvert.co.y),
            str(3*dist_2 + bvert.co.x) + str(dist_1 + bvert.co.y),
            str(dist_1 + bvert.co.x) + str(dist_1 + bvert.co.y),
            border_1.get(connected_right_loc)
        ]
    elif bool(border_2.get(c_u)):  # up
        bverts += [
            str(bvert.co.x) + str(-dist_2 + bvert.co.y),
            str(dist_2 + bvert.co.x) + str(-dist_2 + bvert.co.y),
            str(2*dist_2 + bvert.co.x) + str(-dist_2 + bvert.co.y),
            str(3*dist_2 + bvert.co.x) + str(-dist_2 + bvert.co.y),
            str(dist_1 + bvert.co.x) + str(-dist_2 + bvert.co.y),
            border_1.get(connected_right_loc)
        ]
    bverts = sanitize_face_verts(bverts, border_2)
    return bverts


def add_map_to_scene(map_name, bm):
    # add to scene
    bmesh_data = bpy.data.meshes.new(map_name)
    bm.to_mesh(bmesh_data)
    bmesh_object = bpy.data.objects.new(map_name, bmesh_data)
    bmesh_object.location = [-8000, 8000, 0]
    bmesh_object.scale = [3.90752, -3.90752, 0.012207]
    bpy.context.view_layer.active_layer_collection.collection.objects.link(bmesh_object)

    # fix normals
    bpy.ops.object.select_all(action='DESELECT')
    bmesh_object.select_set(True)
    bpy.context.view_layer.objects.active = bmesh_object
    # go edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    # select all faces
    bpy.ops.mesh.select_all(action='SELECT')
    # recalculate outside normals
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.mesh.select_all(action='DESELECT')
    # go object mode again
    bpy.ops.object.editmode_toggle()

    default_collection = bpy.data.collections.get('Collection')
    if default_collection:
        default_collection.name = map_name

    return bmesh_object


# mubin distance stuff _____________________________________
_mubin_prefixes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
_mubin_prefixes = [f'{pf}-' for pf in _mubin_prefixes]
_grid_rows_cols = [0, 2, 4, 8, 16, 32, 64, 128, 256]
# mubin size is 1000m
# 16x16 mubin squares total in map
# A-1 is at 4,5


def _build_mubin_table():
    table = []
    mubin_xy = {}
    for i in range(1, 9):
        row = []
        for prefix in _mubin_prefixes:
            row.append(f'{prefix}{i}')
        table.append(row)
    # print(table)
    sx = 3
    sy = 4
    for i in range(sx, sx+8):
        for j in range(sy, sy+10):
            mubin_xy[table[i-sx][j-sy]] = (j-1, i+1)
    print(mubin_xy)
    return table


def _distance_to_mubin(mubin: str, detail: int, location: tuple):
    """location tuple formatted (x,y)"""
    mult = (float(16) / float(_grid_rows_cols[detail]))

    location_coords = (location[0]*mult, location[1]*mult)
    mc_tl = (_mubin_xy.get(mubin.upper()))
    mubin_coords = (mc_tl[0]+.5, mc_tl[1]+.5)
    distance = math.dist(mubin_coords, location_coords)

    return distance


def _distance_to_location(target_coords: tuple, detail: int, location: tuple):
    """location tuple formatted (x,y)"""
    mult = (float(16) / float(_grid_rows_cols[detail]))

    location_coords = (location[0]*mult, location[1]*mult)
    distance = math.dist(target_coords, location_coords)

    return distance


_threshold_by_lod = [-1, 20, 8, 6, 4, 1, .75, .5, .25]


def lod_ignore(target, detail: int, location: tuple):
    """target can be either a mubin string like \"E-4\" or a location like (7,7)"""
    # if detail == 1:
    #     return False
    # if detail > 4:
    #     return True
    # if detail < 5:
    #     return False
    threshold = _threshold_by_lod[detail]
    dist = 10
    if type(target) == str:
        dist = _distance_to_mubin(target, detail, location)
    elif type(target) == tuple:
        dist = _distance_to_location(target, detail, location)
    return dist > threshold


# mubin size is 1000m
# 16x16 mubin squares total in map
# A-1 is at 3,4
# E-4 is at 7,7
# H-2 is at 10,5
# top left coordinate of each mubin relative to the 16x16 map
_mubin_xy = {
    'A-1': (3, 4),
    'B-1': (4, 4),
    'C-1': (5, 4),
    'D-1': (6, 4),
    'E-1': (7, 4),
    'F-1': (8, 4),
    'G-1': (9, 4),
    'H-1': (10, 4),
    'I-1': (11, 4),
    'J-1': (12, 4),
    'A-2': (3, 5),
    'B-2': (4, 5),
    'C-2': (5, 5),
    'D-2': (6, 5),
    'E-2': (7, 5),
    'F-2': (8, 5),
    'G-2': (9, 5),
    'H-2': (10, 5),
    'I-2': (11, 5),
    'J-2': (12, 5),
    'A-3': (3, 6),
    'B-3': (4, 6),
    'C-3': (5, 6),
    'D-3': (6, 6),
    'E-3': (7, 6),
    'F-3': (8, 6),
    'G-3': (9, 6),
    'H-3': (10, 6),
    'I-3': (11, 6),
    'J-3': (12, 6),
    'A-4': (3, 7),
    'B-4': (4, 7),
    'C-4': (5, 7),
    'D-4': (6, 7),
    'E-4': (7, 7),
    'F-4': (8, 7),
    'G-4': (9, 7),
    'H-4': (10, 7),
    'I-4': (11, 7),
    'J-4': (12, 7),
    'A-5': (3, 8),
    'B-5': (4, 8),
    'C-5': (5, 8),
    'D-5': (6, 8),
    'E-5': (7, 8),
    'F-5': (8, 8),
    'G-5': (9, 8),
    'H-5': (10, 8),
    'I-5': (11, 8),
    'J-5': (12, 8),
    'A-6': (3, 9),
    'B-6': (4, 9),
    'C-6': (5, 9),
    'D-6': (6, 9),
    'E-6': (7, 9),
    'F-6': (8, 9),
    'G-6': (9, 9),
    'H-6': (10, 9),
    'I-6': (11, 9),
    'J-6': (12, 9),
    'A-7': (3, 10),
    'B-7': (4, 10),
    'C-7': (5, 10),
    'D-7': (6, 10),
    'E-7': (7, 10),
    'F-7': (8, 10),
    'G-7': (9, 10),
    'H-7': (10, 10),
    'I-7': (11, 10),
    'J-7': (12, 10),
    'A-8': (3, 11),
    'B-8': (4, 11),
    'C-8': (5, 11),
    'D-8': (6, 11),
    'E-8': (7, 11),
    'F-8': (8, 11),
    'G-8': (9, 11),
    'H-8': (10, 11),
    'I-8': (11, 11),
    'J-8': (12, 11)
}

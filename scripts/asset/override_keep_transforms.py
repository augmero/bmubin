import bpy
import mathutils

# This script makes an override library from an instanced collection and keeps its transforms the same (just on the armature instead)

# NOTE: This script sometimes doesn't work and I don't know why, probably something with bpy ops
# If the active object disappears just ctrl z and try again
# Most likely the override library part worked but the transforms didn't, it'll be at world origin
# If anyone knows how to fix this let me know / submit a PR

obj = bpy.context.active_object
name = obj.name[:-4]
name_len = len(obj.name)
transforms = {
    'l': obj.location,
    'r': obj.rotation_euler,
    's': obj.scale
}
bpy.ops.object.make_override_library()
print(name)
print('looping')

# find the new object and add the transforms back
for possible_object in bpy.data.objects:
    possible_object: bpy.types.Object = possible_object
    if len(possible_object.name) == name_len and name in possible_object.name:
        if possible_object.type != 'ARMATURE':
            continue
        default_location = bool(x == 0 for x in possible_object.location)
        x = str(round(possible_object.rotation_euler.x, 2))
        default_rotationx = (x == '1.57')
        default_rotationy = (possible_object.rotation_euler.y == 0)
        default_rotationz = (possible_object.rotation_euler.z == 0)
        default_rotation = (default_rotationx and default_rotationy and default_rotationz)
        default_scale = bool(x == 0 for x in possible_object.scale)
        if (default_location and default_rotation and default_scale):
            print(possible_object.name)
            print('setting transforms')
            possible_object.location = transforms['l']
            possible_object.rotation_euler.rotate(mathutils.Euler(transforms['r']))
            possible_object.scale = transforms['s']
            possible_object.select_set(True)
            bpy.context.view_layer.objects.active = possible_object
            break

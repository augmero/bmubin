import bpy
import mathutils

# This script makes an override library from an instanced collection and keeps its transforms the same (just on the armature instead)

# NOTE: This script sometimes doesn't work and I don't know why, probably something with bpy ops
# If the active object disappears just ctrl z and try again
# Most likely the override library part worked but the transforms didn't, it'll be at world origin
# If anyone knows how to fix this let me know / submit a PR

# select_next means the script will make the next selected object active rather than the newly-overriden one
# helps for overriding a bunch of instances
select_next = True

obj = bpy.context.active_object
name = obj.name[:-4]
name_len = len(obj.name)
transforms = {
    'l': obj.location,
    'r': obj.rotation_euler,
    's': obj.scale
}
existing_armatures = [o.name for o in bpy.data.objects if o.type=='ARMATURE' and name in o.name]
print('\n')
print("existing_armatures")
print(existing_armatures)
bpy.ops.object.make_override_library()
print(name)
print('looping')

new_armatures = [o.name for o in bpy.data.objects if o.type=='ARMATURE' and name in o.name and o.name not in existing_armatures]
print("new_armatures")
print(new_armatures)

# sometimes the override becomes the original name somehow
if len(new_armatures) == 0:
    new_armatures = [name]
if len(new_armatures) == 1:
    new_object = bpy.data.objects[new_armatures[0]]
    print(new_object.name)
    print('setting transforms')
    new_object.location = transforms['l']
    new_object.rotation_euler.rotate(mathutils.Euler(transforms['r']))
    new_object.scale = transforms['s']

    selected_objects = bpy.context.selected_objects
    print(selected_objects)
    if select_next and len(selected_objects) > 0:
        bpy.context.view_layer.objects.active = selected_objects[0]
    else:
        new_object.select_set(True)
        bpy.context.view_layer.objects.active = new_object
import bpy
import os
import json


with open("mbconfig.json", "r") as f:
    config = json.load(f)

textures_path = config['texturesPath']


with open(f"{textures_path}\\normals.json", "r") as f:
    normals: dict = json.load(f)
with open(f"{textures_path}\\masks.json", "r") as f:
    masks: dict = json.load(f)
with open(f"{textures_path}\\trs.json", "r") as f:
    trs: dict = json.load(f)


# This function does it's best to fix all the stuff that the collada import missed
def fix_shaders():
    print('\n\n\n')
    print('fixing shaders...')
    batch_collection = bpy.data.collections['Collection']
    textures_path_abs = os.path.abspath(textures_path)
    for o in batch_collection.objects:
        if o.type == 'ARMATURE':
            continue

        print('\n')
        print(o.name)
        # not sure what these are for, maybe could be used for inside volumetrics
        if 'InsideArea' in o.name or 'InsideMat' in o.name:
            o.hide_render = True
            o.hide_viewport = True

        material_nodes = o.active_material.node_tree.nodes
        material_links = o.active_material.node_tree.links
        o.active_material.blend_method = "HASHED"

        shader = material_nodes.get('Principled BSDF')

        if 'metal' in o.name.lower():
            shader.inputs['Metallic'].default_value = 1

        print('getting base color')
        base_color = material_nodes.get('Image Texture')
        if base_color:
            # handle ALPHA
            # first check if there's an available mask, if not just wire the base color
            image_stem = base_color.image.name[:-7]
            print(f'image stem: {image_stem}')

            mask_image_name = image_stem+"Msk.png"
            mask_image = bpy.data.images.get(mask_image_name)
            if not mask_image and masks.get(image_stem):
                mask_image = bpy.data.images.load(f"{textures_path_abs}\\{mask_image_name}")
            if mask_image:
                print('mask found')
                # open image
                mask_image_path = f"{textures_path_abs}\\{mask_image_name}"
                print(mask_image_path)
                mask_image = bpy.data.images.load(mask_image_path)
                mask_image_node = material_nodes.new(type='ShaderNodeTexImage')
                mask_image_node.image = mask_image
                mask_image_node.location[0] -= 600
                mask_image_node.location[1] -= 300
                material_links.new(shader.inputs["Alpha"], mask_image_node.outputs["Color"])
            else:
                material_links.new(shader.inputs["Alpha"], base_color.outputs["Alpha"])

            # handle NORMAL, might already be imported
            normal_image_name = image_stem+"Nrm.png"
            normal_image = bpy.data.images.get(normal_image_name)
            if not normal_image and normals.get(image_stem):
                normal_image = bpy.data.images.load(f"{textures_path_abs}\\{normal_image_name}")
            if normal_image:
                normal_image_node = material_nodes.new(type='ShaderNodeTexImage')
                normal_image_node.image = normal_image
                normal_image_node.location[0] -= 600
                normal_image_node.location[1] -= 600
                bump = material_nodes.new(type='ShaderNodeBump')
                bump.location[0] -= 200
                bump.location[1] -= 400
                bump.inputs["Strength"].default_value = .3
                material_links.new(bump.inputs["Height"], normal_image_node.outputs["Color"])
                material_links.new(shader.inputs["Normal"], bump.outputs["Normal"])
            else:
                print('no normals found')

            # handle trs - roughness and specular
            trs_image_name = image_stem+"Trs.png"
            trs_image = bpy.data.images.get(trs_image_name)
            if not trs_image and trs.get(image_stem):
                trs_image = bpy.data.images.load(f"{textures_path_abs}\\{trs_image_name}")
            if trs_image:
                trs_image_node = material_nodes.new(type='ShaderNodeTexImage')
                trs_image_node.image = trs_image
                trs_image_node.location[0] -= 600
                # easy one is roughness
                material_links.new(shader.inputs["Roughness"], trs_image_node.outputs["Color"])
                material_links.new(shader.inputs["Specular"], trs_image_node.outputs["Color"])
                # TODO: see if possible to color ramp for specular
            else:
                print('no trs found')
        else:
            print('no base color found')

import bpy
import os
import json
from pathlib import Path

with open("mbconfig.json", "r") as f:
    config = json.load(f)

textures_path = config['texturesPath']
textures_path_abs = os.path.abspath(textures_path)
terrain_hybrid = True


with open(f"linked_resources\\json\\generated\\normals.json", "r") as f:
    normals: dict = json.load(f)
with open(f"linked_resources\\json\\generated\\masks.json", "r") as f:
    masks: dict = json.load(f)
with open(f"linked_resources\\json\\generated\\trs.json", "r") as f:
    trs: dict = json.load(f)
with open(f"linked_resources\\json\\terrainmat_names.json", "r") as f:
    terrainmat_names: dict = json.load(f)
with open(f"linked_resources\\json\\assets_info.json", "r") as f:
    assets_info: dict = json.load(f)


def terrain_shader(object: bpy.types.Object, indices: list):
    # Default terrain shader, mixes two terrains textures together by the vertex color and edge detection
    # if there's only 1 uv map add another for the terrain shader
    if len(object.data.uv_layers) == 1:
        object.data.uv_layers.new(name="UVMap1")
    # rename the uv maps for the shader
    for index, uvmap in enumerate(object.data.uv_layers):
        uvmap.name = f'UVMap{index}'
    # get the array indices from texture_array_indices.json
    print(indices)
    if indices:
        # actor terrain material maybe already imported
        actor_terrain_material = bpy.data.materials.get('BotW_Actor_Terrain')

        if not actor_terrain_material:
            # import the actor terrain material from actor_terrain_material.blend
            append_directory = Path(f"linked_resources\\linked.blend").absolute()
            append_directory = f'{str(append_directory)}\\Material\\'
            files = [{'name': 'BotW_Actor_Terrain'}]
            bpy.ops.wm.append(directory=append_directory, files=files, link=True, instance_collections=True)
        actor_terrain_material = bpy.data.materials.get('BotW_Actor_Terrain')

        # replace the material with the actor terrain one
        object.active_material = actor_terrain_material

        # set up custom properties for material0 and material1
        # the shader uses these to determine which terrain texture to use, and then mixes them by vertex color
        material0 = 0
        material1 = 0
        while(len(indices) > 0):
            index = indices.pop(0)
            if index != 0:
                if material0 == 0:
                    material0 = index
                elif material1 == 0 and material0 != index:
                    material1 = index
                    break
        # yes I swapped them instead of fixing the algo
        object["material0"] = material1
        object["material1"] = material0
        object["scale"] = .1

        geometry_nodes_edge(object)

    else:
        terrain_shader_secondary(object)


def append_node_tree(node_group_name):
    node_tree = bpy.data.node_groups.get(node_group_name)
    if not node_tree:
        # link the nodetree from actor_terrain_material.blend
        append_directory = Path(f"linked_resources\\linked.blend").absolute()
        append_directory = f'{str(append_directory)}\\NodeTree\\'
        files = [{'name': node_group_name}]
        bpy.ops.wm.append(directory=append_directory, files=files, link=True, instance_collections=True)
    node_tree = bpy.data.node_groups.get(node_group_name)
    return node_tree


def link_lamp(lamp_name, location=None):
    # link the collection, we can set location of the collection
    append_directory = Path(f"linked_resources\\linked.blend").absolute()
    append_directory = f'{str(append_directory)}\\Collection\\'
    files = [{'name': lamp_name}]
    bpy.ops.wm.append(directory=append_directory, files=files, link=True,
                      instance_collections=True, do_reuse_local_id=True)

    linked_objects = [o for o in bpy.data.objects if lamp_name in o.name]
    object = bpy.data.objects[linked_objects.pop().name]

    if location:
        object.location = location

    # parent to armature root bone
    armature = [o for o in bpy.data.objects if o.type == 'ARMATURE'].pop()
    object.parent = armature
    root_bone = armature.pose.bones.get("Root")
    if root_bone:
        object.parent_bone = 'Root'
        object.parent_type = 'BONE'
    return object


def solidify_modifier(object):
    solidify = object.modifiers.new("Solidify", "SOLIDIFY")
    solidify.offset = 0
    solidify.use_rim = False


def geometry_nodes_edge(object):
    # geometry nodes
    object.data.color_attributes.new('edge', 'FLOAT_COLOR', 'CORNER')
    gn_edge = append_node_tree('GN - Edge')
    gn_modifier = object.modifiers.new("GN Edge", "NODES")
    gn_modifier["Output_3_attribute_name"] = "edge"
    gn_modifier.node_group = gn_edge


def terrain_and_image_shader(object: bpy.types.Object, indices: list):
    # mix terrain and one image shader
    print('\n\n\n')
    print('terrain and image shader')
    print(indices)
    # append link the node group
    # link image and normal to the node group
    # link node group to shader
    # nodetree maybe already imported

    # custom props
    object["material0"] = indices[0]
    object["scale"] = .1

    material_nodes = object.active_material.node_tree.nodes
    material_links = object.active_material.node_tree.links
    shader = material_nodes.get('Principled BSDF')
    base_color = material_nodes.get('Image Texture')

    geometry_nodes_edge(object)

    # shader node
    actor_terrain_image_node_tree = append_node_tree('BotwTerrainAndImage')

    actor_terrain_image_node = material_nodes.new(type='ShaderNodeGroup')
    actor_terrain_image_node.node_tree = actor_terrain_image_node_tree
    actor_terrain_image_node.location[0] -= 300
    base_color.location[0] -= 600

    # handle NORMAL, might already be imported
    image_stem = base_color.image.name[:-7]
    print(image_stem)
    normal_image_name = image_stem+"Nrm.png"
    print(normal_image_name)
    normal_image = bpy.data.images.get(normal_image_name)
    if not normal_image and normals.get(image_stem):
        normal_image = bpy.data.images.load(f"{textures_path_abs}\\{normal_image_name}")
    if normal_image:
        normal_image_node = material_nodes.new(type='ShaderNodeTexImage')
        normal_image_node.image = normal_image
        normal_image_node.location[0] -= 600
        normal_image_node.location[1] -= 300
        material_links.new(actor_terrain_image_node.inputs["Normal Image"], normal_image_node.outputs["Color"])
        material_links.new(shader.inputs["Normal"], actor_terrain_image_node.outputs["Normal"])
    else:
        print('no normals found')

    # make sure base color displays for viewport
    base_color.select = True
    object.active_material.node_tree.nodes.active = base_color

    material_links.new(actor_terrain_image_node.inputs["Color"], base_color.outputs["Color"])
    material_links.new(shader.inputs["Base Color"], actor_terrain_image_node.outputs["Color"])


def terrain_shader_secondary(object: bpy.types.Object, image_stem=None):
    print(f'terrain_shader {image_stem}')
    material_nodes = object.active_material.node_tree.nodes
    material_links = object.active_material.node_tree.links
    shader = material_nodes.get('Principled BSDF')
    if not image_stem:
        image_stem = object.name
    if 'Mt_' in image_stem:
        image_stem = image_stem.split('Mt_')[1]

    slice_index = terrainmat_names.get(image_stem)
    if slice_index:
        print(f'slice_index {slice_index}')
        alb_image_name = f"MaterialAlb_Slice_{slice_index}_.png"
        alb_image = bpy.data.images.get(alb_image_name)
        if not alb_image:
            alb_image = bpy.data.images.load(f"{textures_path_abs}\\{alb_image_name}")
        if alb_image:
            alb_image_node = material_nodes.new(type='ShaderNodeTexImage')
            alb_image_node.image = alb_image
            alb_image_node.location[0] -= 300
            alb_image_node.location[1] += 200
            material_links.new(shader.inputs["Base Color"], alb_image_node.outputs["Color"])
        else:
            print(f'image load failed for {alb_image_name}')

        normal_image_name = f"MaterialCmb_Slice_{slice_index}_.png"
        normal_image = bpy.data.images.get(normal_image_name)
        if not normal_image:
            normal_image = bpy.data.images.load(f"{textures_path_abs}\\{normal_image_name}")
        if normal_image:
            normal_image_node = material_nodes.new(type='ShaderNodeTexImage')
            normal_image_node.image = normal_image
            normal_image_node.location[0] -= 600
            normal_image_node.location[1] -= 200
            bump = material_nodes.new(type='ShaderNodeBump')
            bump.location[0] -= 200
            bump.location[1] -= 200
            bump.inputs["Strength"].default_value = .3
            material_links.new(bump.inputs["Height"], normal_image_node.outputs["Color"])
            material_links.new(shader.inputs["Normal"], bump.outputs["Normal"])
        else:
            print(f'image load failed for {normal_image_name}')

        # if we're 'translucent' alpha blend the edges
        if object.active_material.blend_method == "BLEND":
            geometry_nodes_edge(object)
            solidify_modifier(object)
            # color attribute -> invert -> bright/contrast -> clamp
            color_attribute_node = material_nodes.new(type='ShaderNodeVertexColor')
            color_attribute_node.layer_name = 'edge'
            color_attribute_node.location[0] -= 1200

            invert_node = material_nodes.new(type='ShaderNodeInvert')
            invert_node.location[0] -= 900
            material_links.new(invert_node.inputs["Color"], color_attribute_node.outputs["Color"])

            bright_contrast_node = material_nodes.new(type='ShaderNodeBrightContrast')
            bright_contrast_node.inputs["Bright"].default_value = -2
            bright_contrast_node.inputs["Contrast"].default_value = 4
            bright_contrast_node.location[0] -= 600
            material_links.new(bright_contrast_node.inputs["Color"], invert_node.outputs["Color"])

            clamp_node = material_nodes.new(type='ShaderNodeClamp')
            clamp_node.location[0] -= 300
            material_links.new(clamp_node.inputs["Value"], bright_contrast_node.outputs["Color"])
            material_links.new(shader.inputs["Alpha"], clamp_node.outputs["Result"])

    else:
        # approximate the closest possible terrain texture, for instance some of the objects have similar names or are misspelled
        import difflib
        image_stem = str(image_stem).replace("Criff", "Cliff")
        terrain_keys = terrainmat_names.keys()
        print(image_stem)
        closest_match = difflib.get_close_matches(image_stem, terrain_keys, 1, .5)
        print(closest_match)
        if len(closest_match) == 1 and closest_match[0] != image_stem:
            terrain_shader_secondary(object, closest_match[0])
        else:
            # No confidence, at least make it show as a missing texture
            missing_tree = append_node_tree('missing_texture')
            missing = material_nodes.new(type='ShaderNodeGroup')
            missing.node_tree = missing_tree
            missing.location[0] -= 250
            material_links.new(shader.inputs["Base Color"], missing.outputs["Color"])

            print('no terrain mats found')


def make_light(name: str, power, size, color):
    # if you have photographer addon enabled it breaks setting the energy property of lights
    bpy.ops.preferences.addon_disable(module="photographer")
    print(f'making a light: {name}')
    light = bpy.data.lights.new(name, type='POINT')
    light.energy = power
    light.color = color
    light.shadow_soft_size = size
    light_object = bpy.data.objects.new(name, object_data=light)
    bpy.context.collection.objects.link(light_object)
    return light_object


def fix_shaders(dae_name):
    # This function does its best to fix all the stuff that the collada import missed

    # Vertex color is used as an attribute to mix in a secondary texture
    # try to use Render state - Alpha Control from bfres to set alpha settings in blender
    #   AlphaMask = Alpha Blend??
    print('\n\n\n')
    print('fixing shaders...')
    batch_collection = bpy.data.collections['Collection']
    asset_info = assets_info.get(dae_name)
    for o in batch_collection.objects:
        if o.type != 'MESH':
            continue

        print('\n')
        print(o.name)

        # not sure what these are for, maybe could be used for inside volumetrics
        if 'InsideArea' in o.name or 'InsideMat' in o.name:
            o.hide_render = True
            o.hide_viewport = True
            continue

        material_nodes = o.active_material.node_tree.nodes
        material_links = o.active_material.node_tree.links
        print('getting base color')
        base_color = material_nodes.get('Image Texture')

        if 'flag' not in o.name.lower():
            o.active_material.use_backface_culling = True
        o.active_material.blend_method = "HASHED"

        shader = material_nodes.get('Principled BSDF')

        if 'metal' in o.name.lower():
            shader.inputs['Metallic'].default_value = 1

        # 0 specular seems a bit too flat
        # if shader.inputs['Specular'].default_value < .1:
        #     shader.inputs['Specular'].default_value = .2

        if asset_info:
            mat_info = asset_info.get(o.active_material.name)

            if mat_info:
                print(mat_info)
                render_state = mat_info.get("renderState")
                if render_state:
                    if mat_info.get("renderState") == "Opaque":
                        o.active_material.blend_method = "OPAQUE"
                    elif mat_info.get("renderState") == "AlphaMask":
                        o.active_material.blend_method = "HASHED"
                    elif mat_info.get("renderState") == "Custom":
                        o.active_material.blend_method = "HASHED"
                    elif mat_info.get("renderState") == "Translucent":
                        o.active_material.blend_method = "BLEND"
                else:
                    o.active_material.blend_method = "HASHED"
                indices: list = mat_info.get('indexArray')
                if not base_color:
                    terrain_shader(o, indices)
                    continue
                elif indices and base_color and 'blend' not in o.name.lower() and terrain_hybrid == True:
                    terrain_and_image_shader(o, indices)
                    continue

        if base_color:
            # handle ALPHA
            # first check if there's an available mask, if not just wire the base color
            image_stem = base_color.image.name[:-7]
            print(f'image stem: {image_stem}')
            add_normal = True

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
                is_lamp = 'lamp' in dae_name.lower() or 'lamp' in o.name.lower()
                if 'glass' in o.name.lower() and not is_lamp:
                    # cycles
                    glass_node_tree = append_node_tree('BotW_Cycles_Glass')
                    glass_node = material_nodes.new(type='ShaderNodeGroup')
                    glass_node.node_tree = glass_node_tree

                    # eevee
                    default_alpha = .4
                    if 'inside' in o.name.lower() or 'outside' in o.name.lower():
                        default_alpha = .2
                    shader.inputs['Alpha'].default_value = default_alpha
                else:
                    material_links.new(shader.inputs["Alpha"], base_color.outputs["Alpha"])
                # make lamps emissive warmer, add lights
                if 'glass' in o.name.lower() and is_lamp:
                    print('LAMP DETECTED')
                    add_normal = False
                    emission_image_node = None
                    for nd in material_nodes:
                        if nd.label == 'Emission':
                            emission_image_node = nd
                    if emission_image_node:
                        ramp_tree = append_node_tree('warm_emissive_ramp')
                        ramp = material_nodes.new(type='ShaderNodeGroup')
                        ramp.node_tree = ramp_tree
                        emission_image_node.location[0] -= 300
                        ramp.location[0] -= 150
                        material_links.new(ramp.inputs["Fac"], emission_image_node.outputs["Color"])
                        material_links.new(shader.inputs["Emission"], ramp.outputs["Color"])
                    # find center location
                    # https://blender.stackexchange.com/questions/62040/get-center-of-geometry-of-an-object
                    # local_bbox_center = 0.125 * sum((Vector(b) for b in o.bound_box), Vector())
                    # global_bbox_center = o.matrix_world @ local_bbox_center

                    # add lights
                    # warm_light_color = (1, .639, .366)
                    # light_local = make_light('light_local', 80, .15, warm_light_color)
                    # light_local.location = global_bbox_center
                    # light_global = make_light('light_global', 40, .5, warm_light_color)
                    # light_global.visible_diffuse = False
                    # light_global.location = global_bbox_center
                    link_lamp('lamp_light')

            # handle NORMAL, might already be imported
            normal_image_name = image_stem+"Nrm.png"
            normal_image = None
            if add_normal:
                normal_image = bpy.data.images.get(normal_image_name)
            if add_normal and not normal_image and normals.get(image_stem):
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
            else:
                print('no trs found')
        else:
            print('no base color found, trying terrain shader')
            terrain_shader_secondary(o)

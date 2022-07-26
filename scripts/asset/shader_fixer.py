from genericpath import isfile
import bpy
import bmesh
from mathutils import Vector
import os
import json
from pathlib import Path

with open("mbconfig.json", "r") as f:
    config = json.load(f)
    f.close()

textures_path = config['texturesPath']
textures_path_abs = os.path.abspath(textures_path)
asset_name = "test"


with open(f"linked_resources\\json\\generated\\normals.json", "r") as f:
    normals: dict = json.load(f)
    f.close()
with open(f"linked_resources\\json\\generated\\masks.json", "r") as f:
    masks: dict = json.load(f)
    f.close()
with open(f"linked_resources\\json\\generated\\trs.json", "r") as f:
    trs: dict = json.load(f)
    f.close()
with open(f"linked_resources\\json\\terrainmat_names.json", "r") as f:
    terrainmat_names: dict = json.load(f)
    f.close()
with open(f"linked_resources\\json\\assets_info.json", "r") as f:
    assets_info: dict = json.load(f)
    f.close()
with open(f"linked_resources\\json\\sensible_defaults.json", "r") as f:
    sensible_defaults: dict = json.load(f)
    f.close()


# common patterns for shaderOptionsIndexArray (made from uking_texture_array_texture)
# shader_patterns = {
#     "[0, 1, 1, -1, -1, -1]": 400,
#     "[0, 1, -1, -1, -1, -1]": 116,
#     "[0, 1, 0, 1, 0, -1]": 350,
#     "[-1, -1, 0, 1, 0, -1]": 355,
#     "[0, 1, 0, 1, -1, -1]": 5,
#     "[0, -1, 0, 1, 0, -1]": 17,
#     "[-1, 1, 1, -1, -1, -1]": 4,
#     "[-1, 1, -1, 1, -1, -1]": 4,
#     "[0, 1, -1, 1, -1, -1]": 1,
#     "[-1, 1, 0, 1, 0, -1]": 3,
#     "[0, -1, -1, -1, -1, -1]": 5,
#     "[0, -1, 1, 0, 1, -1]": 2,
#     "[-1, -1, 0, -1, 0, -1]": 2,
#     "[1, 1, 0, 1, -1, -1]": 1
# }


def terrain_shader(object: bpy.types.Object, indices: list, soindices: list, existing_image: bool = False):
    if indices and soindices:
        material0 = -5
        material1 = -5
        # index 6 is always the same, I don't think it's used for anything
        for index in range(5):
            textureIndex = indices[index]
            soIndex = soindices[index]
            if soIndex == -1:
                continue
            elif material0 == -5 and soIndex == 0 and textureIndex != material1:
                material0 = textureIndex
                continue
            elif material1 == -5 and soIndex == 1 and textureIndex != material0:
                material1 = textureIndex
        print(f'material0: {material0}')
        print(f'material1: {material1}')
        # custom properties
        object["scale"] = .1
        object["material0"] = material0
        if existing_image:
            terrain_and_image_shader(object)
        elif material1 == -5:
            terrain_shader_apply(object, dual=False)
        else:
            object["material1"] = material1
            terrain_shader_apply(object, dual=True)
    else:
        terrain_shader_secondary(object)


def terrain_shader_apply(object: bpy.types.Object, dual: bool = True):
    # Default terrain shader, mixes two terrains textures together by the vertex color and edge detection
    # if there's only 1 uv map add another for the terrain shader
    terrain_material_name = 'BotW_Actor_Terrain_Single'
    if dual:
        terrain_material_name = 'BotW_Actor_Terrain_Dual'
        if len(object.data.uv_layers) == 1:
            object.data.uv_layers.new(name="UVMap1")

    if object.active_material.blend_method == "BLEND":
        # translucent terrain shader
        terrain_material_name += '_translucent'
        # set to smooth shading
        object.data.polygons.foreach_set('use_smooth',  [True] * len(object.data.polygons))

    # rename the uv maps for the shader
    for index, uvmap in enumerate(object.data.uv_layers):
        uvmap.name = f'UVMap{index}'

    actor_terrain_material = append_material(terrain_material_name)
    # replace the material with the actor terrain one
    object.active_material = actor_terrain_material

    geometry_nodes_edge(object)


def append_node_tree(node_group_name):
    node_tree = bpy.data.node_groups.get(node_group_name)
    if not node_tree:
        # link the nodetree from actor_terrain_material.blend
        append_directory = Path(f"linked_resources\\linked.blend").absolute()
        append_directory = f'{str(append_directory)}\\NodeTree\\'
        files = [{'name': node_group_name}]
        bpy.ops.wm.append(directory=append_directory, files=files, link=True, instance_collections=True)
    node_tree = bpy.data.node_groups.get(node_group_name)
    if not node_tree:
        print(f'Warning - node tree {node_group_name} append failed')
    return node_tree


def append_material(mat_name):
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        # import the actor terrain material from mat.blend
        append_directory = Path(f"linked_resources\\linked.blend").absolute()
        append_directory = f'{str(append_directory)}\\Material\\'
        files = [{'name': mat_name}]
        bpy.ops.wm.append(directory=append_directory, files=files, link=True, instance_collections=True)
    mat = bpy.data.materials.get(mat_name)
    return mat


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
    if not object.modifiers.get('Solidify'):
        solidify = object.modifiers.new("Solidify", "SOLIDIFY")
        solidify.offset = 0
        solidify.use_rim = False
        return True
    return False


def geometry_nodes_edge(object):
    object: bpy.types.Object = object
    if not object.modifiers.get('GN Edge'):
        # geometry nodes
        object.data.color_attributes.new('edge', 'FLOAT_COLOR', 'CORNER')
        gn_edge = append_node_tree('GN - Edge')
        gn_modifier = object.modifiers.new("GN Edge", "NODES")
        gn_modifier["Output_3_attribute_name"] = "edge"
        gn_modifier.node_group = gn_edge
        return True
    return False


def terrain_and_image_shader(object: bpy.types.Object):
    # mix terrain and one image shader
    print('\n\n\n')
    print('terrain and image shader')
    # append link the node group
    # link image and normal to the node group
    # link node group to shader
    # nodetree maybe already imported

    # custom props
    object["scale"] = .1

    material_nodes = object.active_material.node_tree.nodes
    material_links = object.active_material.node_tree.links
    shader = get_node_by_label('SharedBSDF', material_nodes)
    base_color = get_node_by_label('Base Color', material_nodes)

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
        material_links.new(actor_terrain_image_node.inputs["Normal Color"], normal_image_node.outputs["Color"])
        material_links.new(shader.inputs["Normal Color"], actor_terrain_image_node.outputs["Normal Color"])
    else:
        print('no normals found')

    # make sure base color displays for viewport
    base_color.select = True
    object.active_material.node_tree.nodes.active = base_color

    material_links.new(actor_terrain_image_node.inputs["Color"], base_color.outputs["Color"])
    material_links.new(shader.inputs["Base Color"], actor_terrain_image_node.outputs["Color"])


def alpha_blend_edges(object, material_nodes, material_links, shader):
    # if we're 'translucent' alpha blend the edges
    if object.active_material.blend_method != "BLEND":
        return False

    # exclude some names this shouldn't apply to
    name_exclude = ['paint', 'house', 'sign']
    obj_name_lower = object.name.lower()
    for name in name_exclude:
        if name in obj_name_lower:
            return False

    geometry_nodes_edge(object)
    if not solidify_modifier(object):
        return False
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


def terrain_shader_secondary(object: bpy.types.Object, image_stem=None):
    print(f'terrain_shader_secondary {image_stem}')
    material_nodes = object.active_material.node_tree.nodes
    material_links = object.active_material.node_tree.links
    shader = get_node_by_label('SharedBSDF', material_nodes)
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
            material_links.new(shader.inputs["Normal Color"], normal_image_node.outputs["Color"])
        else:
            print(f'image load failed for {normal_image_name}')
        alpha_blend_edges(object, material_nodes, material_links, shader)

    else:
        # try sensible default
        sensible_default = sensible_defaults.get(object.active_material.name.lower())
        if sensible_default:
            print('Attempting to use sensible default')
            if apply_mat_info(object, sensible_default):
                return

        # approximate the closest possible terrain texture, for instance some of the objects have similar names or are misspelled
        import difflib
        image_stem = str(image_stem).replace("Criff", "Cliff")
        image_stem = str(image_stem).replace("GrassGreen", "GreenGrass")
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

            with open("missing_shaders.txt", "a") as f:
                lines = [f'{asset_name}\n', f'\t{object.active_material.name}\n']
                f.writelines(lines)
                f.close()

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


def apply_mat_info(object, mat_info):
    print(mat_info)
    o = object
    material_nodes = o.active_material.node_tree.nodes
    material_links = o.active_material.node_tree.links
    shader = get_node_by_label('SharedBSDF', material_nodes)
    base_color = get_node_by_label('Base Color', material_nodes)

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
    soindices: list = mat_info.get('shaderOptionsIndexArray')
    existing_image = False
    if base_color:
        existing_image = True
    if indices and soindices:
        terrain_shader(o, indices, soindices, existing_image)
        alpha_blend_edges(o, material_nodes, material_links, shader)
        return True
    return False


def get_node_by_label(label, material_nodes):
    for nd in material_nodes:
        print(nd.label)
        if nd.label == label:
            return nd
    print(f'node {label} not found')
    return None


def flip_negative_x_uv(object):
    # https://blender.stackexchange.com/questions/144589/how-to-make-object-translations-in-the-uv-editor-scripting-blender-python-api
    object: bpy.types.Object = object
    # me = bpy.context.edit_object.data
    # bm = bmesh.from_edit_mesh(me)
    bm = bmesh.new()
    bm.from_mesh(object.data)

    uv_layer = bm.loops.layers.uv.verify()

    # it's useful to organize your UVs into a dictionary if you're manipulating a lot of stuff all at once,
    # otherwise you're going to be looping through bmface.loops a LOT.
    uv_verts = {}

    for face in bm.faces:
        # print(f"Face #{face.index}")
        for loop in face.loops:
            # print(f"\tv{loop.vert.index}: {loop[uv_layer].uv}")
            if loop.vert not in uv_verts:
                uv_verts[loop.vert] = [loop[uv_layer]]
            else:
                uv_verts[loop.vert].append(loop[uv_layer])

    # now that we have a dictionary of UV verts, it's fairly simple to do transformations on the UVs on a per vertex basis
    # here we take all of the selected UV verts and move them up and to the right by .1
    for vert in uv_verts:
        for uv_loop in uv_verts[vert]:
            uv_loop: bmesh.types.BMLoopUV = uv_loop
            # try to flip these?
            if uv_loop.uv.x < 0:
                uv_loop.uv *= Vector((-1, 1))
                # uv_loop.uv += Vector((10.0, 10.0))
            # if uv_loop.select:
                # uv_loop.uv += Vector((10.0, 10.0))

    # bmesh.update_edit_mesh(me, False, False)
    bm.to_mesh(object.data)
    bm.free()


def fix_shaders(dae_name):
    global asset_name
    asset_name = dae_name
    # This function does its best to fix all the stuff that the collada import missed

    # Vertex color is used as an attribute to mix in a secondary texture
    # try to use Render state - Alpha Control from bfres to set alpha settings in blender
    #   AlphaMask = Alpha Blend??
    print('\n\n\n')
    print('fixing shaders...')
    batch_collection = bpy.data.collections.get('Collection')
    if not batch_collection:
        print('Default collection not found, shaders cannot be fixed')
        return
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

        base_color = get_node_by_label('Base Color', material_nodes)
        if not base_color:
            print('base color not found')

        # if 'flag' not in o.name.lower():
        #     o.active_material.use_backface_culling = True
        o.active_material.blend_method = "HASHED"

        # cel shading custom prop
        o["cel"] = 1

        # use shared shader instead
        existing_shader = material_nodes.get('Principled BSDF')
        if existing_shader:
            material_nodes.remove(existing_shader)
        shader_tree = append_node_tree('SharedBSDF')
        shader = material_nodes.new(type='ShaderNodeGroup')
        shader.node_tree = shader_tree
        shader.name = 'SharedBSDF'
        shader.label = 'SharedBSDF'
        shader.location[1] += 300
        material_output = material_nodes.get('Material Output')
        material_links.new(material_output.inputs["Surface"], shader.outputs["BSDF Eevee"])
        material_output_cycles = material_nodes.new(type='ShaderNodeOutputMaterial')
        material_output_cycles.target = 'CYCLES'
        material_output_cycles.location[0] = material_output.location[0]
        material_output_cycles.location[1] = material_output.location[1] - 150
        material_links.new(material_output_cycles.inputs["Surface"], shader.outputs["BSDF Cycles"])

        specular_node = get_node_by_label('Specular', material_nodes)
        if specular_node:
            material_links.new(shader.inputs["Specular"], specular_node.outputs["Color"])

        emission_image_node = get_node_by_label('Emission', material_nodes)
        if emission_image_node:
            material_links.new(shader.inputs["Emission"], emission_image_node.outputs["Color"])

        if 'metal' in o.name.lower():
            shader.inputs['Metallic'].default_value = 1

        mat_info = None
        if asset_info:
            mat_info = asset_info.get(o.active_material.name)

        if mat_info:
            if apply_mat_info(o, mat_info):
                continue

        # handle water
        if ('water' in o.active_material.name.lower() or 'water' in o.name.lower()) and 'fall' not in o.name.lower():
            water_mat_name = 'BotW_DungeonWater'
            o.active_material = append_material(water_mat_name)
            continue

        # handle lava
        if ('lava' in o.active_material.name.lower() or 'lava' in o.name.lower()) and 'fall' not in o.name.lower():
            lava_mat_name = 'BotW_Lava'
            o.active_material = append_material(lava_mat_name)
            continue

        # handle grudge
        if ('grudge' in o.active_material.name.lower() or 'grudge' in o.name.lower()):
            grudge_mat_name = 'BotW_Grudge'
            o.active_material = append_material(grudge_mat_name)
            continue

        if base_color:
            material_links.new(shader.inputs["Base Color"], base_color.outputs["Color"])
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
                possible_lamp_name_artefacts = ['lamp', 'light']
                is_lamp = False
                for ln in possible_lamp_name_artefacts:
                    is_lamp = is_lamp or ln in dae_name.lower() or ln in o.name.lower()
                if 'glass' in o.name.lower() and not is_lamp:
                    # cycles
                    glass_node_tree = append_node_tree('BotW_Cycles_Glass')
                    glass_node = material_nodes.new(type='ShaderNodeGroup')
                    glass_node.node_tree = glass_node_tree
                    glass_node.location[0] += 300

                    # eevee
                    default_alpha = .2
                    # if 'inside' in o.name.lower() or 'outside' in o.name.lower():
                    #     default_alpha = .25
                    shader.inputs['Alpha'].default_value = default_alpha
                    shader.inputs['Transmission'].default_value = 1
                else:
                    material_links.new(shader.inputs["Alpha"], base_color.outputs["Alpha"])
                # make lamps emissive warmer, add lights
                if 'glass' in o.name.lower() and is_lamp:
                    print('LAMP DETECTED')
                    add_normal = False
                    if emission_image_node:
                        ramp_tree = append_node_tree('warm_emissive_ramp')
                        ramp = material_nodes.new(type='ShaderNodeGroup')
                        ramp.node_tree = ramp_tree
                        ramp.location[0] -= 250
                        emission_image_node.location[0] -= 200
                        material_links.new(ramp.inputs["Fac"], emission_image_node.outputs["Color"])
                        material_links.new(shader.inputs["Emission"], ramp.outputs["Color"])

                        add_emissive_tree = append_node_tree('AddEmissive')
                        add_emissive_node = material_nodes.new(type='ShaderNodeGroup')
                        add_emissive_node.node_tree = add_emissive_tree
                        add_emissive_node.location[0] += 200
                        add_emissive_node.location[1] -= 300
                        material_output.location[0] += 150
                        material_output_cycles.location[0] += 150
                        material_links.new(add_emissive_node.inputs["Shader Eevee"], shader.outputs["BSDF Eevee"])
                        material_links.new(add_emissive_node.inputs["Shader Cycles"], shader.outputs["BSDF Cycles"])
                        material_links.new(add_emissive_node.inputs["Color"], ramp.outputs["Color"])
                        material_links.new(material_output.inputs["Surface"], add_emissive_node.outputs["Shader Eevee"])
                        material_links.new(
                            material_output_cycles.inputs["Surface"],
                            add_emissive_node.outputs["Shader Cycles"])
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
                    lamp_obj = link_lamp('lamp_light')
                elif is_lamp:
                    wide2_lamp_names = [
                        'gerudo_light_a_01',
                        'gerudo_light_a_02',
                        'gerudo_light_a_03',
                    ]

                    wide2 = False
                    for ln in wide2_lamp_names:
                        wide2 = wide2 or ln in o.name.lower() or ln in dae_name.lower()

                    # lamp wide 2
                    if wide2:
                        lamp_obj = link_lamp('lamp_light_wide2')
                    # default
                    else:
                        lamp_obj = link_lamp('lamp_light_wide1')

            # handle NORMAL, might already be imported
            normal_image_name = image_stem+"Nrm.png"
            normal_image = None
            normal_image_node = None
            if add_normal:
                normal_image = bpy.data.images.get(normal_image_name)
            if add_normal and not normal_image and normals.get(image_stem):
                normal_image = bpy.data.images.load(f"{textures_path_abs}\\{normal_image_name}")
            if normal_image:
                normal_image_node = material_nodes.new(type='ShaderNodeTexImage')
                normal_image_node.image = normal_image
                normal_image_node.location[0] -= 600
                normal_image_node.location[1] -= 300
                material_links.new(shader.inputs["Normal Color"], normal_image_node.outputs["Color"])
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
                if not specular_node:
                    material_links.new(shader.inputs["Specular"], trs_image_node.outputs["Color"])
            else:
                print('no trs found')

            if 'waterfall' in o.name.lower() or 'lavafall' in o.name.lower():
                # connect a time node to make the uv move
                botw_time_tree = append_node_tree('BotW_time')
                botw_time = material_nodes.new(type='ShaderNodeGroup')
                botw_time.node_tree = botw_time_tree
                botw_time.location[0] -= 1050
                texcoord_node = material_nodes.new(type='ShaderNodeTexCoord')
                texcoord_node.location[0] -= 850
                texcoord_node.location[1] += 200
                combine_node = material_nodes.new(type='ShaderNodeCombineXYZ')
                combine_node.location[0] -= 850
                combine_node.location[1] -= 200
                mapping_node = material_nodes.new(type='ShaderNodeMapping')
                mapping_node.location[0] -= 650
                material_links.new(combine_node.inputs["Y"], botw_time.outputs["Value"])
                material_links.new(mapping_node.inputs["Vector"], texcoord_node.outputs["UV"])
                material_links.new(mapping_node.inputs["Location"], combine_node.outputs["Vector"])
                material_links.new(base_color.inputs["Vector"], mapping_node.outputs["Vector"])
                if normal_image_node:
                    material_links.new(normal_image_node.inputs["Vector"], mapping_node.outputs["Vector"])

        else:
            print('no base color found, trying terrain shader')
            terrain_shader_secondary(o)

        alpha_blend_edges(o, material_nodes, material_links, shader)
        # extra names to solidify
        solidify_names = ['house_t']
        obj_name_lower = o.name.lower()
        for name in solidify_names:
            if name in obj_name_lower:
                solidify_modifier(o)

        if 'cloth' in o.name.lower() or 'cloth' in o.active_material.name.lower():
            flip_negative_x_uv(o)

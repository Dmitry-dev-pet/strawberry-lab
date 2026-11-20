"""Build an editable artist exterior and render it in Blender Cycles.

blender -b --factory-startup --python-exit-code 1 --python src/build_strawberry_exterior.py -- \
    --out build/exterior-v1 --resolution 900 --samples 28
"""

import argparse
from dataclasses import asdict
import json
from math import cos, pi, sin, tau
from pathlib import Path
from random import Random
import sys
from time import perf_counter

import bpy
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exterior_shape import AZIMUTH_STEPS, MERIDIAN_STEPS, ExteriorParams, ExteriorShape, PitField


def mesh_object(name, vertices, faces, material, collection):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    mesh.polygons.foreach_set("use_smooth", [True] * len(faces))
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    if material:
        mesh.materials.append(material)
    return obj


def ring_faces(steps, sides):
    return [
        (j * sides + i, j * sides + (i + 1) % sides,
         (j + 1) * sides + (i + 1) % sides, (j + 1) * sides + i)
        for j in range(steps) for i in range(sides)
    ]


def attribute(mesh, name, values):
    attr = mesh.attributes.new(name, "FLOAT", "POINT")
    attr.data.foreach_set("value", values)


def material(name, color, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*color, 1.0)
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    return mat, shader


def node(mat, kind, label, location):
    new = mat.node_tree.nodes.new(kind)
    new.label = label
    new.location = location
    return new


def noise(mat, coords, scale, detail, label, location):
    new = node(mat, "ShaderNodeTexNoise", label, location)
    new.inputs["Scale"].default_value = scale
    new.inputs["Detail"].default_value = detail
    mat.node_tree.links.new(coords, new.inputs["Vector"])
    return new.outputs["Fac"]


def ramp(mat, factor, stops, label, location):
    new = node(mat, "ShaderNodeValToRGB", label, location)
    new.color_ramp.interpolation = "EASE"
    for index, (position, color) in enumerate(stops):
        elements = new.color_ramp.elements
        element = elements[index] if index < 2 else elements.new(position)
        element.position = position
        element.color = (*color, 1.0)
    mat.node_tree.links.new(factor, new.inputs["Fac"])
    return new.outputs["Color"]


def mix(mat, factor, first, second, label, location):
    new = node(mat, "ShaderNodeMixRGB", label, location)
    for value, socket in zip((factor, first, second), new.inputs):
        if isinstance(value, bpy.types.NodeSocket):
            mat.node_tree.links.new(value, socket)
        else:
            socket.default_value = value
    return new.outputs[0]


def shader_attribute(mat, name, location):
    new = node(mat, "ShaderNodeAttribute", name, location)
    new.attribute_name = name
    return new.outputs["Fac"]


def bump(mat, shader, height, strength, distance, location):
    new = node(mat, "ShaderNodeBump", "Surface relief in mm", location)
    new.inputs["Strength"].default_value = strength
    new.inputs["Distance"].default_value = distance
    mat.node_tree.links.new(height, new.inputs["Height"])
    mat.node_tree.links.new(new.outputs["Normal"], shader.inputs["Normal"])


def skin_material(height_mm):
    mat, shader = material("Skin • strawberry red", (0.47, 0.015, 0.020), 0.30)
    link = mat.node_tree.links.new
    shader.location = (480, 240)
    mat.node_tree.nodes.get("Material Output").location = (790, 240)
    shader.inputs["Specular IOR Level"].default_value = 0.41
    shader.inputs["Coat Weight"].default_value = 0.13
    shader.inputs["Coat Roughness"].default_value = 0.31
    shader.inputs["Subsurface Weight"].default_value = 0.085
    shader.inputs["Subsurface Radius"].default_value = (1.0, 0.30, 0.16)
    shader.inputs["Subsurface Scale"].default_value = 0.85
    coords = node(mat, "ShaderNodeTexCoord", "Local millimetres", (-1130, 200)).outputs["Object"]
    patches = noise(mat, coords, 0.19, 2.4, "Ripening patches", (-920, 420))
    red = ramp(mat, patches, (
        (0.20, (0.24, 0.0035, 0.008)),
        (0.52, (0.50, 0.009, 0.015)),
        (0.80, (0.68, 0.027, 0.022)),
    ), "Crimson to scarlet", (-700, 440))
    xyz = node(mat, "ShaderNodeSeparateXYZ", "Ripeness toward the shoulder", (-920, 100))
    link(coords, xyz.inputs[0])
    neck = node(mat, "ShaderNodeMapRange", "Warm shoulder fade", (-710, 120))
    neck.interpolation_type = "SMOOTHERSTEP"
    neck.inputs["From Min"].default_value = 0.77 * height_mm
    neck.inputs["From Max"].default_value = 0.99 * height_mm
    neck.inputs["To Max"].default_value = 0.60
    link(xyz.outputs["Z"], neck.inputs["Value"])
    blush = ramp(mat, patches, (
        (0.25, (0.49, 0.047, 0.013)),
        (0.75, (0.75, 0.124, 0.040)),
    ), "Warm shoulder tones", (-700, 710))
    base = mix(mat, neck.outputs["Result"], red, blush, "Fruit colour", (-410, 460))
    pit = shader_attribute(mat, "achene_pit", (-420, 130))
    tint = ramp(mat, pit, (
        (0.12, (0, 0, 0)),
        (1.0, (0.28, 0.28, 0.28)),
    ), "Recess tint weight", (-210, 80))
    color = mix(mat, tint, base, (0.205, 0.008, 0.010, 1.0), "Shaded pit floor", (100, 460))
    link(color, shader.inputs["Base Color"])
    fine = noise(mat, coords, 11.0, 2.0, "Fine cuticle relief", (-720, -280))
    roughness = ramp(mat, fine, (
        (0.21, (0.30, 0.30, 0.30)),
        (0.80, (0.39, 0.39, 0.39)),
    ), "Waxy roughness variation", (-420, -240))
    link(roughness, shader.inputs["Roughness"])
    grain = noise(mat, coords, 2.5, 2.6, "Subtle skin grain", (-720, -630))
    relief = mix(mat, 0.36, fine, grain, "Cuticle and skin grain", (-100, -280))
    bump(mat, shader, relief, 0.31, 0.038, (130, -200))
    return mat


def achene_material():
    mat, shader = material("Achenes • straw · amber · olive", (0.43, 0.22, 0.053), 0.39)
    shader.location = (280, 180)
    mat.node_tree.nodes.get("Material Output").location = (600, 180)
    info = node(mat, "ShaderNodeObjectInfo", "Colour variation by achene", (-820, 300))
    color = ramp(mat, info.outputs["Random"], (
        (0.04, (0.19, 0.093, 0.014)),
        (0.43, (0.43, 0.237, 0.057)),
        (0.73, (0.58, 0.365, 0.114)),
        (0.96, (0.42, 0.375, 0.110)),
    ), "Straw, honey, olive", (-590, 320))
    coords = node(mat, "ShaderNodeTexCoord", "Achene coordinates", (-820, -90)).outputs["Generated"]
    xyz = node(mat, "ShaderNodeSeparateXYZ", "Achene axis", (-610, 65))
    mat.node_tree.links.new(coords, xyz.inputs[0])
    tip = ramp(mat, xyz.outputs["Y"], (
        (0.02, (0.51, 0.51, 0.51)),
        (0.26, (0.0, 0.0, 0.0)),
        (0.86, (0.0, 0.0, 0.0)),
        (1.0, (0.27, 0.27, 0.27)),
    ), "Toasted ends", (-430, 30))
    color = mix(mat, tip, color, (0.11, 0.044, 0.010, 1.0), "Coat colour", (-90, 320))
    mat.node_tree.links.new(color, shader.inputs["Base Color"])
    detail = noise(mat, coords, 18.0, 1.5, "Fine shell grain", (-590, -240))
    bump(mat, shader, detail, 0.18, 0.010, (-130, -180))
    return mat


def foliage_material(name, dark, light, veined=False):
    mat, shader = material(name, light, 0.48)
    shader.location = (320, 200)
    mat.node_tree.nodes.get("Material Output").location = (630, 200)
    shader.inputs["Specular IOR Level"].default_value = 0.33
    shader.inputs["Subsurface Weight"].default_value = 0.13
    shader.inputs["Subsurface Radius"].default_value = (0.55, 1.0, 0.23)
    shader.inputs["Subsurface Scale"].default_value = 0.42
    coords = node(mat, "ShaderNodeTexCoord", "Local millimetres", (-900, 160)).outputs["Object"]
    mottle = noise(mat, coords, 0.84, 2.5, "Foliage mottling", (-670, 230))
    color = ramp(mat, mottle, ((0.15, dark), (0.80, light)), "Leaf colour", (-430, 270))
    if veined:
        vein = shader_attribute(mat, "sepal_vein", (-420, 10))
        color = mix(mat, vein, color, (0.18, 0.29, 0.033, 1.0), "Midrib and secondary veins", (20, 270))
    mat.node_tree.links.new(color, shader.inputs["Base Color"])
    grain = noise(mat, coords, 7.0, 2.1, "Fine foliage grain", (-660, -190))
    bump(mat, shader, grain, 0.21, 0.035, (10, -150))
    return mat


def receptacle(shape, anchors, collection):
    pits = PitField(anchors)
    sides = AZIMUTH_STEPS
    rings = MERIDIAN_STEPS - 1
    vertices, mask = [], []
    for j in range(1, rings + 1):
        for i in range(sides):
            point, weight = pits.deform(shape, pi * j / MERIDIAN_STEPS, tau * i / sides)
            vertices.append(point)
            mask.append(weight)
    top = len(vertices)
    bottom = top + 1
    vertices.extend([shape.point(0.0, 0.0), shape.point(pi, 0.0)])
    mask.extend([0.0, 0.0])
    faces = [tuple(reversed(face)) for face in ring_faces(rings - 1, sides)]
    last = (rings - 1) * sides
    for i in range(sides):
        following = (i + 1) % sides
        faces.extend([(top, i, following), (bottom, last + following, last + i)])
    body = mesh_object("Receptacle | sculpted skin and achene pits", vertices, faces,
                       skin_material(shape.params.height_mm), collection)
    attribute(body.data, "achene_pit", mask)
    body["role"] = "receptacle"
    return body


def achene_prototype(variant, mat):
    rows, sides = 12, 16
    vertices = []
    for j in range(1, rows):
        t = pi * j / rows
        y = cos(t)
        for i in range(sides):
            angle = tau * i / sides
            # An ovoid with a shallow longitudinal crease and a slightly curved profile.
            radius = sin(t) * (1.0 - (0.16 + 0.032 * variant) * y)
            radius *= 1.0 - 0.087 * max(0, cos(angle - 1.22)) ** 19 * sin(t)
            vertices.append((0.5 * radius * cos(angle) + 0.04 * sin(t) ** 2,
                             0.5 * y,
                             0.5 * radius * sin(angle) - 0.052 * y * y))
    top = len(vertices)
    vertices.extend([(0, 0.5, -0.052), (0, -0.5, -0.052)])
    faces = ring_faces(rows - 2, sides)
    last = (rows - 2) * sides
    for i in range(sides):
        following = (i + 1) % sides
        faces.extend([(top, following, i), (top + 1, last + i, last + following)])
    mesh = bpy.data.meshes.new(f"Achene ovoid {variant + 1}")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    mesh.polygons.foreach_set("use_smooth", [True] * len(faces))
    mesh.materials.append(mat)
    return mesh


def emit_achenes(anchors, collection):
    mat = achene_material()
    variants = [achene_prototype(index, mat) for index in range(5)]
    for index, anchor in enumerate(anchors):
        obj = bpy.data.objects.new(f"Achene {index + 1:03}", variants[index % len(variants)])
        collection.objects.link(obj)
        obj.location = anchor.center
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = Matrix((anchor.side_axis, anchor.long_axis, anchor.normal)).transposed().to_quaternion()
        obj.scale = (anchor.width_mm, anchor.length_mm, anchor.thickness_mm)
        obj["role"] = "achene"


def emit_calyx(shape, collection):
    rng = Random(shape.params.seed + 82)
    leaf = foliage_material("Calyx • folded olive green", (0.024, 0.063, 0.007),
                            (0.104, 0.217, 0.027), veined=True)
    stem = foliage_material("Pedicel • green", (0.038, 0.08, 0.010), (0.16, 0.25, 0.031))
    cut, _ = material("Pedicel • cut end", (0.28, 0.33, 0.083), 0.58)
    start = rng.uniform(0, tau)
    for index in range(8):
        angle = start + index * tau / 8 + rng.uniform(-0.14, 0.14)
        bend = rng.uniform(-0.30, 0.30)
        reach = rng.uniform(0.40, 0.67)
        half_width = rng.uniform(1.15, 2.14)
        curl = rng.uniform(-0.45, 2.9)
        lift = rng.uniform(0.22, 0.94)
        twist = rng.uniform(-0.65, 0.65)
        vertices, veins, faces = [], [], []
        rows, strips = 36, 12
        for j in range(rows + 1):
            t = j / rows
            a = angle + bend * t * t
            meridian = 0.045 + reach * t
            x, y, z = shape.point(meridian, a)
            z += 0.58 + lift * sin(pi * t) + curl * t ** 5
            width = (0.39 * (1 - t) + 0.024 + half_width * sin(pi * t) ** 0.82 * (1.20 - 0.49 * t))
            for i in range(strips + 1):
                s = 2 * i / strips - 1
                serration = 1.0 + 0.072 * s ** 6 * sin(pi * t) * sin(23 * t + 0.84 * s)
                side = s * width * serration
                fold = 0.50 * s * s * sin(pi * t)
                wave = 0.30 * s ** 3 * sin(14 * t + index)
                vertices.append((x - sin(a) * side, y + cos(a) * side,
                                 z - fold + wave + twist * s * t))
                midrib = max(0.0, 1.0 - 4.9 * abs(s))
                alternating = 2 * pi * (6.0 * t - 0.86 * abs(s))
                secondary = max(0.0, cos(alternating)) ** 7 * (1.0 - 0.45 * abs(s))
                veins.append((0.35 * midrib + 0.22 * secondary) * sin(pi * t) ** 0.55)
        for j in range(rows):
            for i in range(strips):
                a = j * (strips + 1) + i
                faces.append((a, a + strips + 1, a + strips + 2, a + 1))
        obj = mesh_object(f"Sepal {index + 1}", vertices, faces, leaf, collection)
        obj["role"] = "sepal"
        attribute(obj.data, "sepal_vein", veins)
        solid = obj.modifiers.new("Sepal thickness (0.14 mm)", "SOLIDIFY")
        solid.thickness = 0.14

    x, y, z = shape.point(0.0, 0.0)
    sides, rows = 40, 24
    vertices = []
    for j in range(rows + 1):
        t = j / rows
        # A broad calyx junction tapering into a gently bent stalk.
        radius = 1.61 - 0.68 * (1 - (1 - t) ** 5)
        for i in range(sides):
            a = tau * i / sides
            r = radius * (1 + 0.068 * cos(7 * a + 0.9 * t) + 0.025 * sin(4 * a))
            vertices.append((x + 2.8 * t * t + r * cos(a),
                             y - 0.9 * t + r * sin(a),
                             z - 0.35 + 7.7 * t - 0.32 * t ** 5 * cos(a)))
    faces = ring_faces(rows, sides)
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple(rows * sides + i for i in range(sides)))
    stalk = mesh_object("Pedicel | tapered curved green stalk", vertices, faces, stem, collection)
    stalk["role"] = "pedicel"
    stalk.data.materials.append(cut)
    stalk.data.polygons[-1].material_index = 1
    stalk.data.polygons[-1].use_smooth = False


def create_studio(scene, collection, z_floor):
    mat, shader = material("Stage • warm charcoal", (0.028, 0.022, 0.019), 0.63)
    coords = node(mat, "ShaderNodeTexCoord", "Stage coordinates", (-620, 60)).outputs["Object"]
    grain = noise(mat, coords, 2.5, 1.5, "Fine stage grain", (-410, 60))
    bump(mat, shader, grain, 0.15, 0.045, (-150, -150))
    mesh_object("Matte charcoal sweep", [(-600, -600, z_floor), (600, -600, z_floor),
                (600, 600, z_floor), (-600, 600, z_floor)], [(0, 1, 2, 3)], mat, collection)

    def aimed(name, data, location, target):
        obj = bpy.data.objects.new(name, data)
        collection.objects.link(obj)
        obj.location = location
        obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
        return obj

    for name, xyz, size, power, color in (
        ("Key | large softbox", (-56, -61, 92), 56, 164000, (1.00, 0.89, 0.80)),
        ("Fill | tall softbox", (50, -28, 48), 42, 38000, (0.84, 0.91, 1.00)),
        ("Rim | warm softbox", (-15, 47, 72), 42, 97000, (1.00, 0.83, 0.65)),
    ):
        light = bpy.data.lights.new(name, "AREA")
        light.energy = power
        light.size = size
        light.color = color
        aimed(name, light, xyz, (0, 0, 27))

    camera = bpy.data.cameras.new("Whole fruit | three-quarter")
    camera.type = "ORTHO"
    camera.ortho_scale = 67
    camera.clip_end = 1500
    scene.camera = aimed(camera.name, camera, (61, -118, 63), (-4, -2, 26.6))


def new_collection(scene, name):
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    return collection


def configure_view(scene, body, root):
    root.rotation_euler = Euler((0.06, -0.19, 0.0))
    local_rotation = root.rotation_euler.to_matrix()
    bottom = min((local_rotation @ vert.co).z for vert in body.data.vertices)
    root.location.z = -bottom
    bpy.context.view_layer.objects.active = body
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                space = area.spaces.active
                space.clip_end = 1750
                space.shading.color_type = "MATERIAL"
                space.overlay.show_floor = False
                space.overlay.show_axis_x = False
                space.overlay.show_axis_y = False
                space.overlay.show_extras = False
                space.region_3d.view_rotation = scene.camera.rotation_euler.to_quaternion()
                space.region_3d.view_location = (0.0, 0.0, 27.0)
                space.region_3d.view_distance = 97
                space.region_3d.view_perspective = "ORTHO"


def build(args):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    started = perf_counter()
    scene = bpy.context.scene
    scene.name = "Whole Strawberry | exterior study"
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "MILLIMETERS"
    scene.unit_settings.scale_length = 0.001

    model = new_collection(scene, "Strawberry | editable geometry")
    seed_collection = bpy.data.collections.new("Achenes | linked ovoid meshes")
    model.children.link(seed_collection)
    crown_collection = bpy.data.collections.new("Calyx and pedicel")
    model.children.link(crown_collection)
    studio = new_collection(scene, "Studio | lights and backdrop")
    params = ExteriorParams(seed=args.seed)
    shape = ExteriorShape(params)
    anchors = shape.anchors()
    body = receptacle(shape, anchors, model)
    emit_achenes(anchors, seed_collection)
    emit_calyx(shape, crown_collection)
    root = bpy.data.objects.new("Whole strawberry", None)
    root.empty_display_size = 2
    model.objects.link(root)
    for obj in model.all_objects:
        if obj != root:
            obj.parent = root

    create_studio(scene, studio, z_floor=-0.027)
    configure_view(scene, body, root)
    scene.world = bpy.data.worlds.new("Studio ambience")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.62, 0.71, 1.0, 1.0)
    background.inputs["Strength"].default_value = 0.16
    scene.render.engine = "CYCLES"
    scene.cycles.samples = args.samples
    scene.cycles.seed = args.seed % 2147483647
    scene.cycles.use_denoising = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.resolution_x = scene.render.resolution_y = args.resolution
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "AgX"
    scene.render.filepath = "//strawberry-exterior.png"

    bounds = [max(v.co[axis] for v in body.data.vertices) - min(v.co[axis] for v in body.data.vertices)
              for axis in range(3)]
    evidence = {
        "nominal_size_reference": {
            "source": "Ariza et al. 2011, Table 2, published p. 134",
            "access": "EXCERPT; values from repository morphometry registry",
            "records": ["R0015", "R0016"],
            "taxon": "Fragaria × ananassa",
            "cultivar": "Camarosa",
            "stage": "field harvest, well-formed fruit",
            "length_mm": 48.0,
            "width_mm": 32.5,
        },
        "artist_parameters": "Silhouette, achene geometry and distribution, pit geometry, "
                             "calyx, stem, surface colours and materials.",
        "scope": "Independent exterior study, with no specimen-level calibration of shape or surface details.",
    }
    scene["exterior_params"] = json.dumps(asdict(params))
    scene["evidence"] = json.dumps(evidence, ensure_ascii=False)
    stats = {
        "blender": bpy.app.version_string,
        "renderer": scene.render.engine,
        "resolution_px": args.resolution,
        "samples": args.samples,
        "millimetres_per_blender_unit": 1.0,
        "parameters": asdict(params),
        "evidence": evidence,
        "body_local_bbox_mm": dict(zip(("x", "y", "z"), bounds)),
        "body_vertices": len(body.data.vertices),
        "body_faces": len(body.data.polygons),
        "scene_objects": len(scene.objects),
        "achene_count": len(anchors),
        "sepal_count": sum(obj.get("role") == "sepal" for obj in crown_collection.objects),
        "build_seconds": round(perf_counter() - started, 3),
        "render_seconds": None,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(args.out / "strawberry-exterior.blend"))
    if not args.no_render:
        render_started = perf_counter()
        bpy.ops.render.render(write_still=True)
        stats["render_seconds"] = round(perf_counter() - render_started, 3)
    (args.out / "stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(stats, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("build/exterior-v1"))
    parser.add_argument("--samples", type=int, default=28)
    parser.add_argument("--resolution", type=int, default=900)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--no-render", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    if args.samples < 1 or args.resolution < 4:
        parser.error("Samples must be positive and resolution must be at least 4 px")
    args.out = args.out.resolve()
    build(args)


if __name__ == "__main__":
    main()

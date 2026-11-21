"""Integrate the saved PR29 cut scene and PR13 exterior emitters."""

import argparse
from dataclasses import replace
import json
from math import cos, pi, sin
from pathlib import Path
import sys
from time import perf_counter

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from integration import (ATLAS, BODY, CUT_POSE, CUTTER, DIAGNOSTIC_COUNTS, DIAGNOSTICS,
                         KNIFE, REST, ROOT, SCENE, SCENE_FILE, SOURCE_BODY, SOURCE_SCENE,
                         SOURCE_SHA256, WARNING, check_source, pose_knife, script_args)

sys.path.insert(0, str(ROOT / "src"))
from build_strawberry_exterior import attribute, emit_achenes, emit_calyx, new_collection, skin_material
from exterior_shape import ExteriorParams, ExteriorShape, PitField
from fruit_morphometry import load_catalog
from fruit_platform import make_context


class HullInMillimetres(ExteriorShape):
    """Adapt PR13's meridian/azimuth entry point to the actual PR29 mesh."""

    def __init__(self, mesh, context):
        self.bottom = min(vertex.co.z for vertex in mesh.vertices)
        self.top = max(vertex.co.z for vertex in mesh.vertices)
        self.mm_per_unit = context.specimen.fruit_height.mm / (self.top - self.bottom)
        self.params = ExteriorParams(seed=context.seed, height_mm=context.specimen.fruit_height.mm)
        self.bvh = BVHTree.FromPolygons([vertex.co for vertex in mesh.vertices],
                                        [face.vertices[:] for face in mesh.polygons])
        self.height_origin = Vector((0, 0, self.bottom))

    def to_mm(self, point):
        return (Vector(point) - self.height_origin) * self.mm_per_unit

    def to_model(self, point):
        return Vector(point) / self.mm_per_unit + self.height_origin

    def point(self, meridian, angle):
        if meridian == 0.0 or meridian == pi:
            return (0.0, 0.0, self.params.height_mm if meridian == 0.0 else 0.0)
        z = self.bottom + (self.top - self.bottom) * (1 + cos(meridian)) / 2
        direction = Vector((cos(angle), sin(angle), 0))
        hit, _, _, _ = self.bvh.ray_cast(Vector((0, 0, z)), direction)
        if hit is None:
            raise ValueError(f"PR29 radial surface projection missed at z={z}, angle={angle}")
        return tuple(self.to_mm(hit))


def material_mm_coordinates(mat, hull, rest):
    """Feed PR13 shader frequencies and shoulder thresholds in millimetres."""
    tree = mat.node_tree
    coord = next(node for node in tree.nodes if node.type == "TEX_COORD")
    coord.object = rest
    coord.label = "PR29 rest coordinates"
    links = list(coord.outputs["Object"].links)
    scale = tree.nodes.new("ShaderNodeVectorMath")
    scale.operation = "SCALE"
    scale.label = "Rest units to millimetres"
    scale.location = (coord.location.x, coord.location.y - 250)
    scale.inputs["Scale"].default_value = hull.mm_per_unit
    origin = tree.nodes.new("ShaderNodeVectorMath")
    origin.operation = "ADD"
    origin.label = "Measure height from the tip"
    origin.location = (coord.location.x, coord.location.y - 430)
    origin.inputs[1].default_value = -hull.height_origin * hull.mm_per_unit
    tree.links.new(coord.outputs["Object"], scale.inputs[0])
    tree.links.new(scale.outputs[0], origin.inputs[0])
    for link in links:
        tree.links.new(origin.outputs[0], link.to_socket)

    for node in tree.nodes:
        if node.type == "BUMP":
            node.inputs["Distance"].default_value /= hull.mm_per_unit
        elif node.type == "BSDF_PRINCIPLED":
            node.inputs["Subsurface Scale"].default_value /= hull.mm_per_unit


def update_skin(body, anchors, hull, rest):
    pits = PitField(anchors)
    attribute(body.data, "achene_pit", [pits.sample(tuple(hull.to_mm(v.co)))[1] for v in body.data.vertices])
    skin = skin_material(hull.params.height_mm)
    material_mm_coordinates(skin, hull, rest)
    tree = skin.node_tree
    detail = next(node for node in tree.nodes if node.type == "BUMP")
    pit = next(node for node in tree.nodes if node.type == "ATTRIBUTE")
    recess = tree.nodes.new("ShaderNodeBump")
    recess.label = "Shallow skin relief at achene contacts"
    recess.location = (315, -150)
    recess.invert = True
    recess.inputs["Strength"].default_value = 0.25
    recess.inputs["Distance"].default_value = 0.16 / hull.mm_per_unit
    shader = next(node for node in tree.nodes if node.type == "BSDF_PRINCIPLED")
    tree.links.new(pit.outputs["Fac"], recess.inputs["Height"])
    tree.links.new(detail.outputs["Normal"], recess.inputs["Normal"])
    tree.links.new(recess.outputs["Normal"], shader.inputs["Normal"])
    body.data.materials[0] = skin
    body.data.polygons.foreach_set("use_smooth", [True] * len(body.data.polygons))


def register_atlas_space(flesh, rest):
    """Keep every original atlas and bump lookup in PR29 rest coordinates."""
    tree = flesh.node_tree
    position = next(node for node in tree.nodes if node.type == "NEW_GEOMETRY").outputs["Position"]
    reference = tree.nodes.new("ShaderNodeTexCoord")
    reference.location = (-1660, 150)
    reference.name = "PR29 rest coordinates"
    reference.object = rest
    links = list(position.links)
    assert {link.to_node.type for link in links} == {"SEPXYZ", "TEX_NOISE"}
    for link in links:
        tree.links.new(reference.outputs["Object"], link.to_socket)
    tree.nodes.remove(position.node)


def cut_with(obj, cutter):
    modifier = obj.modifiers.new("Shared knife | solid cut", "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.material_mode = "INDEX"
    modifier.object = cutter
    return modifier


def clip_diagnostic_material(mat, knife):
    mat = mat.copy()
    mat.name += " | shared knife display"
    tree = mat.node_tree
    output = next(node for node in tree.nodes if node.type == "OUTPUT_MATERIAL" and node.is_active_output)
    original = output.inputs["Surface"].links[0].from_socket
    coord = tree.nodes.new("ShaderNodeTexCoord")
    coord.object = knife
    coord.location = (-860, -160)
    separate = tree.nodes.new("ShaderNodeSeparateXYZ")
    separate.location = (-630, -160)
    tree.links.new(coord.outputs["Object"], separate.inputs[0])
    clamp = tree.nodes.new("ShaderNodeMath")
    clamp.operation = "LESS_THAN"
    clamp.inputs[1].default_value = 0
    clamp.location = (-450, -160)
    tree.links.new(separate.outputs["Y"], clamp.inputs[0])
    transparent = tree.nodes.new("ShaderNodeBsdfTransparent")
    transparent.location = (-250, -60)
    mix = tree.nodes.new("ShaderNodeMixShader")
    mix.location = (20, 160)
    tree.links.new(clamp.outputs[0], mix.inputs[0])
    tree.links.new(original, mix.inputs[1])
    tree.links.new(transparent.outputs["BSDF"], mix.inputs[2])
    tree.links.new(mix.outputs[0], output.inputs["Surface"])
    output.location = (235, 160)
    return mat


def configure_studio(scene, camera):
    camera.location = (3.5, -5.9, 2.05)
    target = Vector((0, 0, 0.035))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.ortho_scale = 2.95
    scene.camera = camera
    for obj in scene.objects:
        if obj.type == "LIGHT":
            obj.data.energy *= 0.55
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16
    scene.cycles.seed = 1729
    scene.cycles.use_denoising = True
    scene.cycles.transparent_max_bounces = 192
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 4
    scene.render.resolution_x = scene.render.resolution_y = 650
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = "//cut.png"


def configure_editing(scene, knife, guide):
    bpy.context.view_layer.objects.active = knife
    knife.select_set(True)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "TEXT_EDITOR":
                area.spaces.active.text = guide
            if area.type == "VIEW_3D":
                space = area.spaces.active
                space.shading.color_type = "MATERIAL"
                space.overlay.show_floor = False
                space.overlay.show_axis_x = False
                space.overlay.show_axis_y = False
                space.region_3d.view_perspective = "ORTHO"
                space.region_3d.view_rotation = scene.camera.rotation_euler.to_quaternion()
                space.region_3d.view_location = (0, 0, 0)
                space.region_3d.view_distance = 4.4


def build(source, out):
    started = perf_counter()
    check_source(source)
    out.mkdir(parents=True)
    bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
    old_scenes = list(bpy.data.scenes)
    source_scene = bpy.data.scenes[SOURCE_SCENE]
    scene = bpy.data.scenes.new(SCENE)
    bpy.context.window.scene = scene
    studio = new_collection(scene, "Studio")
    controls = new_collection(scene, "One shared knife")
    fruit = new_collection(scene, "PR29 body")
    seeds = new_collection(scene, "Exterior | 264 editable achenes")
    crown = new_collection(scene, "Exterior | calyx and pedicel")
    diagnostics = new_collection(scene, DIAGNOSTICS)

    knife, cutter = (bpy.data.objects[name] for name in (KNIFE, CUTTER))
    for obj in (knife, cutter):
        controls.objects.link(obj)
    pose_knife(knife, CUT_POSE)
    cutter.hide_set(True)
    assert cutter.hide_render and cutter.parent is knife
    knife["operation"] = "Move along Y or rotate. Whole pose = Y -1.6, rotation (0, 0, 0)."
    knife["plane_equation"] = "Keep local +Y. Boolean solids and optional diagnostic shader clipping."
    knife.lock_scale = (True, True, True)

    body = bpy.data.objects[SOURCE_BODY]
    body.name = BODY
    body["role"] = "receptacle"
    fruit.objects.link(body)
    rest = bpy.data.objects.new(REST, None)
    fruit.objects.link(rest)
    rest.empty_display_size = 0.1
    rest.hide_set(True)
    body.parent = rest
    # The closed inputs qualify for Blender's Manifold solver. It closes
    # the center cut where Exact leaves a seam on near-coplanar hull edges.
    body.modifiers[0].solver = "MANIFOLD"
    knife.parent = rest

    context = make_context(load_catalog(ROOT / "data/morphometry/measurements-v1.json"),
                           "Camarosa", "pr29-live-exterior")
    hull = HullInMillimetres(body.data, context)
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "MILLIMETERS"
    scene.unit_settings.scale_length = hull.mm_per_unit / 1000
    scene["FruitContext"] = context.instance_id
    scene["Reference height"] = f"{context.specimen.fruit_height.mm} mm nominal ({context.specimen.fruit_height.observation_id})"
    scene["Scale"] = f"{hull.mm_per_unit:.8g} mm per native PR29 model unit (uniform, artist height reference)"
    scene["WARNING"] = WARNING
    scene["Source SHA-256"] = SOURCE_SHA256

    anchors = [replace(anchor, pit_depth_mm=0.0) for anchor in hull.anchors()]
    emit_achenes(anchors, seeds)
    for obj, anchor in zip(seeds.objects, anchors, strict=True):
        obj.parent = rest
        obj.location = hull.to_model(anchor.center)
        obj.scale /= hull.mm_per_unit
        obj["hull_anchor_rest"] = tuple(hull.to_model(anchor.point))
        obj["hull_normal_rest"] = anchor.normal
        cut_with(obj, cutter)
    # The dimensionless prototype coordinates for achenes remain untouched.
    seed_material = next(iter(seeds.objects)).data.materials[0]
    for node in seed_material.node_tree.nodes:
        if node.type == "BUMP":
            node.inputs["Distance"].default_value /= hull.mm_per_unit

    emit_calyx(hull, crown)
    to_model = Matrix.Translation(hull.height_origin) @ Matrix.Scale(1.0 / hull.mm_per_unit, 4)
    foliage_materials = set()
    for obj in crown.objects:
        obj.parent = rest
        obj.data.transform(to_model)
        foliage_materials.add(obj.data.materials[0])
        for modifier in obj.modifiers:
            if modifier.type == "SOLIDIFY":
                modifier.thickness /= hull.mm_per_unit
        modifier = cut_with(obj, cutter)
        # Narrow folded tips can self-intersect after solidification.
        modifier.use_self = obj["role"] == "sepal"
    for mat in foliage_materials:
        material_mm_coordinates(mat, hull, rest)

    update_skin(body, anchors, hull, rest)
    cutter.data.materials[0] = body.data.materials[0]
    register_atlas_space(body.data.materials[1], rest)
    assert bpy.data.images[ATLAS].packed_file

    diagnostics["WARNING"] = WARNING
    for name in DIAGNOSTIC_COUNTS:
        obj = bpy.data.objects[name]
        diagnostics.objects.link(obj)
        obj.parent = rest
        obj.hide_render = False
        obj.hide_viewport = False
        obj.visible_shadow = False
        obj["WARNING"] = WARNING
        obj.data.materials[0] = clip_diagnostic_material(obj.data.materials[0], knife)
    bpy.context.view_layer.layer_collection.children[diagnostics.name].exclude = True

    for obj in source_scene.objects:
        if obj.type in {"CAMERA", "LIGHT"}:
            studio.objects.link(obj)
    scene.world = source_scene.world
    for setting in ("view_transform", "look", "gamma", "exposure"):
        setattr(scene.view_settings, setting, getattr(source_scene.view_settings, setting))
    configure_studio(scene, source_scene.camera)

    keep = set(scene.objects)
    for obj in list(bpy.data.objects):
        if obj not in keep:
            bpy.data.objects.remove(obj, do_unlink=True)
    for old_scene in old_scenes:
        bpy.data.scenes.remove(old_scene)
    for old_collection in list(bpy.data.collections):
        if old_collection not in scene.collection.children.values():
            bpy.data.collections.remove(old_collection)
    for old_text in list(bpy.data.texts):
        bpy.data.texts.remove(old_text)
    guide = bpy.data.texts.new("START HERE | Live exterior.txt")
    guide.use_fake_user = True
    guide.write(
        "LIVE EXTERIOR | Strawberry Lab\n\n"
        "Select the Empty in One shared knife and move or rotate it. Local +Y stays.\n"
        "Whole fruit: set Y = -1.6 model units (-35.56 mm), rotation = (0, 0, 0).\n"
        "Example cut: Y = -0.10 model units (-2.22 mm), Z rotation = -23 degrees.\n"
        "One knife cuts the body, achenes, calyx and pedicel as solids.\n"
        "The tissue atlas is packed and sampled in native PR29 rest coordinates.\n"
        "Skin depressions are shading relief on the canonical hull.\n\n"
        "Optional diagnostics: enable the Diagnostics collection in the active View Layer.\n"
        "Use Material Preview or Cycles to see its plane opacity mask.\n"
        f"WARNING: {WARNING}\n"
        "This is an artist-scale integration of the original PR29 tissue and PR13 exterior.\n"
    )
    bpy.data.orphans_purge(do_recursive=True)
    configure_editing(scene, knife, guide)
    bpy.context.view_layer.update()

    path = out / SCENE_FILE
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
    report = {
        "blender": bpy.app.version_string,
        "source_sha256": SOURCE_SHA256,
        "body_vertices": len(body.data.vertices),
        "body_faces": len(body.data.polygons),
        "scene_objects": len(scene.objects),
        "mm_per_model_unit": hull.mm_per_unit,
        "nominal_height_mm": hull.params.height_mm,
        "scene_bytes": path.stat().st_size,
        "elapsed_seconds": round(perf_counter() - started, 3),
    }
    # Object dimensions follow the live modifier; report the full source hull extents.
    report["body_width_xy_mm"] = [
        (max(v.co[axis] for v in body.data.vertices) - min(v.co[axis] for v in body.data.vertices)) * hull.mm_per_unit
        for axis in (0, 1)
    ]
    (out / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path, help="Fresh output directory")
    args = parser.parse_args(script_args())
    build(args.source.resolve(), args.out.resolve())

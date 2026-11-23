"""Render one reproducible Cycles PNG from the saved scene."""

import argparse
import json
from math import degrees
from pathlib import Path
import sys
from time import perf_counter

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_exact_cut import activate_runtime
from integration import BODY, CUT_POSE, DIAGNOSTICS, KNIFE, pose_knife, script_args, sha256

POSES = {"saved": CUT_POSE, "center": (0, 0, 0), "oblique": (0.08, 29, 32)}


def clay_studio(scene, layer, knife):
    layer.layer_collection.children[DIAGNOSTICS].exclude = True
    material = bpy.data.materials.new("Render QA | uniform clay")
    material.use_nodes = True
    bsdf = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.39, 0.36, 0.32, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.74
    layer.material_override = material

    matrix = knife.matrix_world
    camera = scene.camera
    target = matrix @ Vector((0, 0.0, 0.015))
    camera.location = matrix @ Vector((1.15, -6.0, 1.0))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.ortho_scale = 2.60
    lights = [obj for obj in scene.objects if obj.type == "LIGHT"]
    for obj, location, energy, size in zip(lights, ((-3.25, -1.15, 2.6), (1.4, -3.1, .85),
                                                  (0, 2.6, 2.3)),
                                            (495, 38, 145), (.95, 3.0, 2.2), strict=True):
        obj.location = matrix @ Vector(location)
        obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()
        obj.data.energy = energy
        obj.data.size = size
        obj.data.color = (1, 1, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--quality", choices=("fast", "exact"), required=True)
    parser.add_argument("--look", choices=("beauty", "clay"), required=True)
    parser.add_argument("--pose", choices=POSES, default="saved")
    args = parser.parse_args(script_args())
    args.out = args.out.resolve()
    receipt = args.out.with_suffix(".json")
    if args.out.suffix != ".png" or args.out.exists() or receipt.exists():
        raise ValueError("Select a fresh .png output path")
    args.out.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.open_mainfile(filepath=str(args.scene.resolve()), use_scripts=False)
    scene = bpy.context.scene
    layer = bpy.context.window.view_layer = scene.view_layers["MATCHED"]
    knife = scene.objects[KNIFE]
    pose_knife(knife, POSES[args.pose])
    layer.update()
    if args.look == "clay":
        clay_studio(scene, layer, knife)
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16
    scene.cycles.use_adaptive_sampling = False
    scene.render.resolution_x = scene.render.resolution_y = 650
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    layer.update()
    evaluated_knife = knife.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world
    angles = evaluated_knife.to_euler()
    evaluated_pose = [evaluated_knife.translation.y, degrees(angles.x), degrees(angles.z)]
    assert all(abs(a - b) < 1e-4 for a, b in zip(evaluated_pose, POSES[args.pose], strict=True))
    stats = None
    if args.quality == "exact":
        runtime = activate_runtime()
        assert bpy.ops.strawberry.exact_quality(exact=True) == {"FINISHED"}
        session = runtime["session"]
        stats = session.last
        assert stats["cap"] and session.error is None
        mesh = scene.objects[BODY].evaluated_get(bpy.context.evaluated_depsgraph_get()).data
        assert len(mesh.vertices) == stats["vertices"]
    scene.render.filepath = str(args.out)
    started = perf_counter()
    assert bpy.ops.render.render(write_still=True, layer=layer.name) == {"FINISHED"}
    assert args.out.is_file()
    report = {
        "scene_sha256": sha256(args.scene), "png_sha256": sha256(args.out),
        "quality": args.quality, "look": args.look, "pose_y_xrot_zrot": POSES[args.pose],
        "evaluated_pose_y_xrot_zrot": evaluated_pose,
        "view_layer": layer.name, "resolution": [650, 650], "samples": scene.cycles.samples,
        "cycles_seed": scene.cycles.seed, "threads": scene.render.threads,
        "camera_world": [list(row) for row in scene.camera.matrix_world],
        "camera_ortho_scale": scene.camera.data.ortho_scale,
        "lights": {obj.name: {"matrix": [list(row) for row in obj.matrix_world],
                           "energy": obj.data.energy, "color": list(obj.data.color), "size": obj.data.size}
                   for obj in scene.objects if obj.type == "LIGHT"},
        "render_seconds": perf_counter() - started, "exact": stats,
    }
    with receipt.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()

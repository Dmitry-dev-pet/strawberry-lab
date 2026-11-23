"""Render one matched Cycles plate in a fresh Blender process."""
import argparse
from hashlib import file_digest
import json
from pathlib import Path
import resource
import sys
from time import perf_counter

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


def sha(path):
    with path.open("rb") as file:
        return file_digest(file, "sha256").hexdigest()


def aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def matrix(obj):
    return [list(row) for row in obj.matrix_world]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path)
    parser.add_argument("frame", choices=("whole", "macro", "clay"))
    parser.add_argument("png", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    image = args.png.resolve()
    assert not image.exists() and not image.with_suffix(".json").exists()
    source_hash = sha(args.scene)
    bpy.ops.wm.open_mainfile(filepath=str(args.scene.resolve()), use_scripts=False)
    scene = bpy.context.scene
    layer = bpy.context.window.view_layer = scene.view_layers["WHOLE"]
    camera = scene.camera
    camera.data.type = "ORTHO"
    camera.data.dof.use_dof = False
    camera.location = (3.5, -5.9, 2.05)
    camera.data.ortho_scale = 3.05
    target = Vector((0, 0, .06))
    lights = sorted((o for o in scene.objects if o.type == "LIGHT"), key=lambda o: o.name)
    seeds = [o for o in scene.objects if o.get("role") == "achene"]
    seed = None
    if args.frame != "whole":
        seed = min(seeds, key=lambda o: (Vector(o["hull_anchor_rest"]) - Vector((.15, -.77, .22))).length)
        target = Vector(seed["hull_anchor_rest"])
        normal = Vector((target.x, target.y, 0)).normalized()
        tangent = Vector((-normal.y, normal.x, 0))
        camera.location = target + normal * 3 + Vector((0, 0, .22))
        camera.data.ortho_scale = .56
        for obj, offset, energy, size in zip(lights,
                (tangent*2 + normal*.35 + Vector((0, 0, .65)),
                 -tangent*2 + normal*1.8, normal*1.7 + Vector((0, 0, 2))),
                (145, 18, 35), (.45, 2, 1.5), strict=True):
            obj.location = target + offset
            obj.data.energy = energy
            obj.data.size = size
            aim(obj, target)
    aim(camera, target)
    if args.frame == "clay":
        for mat in bpy.data.materials:
            if mat.node_tree:
                for node in mat.node_tree.nodes:
                    if node.type == "BUMP":
                        node.mute = True
        clay = bpy.data.materials.new("Bump-free clay")
        clay.use_nodes = True
        shader = next(n for n in clay.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        shader.inputs["Base Color"].default_value = (.43, .43, .43, 1)
        shader.inputs["Roughness"].default_value = .58
        layer.material_override = clay
        assert not any(n.type == "BUMP" for n in clay.node_tree.nodes)
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 12
    scene.cycles.seed = 1729
    scene.cycles.use_denoising = True
    scene.cycles.use_adaptive_sampling = False
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 4
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.filepath = str(image)
    layer.update()
    visible = []
    if seed:
        toward_camera = (camera.location - target).normalized()
        for obj in seeds:
            anchor = Vector(obj["hull_anchor_rest"])
            coords = world_to_camera_view(scene, camera, anchor)
            if (0 <= coords.x <= 1 and 0 <= coords.y <= 1
                    and toward_camera.dot(Vector(obj["hull_normal_rest"])) > .25):
                visible.append(obj.name)
        assert 6 <= len(visible) <= 15, visible
    started = perf_counter()
    assert bpy.ops.render.render(write_still=True, layer=layer.name) == {"FINISHED"}
    assert sha(args.scene) == source_hash
    report = {"source_sha256": source_hash, "png_sha256": sha(image), "blender": bpy.app.version_string,
              "frame": args.frame, "resolution": [1000, 1000], "view_layer": layer.name,
              "samples": 12, "seed": 1729, "threads": 4, "denoise": True,
              "render_seconds": perf_counter() - started,
              "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "camera_matrix": matrix(camera), "ortho_scale": camera.data.ortho_scale,
              "macro_anchor": seed.name if seed else None, "macro_anchor_centers_in_frame": visible,
              "clay_override_and_all_bumps_muted": args.frame == "clay",
              "lights": {o.name: {"matrix": matrix(o), "energy": o.data.energy, "size": o.data.size}
                         for o in lights}}
    image.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n")
    print(report, flush=True)


if __name__ == "__main__":
    main()

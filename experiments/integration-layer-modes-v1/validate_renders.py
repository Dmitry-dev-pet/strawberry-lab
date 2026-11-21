"""Check real Cycles comparisons and instrument MATCHED to expose its hidden network."""

import argparse
import json
from pathlib import Path
import sys
import subprocess
from tempfile import TemporaryDirectory
from time import perf_counter

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layer_modes import MARKERS, MODES
from integration import CUT_POSE, KNIFE, WHOLE_POSE, pose_knife, script_args, sha256


def read_pixels(path):
    image = bpy.data.images.load(str(path), check_existing=False)
    try:
        width, height = image.size
        pixels = np.empty(width * height * 4, dtype=np.float32)
        image.pixels.foreach_get(pixels)
        return pixels.reshape(height, width, 4)
    finally:
        bpy.data.images.remove(image)


def check_receipts(scene, renders):
    report = json.loads((renders / "render-report.json").read_text())
    assert report["scene_sha256"] == sha256(Path(bpy.data.filepath))
    assert report["renderer"] == scene.render.engine == "CYCLES"
    assert report["camera"] == scene.camera.name
    assert report["lights"] == sorted(obj.name for obj in scene.objects if obj.type == "LIGHT")
    assert report["samples"] == scene.cycles.samples and report["seed"] == scene.cycles.seed
    rows = report["renders"]
    matrices = [rows[mode]["knife_matrix"] for mode in ("matched", "flesh-only", "fibers-only", "matched-repeat")]
    assert all(matrix == matrices[0] for matrix in matrices)
    assert np.allclose(rows["matched"]["knife_y_xrot_zrot"], CUT_POSE)
    assert np.allclose(rows["whole"]["knife_y_xrot_zrot"], WHOLE_POSE)

    pixels = {}
    for name in (*MODES, "matched-repeat"):
        path = renders / f"{name}.png"
        assert rows[name]["sha256"] == sha256(path)
        raw_rgb = subprocess.check_output(["magick", str(path), "-depth", "8", "RGB:-"])
        pixels[name] = np.frombuffer(raw_rgb, dtype=np.uint8).reshape(
            scene.render.resolution_y, scene.render.resolution_x, 3).astype(np.int16)
        assert pixels[name].shape == (scene.render.resolution_y, scene.render.resolution_x, 3)
    assert np.array_equal(pixels["matched"], pixels["matched-repeat"])

    matched, flesh, fibers = (pixels[name] for name in ("matched", "flesh-only", "fibers-only"))
    delta = np.abs(flesh - matched)
    changed = delta.max(axis=2) > 15
    # The fixed studio has a uniform backdrop. Count the diagnostic pixels
    # restored where MATCHED has backdrop and the full network has geometry.
    backdrop = matched[0, 0]
    assert np.allclose([img[0, 0] for img in pixels.values()], backdrop, atol=2)
    in_removed_region = (np.abs(matched - backdrop).max(axis=2) <= 2) & (
        np.abs(fibers - backdrop).max(axis=2) > 15)
    restored = int(np.count_nonzero(changed & in_removed_region))
    assert restored > 500 and changed.mean() > .02
    assert not np.array_equal(pixels["whole"], matched)
    return {
        "matched_repeat_pixels_identical": True,
        "matched_flesh_mean_absolute_rgb_delta_8bit_scale": float(delta.mean()),
        "matched_flesh_fraction_over_15_levels": float(changed.mean()),
        "restored_diagnostic_pixels_over_matched_backdrop": restored,
    }


def diagnostic_probes(scene):
    scene.render.film_transparent = True
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.resolution_percentage = 50
    marker, = bpy.data.collections[MARKERS].objects
    knife = scene.objects[KNIFE]
    layer = scene.view_layers[MODES["matched"]]
    for obj in scene.objects:
        if obj.get("role") in {"receptacle", "achene", "sepal", "pedicel"}:
            for collection in obj.users_collection:
                layer.layer_collection.children[collection.name].exclude = True

    def measure(mode, pose, path):
        bpy.context.window.view_layer = scene.view_layers[MODES[mode]]
        pose_knife(knife, pose)
        bpy.context.view_layer.update()
        scene.render.filepath = str(path)
        started = perf_counter()
        # Exercise the default render operator used by F12 in this saved scene.
        assert bpy.ops.render.render(write_still=True) == {"FINISHED"}
        return read_pixels(path)[:, :, 3], round(perf_counter() - started, 3)

    with TemporaryDirectory(prefix="strawberry-clip-probe-") as temp:
        folder = Path(temp)
        moved_pose = (.08, 29, 32)
        full, full_seconds = measure("fibers-only", CUT_POSE, folder / "full.png")
        cut, cut_seconds = measure("matched", CUT_POSE, folder / "cut.png")
        moved, moved_seconds = measure("matched", moved_pose, folder / "moved.png")
        plane_inverse = knife.matrix_world.inverted()

    full_mask, cut_mask, moved_mask = (alpha > .5 for alpha in (full, cut, moved))
    assert 1000 < np.count_nonzero(cut_mask) < np.count_nonzero(full_mask)
    assert 1000 < np.count_nonzero(moved_mask) < np.count_nonzero(full_mask)
    assert np.count_nonzero(cut_mask ^ moved_mask) > 1000

    # Octahedron centers are the mean of the original six vertices. Require
    # actual full-network pixels around several centers on the removed side
    # of the moved knife that disappear from the isolated MATCHED render.
    height, width = full_mask.shape
    centers_disappeared = 0
    for start in range(0, len(marker.data.vertices), 6):
        center = marker.matrix_world @ (
            sum((marker.data.vertices[i].co for i in range(start, start + 6)), Vector()) / 6)
        if (plane_inverse @ center).y >= -.02:
            continue
        u, v, _ = world_to_camera_view(scene, scene.camera, center)
        x, y = int(u * width), int(v * height)
        if 1 <= x < width - 1 and 1 <= y < height - 1:
            patch = np.s_[y - 1:y + 2, x - 1:x + 2]
            centers_disappeared += bool(full_mask[patch].any() and not moved_mask[patch].any())
    assert centers_disappeared >= 10
    return {
        "full_network_pixels": int(full_mask.sum()),
        "clipped_pixels_at_cut_pose": int(cut_mask.sum()),
        "clipped_pixels_at_moved_pose": int(moved_mask.sum()),
        "pixels_changed_when_knife_moves": int(np.count_nonzero(cut_mask ^ moved_mask)),
        "hidden_negative_side_marker_centers_at_moved_pose": centers_disappeared,
        "probe_render_seconds": [full_seconds, cut_seconds, moved_seconds],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--renders", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(script_args())
    if args.out.exists():
        raise FileExistsError(args.out)
    scene = bpy.context.scene
    report = {
        "status": "PASS",
        "saved_mode_renders": check_receipts(scene, args.renders.resolve()),
        "isolated_diagnostic_probe": diagnostic_probes(scene),
    }
    with args.out.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)

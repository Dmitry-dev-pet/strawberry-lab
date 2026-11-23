"""Render saved modes in one Cycles session, then repeat MATCHED to test switching."""

import argparse
import json
import math
from pathlib import Path
import sys
from time import perf_counter

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layer_modes import MODES
from integration import CUT_POSE, KNIFE, SCENE, pose_knife, script_args, sha256


def render(scene, mode, output):
    layer = scene.view_layers[MODES[mode]]
    bpy.context.window.view_layer = layer
    layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    knife = scene.objects[KNIFE].evaluated_get(depsgraph).matrix_world.copy()
    scene.render.filepath = str(output)
    started = perf_counter()
    result = bpy.ops.render.render(write_still=True, layer=layer.name)
    assert result == {"FINISHED"} and output.is_file()
    return {
        "mode": mode,
        "view_layer": layer.name,
        "knife_matrix": [list(row) for row in knife],
        "knife_y_xrot_zrot": [
            float(knife.translation.y),
            math.degrees(knife.to_euler().x),
            math.degrees(knife.to_euler().z),
        ],
        "seconds": round(perf_counter() - started, 3),
        "sha256": sha256(output),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=(*MODES, "all"), default="all")
    parser.add_argument("--out", type=Path, required=True, help="Fresh render directory")
    args = parser.parse_args(script_args())
    output = args.out.resolve()
    scene_path = Path(bpy.data.filepath)
    scene = bpy.context.scene
    assert scene.name == SCENE and scene.render.engine == "CYCLES"
    output.mkdir(parents=True, exist_ok=False)
    pose_knife(scene.objects[KNIFE], CUT_POSE)
    modes = (args.mode,) if args.mode != "all" else ("matched", "flesh-only", "fibers-only", "whole")
    rows = {mode: render(scene, mode, output / f"{mode}.png") for mode in modes}
    if args.mode == "all":
        rows["matched-repeat"] = render(scene, "matched", output / "matched-repeat.png")
    report = {
        "blender": bpy.app.version_string,
        "scene_sha256": sha256(scene_path),
        "renderer": scene.render.engine,
        "device": scene.cycles.device,
        "samples": scene.cycles.samples,
        "seed": scene.cycles.seed,
        "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        "film_transparent": scene.render.film_transparent,
        "camera": scene.camera.name,
        "lights": sorted(obj.name for obj in scene.objects if obj.type == "LIGHT"),
        "renders": rows,
    }
    (output / "render-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()

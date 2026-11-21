"""Render one saved integration pose in Cycles."""

import argparse
import json
from pathlib import Path
import sys
from time import perf_counter

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from integration import CUT_POSE, KNIFE, SCENE, WHOLE_POSE, pose_knife, script_args, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pose", choices=("whole", "cut"), required=True)
    parser.add_argument("--out", required=True, type=Path, help="Fresh output PNG path")
    args = parser.parse_args(script_args())
    output = args.out.resolve()
    report_path = output.with_suffix(".json")
    if output.suffix.lower() != ".png" or output.exists() or report_path.exists():
        raise ValueError("Choose a fresh PNG output path")

    scene = bpy.data.scenes[SCENE]
    assert scene.render.engine == "CYCLES"
    pose_knife(scene.objects[KNIFE], WHOLE_POSE if args.pose == "whole" else CUT_POSE)
    bpy.context.view_layer.update()
    output.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(output)
    started = perf_counter()
    bpy.ops.render.render(write_still=True, scene=scene.name)
    report = {
        "blender": bpy.app.version_string,
        "scene_sha256": sha256(Path(bpy.data.filepath)),
        "pose": args.pose,
        "renderer": scene.render.engine,
        "device": scene.cycles.device,
        "samples": scene.cycles.samples,
        "seed": scene.cycles.seed,
        "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        "seconds": round(perf_counter() - started, 3),
        "render_sha256": sha256(output),
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()

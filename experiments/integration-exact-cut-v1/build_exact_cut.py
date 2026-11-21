"""Build a scripts-disabled-safe scene from the authenticated PR31 source."""

import argparse
import json
from pathlib import Path
import sys
from time import perf_counter

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "integration-layer-modes-v1"))
from layer_modes import GUIDE_TEXT
from integration import BODY, SCENE, script_args, sha256

PR31_SHA256 = "509725824a8707aade9ca19153c95b4d2de6a2a5b49a827afbb6c0ca11cb4a53"
SCENE_FILE = "strawberry-exact-cut.blend"
TEXT = "EXACT_CUT__RUN.py"
RUNTIME = "strawberry.integration.exact_cut.v1"


def runtime_source():
    return "\n\n".join((HERE / name).read_text(encoding="utf-8")
                       for name in ("cap_geometry.py", "exact_runtime.py"))


def activate_runtime():
    text = bpy.data.texts[TEXT]
    exec(compile(text.as_string(), text.name, "exec"), {"__name__": "__main__"})
    return bpy.app.driver_namespace[RUNTIME]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="Fresh output directory")
    args = parser.parse_args(script_args())
    started = perf_counter()
    source, out = args.source.resolve(), args.out.resolve()
    digest = sha256(source)
    if digest != PR31_SHA256:
        raise ValueError(f"Expected authenticated PR31 SHA-256 {PR31_SHA256}, got {digest}")
    bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
    scene = bpy.context.scene
    assert scene.name == SCENE
    scene["strawberry_exact_height_mm"] = 0.23
    scene.id_properties_ui("strawberry_exact_height_mm").update(
        min=0.0, max=0.6, default=0.23, description="Scale for cap displacement in mm")
    scene["strawberry_exact_strand_influence"] = 0.65
    scene.id_properties_ui("strawberry_exact_strand_influence").update(
        min=0.0, max=1.0, default=0.65, description="Relief influence of the preserved 3D strands")
    text = bpy.data.texts.new(TEXT)
    text.use_fake_user = True
    text.write(runtime_source())
    guide = bpy.data.texts[GUIDE_TEXT]
    guide.write(
        "\nEXACT CUT\n\n"
        "The scene opens with Fast (the native live Boolean). For geometric cap relief,\n"
        "open Scripting, select EXACT_CUT__RUN.py in the Text Editor, and click Run Script.\n"
        "In the 3D View use N > Strawberry Cut > Exact in MATCHED or FLESH ONLY.\n"
        "Move the shared knife, or adjust Relief height and Strand influence in the panel.\n"
        "Exact rebuilds on the CPU. Saving resets the body to Fast and keeps the controls.\n"
        "After reopening, run the Text again to opt in. Disable Exact Runtime removes its panel.\n"
        "The cap uses the original packed atlas sampled at the undeformed positions.\n"
        "The relief controls are artist settings.\n"
    )
    out.mkdir(parents=True, exist_ok=False)
    path = out / SCENE_FILE
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
    report = {
        "blender": bpy.app.version_string, "source_sha256": digest, "scene_sha256": sha256(path),
        "scene_bytes": path.stat().st_size, "objects": len(scene.objects),
        "body_vertices": len(scene.objects[BODY].data.vertices),
        "view_layers": list(scene.view_layers.keys()), "build_seconds": perf_counter() - started,
    }
    (out / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()

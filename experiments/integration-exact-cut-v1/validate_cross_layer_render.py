"""Render an edited cut from WHOLE and compare it with a freshly prepared control."""

import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_exact_cut import activate_runtime
from cap_geometry import REST_ATTRIBUTE
from integration import KNIFE, script_args, sha256


def render(scene_path, destination, target, stale_candidate):
    bpy.ops.wm.open_mainfile(filepath=str(scene_path), use_scripts=False)
    scene = bpy.context.scene
    knife = scene.objects[KNIFE]
    runtime = activate_runtime()
    if stale_candidate:
        assert bpy.ops.strawberry.exact_quality(exact=True) == {"FINISHED"}
        bpy.context.window.view_layer = scene.view_layers["WHOLE"]
        bpy.context.view_layer.update()
    knife.location.y += 0.25
    bpy.context.view_layer.update()
    if not stale_candidate:
        assert bpy.ops.strawberry.exact_quality(exact=True) == {"FINISHED"}
        bpy.context.window.view_layer = scene.view_layers["WHOLE"]
        bpy.context.view_layer.update()
    session = runtime["session"]
    before = session.refresh_count
    scene.render.resolution_percentage = 10
    scene.cycles.samples = 1
    scene.render.filepath = str(destination)
    assert bpy.ops.render.render(write_still=True, layer=target) == {"FINISHED"}
    assert bpy.context.view_layer.name == "WHOLE", "Render changed the selected layer"
    assert session.enabled and session.error is None and session.cache is not None
    if stale_candidate:
        assert session.refresh_count > before, "Render did not rebuild the edited cut"
    mesh = session.cache.data
    indices = {i for face in mesh.polygons if face.material_index == 1 for i in face.vertices}
    knife_inverse = knife.matrix_basis.inverted()
    error = max(abs((knife_inverse @ Vector(mesh.attributes[REST_ATTRIBUTE].data[i].vector)).y)
                for i in indices) * scene.unit_settings.scale_length * 1000
    assert error < 1e-4, f"Stale cap is {error} mm from the knife"
    image = bpy.data.images.load(str(destination), check_existing=False)
    try:
        pixels = tuple(image.pixels[:])
    finally:
        bpy.data.images.remove(image)
    return pixels, {"cap_plane_error_mm": error, "sha256": sha256(destination),
                    "vertices": len(mesh.vertices), "refresh_count": session.refresh_count}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(script_args())
    args.out.mkdir(parents=True, exist_ok=False)
    report = {"status": "PASS", "scene_sha256": sha256(args.scene), "layers": {}}
    for target in ("MATCHED", "FLESH ONLY"):
        name = target.lower().replace(" ", "-")
        a, candidate = render(args.scene, args.out / f"{name}-candidate.png", target, True)
        b, control = render(args.scene, args.out / f"{name}-control.png", target, False)
        assert a == b, f"{target} differs from the refreshed control"
        report["layers"][target] = {"candidate": candidate, "control": control,
                                     "decoded_pixels_identical": True}
    (args.out / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()

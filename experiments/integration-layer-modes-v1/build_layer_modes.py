"""Install four native View Layers into the authenticated PR30 scene."""

import argparse
import json
from math import radians
from pathlib import Path
import sys
from time import perf_counter

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layer_modes import (CLIP_DIAGNOSTICS, GUIDE_TEXT, HERE, MARKERS, MODES,
                         PARK_KNIFE, PR30_SHA256, SCENE_FILE, UI_TEXT)
from integration import (BODY, DIAGNOSTIC_COUNTS, DIAGNOSTICS, KNIFE, SCENE,
                         WARNING, WHOLE_POSE, script_args, sha256)


def drive_parking(constraint):
    constraint.owner_space = "LOCAL"
    constraint.influence = 0
    driver = constraint.driver_add("influence").driver
    driver.type = "AVERAGE"
    variable = driver.variables.new()
    variable.name = "park"
    variable.type = "CONTEXT_PROP"
    target = variable.targets[0]
    target.context_property = "ACTIVE_VIEW_LAYER"
    target.data_path = f'["{PARK_KNIFE}"]'
    target.use_fallback_value = True
    target.fallback_value = 0


def add_knife_parking(knife):
    offset, tilt, turn = WHOLE_POSE
    location = knife.constraints.new("LIMIT_LOCATION")
    location.name = "WHOLE | park knife outside fruit"
    for axis, value in zip("xyz", (0, offset, 0)):
        setattr(location, f"use_min_{axis}", True)
        setattr(location, f"use_max_{axis}", True)
        setattr(location, f"min_{axis}", value)
        setattr(location, f"max_{axis}", value)
    drive_parking(location)
    rotation = knife.constraints.new("LIMIT_ROTATION")
    rotation.name = "WHOLE | square parked knife"
    for axis, value in zip("xyz", (tilt, 0, turn)):
        setattr(rotation, f"use_limit_{axis}", True)
        setattr(rotation, f"min_{axis}", radians(value))
        setattr(rotation, f"max_{axis}", radians(value))
    drive_parking(rotation)


def gate_original_clip(obj):
    tree = obj.data.materials[0].node_tree
    mix, = (node for node in tree.nodes if node.type == "MIX_SHADER")
    original_mask = mix.inputs[0].links[0].from_socket
    attribute = tree.nodes.new("ShaderNodeAttribute")
    attribute.name = "View Layer | diagnostic clipping"
    attribute.attribute_type = "VIEW_LAYER"
    attribute.attribute_name = CLIP_DIAGNOSTICS
    attribute.location = (-450, -410)
    gate = tree.nodes.new("ShaderNodeMath")
    gate.name = "Clip only in MATCHED"
    gate.operation = "MULTIPLY"
    gate.location = (-230, -250)
    tree.links.new(original_mask, gate.inputs[0])
    tree.links.new(attribute.outputs["Fac"], gate.inputs[1])
    tree.links.new(gate.outputs[0], mix.inputs[0])


def configure_layers(scene):
    first, = scene.view_layers
    first.name = MODES["matched"]
    diagnostics = bpy.data.collections[DIAGNOSTICS]
    markers = bpy.data.collections.new(MARKERS)
    diagnostics.children.link(markers)
    marker, = (scene.objects[name] for name in DIAGNOSTIC_COUNTS if scene.objects[name].type == "MESH")
    markers.objects.link(marker)
    diagnostics.objects.unlink(marker)
    # Leave these native flags independent in every View Layer.
    solid_collections = {coll.name for obj in scene.objects
                         if obj.get("role") in {"receptacle", "achene", "sepal", "pedicel"}
                         for coll in obj.users_collection}
    for key, name in MODES.items():
        layer = first if key == "matched" else scene.view_layers.new(name)
        layer[PARK_KNIFE] = float(key == "whole")
        layer[CLIP_DIAGNOSTICS] = float(key == "matched")
        children = layer.layer_collection.children
        for collection in solid_collections:
            children[collection].exclude = key == "fibers-only"
        children[DIAGNOSTICS].exclude = key == "whole"
    bpy.context.window.view_layer = first
    scene.render.use_single_layer = True


def add_guide():
    old_guide = bpy.data.texts["START HERE | Live exterior.txt"]
    old_guide.name = GUIDE_TEXT
    old_guide.clear()
    old_guide.write(
        "STRAWBERRY LAYER MODES\n\n"
        "Use Blender's View Layer selector at the top right. Render the active layer with F12.\n"
        "WHOLE: full fruit, 264 exterior achenes, 8 sepals and pedicel. The evaluated\n"
        "knife parks at Y = -1.6 model units (-35.56 mm) with zero rotation. Its editable\n"
        "transform stores the previous cut pose and takes effect when returning to a cut layer.\n"
        "MATCHED: flesh and exterior Boolean cut, with diagnostics clipped on the same plane.\n"
        "FLESH ONLY: same cut, with the full diagnostic network and markers visible.\n"
        "FIBERS ONLY: full diagnostic network and markers, with all solids hidden.\n\n"
        "In either cut layer select the Empty under One shared knife. Move or rotate it.\n"
        "Its local positive Y side stays. The starting cut is Y = -0.10 (-2.22 mm), Z = -23 degrees.\n"
        "Use Cycles Rendered view or render to evaluate shader clipping. Solid shading shows full curves.\n"
        "The Markers collection checkbox is independent in each diagnostic View Layer.\n"
        "Optional panel: in Scripting, select LAYER_MODES_CONTROLS__RUN.py and Run Script.\n"
        "In the 3D View press N and select Strawberry Layers. Repeat after reopening for the panel.\n\n"
        f"WARNING: {WARNING}\n"
        "The original 28 core splines, 539 branches and 539 octahedral markers keep their source geometry.\n"
        "Clipping is an opacity mask. Exported diagnostic meshes still contain the full paths.\n"
        "The original atlas is packed, and skin pits are shader relief.\n"
        "See the experiment README for reproduction and measured checks.\n"
    )
    ui = bpy.data.texts.new(UI_TEXT)
    ui.use_fake_user = True
    ui.write((HERE / "layer_modes_ui.py").read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="Fresh output directory")
    args = parser.parse_args(script_args())
    started = perf_counter()
    source, out = args.source.resolve(), args.out.resolve()
    digest = sha256(source)
    if digest != PR30_SHA256:
        raise ValueError(f"Expected the corrected PR30 .blend, got SHA-256 {digest} for {source}")
    bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
    scene = bpy.context.scene
    assert scene.name == SCENE
    configure_layers(scene)
    add_knife_parking(scene.objects[KNIFE])
    for name in DIAGNOSTIC_COUNTS:
        gate_original_clip(scene.objects[name])
    add_guide()
    bpy.context.view_layer.update()
    out.mkdir(parents=True, exist_ok=False)
    path = out / SCENE_FILE
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
    report = {
        "blender": bpy.app.version_string,
        "source_sha256": digest,
        "scene_sha256": sha256(path),
        "scene_bytes": path.stat().st_size,
        "objects": len(scene.objects),
        "body_vertices": len(scene.objects[BODY].data.vertices),
        "view_layers": list(scene.view_layers.keys()),
        "build_seconds": round(perf_counter() - started, 3),
    }
    (out / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()

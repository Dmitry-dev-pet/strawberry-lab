"""Independently reopen both sources and the four-mode scene for geometry and UI QA."""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layer_modes import (CLIP_DIAGNOSTICS, GUIDE_TEXT, HERE, MARKERS, MODES,
                         PARK_KNIFE, PR30_SHA256, UI_TEXT)
from integration import (ATLAS, BODY, CUT_POSE, CUTTER, DIAGNOSTIC_COUNTS, DIAGNOSTICS,
                         KNIFE, REST, SCENE, SOURCE_SHA256, WARNING, WHOLE_POSE,
                         check_source, pose_knife, script_args, sha256)
from validate_integration import (EPS, cap_graph_signature, check_pose, diagnostic_digest,
                                  mesh_digest, packed_atlas_digest, source_snapshot)

EXPECTED_ROLES = {"receptacle": 1, "achene": 264, "sepal": 8, "pedicel": 1}
CUT_TESTS = (CUT_POSE, (0.0, 0, 0), (-.26, 0, 0), (.08, 29, 32))


def activate(scene, mode):
    layer = scene.view_layers[MODES[mode]]
    bpy.context.window.view_layer = layer
    layer.update()
    return layer, bpy.context.evaluated_depsgraph_get()


def matrix_tuple(matrix):
    return tuple(tuple(row) for row in matrix)


def knife_pose(knife, depsgraph):
    matrix = knife.evaluated_get(depsgraph).matrix_world
    rotation = matrix.to_euler()
    return (matrix.translation.y, math.degrees(rotation.x), math.degrees(rotation.z))


def near(actual, expected):
    return all(abs(a - b) < EPS for a, b in zip(actual, expected, strict=True))


def pr30_snapshot(scene):
    meshes = {obj.data: mesh_digest(obj.data) for obj in scene.objects if obj.type == "MESH"}
    return {
        "objects": {obj.name: (
            obj.type, obj.parent.name if obj.parent else None, obj.get("role"),
            matrix_tuple(obj.matrix_basis), matrix_tuple(obj.matrix_parent_inverse),
            meshes.get(obj.data), obj.hide_render,
        ) for obj in scene.objects},
        "camera": (scene.camera.name, scene.camera.data.type, scene.camera.data.ortho_scale),
        "lights": {obj.name: (obj.data.type, obj.data.energy, tuple(obj.data.color))
                   for obj in scene.objects if obj.type == "LIGHT"},
        "scale_length": scene.unit_settings.scale_length,
    }


def check_diagnostics(scene, body, knife, reference):
    for name, count in DIAGNOSTIC_COUNTS.items():
        obj = scene.objects[name]
        assert obj["WARNING"] == WARNING and diagnostic_digest(obj, count) == reference["diagnostics"][name]
        matrix = body.matrix_world.inverted() @ obj.matrix_world
        assert all(abs(a - b) < 1e-7 for row, expected in
                   zip(matrix, reference["diagnostic_relative_transforms"][name])
                   for a, b in zip(row, expected)), name
        tree = obj.data.materials[0].node_tree
        mix, = (node for node in tree.nodes if node.type == "MIX_SHADER")
        gate = mix.inputs[0].links[0].from_node
        assert gate.operation == "MULTIPLY"
        mask = gate.inputs[0].links[0].from_node
        assert mask.operation == "LESS_THAN" and mask.inputs[1].default_value == 0
        component = mask.inputs[0].links[0].from_socket
        assert component.name == "Y" and component.node.type == "SEPXYZ"
        coordinates = component.node.inputs[0].links[0].from_socket
        assert coordinates.name == "Object" and coordinates.node.object is knife
        attribute = gate.inputs[1].links[0].from_socket
        assert attribute.identifier == "Fac" and attribute.node.attribute_type == "VIEW_LAYER"
        assert attribute.node.attribute_name == CLIP_DIAGNOSTICS
        assert mix.inputs[2].links[0].from_node.type == "BSDF_TRANSPARENT"
        output, = (node for node in tree.nodes if node.type == "OUTPUT_MATERIAL")
        assert output.inputs["Surface"].links[0].from_node == mix


def check_visibility(scene, solids, knife):
    diagnostics = [scene.objects[name] for name in DIAGNOSTIC_COUNTS]
    visible_views = {}
    edited_pose = (-.26, 15, 32)
    pose_knife(knife, edited_pose)
    for mode in ("matched", "whole", "flesh-only", "fibers-only", "whole", "matched"):
        layer, depsgraph = activate(scene, mode)
        assert layer[PARK_KNIFE] == float(mode == "whole")
        assert layer[CLIP_DIAGNOSTICS] == float(mode == "matched")
        assert all(obj.visible_get() == (mode != "fibers-only") for obj in solids)
        assert all(obj.visible_get() == (mode != "whole") for obj in diagnostics)
        assert scene.camera.visible_get() and all(obj.visible_get() for obj in scene.objects if obj.type == "LIGHT")
        assert near(knife_pose(knife, depsgraph), WHOLE_POSE if mode == "whole" else edited_pose), mode
        assert near((knife.location.y, math.degrees(knife.rotation_euler.x),
                     math.degrees(knife.rotation_euler.z)), edited_pose)
        # Test actual geometry with the edited, tilted pose still in the knife fields.
        body = solids[0]
        if mode == "whole":
            assert len(body.evaluated_get(depsgraph).data.polygons) == len(body.data.polygons)
        visible_views[mode] = {
            "visible_solid_objects": sum(obj.visible_get() for obj in solids),
            "visible_diagnostic_objects": sum(obj.visible_get() for obj in diagnostics),
            "effective_knife_pose": knife_pose(knife, depsgraph),
        }

    pose_knife(knife, CUT_POSE)
    actual_meshes = {}
    for mode in ("matched", "flesh-only"):
        _, depsgraph = activate(scene, mode)
        assert near(knife_pose(knife, depsgraph), CUT_POSE)
        # Memoize shared evaluated mesh data while retaining a per-object comparison.
        meshes = [obj.evaluated_get(depsgraph).data for obj in solids]
        digests = {mesh: mesh_digest(mesh) for mesh in set(meshes)}
        actual_meshes[mode] = [digests[mesh] for mesh in meshes]
    assert actual_meshes["matched"] == actual_meshes["flesh-only"]
    return visible_views


def check_embedded_ui(scene, knife):
    ui = bpy.data.texts[UI_TEXT]
    assert not ui.use_module and ui.as_string() == (HERE / "layer_modes_ui.py").read_text()
    assert not hasattr(bpy.types, "STRAWBERRY_PT_layer_modes")
    for _ in range(2):
        exec(compile(ui.as_string(), ui.name, "exec"), {"__name__": "__main__"})
    assert hasattr(bpy.types, "STRAWBERRY_PT_layer_modes")
    pose_knife(knife, (.08, 29, 32))
    for mode in ("whole", "matched", "flesh-only", "fibers-only", "matched"):
        assert bpy.ops.strawberry.select_layer(layer=MODES[mode]) == {"FINISHED"}
        layer = bpy.context.view_layer
        assert layer.name == MODES[mode]
        pose = WHOLE_POSE if mode == "whole" else (.08, 29, 32)
        assert near(knife_pose(knife, bpy.context.evaluated_depsgraph_get()), pose)

    marker, = bpy.data.collections[MARKERS].objects
    collection = bpy.context.view_layer.layer_collection.children[DIAGNOSTICS].children[MARKERS]
    collection.exclude = True
    bpy.context.view_layer.update()
    assert not marker.visible_get()
    bpy.ops.strawberry.select_layer(layer=MODES["flesh-only"])
    assert marker.visible_get()
    bpy.ops.strawberry.select_layer(layer=MODES["matched"])
    assert not marker.visible_get()
    collection.exclude = False
    bpy.context.view_layer.update()
    assert marker.visible_get()


def validate(pr29, pr30, scene_path):
    check_source(pr29)
    assert sha256(pr30) == PR30_SHA256
    bpy.ops.wm.open_mainfile(filepath=str(pr29), use_scripts=False)
    source = source_snapshot()
    bpy.ops.wm.open_mainfile(filepath=str(pr30), use_scripts=False)
    original = pr30_snapshot(bpy.context.scene)
    bpy.ops.wm.open_mainfile(filepath=str(scene_path), use_scripts=False)
    scene = bpy.context.scene
    assert len(bpy.data.scenes) == 1 and scene.name == SCENE
    assert set(scene.view_layers.keys()) == set(MODES.values())
    assert all(layer.use for layer in scene.view_layers) and scene.render.use_single_layer
    assert bpy.context.view_layer.name == MODES["matched"]
    assert WARNING in bpy.data.texts[GUIDE_TEXT].as_string()
    assert pr30_snapshot(scene) == original
    assert set(bpy.data.objects.keys()) == set(original["objects"])
    body, knife, cutter, rest = (scene.objects[name] for name in (BODY, KNIFE, CUTTER, REST))
    assert knife.parent is rest and cutter.parent is knife and cutter.hide_render
    assert mesh_digest(body.data) == source["hull"] and mesh_digest(cutter.data) == source["cutter"]
    assert packed_atlas_digest() == source["atlas"]
    height = max(v.co.z for v in body.data.vertices) - min(v.co.z for v in body.data.vertices)
    assert abs(height * scene.unit_settings.scale_length * 1000 - 48) < EPS
    assert cutter.data.materials[1] is body.data.materials[1]
    tree = body.data.materials[1].node_tree
    assert cap_graph_signature(tree) == source["cap_graph"]
    assert tree.nodes["PR29 rest coordinates"].object is rest
    samples = [node for node in tree.nodes if node.type == "TEX_IMAGE"]
    assert len(samples) == 2 and all(node.image is bpy.data.images[ATLAS] for node in samples)

    exterior = [obj for obj in scene.objects if obj.get("role") in {"achene", "sepal", "pedicel"}]
    solids = [body, *exterior]
    assert Counter(obj["role"] for obj in solids) == EXPECTED_ROLES
    assert [obj for obj in bpy.data.objects if obj.data is body.data] == [body]
    for obj in solids:
        assert obj.parent is rest and not obj.hide_render
        modifier, = (item for item in obj.modifiers if item.type == "BOOLEAN")
        assert modifier.object is cutter and modifier.operation == "DIFFERENCE"
        assert modifier.solver == ("EXACT" if obj["role"] == "achene" else "MANIFOLD")
        assert modifier.material_mode == "INDEX" and modifier.show_viewport and modifier.show_render

    check_diagnostics(scene, body, knife, source)
    visibility = check_visibility(scene, solids, knife)
    activate(scene, "whole")
    whole = check_pose(rest, knife, body, exterior, WHOLE_POSE, whole=True)
    assert whole["retained_exterior_by_role"] == {"achene": 264, "sepal": 8, "pedicel": 1}
    activate(scene, "matched")
    cuts = [check_pose(rest, knife, body, exterior, pose) for pose in CUT_TESTS]
    assert len({row["body_faces"] for row in cuts}) == 4
    assert all(row["body_volume_model_units_cubed"] < whole["body_volume_model_units_cubed"] for row in cuts)
    assert all(any(row["intersected_exterior_by_role"].get(role) for row in cuts)
               for role in ("achene", "sepal", "pedicel"))
    check_diagnostics(scene, body, knife, source)
    check_embedded_ui(scene, knife)
    return {
        "status": "PASS",
        "blender": bpy.app.version_string,
        "scene_sha256": sha256(scene_path),
        "pr29_sha256": SOURCE_SHA256,
        "pr30_sha256": PR30_SHA256,
        "source_diagnostics_sha256": source["diagnostics"],
        "packed_atlas_sha256": source["atlas"],
        "cap_graph_unchanged": True,
        "solid_objects": EXPECTED_ROLES,
        "diagnostics": DIAGNOSTIC_COUNTS,
        "native_view_layers_without_scripts": visibility,
        "matched_and_flesh_only_evaluated_meshes_identical": True,
        "embedded_ui_run_twice_and_switch_callbacks_pass": True,
        "marker_checkbox_independent": True,
        "whole": whole,
        "cut_poses": cuts,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr29", type=Path, required=True)
    parser.add_argument("--pr30", type=Path, required=True)
    parser.add_argument("--scene", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(script_args())
    if args.out.exists():
        raise FileExistsError(args.out)
    report = json.dumps(validate(args.pr29.resolve(), args.pr30.resolve(), args.scene.resolve()), indent=2)
    with args.out.open("x", encoding="utf-8") as stream:
        stream.write(report + "\n")
    print(report, flush=True)

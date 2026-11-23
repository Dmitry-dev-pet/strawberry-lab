"""Validate the saved native fallback and the geometry emitted by the opt-in runtime."""

import argparse
from collections import Counter
import json
from math import radians, sqrt
from pathlib import Path
import resource
import sys
from time import perf_counter

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_exact_cut import PR31_SHA256, RUNTIME, TEXT, activate_runtime, runtime_source
from cap_geometry import REST_ATTRIBUTE
from exact_runtime import HEIGHT_CONTROL, INFLUENCE_CONTROL, TAG
from integration import (BODY, CUT_POSE, DIAGNOSTIC_COUNTS, KNIFE, WHOLE_POSE, pose_knife,
                         script_args, sha256)
from validate_integration import diagnostic_digest, mesh_digest, packed_atlas_digest
from validate_layer_modes import CUT_TESTS, activate, pr30_snapshot, validate

EPS = 1e-4


def body_mesh(body):
    return body.evaluated_get(bpy.context.evaluated_depsgraph_get()).data


def surface(mesh):
    coords = [tuple(v.co) for v in mesh.vertices]
    outer = [face for face in mesh.polygons if face.material_index != 1]
    skin = Counter()
    cap_edges, skin_edges = set(), set()
    for face in mesh.polygons:
        vertices = tuple(coords[i] for i in face.vertices)
        if face.material_index != 1:
            start = vertices.index(min(vertices))
            skin[(face.material_index, face.use_smooth, vertices[start:] + vertices[:start])] += 1
        edges = cap_edges if face.material_index == 1 else skin_edges
        edges.update(tuple(sorted(e)) for e in zip(vertices, vertices[1:] + vertices[:1], strict=True))
    pit = mesh.attributes["achene_pit"]
    skin_pits = {coords[i]: pit.data[i].value for face in outer for i in face.vertices}
    return skin, cap_edges & skin_edges, skin_pits


def topology(mesh):
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        assert all(edge.is_manifold and edge.is_contiguous for edge in bm.edges)
        assert all(v.link_faces for v in bm.verts)
        first = next(iter(bm.verts))
        seen, stack = {first}, [first]
        while stack:
            for edge in stack.pop().link_edges:
                for vertex in edge.verts:
                    if vertex not in seen:
                        seen.add(vertex)
                        stack.append(vertex)
        assert len(seen) == len(bm.verts), "Extra connected component"
        volume = bm.calc_volume(signed=True)
        assert volume > 0
        return volume
    finally:
        bm.free()


def measure(scene, body, mesh):
    volume = topology(mesh)
    cap = [face for face in mesh.polygons if face.material_index == 1]
    points = {i for face in cap for i in face.vertices}
    assert cap and points
    rest_attribute = mesh.attributes[REST_ATTRIBUTE]
    assert rest_attribute.domain == "POINT" and rest_attribute.data_type == "FLOAT_VECTOR"
    graph = bpy.context.evaluated_depsgraph_get()
    knife = scene.objects[KNIFE].evaluated_get(graph)
    model = body.evaluated_get(graph).matrix_world
    plane = knife.matrix_world.inverted()
    model_to_knife = plane @ model
    rest_to_knife = plane @ scene.objects[body.parent.name].matrix_world
    mm = scene.unit_settings.scale_length * 1000
    offsets, errors, tangents, profile = [], [], [], {}
    for index in points:
        pos = model_to_knife @ mesh.vertices[index].co
        rest = Vector(rest_attribute.data[index].vector)
        flat = rest_to_knife @ rest
        displacement = flat.y - pos.y
        profile[tuple(rest)] = displacement * mm
        offsets.append(displacement * mm)
        errors.append(abs(flat.y))
        tangents.append(sqrt((pos.x - flat.x)**2 + (pos.z - flat.z)**2))
    assert min(offsets) > -EPS and max(errors) < EPS and max(tangents) < EPS
    mesh.calc_loop_triangles()
    return {
        "vertices": len(mesh.vertices), "triangles": len(mesh.loop_triangles),
        "cap_faces": len(cap), "nonmanifold_edges": 0, "connected_components": 1,
        "volume_model_units_cubed": volume, "min_displacement_mm": min(offsets),
        "max_displacement_mm": max(offsets), "mean_displacement_mm": sum(offsets) / len(offsets),
        "displaced_cap_vertices_over_0_01_mm": sum(value > 0.01 for value in offsets),
        "max_undeformed_plane_error_model_units": max(errors),
        "max_tangential_drift_model_units": max(tangents),
    }, profile


def flush_callback(runtime):
    timer = runtime["timer"]
    # Background runs don't pump Blender's UI event loop. Consume its queued callback.
    assert bpy.app.timers.is_registered(timer), "A real depsgraph edit did not schedule the refresh"
    bpy.app.timers.unregister(timer)
    assert timer() is None
    assert not bpy.app.timers.is_registered(timer)
    assert runtime["session"].error is None, runtime["session"].error


def assert_fast(body, expected=None):
    bpy.context.view_layer.update()
    assert all(mod.type != "NODES" for mod in body.modifiers)
    assert body.animation_data is None
    assert not any(item.get(TAG) for ids in
                   (bpy.data.objects, bpy.data.node_groups, bpy.data.meshes, bpy.data.materials)
                   for item in ids)
    mesh = body_mesh(body)
    assert REST_ATTRIBUTE not in mesh.attributes
    if expected is not None:
        assert mesh_digest(mesh) == expected


def compare_pose(scene, body, baseline, runtime):
    flush_callback(runtime)
    mesh = body_mesh(body)
    exact, _ = measure(scene, body, mesh)
    fast_vertices, fast_triangles, fast_surface, _, fast_seconds = baseline
    assert exact["vertices"] > fast_vertices and exact["triangles"] > fast_triangles
    assert exact["max_displacement_mm"] > 0.05
    assert exact["displaced_cap_vertices_over_0_01_mm"] > 100
    assert surface(mesh) == fast_surface, "Skin faces, pit values, or seam edges changed"
    return dict(exact, fast_vertices=fast_vertices, fast_triangles=fast_triangles, fast_update_seconds=fast_seconds,
                exact_refresh_seconds=runtime["session"].last["refresh_seconds"])


def run(args):
    assert sha256(args.pr31) == PR31_SHA256
    bpy.ops.wm.open_mainfile(filepath=str(args.pr31), use_scripts=False)
    pr31 = pr30_snapshot(bpy.context.scene)
    pr31_atlas = packed_atlas_digest()
    upstream = validate(args.pr29, args.pr30, args.scene)

    bpy.ops.wm.open_mainfile(filepath=str(args.scene), use_scripts=False)
    scene = bpy.context.scene
    assert pr30_snapshot(scene) == pr31 and packed_atlas_digest() == pr31_atlas
    assert not hasattr(bpy.types, "STRAWBERRY_PT_exact_cut")
    text = bpy.data.texts[TEXT]
    assert not text.use_module and text.as_string() == runtime_source()
    body, knife = scene.objects[BODY], scene.objects[KNIFE]
    raw = mesh_digest(body.data)
    assert_fast(body)
    baseline = {}
    pose_knife(knife, WHOLE_POSE)
    bpy.context.view_layer.update()
    for pose in CUT_TESTS:
        started = perf_counter()
        pose_knife(knife, pose)
        bpy.context.view_layer.update()
        mesh = body_mesh(body)
        seconds = perf_counter() - started
        mesh.calc_loop_triangles()
        baseline[pose] = len(mesh.vertices), len(mesh.loop_triangles), surface(mesh), mesh_digest(mesh), seconds
        assert topology(mesh) > 0
        assert seconds > 0
    pose_knife(knife, CUT_POSE)
    bpy.context.view_layer.update()
    first = activate_runtime()
    runtime = activate_runtime()
    handlers = bpy.app.handlers.depsgraph_update_post
    assert first["handler"] not in handlers and handlers.count(runtime["handler"]) == 1
    assert bpy.types.STRAWBERRY_PT_exact_cut.is_registered
    session = runtime["session"]
    assert bpy.ops.strawberry.exact_quality(exact=True) == {"FINISHED"}, session.error
    exact, _ = measure(scene, body, body_mesh(body))
    assert surface(body_mesh(body)) == baseline[CUT_POSE][2]
    assert exact["max_displacement_mm"] > 0.05
    assert exact["vertices"] > baseline[CUT_POSE][0] and exact["triangles"] > baseline[CUT_POSE][1]
    cuts = [dict(exact, pose_y_xrot_zrot=CUT_POSE, fast_vertices=baseline[CUT_POSE][0],
                 fast_triangles=baseline[CUT_POSE][1], fast_update_seconds=baseline[CUT_POSE][4],
                 exact_refresh_seconds=session.last["refresh_seconds"])]

    # Exercise translation and rotation separately through the registered post-update callback.
    knife.location.y = 0.0
    bpy.context.view_layer.update()
    flush_callback(runtime)
    translated = mesh_digest(body_mesh(body))
    knife.rotation_euler.z = 0.0
    bpy.context.view_layer.update()
    center = CUT_TESTS[1]
    cuts.append(dict(compare_pose(scene, body, baseline[center], runtime), pose_y_xrot_zrot=center))
    assert mesh_digest(body_mesh(body)) != translated
    for pose in CUT_TESTS[2:]:
        pose_knife(knife, pose)
        bpy.context.view_layer.update()
        cuts.append(dict(compare_pose(scene, body, baseline[pose], runtime), pose_y_xrot_zrot=pose))

    before_idle = session.refresh_count
    current_digest = mesh_digest(body_mesh(body))
    for mode in ("whole", "fibers-only", "flesh-only", "matched"):
        layer, graph = activate(scene, mode)
        assert not session.cache.visible_get(view_layer=layer) and session.cache.hide_render
        assert body.visible_get() == (mode != "fibers-only")
        for name in DIAGNOSTIC_COUNTS:
            assert scene.objects[name].visible_get() == (mode != "whole")
        if mode == "whole":
            assert abs(knife.evaluated_get(graph).matrix_world.translation.y + 1.6) < EPS
            assert surface(body_mesh(body))[1] == set()
            assert len(body_mesh(body).vertices) == len(body.data.vertices)
        elif mode in ("flesh-only", "matched"):
            assert mesh_digest(body_mesh(body)) == current_digest
            assert abs(knife.evaluated_get(graph).matrix_world.translation.y - 0.08) < EPS
        assert not bpy.app.timers.is_registered(runtime["timer"])
    assert session.refresh() is None and session.refresh_count == before_idle

    layer, graph = activate(scene, "whole")
    knife.location.y += 0.035
    layer.update()
    assert abs(knife.evaluated_get(graph).matrix_world.translation.y + 1.6) < EPS
    assert not bpy.app.timers.is_registered(runtime["timer"])
    activate(scene, "matched")
    flush_callback(runtime)
    assert mesh_digest(body_mesh(body)) != current_digest
    pose_knife(knife, CUT_TESTS[-1])
    bpy.context.view_layer.update()
    flush_callback(runtime)
    assert mesh_digest(body_mesh(body)) == current_digest

    _, profile = measure(scene, body, body_mesh(body))
    influence = getattr(scene, INFLUENCE_CONTROL)
    setattr(scene, INFLUENCE_CONTROL, 0.0)
    flush_callback(runtime)
    no_strands, quiet_profile = measure(scene, body, body_mesh(body))
    assert profile.keys() == quiet_profile.keys()
    differences = [profile[key] - quiet_profile[key] for key in profile]
    assert min(differences) > -0.00001 and max(differences) > 0.015
    assert no_strands["max_displacement_mm"] > 0.05
    setattr(scene, INFLUENCE_CONTROL, influence)
    height = getattr(scene, HEIGHT_CONTROL)
    setattr(scene, HEIGHT_CONTROL, 0.0)
    flush_callback(runtime)
    zero, _ = measure(scene, body, body_mesh(body))
    assert zero["max_displacement_mm"] < 1e-5
    setattr(scene, HEIGHT_CONTROL, height)
    flush_callback(runtime)

    knife.location.y = -1.6
    knife.rotation_euler.x = knife.rotation_euler.z = 0
    bpy.context.view_layer.update()
    flush_callback(runtime)
    assert session.enabled and not session.last["cap"]
    assert_fast(body)
    pose_knife(knife, CUT_TESTS[-1])
    bpy.context.view_layer.update()
    flush_callback(runtime)
    assert session.cache

    assert bpy.ops.strawberry.exact_quality(exact=False) == {"FINISHED"}
    assert_fast(body, baseline[CUT_TESTS[-1]][3])
    assert bpy.ops.strawberry.exact_quality(exact=True) == {"FINISHED"}
    namespace = session.refresh.__func__.__globals__

    def broken_mesh(*_args):
        raise ValueError("QA injected reconstruction failure")

    original = namespace["make_mesh"]
    namespace["make_mesh"] = broken_mesh
    try:
        pose_knife(knife, CUT_POSE)
        bpy.context.view_layer.update()
        timer = runtime["timer"]
        assert bpy.app.timers.is_registered(timer)
        bpy.app.timers.unregister(timer)
        timer()
    finally:
        namespace["make_mesh"] = original
    assert not session.enabled and session.error == "QA injected reconstruction failure"
    assert_fast(body, baseline[CUT_POSE][3])
    assert mesh_digest(body.data) == raw
    assert packed_atlas_digest() == pr31_atlas
    for name, count in DIAGNOSTIC_COUNTS.items():
        assert diagnostic_digest(scene.objects[name], count) == upstream["source_diagnostics_sha256"][name]
    assert pr30_snapshot(scene) == pr31

    assert bpy.ops.strawberry.exact_unload() == {"FINISHED"}
    assert bpy.app.timers.is_registered(runtime["unregister"])
    bpy.app.timers.unregister(runtime["unregister"])
    runtime["unregister"]()
    assert not hasattr(bpy.types, "STRAWBERRY_PT_exact_cut") and runtime["handler"] not in handlers
    runtime = activate_runtime()
    assert bpy.ops.strawberry.exact_quality(exact=True) == {"FINISHED"}
    bpy.ops.wm.save_as_mainfile(filepath=str(args.out.parent / "qa-saved-from-exact.blend"), compress=True)
    assert_fast(body, baseline[CUT_POSE][3])
    assert bpy.ops.strawberry.exact_quality(exact=True) == {"FINISHED"}
    bpy.ops.wm.open_mainfile(filepath=str(args.out.parent / "qa-saved-from-exact.blend"), use_scripts=False)
    assert RUNTIME not in bpy.app.driver_namespace and not hasattr(bpy.types, "STRAWBERRY_PT_exact_cut")
    assert_fast(bpy.context.scene.objects[BODY], baseline[CUT_POSE][3])

    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "status": "PASS", "pr31_sha256": PR31_SHA256, "native_fast": upstream,
        "exact_cuts": cuts, "strand_test": {"maximum_added_height_mm": max(differences),
                                           "vertices_affected_over_0_001_mm": sum(d > 0.001 for d in differences)},
        "zero_height_max_displacement_mm": zero["max_displacement_mm"],
        "view_layer_switch_has_no_idle_rebuild": True, "load_and_save_cleanup": True,
        "source_snapshots_unchanged": True, "failure_restores_live_fast": True,
        "peak_validator_rss_bytes": peak_rss if sys.platform == "darwin" else peak_rss * 1024,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("pr29", "pr30", "pr31", "scene", "out"):
        parser.add_argument("--" + key, type=lambda path: Path(path).resolve(), required=True)
    args = parser.parse_args(script_args())
    if args.out.exists() or (args.out.parent / "qa-saved-from-exact.blend").exists():
        raise FileExistsError("Use a fresh validation destination")
    report = json.dumps(run(args), indent=2)
    with args.out.open("x", encoding="utf-8") as stream:
        stream.write(report + "\n")
    print(report, flush=True)

"""Reopen and exercise the saved tissue scene and its canonical PR32 baseline."""

import argparse
from hashlib import sha256
import json
from math import dist, sqrt
from pathlib import Path
import resource
import sys
from time import perf_counter

import bpy
from mathutils import Vector
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_tissue_zones import (CONTROLS, PR32_SHA256, RUNTIME, TEXT, activate_runtime, runtime_source)
from build_exact_cut import PR31_SHA256, activate_runtime as activate_pr32
from integration import BODY, CUT_POSE, DIAGNOSTIC_COUNTS, KNIFE, REST, pose_knife, script_args
from validate_exact_cut import assert_fast, body_mesh, flush_callback, measure, surface, topology
from validate_integration import diagnostic_digest, mesh_digest, packed_atlas_digest
from validate_layer_modes import CUT_TESTS, activate, pr30_snapshot, validate

POSES = (*CUT_TESTS, (-.18, -23, 39))
PROBES = [(0, 0, .2), (.10, .04, -.7), (.22, -.08, .52), (.38, .11, .5), (.57, 0, .2),
          (.06, .16, .72), (-.25, .01, -.23), (-.19, -.12, .17), (.34, .10, .03)]


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def outside_normals(mesh):
    coords = [tuple(v.co) for v in mesh.vertices]
    normals = mesh.corner_normals
    result = {}
    for face in mesh.polygons:
        if face.material_index == 1:
            continue
        loop = list(face.loop_indices)
        polygon = [coords[i] for i in face.vertices]
        start = polygon.index(min(polygon))
        result[tuple(polygon[start:] + polygon[:start])] = [tuple(normals[i].vector)
                                                            for i in loop[start:] + loop[:start]]
    return result


def normal_error(before, after):
    assert before.keys() == after.keys()
    return max(dist(a, b) for key in before for a, b in zip(before[key], after[key], strict=True))


def solid_digests(scene):
    graph = bpy.context.evaluated_depsgraph_get()
    meshes = {obj.name: obj.evaluated_get(graph).data for obj in scene.objects
              if obj.get("role") in {"receptacle", "achene", "sepal", "pedicel"}}
    digests = {mesh: mesh_digest(mesh) for mesh in set(meshes.values())}
    return {name: digests[mesh] for name, mesh in meshes.items()}


def field_values(scene, session, rest_points):
    graph = bpy.context.evaluated_depsgraph_get()
    _, _, body_to_knife, body_to_rest, _, _, mm, _ = session.inputs(scene, graph)
    field = session.refresh.__func__.__globals__
    result = []
    for point in rest_points:
        rest = Vector(point)
        knife_space = body_to_knife @ (body_to_rest.inverted() @ rest)
        reconstructed = body_to_rest @ (body_to_knife.inverted() @ knife_space)
        def sample(p):
            return (*field["tissue_masks"](p, session.atlas),
                    *field["tissue_components"](p, mm, session.atlas, session.strands))
        result.append((sample(rest), sample(reconstructed)))
    return np.array(result)


def check_continuity(scene, session):
    mm = scene.unit_settings.scale_length * 1000
    rng = np.random.default_rng(580)
    # Include tile row transitions in Z, plus regular XYZ probes in the interior.
    atlas = session.atlas
    field = session.refresh.__func__.__globals__
    lo, span, n = (field[name] for name in ("LO", "SPAN", "N"))
    points = rng.uniform([-.58, -.58, -.85], [.58, .58, .80], (350, 3))
    points[:9, 2] = [lo[2] + span[2] * k/(n-1) for k in range(15, 150, 15)]
    def values(point):
        return np.array((atlas.sample_green(point), *field["tissue_masks"](point, atlas),
                         *field["tissue_components"](point, mm, atlas, session.strands)))
    def differences(step):
        offsets = np.eye(3)*step/(2*mm)
        return np.array([np.abs(values(Vector(p-e))-values(Vector(p+e)))
                         for p in points for e in offsets]).max(axis=0)
    ordinary = differences(.002)
    tight = differences(.0002)
    assert np.all(tight < .002)
    assert np.all(tight <= .13*ordinary + 2e-6), (tight, ordinary)
    return {"probes": len(points)*3, "distance_mm": .0002,
            "max_difference_at_0_002_mm": ordinary.tolist(),
            "max_difference_green_cortexmask_pithmask_cortex_pith_vascular": tight.tolist()}


def check_controls(scene, body, runtime):
    session = runtime["session"]
    namespace = session.refresh.__func__.__globals__
    mm = scene.unit_settings.scale_length * 1000
    _, full = measure(scene, body, body_mesh(body))
    points = list(full)
    masks = np.array([namespace["tissue_masks"](Vector(p), session.atlas) for p in points])
    distances = np.array([session.strands.distance(Vector(p), 2/mm)*mm for p in points])
    cortex, pith, near, far = masks[:, 0] > .9, masks[:, 1] > .9, distances < .35, distances > 1.01
    assert min(map(np.count_nonzero, (cortex, pith, near, far))) > 50
    full_values = np.array(list(full.values()))
    reports, contributions = {}, []
    for key, label, default, _ in CONTROLS:
        setattr(scene, key + "_control", 0)
        flush_callback(runtime)
        _, reduced = measure(scene, body, body_mesh(body))
        assert full.keys() == reduced.keys()
        delta = full_values - np.array([reduced[p] for p in points])
        assert delta.min() > -1e-5 and delta.max() > .013
        reports[label] = {"maximum_mm": float(delta.max()), "cortex_mean_mm": float(delta[cortex].mean()),
                          "pith_mean_mm": float(delta[pith].mean()), "near_path_mean_mm": float(delta[near].mean()),
                          "outside_path_max_mm": float(delta[far].max()), "vertices_over_0_001_mm": int((delta > .001).sum())}
        contributions.append(delta)
        setattr(scene, key + "_control", default)
        flush_callback(runtime)
    assert contributions[0][cortex].mean() > 16 * contributions[0][pith].mean()
    assert contributions[1][pith].mean() > 16 * contributions[1][cortex].mean()
    assert contributions[2][near].mean() > .01 and contributions[2][far].max() < 1e-5
    # Compare local roughness at identical mesh edges in high-membership ROIs.
    mesh = body_mesh(body)
    indices = {tuple(a.vector): i for i, a in enumerate(mesh.attributes["strawberry_exact_rest"].data)
               if tuple(a.vector) in full}
    zones = [{indices[p]: delta for p, delta, use in zip(points, contrib, zone) if use}
             for contrib, zone in zip(contributions, (cortex, pith))]
    roughness = []
    for values in zones:
        gradients = []
        positions = mesh.attributes["strawberry_exact_rest"].data
        for edge in mesh.edges:
            i, j = edge.vertices
            if i in values and j in values:
                length = dist(positions[i].vector, positions[j].vector)*mm
                if .23 < length < .30:
                    gradients.append((values[i] - values[j])/length)
        assert len(gradients) > 30
        roughness.append({"edges": len(gradients), "rms_delta_mm_per_mm": sqrt(np.mean(np.square(gradients)))})
    assert roughness[0]["rms_delta_mm_per_mm"] > 2*roughness[1]["rms_delta_mm_per_mm"]
    for key, *_ in CONTROLS:
        setattr(scene, key + "_control", 0)
    flush_callback(runtime)
    zero, _ = measure(scene, body, body_mesh(body))
    assert zero["max_displacement_mm"] < 1e-5
    for key, _, default, _ in CONTROLS:
        setattr(scene, key + "_control", default)
    flush_callback(runtime)
    return {"individual_removed_strengths": reports, "zero_max_displacement_mm": zero["max_displacement_mm"],
            "cortex_pith_own_component_local_roughness": roughness}


def run(args):
    assert sha(args.pr32) == PR32_SHA256 and sha(args.pr31) == PR31_SHA256
    native = validate(args.pr29, args.pr30, args.scene)
    bpy.ops.wm.open_mainfile(filepath=str(args.pr32), use_scripts=False)
    scene = bpy.context.scene
    source = pr30_snapshot(scene)
    atlas_digest = packed_atlas_digest()
    body, knife = scene.objects[BODY], scene.objects[KNIFE]
    raw_pits = tuple(a.value for a in body.data.attributes["achene_pit"].data)
    baseline = {}
    old = activate_pr32()
    for pose in POSES:
        pose_knife(knife, pose)
        start = perf_counter()
        bpy.context.view_layer.update()
        mesh = body_mesh(body)
        fast_seconds = perf_counter() - start
        fast_surface, fast_digest = surface(mesh), mesh_digest(mesh)
        fast_normals = outside_normals(mesh)
        assert topology(mesh) > 0
        assert bpy.ops.strawberry.exact_quality(exact=True) == {"FINISHED"}
        mesh = body_mesh(body)
        assert surface(mesh) == fast_surface
        prior, _ = measure(scene, body, mesh)
        old_normals = outside_normals(mesh)
        baseline[pose] = (fast_surface, fast_digest, fast_normals, old_normals,
                          dict(prior, refresh_seconds=old["session"].last["refresh_seconds"],
                               fast_update_seconds=fast_seconds))
        assert bpy.ops.strawberry.exact_quality(exact=False) == {"FINISHED"}
    old["unregister"]()

    bpy.ops.wm.open_mainfile(filepath=str(args.scene), use_scripts=False)
    scene = bpy.context.scene
    body, knife = scene.objects[BODY], scene.objects[KNIFE]
    assert pr30_snapshot(scene) == source
    assert bpy.context.view_layer.name == "MATCHED"
    assert not hasattr(bpy.types, "STRAWBERRY_PT_exact_cut")
    text = bpy.data.texts[TEXT]
    assert not text.use_module and runtime_source() == text.as_string()
    assert_fast(body, baseline[CUT_POSE][1])
    handlers = bpy.app.handlers.depsgraph_update_post
    first, runtime = activate_runtime(), activate_runtime()
    assert first["handler"] not in handlers and handlers.count(runtime["handler"]) == 1
    session = runtime["session"]
    assert bpy.ops.strawberry.exact_quality(exact=True) == {"FINISHED"}, session.error

    reports, reference = [], None
    for i, pose in enumerate(POSES):
        if i == 1:
            knife.location.y = 0
            bpy.context.view_layer.update()
            flush_callback(runtime)
            translated = mesh_digest(body_mesh(body))
            knife.rotation_euler.z = 0
        elif i:
            pose_knife(knife, pose)
        if i:
            bpy.context.view_layer.update()
            flush_callback(runtime)
        mesh = body_mesh(body)
        if i == 1:
            assert translated != mesh_digest(mesh)
        exact, _ = measure(scene, body, mesh)
        assert exact["max_displacement_mm"] > .045
        assert exact["displaced_cap_vertices_over_0_01_mm"] > 100
        fast_surface, _, fast_normals, old_normals, prior = baseline[pose]
        assert surface(mesh) == fast_surface, "Skin faces, pits or seam edges changed"
        normals = outside_normals(mesh)
        error = normal_error(old_normals, normals)
        assert error < 1e-6, error
        values = field_values(scene, session, PROBES)
        if reference is None:
            reference = values[:, 0]
        assert np.array_equal(reference, values[:, 0])
        transformed_error = float(np.abs(values[:, 1] - reference).max())
        assert transformed_error < 2e-5
        reports.append({"pose_y_xrot_zrot": pose, "pr32": prior, "zones": exact,
                        "zones_refresh_seconds": session.last["refresh_seconds"],
                        "skin_corner_normal_max_error_vs_pr32_exact": error,
                        "skin_corner_normal_max_error_vs_fast": normal_error(fast_normals, normals),
                        "rest_probe_error_after_knife_frame_roundtrip": transformed_error})

    continuation = check_continuity(scene, session)
    controls = check_controls(scene, body, runtime)
    all_solids = solid_digests(scene)
    assert len(all_solids) == 274
    current_digest = mesh_digest(body_mesh(body))
    before_idle = session.refresh_count
    for mode in ("whole", "fibers-only", "flesh-only", "matched"):
        layer, graph = activate(scene, mode)
        assert not session.cache.visible_get(view_layer=layer) and session.cache.hide_render
        assert body.visible_get() == (mode != "fibers-only")
        for name in DIAGNOSTIC_COUNTS:
            assert scene.objects[name].visible_get() == (mode != "whole")
        if mode == "whole":
            assert abs(knife.evaluated_get(graph).matrix_world.translation.y + 1.6) < 1e-4
            assert not surface(body_mesh(body))[1]
            assert len(body_mesh(body).vertices) == len(body.data.vertices)
        elif mode in ("flesh-only", "matched"):
            assert solid_digests(scene) == all_solids
        assert not bpy.app.timers.is_registered(runtime["timer"])
    assert session.refresh() is None and session.refresh_count == before_idle

    layer, graph = activate(scene, "whole")
    knife.location.y += .035
    layer.update()
    assert abs(knife.evaluated_get(graph).matrix_world.translation.y + 1.6) < 1e-4
    assert not bpy.app.timers.is_registered(runtime["timer"])
    activate(scene, "matched")
    flush_callback(runtime)
    assert mesh_digest(body_mesh(body)) != current_digest

    knife.location.y = -1.6
    knife.rotation_euler.x = knife.rotation_euler.z = 0
    bpy.context.view_layer.update()
    flush_callback(runtime)
    assert session.enabled and not session.last["cap"]
    assert_fast(body)
    pose_knife(knife, POSES[-1])
    bpy.context.view_layer.update()
    flush_callback(runtime)
    assert session.cache
    assert bpy.ops.strawberry.exact_quality(exact=False) == {"FINISHED"}
    assert_fast(body, baseline[POSES[-1]][1])
    assert bpy.ops.strawberry.exact_quality(exact=True) == {"FINISHED"}

    namespace = session.refresh.__func__.__globals__
    original = namespace["make_mesh"]

    def broken_mesh(*_args):
        raise ValueError("QA injected reconstruction failure")

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
    assert_fast(body, baseline[CUT_POSE][1])
    assert tuple(a.value for a in body.data.attributes["achene_pit"].data) == raw_pits
    assert packed_atlas_digest() == atlas_digest
    for name, count in DIAGNOSTIC_COUNTS.items():
        assert diagnostic_digest(scene.objects[name], count) == native["source_diagnostics_sha256"][name]
    assert pr30_snapshot(scene) == source

    assert bpy.ops.strawberry.exact_unload() == {"FINISHED"}
    assert bpy.app.timers.is_registered(runtime["unregister"])
    bpy.app.timers.unregister(runtime["unregister"])
    runtime["unregister"]()
    assert not hasattr(bpy.types, "STRAWBERRY_PT_exact_cut") and runtime["handler"] not in handlers
    assert not any(hasattr(bpy.types.Scene, key + "_control") for key, *_ in CONTROLS)
    runtime = activate_runtime()
    assert bpy.ops.strawberry.exact_quality(exact=True) == {"FINISHED"}
    changed_key = CONTROLS[1][0]
    setattr(scene, changed_key + "_control", .071)
    flush_callback(runtime)
    save_as = args.out.parent / "qa-saved-from-exact.blend"
    assert not save_as.exists()
    bpy.ops.wm.save_as_mainfile(filepath=str(save_as), compress=True)
    assert_fast(body, baseline[CUT_POSE][1])
    assert bpy.ops.strawberry.exact_quality(exact=True) == {"FINISHED"}
    bpy.ops.wm.open_mainfile(filepath=str(save_as), use_scripts=False)
    assert RUNTIME not in bpy.app.driver_namespace and not hasattr(bpy.types, "STRAWBERRY_PT_exact_cut")
    assert_fast(bpy.context.scene.objects[BODY], baseline[CUT_POSE][1])
    assert abs(bpy.context.scene[changed_key] - .071) < 1e-6

    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {"status": "PASS", "source_pr32_sha256": PR32_SHA256, "source_pr31_sha256": PR31_SHA256,
            "native_fast": native, "poses": reports, "controls": controls, "field_continuity": continuation,
            "rest_probes": [{"rest": p, "masks_and_components": values.tolist()}
                            for p, values in zip(PROBES, reference)],
            "source_snapshots_unchanged": True, "save_and_reopen_restored_fast_and_persisted_control": True,
            "callback_moves_and_reload": True, "failure_restored_fast": True,
            "exact_matched_and_flesh_solid_count_compared": len(all_solids),
            "peak_validator_rss_bytes": peak if sys.platform == "darwin" else peak*1024}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("pr29", "pr30", "pr31", "pr32", "scene", "out"):
        parser.add_argument("--" + key, type=lambda path: Path(path).resolve(), required=True)
    args = parser.parse_args(script_args())
    if args.out.exists():
        raise FileExistsError(args.out)
    report = json.dumps(run(args), indent=2)
    args.out.write_text(report + "\n")
    print(report, flush=True)

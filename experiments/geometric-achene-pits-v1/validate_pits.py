"""Validate the saved pit contract and native and opt-in cut paths."""
import argparse
from collections import Counter
import json
from pathlib import Path
import resource
import sys
from time import perf_counter

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), *(str(HERE.parent / name) for name in (
    "exact-tissue-zones-v1", "integration-exact-cut-v1",
    "integration-layer-modes-v1", "integration-live-exterior-v1"))]

from build_pits import (BODY, DIRECTION, REFERENCE, SOURCE_FACE, SOURCE_SHA, SUPPORT_BAND_MM, MAX_SEAT_LIFT_MM,
                        floor_hit, saved_seats, stats, tree_for_mesh)
from build_tissue_zones import CONTROLS, RUNTIME, TEXT, activate_runtime, runtime_source
from exterior_shape import PitField
from integration import CUT_POSE, DIAGNOSTIC_COUNTS, KNIFE, REST, SOURCE_BODY, WHOLE_POSE, check_source, pose_knife
from render_pits import sha
from validate_exact_cut import assert_fast, body_mesh, flush_callback, measure, surface, topology
from validate_integration import cap_graph_signature, check_pose, diagnostic_digest, mesh_digest, packed_atlas_digest
from validate_layer_modes import activate, check_diagnostics, check_embedded_ui, check_visibility, pr30_snapshot
from validate_tissue_zones import (POSES, check_continuity, check_controls, normal_error,
                                  outside_normals, solid_digests)


def vecs(attribute):
    return np.array([tuple(item.vector) for item in attribute.data])


def immutable_snapshot(scene):
    result = pr30_snapshot(scene)
    objects = result["objects"]
    seeds = {}
    for obj in scene.objects:
        if obj.get("role") == "achene":
            roles = objects[obj.name]
            basis = tuple(row[:3] for row in roles[3])
            objects[obj.name] = (*roles[:3], basis, *roles[4:])
            seeds[obj.name] = (obj.data.name, tuple(obj["hull_anchor_rest"]), tuple(obj["hull_normal_rest"]),
                               obj.rotation_mode, tuple(obj.rotation_quaternion), tuple(obj.scale))
    roles = objects[BODY]
    objects[BODY] = (*roles[:5], None, *roles[6:])
    result.update(seeds=seeds, atlas=packed_atlas_digest(),
                  diagnostics={name: diagnostic_digest(scene.objects[name], count)
                               for name, count in DIAGNOSTIC_COUNTS.items()},
                  materials={mat.name: (cap_graph_signature(mat.node_tree),
                      {node.name: (node.color_ramp.color_mode, node.color_ramp.interpolation,
                                   node.color_ramp.hue_interpolation,
                                   [(element.position, tuple(element.color)) for element in node.color_ramp.elements])
                       for node in mat.node_tree.nodes if node.type == "VALTORGB"},
                      {node.name: node.attribute_name for node in mat.node_tree.nodes if node.type == "ATTRIBUTE"},
                      {node.name: node.image.name if node.image else None
                       for node in mat.node_tree.nodes if node.type == "TEX_IMAGE"})
                             for mat in bpy.data.materials if mat.node_tree},
                  material_slots={obj.name: [slot.material.name if slot.material else None
                                            for slot in obj.material_slots] for obj in scene.objects},
                  modifiers={obj.name: [(mod.name, mod.type, mod.solver, mod.operation,
                                         mod.object.name, mod.material_mode)
                                        for mod in obj.modifiers if mod.type == "BOOLEAN"]
                             for obj in scene.objects},
                  texts={t.name: t.as_string() for t in bpy.data.texts if t.name.endswith(".py")},
                  tissue_defaults={key: scene[key] for key, *_ in CONTROLS})
    return result


def loop_faces(mesh):
    mesh.calc_loop_triangles()
    return np.array([tuple(t.vertices) for t in mesh.loop_triangles])


def source_data(scene):
    body = scene.objects[BODY]
    mesh = body.data
    mm = scene.unit_settings.scale_length * 1000
    positions = np.array([tuple(v.co) for v in mesh.vertices])
    triangles = loop_faces(mesh)
    normals = np.array([tuple(v.normal) for v in mesh.vertices])
    reference = np.empty((len(mesh.polygons), 2), dtype=np.int32)
    counts = Counter()
    for i, tri in enumerate(mesh.loop_triangles):
        index = tri.polygon_index
        if counts[index] == 0:
            reference[index, 0] = reference[index, 1] = i
        else:
            reference[index, 1] = i
        counts[index] += 1
    seat_centers = {seat.obj.name: seat.obj.location.copy() for seat in saved_seats(scene, mm)}
    return positions, normals, triangles, reference, tree_for_mesh(mesh), seat_centers


def correspondence(mesh, source, mm):
    """Verify each child triangle is an oriented subset of its source polygon tessellation."""
    base, normals, triangles, reference, _, _ = source
    refined = vecs(mesh.attributes[REFERENCE])
    direction = vecs(mesh.attributes[DIRECTION])
    index = loop_faces(mesh)
    points = refined[index]
    parent_ids = np.array([p.value for p in mesh.attributes[SOURCE_FACE].data])
    assert parent_ids.min() == 0 and parent_ids.max() == len(reference) - 1
    choices = reference[parent_ids[[t.polygon_index for t in mesh.loop_triangles]]]
    assigned = np.full(len(index), -1)
    child_area_vec = np.cross(points[:, 1] - points[:, 0], points[:, 2] - points[:, 0])
    child_area = np.linalg.norm(child_area_vec, axis=1)
    assert child_area.min() > 0
    direction_error = np.zeros(len(index))
    for matching in choices.T:
        vertices = triangles[matching]
        a, b, c = base[vertices].transpose((1, 0, 2))
        u, v = b - a, c - a
        normal = np.cross(u, v)
        offset = points - a[:, None, :]
        area2 = np.einsum("ij,ij->i", normal, normal)
        plane = np.einsum("ijk,ik->ij", offset, normal) / np.sqrt(area2)[:, None]
        wb = np.einsum("ijk,ik->ij", np.cross(offset, v[:, None, :]), normal) / area2[:, None]
        wc = np.einsum("ijk,ik->ij", np.cross(u[:, None, :], offset), normal) / area2[:, None]
        bary = np.stack((1 - wb - wc, wb, wc), axis=2)
        fits = ((np.abs(plane).max(axis=1) < 2e-7) & (bary.min(axis=(1, 2)) > -4e-5)
                & (np.einsum("ij,ij->i", child_area_vec, normal) > 0))
        assigned[fits] = matching[fits]
        interpolated = np.einsum("ncv,nvd->ncd", bary, normals[vertices])
        interpolated /= np.linalg.norm(interpolated, axis=2)[:, :, None]
        direction_error[fits] = np.linalg.norm(interpolated - direction[index], axis=2).max(axis=1)[fits]
    assert assigned.min() >= 0, int((assigned < 0).sum())
    a, b, c = base[triangles].transpose((1, 0, 2))
    original_area = np.linalg.norm(np.cross(b-a, c-a), axis=1)
    total = np.bincount(assigned, weights=child_area, minlength=len(triangles))
    area_error = np.max(np.abs(total - original_area)) * .5 * mm**2
    assert area_error < 5e-5, area_error
    assert direction_error.max() < 2e-4, direction_error.max()
    # Preserve every original sample in the correspondence, including the poles.
    assert set(map(tuple, base)) <= set(map(tuple, refined))
    return refined, direction, index, float(area_error), float(direction_error.max())


def geometry(scene, source):
    body = scene.objects[BODY]
    mesh = body.data
    mm = scene.unit_settings.scale_length * 1000
    seats = saved_seats(scene, mm)
    field = PitField([s.anchor for s in seats])
    refined, direction, triangles, area_error, direction_error = correspondence(mesh, source, mm)
    assert all(p.material_index == 0 and p.use_smooth for p in mesh.polygons)
    assert mesh.has_custom_normals and len(mesh.vertices) > len(source[0])
    sampled = np.array([field.sample(tuple(Vector(p) * mm)) for p in refined])
    coords = np.array([tuple(v.co) for v in mesh.vertices])
    delta = (refined - coords) * mm
    actual = np.einsum("ij,ij->i", delta, direction)
    moved = np.linalg.norm(delta, axis=1) > 0
    expected = sampled[:, 0] > 0
    tangent = np.linalg.norm(delta - actual[:, None] * direction, axis=1)
    field_error = np.abs(actual - sampled[:, 0]).max()
    assert (actual[moved] > 0).all() and (tangent < 2e-6).all() and field_error < 2e-6
    assert np.array_equal(refined[~expected], coords[~expected])
    mask_error = np.max(np.abs(np.array([v.value for v in mesh.attributes["achene_pit"].data]) - sampled[:, 1]))
    assert mask_error < 2e-6

    # Distance to a convex ellipsoid is convex. For each moved triangle,
    # distance to its selected support is bounded by its farthest corner.
    # A circumscribing sphere would underestimate distance to the ellipse.
    moved_faces = triangles[moved[triangles].any(axis=1)]
    triangle_mm = refined[moved_faces] * mm
    centers = triangle_mm.mean(axis=1)
    anchors = np.array([tuple(s.point * mm) for s in seats])
    axes = np.array([[s.anchor.long_axis, s.anchor.side_axis, s.anchor.normal] for s in seats])
    radii = np.array([[s.anchor.pit_length_radius_mm, s.anchor.pit_width_radius_mm,
                       .62 * s.anchor.pit_width_radius_mm] for s in seats])
    nearest = np.concatenate([np.argmin(((chunk[:, None, :] - anchors)**2).sum(axis=2), axis=1)
                              for chunk in np.array_split(centers, 40)])
    local = np.einsum("nci,nji->ncj", triangle_mm - anchors[nearest, None, :], axes[nearest])
    radius = radii[nearest, None, :]
    squared = radius**2
    outside = ((local / radius)**2).sum(axis=-1) > 1
    low = np.zeros(outside.shape)
    high = radius.max(axis=-1) * np.linalg.norm(local, axis=-1)
    for _ in range(35):
        lam = (low + high) * .5
        beyond = ((radius * local / (lam[..., None] + squared))**2).sum(axis=-1) > 1
        low = np.where(beyond, lam, low)
        high = np.where(beyond, high, lam)
    distances = np.where(outside, np.linalg.norm(local * high[..., None] /
                                                 (high[..., None] + squared), axis=-1), 0.)
    spill = distances.max(axis=1)
    assert max(spill) <= SUPPORT_BAND_MM, (max(spill), SUPPORT_BAND_MM)

    original_tree, original_centers = source[-2:]
    tree = tree_for_mesh(mesh)
    profiles = {}
    fractions, embeddings, exposures, drifts, floor_errors = [], [], [], [], []
    steps = (-1.16, -.8, -.5, 0, .5, .8, 1.16)
    for seat in seats:
        obj, point, normal, anchor = seat.obj, seat.point, seat.normal, seat.anchor
        movement = original_centers[obj.name] - obj.location
        tangential = (movement - movement.dot(normal)*normal).length * mm
        drifts.append(tangential)
        assert tangential < 1e-5, (obj.name, tangential)
        profiles[obj.name] = row = {}
        for name, axis, radius in (("long", anchor.long_axis, anchor.pit_length_radius_mm),
                                   ("side", anchor.side_axis, anchor.pit_width_radius_mm)):
            depths = []
            for step in steps:
                p = point + Vector(axis) * (step * radius / mm)
                depths.append((floor_hit(original_tree, p, normal, mm)
                               - floor_hit(tree, p, normal, mm)).dot(normal)*mm)
            assert .15 <= depths[3] <= .32 and depths[3] > max(depths[1], depths[-2]), (obj.name, name, depths)
            row[name] = depths
        floor = floor_hit(tree, point, normal, mm)
        lift = float(obj.get("pit_seat_lift_mm", 0.0))
        assert 0 <= lift <= MAX_SEAT_LIFT_MM, (obj.name, lift)
        floor_error = abs((obj.location-floor).dot(normal)*mm - .19*anchor.thickness_mm - lift)
        assert floor_error < 3e-6
        floor_errors.append(floor_error)
        signed = []
        for vertex in obj.data.vertices:
            p = obj.matrix_local @ vertex.co
            near, outward, _, _ = tree.find_nearest(p)
            signed.append((p-near).dot(outward)*mm)
        exposed_fraction = sum(value > 0 for value in signed) / len(signed)
        embedded, exposed = -min(signed), max(signed)
        assert embedded >= .055 and exposed >= .13 and .40 <= exposed_fraction <= .85, (
            obj.name, embedded, exposed, exposed_fraction)
        fractions.append(exposed_fraction)
        embeddings.append(embedded)
        exposures.append(exposed)
        row.update(embedded_mm=embedded, exposed_mm=exposed, exposed_mesh_vertex_fraction=exposed_fraction)

    return {
        "raw_signed_volume_bu3": topology(mesh), "raw_mesh_sha256": mesh_digest(mesh),
        "raw_vertices": len(mesh.vertices), "outside_field_vertices_unchanged": int((~expected).sum()),
        "displaced_vertices": int(moved.sum()), "vertex_inward_mm": stats(actual[moved].tolist()),
        "max_vertex_tangent_mm": float(tangent.max()), "max_field_error_mm": float(field_error),
        "max_mask_error": float(mask_error), "max_source_triangle_area_error_mm2": area_error,
        "max_source_normal_interpolation_error": direction_error,
        "max_triangle_support_extension_mm": max(spill), "allowed_support_extension_mm": SUPPORT_BAND_MM,
        "profile_axis_fraction_samples": steps, "achene_profiles": profiles,
        "achene_center_depth_mm": stats([p["long"][3] for p in profiles.values()]),
        "achene_tangent_drift_mm": stats(drifts), "achene_seat_offset_error_mm": stats(floor_errors),
        "achene_embedded_mm": stats(embeddings), "achene_exposed_mm": stats(exposures),
        "achene_exposed_mesh_vertex_fraction": stats(fractions),
    }


def runtime_check(scene, body, knife, fast, save_path):
    handlers = bpy.app.handlers.depsgraph_update_post
    first, runtime = activate_runtime(), activate_runtime()
    assert first["handler"] not in handlers and handlers.count(runtime["handler"]) == 1
    session = runtime["session"]
    fast_pose_data = fast[CUT_POSE]
    pose_knife(knife, CUT_POSE)
    bpy.context.view_layer.update()
    case_fast_normals = outside_normals(body_mesh(body))
    assert bpy.ops.strawberry.exact_quality(exact=True) == {"FINISHED"}, session.error
    case_exact = body_mesh(body)
    assert case_exact.has_custom_normals
    normal_delta = normal_error(case_fast_normals, outside_normals(case_exact))
    assert normal_delta < 1e-6
    del case_fast_normals
    results = []
    for i, pose in enumerate(POSES):
        if i == 1:
            knife.location.y = 0
            bpy.context.view_layer.update()
            flush_callback(runtime)
            translated = mesh_digest(body_mesh(body))
        if i:
            pose_knife(knife, pose)
            bpy.context.view_layer.update()
            flush_callback(runtime)
        mesh = body_mesh(body)
        if i == 1:
            assert translated != mesh_digest(mesh)
        exact, _ = measure(scene, body, mesh)
        assert exact["max_displacement_mm"] > .045 and exact["displaced_cap_vertices_over_0_01_mm"] > 100
        assert surface(mesh) == fast[pose][1], "Exact altered pitted skin, pit mask or cap seam"
        results.append(dict(exact, pose=pose, first_refresh_seconds=session.last["refresh_seconds"]))
    controls = check_controls(scene, body, runtime)
    continuity = check_continuity(scene, session)
    # Finish any pending control/depsgraph update before testing idle layer switches.
    bpy.context.view_layer.update()
    if bpy.app.timers.is_registered(runtime["timer"]):
        flush_callback(runtime)
    solid_before = solid_digests(scene)
    assert len(solid_before) == 274
    layer_refreshes = {}
    for mode in ("whole", "fibers-only", "flesh-only", "matched"):
        before = session.refresh_count
        layer, _ = activate(scene, mode)
        assert not session.cache.visible_get(view_layer=layer) and session.cache.hide_render
        if mode in ("whole", "fibers-only"):
            assert not bpy.app.timers.is_registered(runtime["timer"]), mode
            if mode == "whole":
                assert len(body_mesh(body).vertices) == len(body.data.vertices) and not surface(body_mesh(body))[1]
        else:
            # A first visit can invalidate the cut graph after a tissue control edit.
            # Any such rebuild must produce exactly the same cut solids.
            if bpy.app.timers.is_registered(runtime["timer"]):
                flush_callback(runtime)
            assert solid_digests(scene) == solid_before
        assert not bpy.app.timers.is_registered(runtime["timer"]), mode
        layer_refreshes[mode] = session.refresh_count - before
    before_idle = session.refresh_count
    assert session.refresh() is None and session.refresh_count == before_idle

    pose_knife(knife, WHOLE_POSE)
    bpy.context.view_layer.update()
    flush_callback(runtime)
    assert session.enabled and not session.last["cap"]
    assert_fast(body, fast[WHOLE_POSE][0])
    pose_knife(knife, POSES[-1])
    bpy.context.view_layer.update()
    flush_callback(runtime)
    assert session.cache
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
    assert_fast(body, fast_pose_data[0])
    assert bpy.ops.strawberry.exact_unload() == {"FINISHED"}
    assert bpy.app.timers.is_registered(runtime["unregister"])
    bpy.app.timers.unregister(runtime["unregister"])
    runtime["unregister"]()
    assert runtime["handler"] not in handlers and not hasattr(bpy.types, "STRAWBERRY_PT_exact_cut")
    runtime = activate_runtime()
    assert bpy.ops.strawberry.exact_quality(exact=True) == {"FINISHED"}
    control = CONTROLS[1][0]
    setattr(scene, control + "_control", .071)
    flush_callback(runtime)
    bpy.ops.wm.save_as_mainfile(filepath=str(save_path), compress=True)
    assert_fast(body, fast_pose_data[0])
    bpy.ops.wm.open_mainfile(filepath=str(save_path), use_scripts=False)
    assert RUNTIME not in bpy.app.driver_namespace and not hasattr(bpy.types, "STRAWBERRY_PT_exact_cut")
    assert abs(bpy.context.scene[control] - .071) < 1e-6
    assert_fast(bpy.context.scene.objects[BODY], fast_pose_data[0])
    return {"poses": results, "controls": controls, "atlas_field_continuity": continuity,
            "enabled_translation_rotation_reregistration_unload": True,
            "all_274_solids_match_in_cut_layers": True, "layer_switch_refreshes_after_controls": layer_refreshes,
            "saved_pose_exact_vs_fast_skin_corner_normal_max_error": normal_delta,
            "failure_restored_pitted_fast": True, "save_reopened_fast_with_persisted_control": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("pr29", "pr33", "scene", "out"):
        parser.add_argument(arg, type=lambda p: Path(p).resolve())
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    save = args.out.with_name("qa-reopened-from-exact.blend")
    assert not args.out.exists() and not save.exists()
    start = perf_counter()
    check_source(args.pr29)
    assert sha(args.pr33) == SOURCE_SHA
    bpy.ops.wm.open_mainfile(filepath=str(args.pr29), use_scripts=False)
    original = mesh_digest(bpy.data.objects[SOURCE_BODY].data)
    bpy.ops.wm.open_mainfile(filepath=str(args.pr33), use_scripts=False)
    scene = bpy.context.scene
    snapshot = immutable_snapshot(scene)
    body = scene.objects[BODY]
    assert mesh_digest(body.data) == original
    source = source_data(scene)
    baseline = []
    for pose in (WHOLE_POSE, *POSES):
        pose_knife(scene.objects[KNIFE], pose)
        before = perf_counter()
        bpy.context.view_layer.update()
        mesh = body_mesh(body)
        baseline.append({"pose": pose, "update_seconds": perf_counter() - before,
                         "vertices": len(mesh.vertices), "volume_bu3": topology(mesh)})

    bpy.ops.wm.open_mainfile(filepath=str(args.scene), use_scripts=False)
    scene = bpy.context.scene
    body, knife, rest = (scene.objects[n] for n in (BODY, KNIFE, REST))
    assert len(bpy.data.scenes) == 1 and immutable_snapshot(scene) == snapshot
    assert set(scene.view_layers.keys()) == {"WHOLE", "MATCHED", "FLESH ONLY", "FIBERS ONLY"}
    assert bpy.context.view_layer.name == "MATCHED" and scene.render.use_single_layer
    assert not hasattr(bpy.types, "STRAWBERRY_PT_exact_cut") and not any(t.use_module for t in bpy.data.texts)
    assert bpy.data.texts[TEXT].as_string() == runtime_source()
    assert_fast(body)
    report = geometry(scene, source)
    assert report["raw_mesh_sha256"] != original
    solids = [body] + [obj for obj in scene.objects if obj.get("role") in {"achene","sepal","pedicel"}]
    assert Counter(obj["role"] for obj in solids) == {"receptacle": 1, "achene": 264, "sepal": 8, "pedicel": 1}
    check_diagnostics(scene, body, knife, {"diagnostics": snapshot["diagnostics"],
        "diagnostic_relative_transforms": {name: snapshot["objects"][name][3] for name in DIAGNOSTIC_COUNTS}})
    check_embedded_ui(scene, knife)
    views = check_visibility(scene, solids, knife)
    fast, fast_poses = {}, []
    for pose in (WHOLE_POSE, *POSES):
        data = check_pose(rest, knife, body, solids[1:], pose, whole=pose == WHOLE_POSE)
        mesh = body_mesh(body)
        assert topology(mesh) > 0
        fast[pose] = (mesh_digest(mesh), surface(mesh))
        fast_poses.append(data)
    exact = runtime_check(scene, body, knife, fast, save)
    assert mesh_digest(bpy.context.scene.objects[BODY].data) == report["raw_mesh_sha256"]
    assert packed_atlas_digest() == snapshot["atlas"]
    receipt = {"status": "PASS", "blender": bpy.app.version_string, "pr29_sha256": sha(args.pr29),
               "pr33_sha256": SOURCE_SHA, "pitted_scene_sha256": sha(args.scene),
               "pr29_and_pr33_equal_raw_hull_sha256": original,
               "immutable_scene_snapshot_equal": True, "diagnostic_sha256": snapshot["diagnostics"],
               "packed_atlas_sha256": snapshot["atlas"], "native_views": views,
               "geometry": report, "pr33_native_topology": baseline, "pitted_native_poses": fast_poses,
               "pitted_exact": exact, "validation_seconds": perf_counter() - start,
               "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    print({k: receipt[k] for k in ("status", "validation_seconds", "peak_rss_bytes")}, flush=True)


if __name__ == "__main__":
    main()

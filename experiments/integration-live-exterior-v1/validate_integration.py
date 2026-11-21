"""Reopen the verified source and the built scene and measure the live cut."""

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
from struct import pack
import sys
from time import perf_counter

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from integration import (ATLAS, BODY, CUT_POSE, CUTTER, DIAGNOSTIC_COUNTS, DIAGNOSTICS,
                         KNIFE, REST, SCENE, SOURCE_BODY, SOURCE_SHA256, WARNING, WHOLE_POSE,
                         check_source, pose_knife, script_args)

EPS = 1e-4  # Native PR29 model units.


def mesh_digest(mesh):
    digest = sha256()
    for vertex in mesh.vertices:
        digest.update(pack("<3f", *vertex.co))
    for face in mesh.polygons:
        digest.update(pack("<I", len(face.vertices)))
        digest.update(pack(f"<{len(face.vertices)}I", *face.vertices))
    return digest.hexdigest()


def diagnostic_digest(obj, expected):
    if obj.type == "MESH":
        assert len(obj.data.vertices) == expected * 6
        return mesh_digest(obj.data)
    assert obj.type == "CURVE" and len(obj.data.splines) == expected
    digest = sha256()
    curve = obj.data
    digest.update(pack("<fii?", curve.bevel_depth, curve.bevel_resolution,
                       curve.resolution_u, curve.use_fill_caps))
    for spline in curve.splines:
        assert spline.type == "POLY"
        digest.update(pack("<I?", len(spline.points), spline.use_cyclic_u))
        for point in spline.points:
            digest.update(pack("<6f", *point.co, point.radius, point.tilt))
    return digest.hexdigest()


def packed_atlas_digest():
    image = bpy.data.images[ATLAS]
    assert tuple(image.size) == (2250, 1500)
    assert image.colorspace_settings.name == "Non-Color" and image.packed_file
    return sha256(image.packed_file.data).hexdigest()


def source_snapshot():
    return {
        "hull": mesh_digest(bpy.data.objects[SOURCE_BODY].data),
        "atlas": packed_atlas_digest(),
        "cutter": mesh_digest(bpy.data.objects[CUTTER].data),
        "diagnostics": {name: diagnostic_digest(bpy.data.objects[name], count)
                        for name, count in DIAGNOSTIC_COUNTS.items()},
    }


def contact_measurement(body, achenes):
    surface = BVHTree.FromPolygons([vertex.co for vertex in body.data.vertices],
                                   [face.vertices[:] for face in body.data.polygons])
    distances, embed_depths, raised_heights = [], [], []
    for obj in achenes:
        anchor = Vector(obj["hull_anchor_rest"])
        normal = Vector(obj["hull_normal_rest"])
        _, _, _, distance = surface.find_nearest(anchor)
        assert distance < EPS, (obj.name, distance)
        assert (obj.rotation_quaternion @ Vector((0, 0, 1))).dot(normal) > .999
        signed = [(obj.matrix_local @ vertex.co - anchor).dot(normal) for vertex in obj.data.vertices]
        # Contact against the actual hull rather than only the local tangent plane.
        signed_surface = []
        for vertex in obj.data.vertices:
            point = obj.matrix_local @ vertex.co
            closest, outward, _, _ = surface.find_nearest(point)
            signed_surface.append((point - closest).dot(outward))
        assert min(signed_surface) < -EPS and max(signed_surface) > EPS, obj.name
        distances.append(distance)
        embed_depths.append(-min(signed))
        raised_heights.append(max(signed))
    return {
        "count": len(distances),
        "max_anchor_distance_model_units": max(distances),
        "minimum_embed_depth_model_units": min(embed_depths),
        "minimum_exposed_height_model_units": min(raised_heights),
    }


def check_body_topology(mesh):
    topology = bmesh.new()
    try:
        topology.from_mesh(mesh)
        assert all(edge.is_manifold for edge in topology.edges)
        assert all(vertex.link_faces for vertex in topology.verts)
        return topology.calc_volume(signed=True)
    finally:
        topology.free()


def check_pose(rest, knife, body, exterior, pose, whole=False):
    started = perf_counter()
    pose_knife(knife, pose)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    plane = knife.matrix_world.inverted()

    def signed_distances(obj, mesh):
        model_to_plane = plane @ obj.matrix_world
        return [(model_to_plane @ vertex.co).y for vertex in mesh.vertices]

    evaluated_body = body.evaluated_get(depsgraph)
    mesh = evaluated_body.data
    signed = signed_distances(evaluated_body, mesh)
    cap = [face for face in mesh.polygons if face.material_index == 1]
    try:
        volume = check_body_topology(mesh)
    except AssertionError as error:
        raise AssertionError(f"Body has a non-manifold result at pose {pose}") from error
    assert volume > 0
    if whole:
        assert not cap and len(mesh.polygons) == len(body.data.polygons)
        # The solver can reorder the untouched whole hull.
        assert sorted(tuple(v.co) for v in mesh.vertices) == sorted(tuple(v.co) for v in body.data.vertices)
        assert abs(volume - check_body_topology(body.data)) < EPS
        max_cap_distance = None
    else:
        assert cap
        max_cap_distance = max(abs(signed[i]) for face in cap for i in face.vertices)
        assert min(signed) >= -EPS and max_cap_distance < EPS
    retained, partial = Counter(), Counter()
    for obj in exterior:
        original_distances = signed_distances(obj, obj.data)
        evaluated = obj.evaluated_get(depsgraph)
        remaining = signed_distances(evaluated, evaluated.data)
        role = obj["role"]
        if remaining:
            assert min(remaining) >= -EPS, (obj.name, pose, min(remaining))
            retained[role] += 1
        if max(original_distances) < -EPS:
            assert not remaining, (obj.name, pose)
        elif min(original_distances) > EPS:
            assert remaining, (obj.name, pose)
        elif min(original_distances) < -EPS and max(original_distances) > EPS:
            assert remaining, (obj.name, pose)
            # A crossing solid has an actual face on the same plane, even
            # when its cap inherits the sole exterior material.
            assert any(all(abs(remaining[index]) < EPS for index in face.vertices)
                       for face in evaluated.data.polygons), (obj.name, pose)
            partial[role] += 1
    assert rest.matrix_world.is_identity
    return {
        "pose_y_xrot_zrot": pose,
        "body_vertices": len(mesh.vertices),
        "body_faces": len(mesh.polygons),
        "body_volume_model_units_cubed": volume,
        "cap_faces": len(cap),
        "max_cap_plane_error_model_units": max_cap_distance,
        "retained_exterior_by_role": dict(retained),
        "intersected_exterior_by_role": dict(partial),
        "update_and_measure_seconds": round(perf_counter() - started, 3),
    }


def validate(source, scene_path):
    check_source(source)
    bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
    reference = source_snapshot()
    bpy.ops.wm.open_mainfile(filepath=str(scene_path), use_scripts=False)
    assert len(bpy.data.scenes) == 1
    scene = bpy.data.scenes[SCENE]
    assert bpy.context.scene is scene and scene.camera and scene["WARNING"] == WARNING
    guides = [block.as_string() for block in bpy.data.texts]
    assert any(WARNING in guide and "Whole fruit" in guide for guide in guides)
    body, rest, knife, cutter = (scene.objects[name] for name in (BODY, REST, KNIFE, CUTTER))
    assert knife.parent is rest and cutter.parent is knife and cutter.hide_render
    assert mesh_digest(body.data) == reference["hull"]
    assert mesh_digest(cutter.data) == reference["cutter"]
    assert packed_atlas_digest() == reference["atlas"]
    dz = max(v.co.z for v in body.data.vertices) - min(v.co.z for v in body.data.vertices)
    assert abs(dz * scene.unit_settings.scale_length * 1000 - 48) < EPS
    assert body.visible_get() and not body.hide_render
    assert len(body.data.vertices) == 30242
    assert [obj for obj in bpy.data.objects if obj.data is body.data] == [body]

    flesh = body.data.materials[1]
    assert cutter.data.materials[1] is flesh
    tree = flesh.node_tree
    samples = [node for node in tree.nodes if node.type == "TEX_IMAGE"]
    assert len(samples) == 2 and all(node.image is bpy.data.images[ATLAS] for node in samples)
    coordinates = tree.nodes["PR29 rest coordinates"]
    assert coordinates.object is rest
    assert {link.to_node.type for link in coordinates.outputs["Object"].links} == {"SEPXYZ", "TEX_NOISE"}

    collections = bpy.context.view_layer.layer_collection.children
    diagnostics = collections[DIAGNOSTICS]
    assert diagnostics.exclude and diagnostics.collection["WARNING"] == WARNING
    assert set(diagnostics.collection.objects.keys()) == set(DIAGNOSTIC_COUNTS)
    for name, count in DIAGNOSTIC_COUNTS.items():
        obj = scene.objects[name]
        assert obj.parent is rest and obj.matrix_basis.is_identity
        assert diagnostic_digest(obj, count) == reference["diagnostics"][name]
        assert obj["WARNING"] == WARNING
        nodes = obj.data.materials[0].node_tree.nodes
        assert any(node.type == "TEX_COORD" and node.object is knife for node in nodes)
    diagnostics.exclude = False
    bpy.context.view_layer.update()
    assert all(scene.objects[name].visible_get() for name in DIAGNOSTIC_COUNTS)
    diagnostics.exclude = True

    roles = defaultdict(list)
    for obj in scene.objects:
        roles[obj.get("role")].append(obj)
    expected = {"receptacle": 1, "achene": 264, "sepal": 8, "pedicel": 1}
    assert {role: len(roles[role]) for role in expected} == expected
    # Exact mesh inventory rules out anonymous, hidden, or render-only duplicate shells.
    assert {obj.name for obj in bpy.data.objects if obj.type == "MESH"} == {
        *(obj.name for role in expected for obj in roles[role]), cutter.name,
        "V2 | 539 seed positions and branch endpoints",
    }

    achenes = roles["achene"]
    exterior = achenes + roles["sepal"] + roles["pedicel"]
    for obj in [body, *exterior]:
        assert obj.parent is rest and not obj.hide_render
        modifier, = [item for item in obj.modifiers if item.type == "BOOLEAN"]
        assert modifier.object is cutter and modifier.operation == "DIFFERENCE"
        assert modifier.solver == ("MANIFOLD" if obj is body else "EXACT")
        assert modifier.material_mode == "INDEX"
        assert modifier.show_viewport and modifier.show_render

    bpy.context.view_layer.update()
    contact = contact_measurement(body, achenes)
    whole = check_pose(rest, knife, body, exterior, WHOLE_POSE, whole=True)
    assert whole["retained_exterior_by_role"] == {"achene": 264, "sepal": 8, "pedicel": 1}
    rows = [check_pose(rest, knife, body, exterior, pose)
            for pose in (CUT_POSE, (0.0, 0, 0), (-.26, 0, 0), (.08, 29, 32))]
    assert len({row["body_faces"] for row in rows}) == 4
    assert all(row["body_volume_model_units_cubed"] < whole["body_volume_model_units_cubed"] for row in rows)
    for role in ("achene", "sepal", "pedicel"):
        assert any(row["intersected_exterior_by_role"].get(role) for row in rows), (role, rows)
    for name, count in DIAGNOSTIC_COUNTS.items():
        assert diagnostic_digest(scene.objects[name], count) == reference["diagnostics"][name]
    return {
        "status": "PASS",
        "blender": bpy.app.version_string,
        "source_sha256": SOURCE_SHA256,
        "verified_source_data_digests": reference,
        "parts_cut_by_one_cutter": expected,
        "achene_contacts": contact,
        "whole": whole,
        "cut_poses": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--scene", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path, help="Fresh JSON output path")
    args = parser.parse_args(script_args())
    if args.out.exists():
        raise FileExistsError(args.out)
    report = json.dumps(validate(args.source.resolve(), args.scene.resolve()), indent=2)
    with args.out.open("x", encoding="utf-8") as stream:
        stream.write(report + "\n")
    print(report, flush=True)

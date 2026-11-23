"""Displace the authenticated PR29 surface around saved PR33 achene anchors."""
import argparse
from dataclasses import dataclass
import json
from math import dist, fsum
from pathlib import Path
from random import Random
import resource
from statistics import median
import sys
from time import perf_counter

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "src")]
from render_pits import sha
from exterior_shape import AcheneAnchor, ExteriorParams, PitField

SOURCE_SHA = "0f552c79054dec8ca82d2891bc2b5d6930eef64bc545e8188d808b946e1c66e2"
BODY = "Receptacle | canonical PR29 hull"
REFERENCE = "pit_base_position"
DIRECTION = "pit_source_normal"
SOURCE_FACE = "pit_source_polygon"
SUPPORT_BAND_MM = .72
EDGE_MM = .45
REFINE_PASSES = 2
MAX_VERTICES = 180_000
PIT_MIN_MM = .16
PIT_MAX_MM = .21
FOOTPRINT_SCALE = .72
MAX_SEAT_LIFT_MM = .04
TARGET_EXPOSED_FRACTION = .42


@dataclass
class Seat:
    obj: object
    point: Vector
    normal: Vector
    anchor: AcheneAnchor


def saved_seats(scene, mm):
    """Use saved positions, normals, object orientations, size and ordered IDs."""
    params = ExteriorParams()
    rng = Random(params.seed)
    seeds = sorted((o for o in scene.objects if o.get("role") == "achene"), key=lambda o: o.name)
    assert [o.name for o in seeds] == [f"Achene {i:03}" for i in range(1, 265)]
    seats = []
    for obj in seeds:
        point = Vector(obj["hull_anchor_rest"])
        normal = Vector(obj["hull_normal_rest"]).normalized()
        q = obj.rotation_quaternion
        side, along, up = (q @ Vector(v) for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1)))
        assert normal.dot(up) > .999999 and obj.rotation_mode == "QUATERNION"
        width, length, thickness = (value * mm for value in obj.scale)
        size = length / params.achene_length_mm
        anchor = AcheneAnchor(0, 0, tuple(point * mm), tuple(normal),
                              tuple(along), tuple(side), length, width, thickness,
                              FOOTPRINT_SCALE * .5 * params.pit_length_mm * size,
                              FOOTPRINT_SCALE * .5 * params.pit_width_mm * size,
                              rng.uniform(PIT_MIN_MM, PIT_MAX_MM))
        seats.append(Seat(obj, point, normal, anchor))
    return seats


def tree_for_mesh(mesh):
    return BVHTree.FromPolygons([v.co for v in mesh.vertices],
                                [t.vertices[:] for t in mesh.loop_triangles], all_triangles=True)


def floor_hit(tree, point, normal, mm):
    hit, _, _, _ = tree.ray_cast(point + normal / mm, -normal, 2 / mm)
    assert hit is not None
    return hit


def seat_exposure(tree, seat, mm):
    signed = []
    transform = seat.obj.matrix_parent_inverse @ Matrix.LocRotScale(
        seat.obj.location, seat.obj.rotation_quaternion, seat.obj.scale)
    for vertex in seat.obj.data.vertices:
        point = transform @ vertex.co
        near, outward, _, _ = tree.find_nearest(point)
        signed.append((point - near).dot(outward) * mm)
    return sum(value > 0 for value in signed) / len(signed), -min(signed), max(signed)


def fit_seat_exposure(tree, seat, mm):
    """Keep the exposure criterion; fit a bounded outward seating correction."""
    initial = seat.obj.location.copy()
    fraction, embedded, exposed = seat_exposure(tree, seat, mm)
    lift = 0.0
    if fraction < TARGET_EXPOSED_FRACTION:
        low, high = 0.0, MAX_SEAT_LIFT_MM
        seat.obj.location = initial + seat.normal * (high / mm)
        assert seat_exposure(tree, seat, mm)[0] >= TARGET_EXPOSED_FRACTION, seat.obj.name
        for _ in range(16):
            trial = (low + high) * .5
            seat.obj.location = initial + seat.normal * (trial / mm)
            if seat_exposure(tree, seat, mm)[0] >= TARGET_EXPOSED_FRACTION:
                high = trial
            else:
                low = trial
        lift = high
        seat.obj.location = initial + seat.normal * (lift / mm)
        fraction, embedded, exposed = seat_exposure(tree, seat, mm)
    assert .40 <= fraction <= .85 and embedded >= .055 and exposed >= .13, (seat.obj.name, fraction, embedded, exposed)
    seat.obj["pit_seat_lift_mm"] = lift
    return lift


def local_refine(bm, mesh, seats, mm):
    """Subdivide only near pits; use Blender's original tessellation for each split quad."""
    lookup = KDTree(len(seats))
    for i, seat in enumerate(seats):
        lookup.insert(seat.point, i)
    lookup.balance()
    radius = max(s.anchor.pit_length_radius_mm for s in seats) / mm
    target = EDGE_MM / mm
    ellipses = [
        (Vector(s.anchor.long_axis) * (mm / s.anchor.pit_length_radius_mm),
         Vector(s.anchor.side_axis) * (mm / s.anchor.pit_width_radius_mm),
         s.normal * (mm / (.62 * s.anchor.pit_width_radius_mm))) for s in seats
    ]
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    ids = bm.faces.layers.int.new(SOURCE_FACE)
    for i, face in enumerate(bm.faces):
        face[ids] = i
    triangulations = {}
    for triangle in mesh.loop_triangles:
        triangulations.setdefault(triangle.polygon_index, []).append(triangle.vertices[:])
    vertices = list(bm.verts)
    refined_ids = {face[ids] for face in bm.faces if len(face.verts) == 3}
    for face in list(bm.faces):
        if len(face.verts) == 3:
            continue
        center = face.calc_center_median()
        bound = max((v.co - center).length for v in face.verts)
        # Includes any face incident to an edge chosen for bisection below.
        max_edge = max(edge.calc_length() for edge in face.edges)
        if lookup.find(center)[2] > radius + bound + max_edge / 2:
            continue
        index, mat, smooth = face[ids], face.material_index, face.smooth
        refined_ids.add(index)
        bm.faces.remove(face)
        for indexes in triangulations[index]:
            child = bm.faces.new([vertices[i] for i in indexes])
            child.material_index = mat
            child.smooth = smooth
            child[ids] = index

    def refine_edge(edge):
        length = edge.calc_length()
        if length <= target:
            return False
        a, b = (v.co for v in edge.verts)
        for point, i, _ in lookup.find_range((a + b) * .5, radius + length / 2):
            frame = ellipses[i]
            relative = a - point
            u = Vector(tuple(axis.dot(relative) for axis in frame))
            direction = b - a
            v = Vector(tuple(axis.dot(direction) for axis in frame))
            t = min(1.0, max(0.0, -u.dot(v) / v.length_squared))
            if (u + t * v).length_squared <= 1:
                return True
        return False

    counts = []
    for _ in range(REFINE_PASSES):
        edges = [edge for edge in bm.edges if refine_edge(edge)]
        if not edges:
            break
        assert all(len(face.verts) == 3 for edge in edges for face in edge.link_faces)
        bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=True, use_single_edge=True)
        polys = [face for face in bm.faces if len(face.verts) > 3 and face[ids] in refined_ids]
        if polys:
            bmesh.ops.triangulate(bm, faces=polys, quad_method="BEAUTY")
        counts.append(len(edges))
        assert len(bm.verts) < MAX_VERTICES, (counts, len(bm.verts))
    return counts


def smooth_skin_normals(mesh, field, mm):
    """Use the continuous pit slope to shade the two-pass approximation."""
    base = mesh.attributes[REFERENCE].data
    normal = mesh.attributes[DIRECTION].data
    step = .025
    values = []
    for point_attr, normal_attr in zip(base, normal, strict=True):
        point, n = point_attr.vector * mm, normal_attr.vector.copy()
        if field.sample(tuple(point))[1]:
            t = n.orthogonal().normalized()
            b = n.cross(t).normalized()
            for axis in (t, b):
                up = field.sample(tuple(point + axis * step))[0]
                down = field.sample(tuple(point - axis * step))[0]
                n += axis * ((up - down) / (2 * step))
        values.append(n.normalized())
    mesh.normals_split_custom_set_from_vertices(values)



def deform(body, seats, mm):
    mesh = body.data
    mesh.calc_loop_triangles()
    original_count = len(mesh.vertices)
    raw_normals = [v.normal.copy() for v in mesh.vertices]
    base_tree = tree_for_mesh(mesh)
    triangle_vertices = [t.vertices[:] for t in mesh.loop_triangles]
    for seat in seats:
        _, outward, _, distance = base_tree.find_nearest(seat.point)
        assert distance * mm < .02 and outward.dot(seat.normal) > .94, (seat.obj.name, distance * mm, outward.dot(seat.normal))
        old = seat.point + seat.normal * (.19 * seat.anchor.thickness_mm / mm)
        assert dist(old, seat.obj.location) * mm < .001, seat.obj.name

    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        # BMesh linearly interpolates this layer for each inserted edge midpoint.
        normals = bm.verts.layers.float_vector.new(DIRECTION)
        for vertex, normal in zip(bm.verts, raw_normals, strict=True):
            vertex[normals] = normal
        def triangle_volume(triangles):
            return fsum(a.dot(b.cross(c)) for a, b, c in triangles) / 6

        volume = triangle_volume(tuple(mesh.vertices[i].co for i in tri)
                                 for tri in triangle_vertices)
        counts = local_refine(bm, mesh, seats, mm)
        refined_volume = triangle_volume(tuple(loop.vert.co for loop in tri)
                                         for tri in bm.calc_loop_triangles())
        assert abs(refined_volume - volume) < 1e-5, (refined_volume, volume)
        base = bm.verts.layers.float_vector.new(REFERENCE)
        mask = bm.verts.layers.float.get("achene_pit")
        field = PitField([s.anchor for s in seats])
        depths = []
        for vertex in bm.verts:
            vertex[base] = vertex.co
            normal = Vector(vertex[normals]).normalized()
            vertex[normals] = normal
            depth, weight = field.sample(tuple(vertex.co * mm))
            if depth:
                vertex.co -= normal * (depth / mm)
                depths.append(depth)
            vertex[mask] = weight
        bm.normal_update()
        assert all(edge.is_manifold and edge.is_contiguous for edge in bm.edges)
        deformed_volume = bm.calc_volume(signed=True)
        assert 0 < deformed_volume < volume
        bm.to_mesh(mesh)
        mesh.update()
        smooth_skin_normals(mesh, field, mm)
    finally:
        bm.free()

    mesh.calc_loop_triangles()
    new_tree = tree_for_mesh(mesh)
    center_depths, seat_lifts = [], []
    for seat in seats:
        base_hit = floor_hit(base_tree, seat.point, seat.normal, mm)
        skin_hit = floor_hit(new_tree, seat.point, seat.normal, mm)
        depth = (base_hit - skin_hit).dot(seat.normal) * mm
        assert .15 <= depth <= .32, (seat.obj.name, depth)
        center_depths.append(depth)
        # Fit the authored embed offset to the actual triangulated floor.
        seat.obj.location = skin_hit + seat.normal * (.19 * seat.anchor.thickness_mm / mm)
        seat_lifts.append(fit_seat_exposure(new_tree, seat, mm))

    return {"original_vertices": original_count, "original_triangles": len(triangle_vertices),
            "vertices": len(mesh.vertices), "faces": len(mesh.polygons),
            "triangles": len(mesh.loop_triangles), "split_edge_counts": counts,
            "displaced_vertices": len(depths), "vertex_displacement_mm": stats(depths),
            "center_depth_mm": stats(center_depths), "seat_lift_mm": stats(seat_lifts),
            "adjusted_achenes": sum(value > 0 for value in seat_lifts), "original_volume_bu3": volume,
            "pitted_volume_bu3": deformed_volume, "refined_base_volume_bu3": refined_volume}


def stats(values):
    return {"min": min(values), "median": median(values), "max": max(values)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    started = perf_counter()
    out = args.out.resolve()
    receipt = out.with_name("build-report.json")
    assert not out.exists() and not receipt.exists()
    assert sha(args.source) == SOURCE_SHA
    bpy.ops.wm.open_mainfile(filepath=str(args.source.resolve()), use_scripts=False)
    scene = bpy.context.scene
    body = scene.objects[BODY]
    assert body.matrix_local.is_identity and bpy.context.view_layer.name == "MATCHED"
    mm = scene.unit_settings.scale_length * 1000
    begin_geometry = perf_counter()
    report = deform(body, saved_seats(scene, mm), mm)
    geometry_seconds = perf_counter() - begin_geometry
    guide = bpy.data.texts["START HERE | Strawberry layer modes.txt"]
    guide.write("\nGeometric achene pits v1: finite inward deformation of the existing hull, "
                "with each original achene seated against its pit floor. "
                "Pit depths are artist parameters. The TISSUE_ZONES script remains opt-in.\n")
    assert not any(block.use_module for block in bpy.data.texts)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    report.update(source_sha256=SOURCE_SHA, scene_sha256=sha(out), builder_sha256=sha(Path(__file__)),
                  geometry_seconds=geometry_seconds, build_seconds=perf_counter() - started,
                  peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  blender=bpy.app.version_string)
    receipt.write_text(json.dumps(report, indent=2) + "\n")
    print(report, flush=True)


if __name__ == "__main__":
    main()

"""Independent, read-only evaluated-mesh QA for one saved strawberry pose.

Run a fresh Blender process for every pose. The script opens the file itself so
the reported elapsed time includes file loading and dependency-graph updates:

  blender --background --factory-startup --disable-autoexec \
    --python-exit-code 1 --python validate_saved_pose.py -- \
    --scene /absolute/scene.blend --pose plane --output /absolute/qa.json

Geometry is measured in world-space millimetres, using scene scale_length.
This is an engineering diagnostic, not visual acceptance or anatomical proof.
"""
import time
START = time.perf_counter()

import argparse
import hashlib
import json
import math
import resource
import sys
from array import array
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

WHOLE = 'Receptacle | sculpted skin and achene pits'
PLANE = 'SDF cutter | planar (move or rotate)'
BITE = 'SDF cutter | spherical bite (move or scale)'
AREA_LIMIT_MM2 = 1e-10


def digest_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def digest_array(values, dtype):
    return hashlib.sha256(np.ascontiguousarray(values, dtype=dtype).tobytes()).hexdigest()


def get_array(collection, field, width, dtype):
    out = np.empty(len(collection) * width, dtype=dtype)
    collection.foreach_get(field, out)
    return out.reshape((-1, width)) if width != 1 else out


def world_vertices(mesh, matrix, mm_per_bu):
    local = get_array(mesh.vertices, 'co', 3, np.float32)
    transform = np.asarray(matrix, dtype=np.float64)
    world = (local.astype(np.float64) @ transform[:3, :3].T + transform[:3, 3]) * mm_per_bu
    return local, world


def connected_labels(nverts, edges):
    """Union by cardinality, then full path compression; isolated verts count."""
    parents = array('i', range(nverts))
    sizes = array('i', [1]) * nverts

    def root(v):
        current = v
        while parents[current] != current:
            current = parents[current]
        while parents[v] != v:
            after = parents[v]
            parents[v] = current
            v = after
        return current

    for a, b in edges:
        ra, rb = root(int(a)), root(int(b))
        if ra == rb:
            continue
        if sizes[ra] < sizes[rb]:
            ra, rb = rb, ra
        parents[rb] = ra
        sizes[ra] += sizes[rb]
    roots = np.fromiter((root(i) for i in range(nverts)), dtype=np.int32, count=nverts)
    _, labels, counts = np.unique(roots, return_inverse=True, return_counts=True)
    order = np.argsort(-counts, kind='stable')
    ranked = np.empty(len(order), np.int32)
    ranked[order] = np.arange(len(order), dtype=np.int32)
    return ranked[labels], counts[order]


def attribute_report(mesh, name):
    attr = mesh.attributes.get(name)
    if attr is None:
        return {'present': False}
    fields = {'FLOAT_VECTOR': ('vector', 3), 'FLOAT': ('value', 1)}
    result = {'present': True, 'domain': attr.domain, 'data_type': attr.data_type, 'length': len(attr.data)}
    if attr.data_type in fields:
        field, width = fields[attr.data_type]
        vals = get_array(attr.data, field, width, np.float32)
        result.update(finite=bool(np.isfinite(vals).all()), sha256_float32_le=digest_array(vals, '<f4'),
                      minimum=np.min(vals, axis=0).tolist() if len(vals) else None,
                      maximum=np.max(vals, axis=0).tolist() if len(vals) else None)
    return result


def image_report(image):
    width, height = image.size
    vals = np.empty(width * height * image.channels, np.float32)
    image.pixels.foreach_get(vals)
    pixels = vals.reshape(height, width, image.channels)
    result = {'name': image.name, 'size': [width, height], 'channels': image.channels,
              'users': image.users, 'source': image.source, 'colorspace': image.colorspace_settings.name,
              'packed': image.packed_file is not None, 'finite_pixels': bool(np.isfinite(vals).all()),
              'sha256_float32_le': digest_array(vals, '<f4')}
    if image.channels == 4:
        for index, channel in enumerate('RGBA'):
            result[channel + '_sha256_float32_le'] = digest_array(pixels[:, :, index], '<f4')
        result['GBA_sha256_float32_le'] = digest_array(pixels[:, :, 1:], '<f4')
        result['BA_sha256_float32_le'] = digest_array(pixels[:, :, 2:], '<f4')
    if image.packed_file is not None:
        result['packed_sha256'] = hashlib.sha256(image.packed_file.data).hexdigest()
        result['packed_bytes'] = image.packed_file.size
    return result


def nearest_hull_by_material(source_object, mm_per_bu, triangle_centers, material_ids, material_names):
    """Distance diagnostic; does not infer material identity from slot number."""
    _, points = world_vertices(source_object.data, source_object.matrix_world, mm_per_bu)
    source_object.data.calc_loop_triangles()
    triangles = get_array(source_object.data.loop_triangles, 'vertices', 3, np.int32)
    tree = BVHTree.FromPolygons(points.tolist(), triangles.tolist(), all_triangles=True)
    distances = np.empty(len(triangle_centers), np.float64)
    signed_nearest = np.empty_like(distances)
    for i, center in enumerate(triangle_centers):
        q = Vector(center)
        near, normal, _, distance = tree.find_nearest(q)
        distances[i] = distance if near is not None else float('nan')
        signed_nearest[i] = (q - near).dot(normal) if near is not None else float('nan')
    rows = []
    for matid in np.unique(material_ids):
        selection = material_ids == matid
        dist = distances[selection]
        signed = signed_nearest[selection]
        rows.append({'slot': int(matid), 'name': material_names.get(int(matid)), 'triangles': int(selection.sum()),
                     'distance_min_mm': float(dist.min()), 'distance_max_mm': float(dist.max()),
                     'distance_median_mm': float(np.median(dist)),
                     'farther_than_0_5_mm': int((dist > 0.5).sum()),
                     'farther_than_0_5_mm_and_inward_nearest_normal': int(((dist > 0.5) & (signed < 0)).sum())})
    return {'reference': source_object.name, 'reference_geometry': 'raw source mesh of the evaluated body, in that same object frame; modifiers not evaluated',
            'query': 'centroid of every evaluated loop triangle', 'signed_test_limit': 'nearest-surface normal, not a general inside/outside proof',
            'by_material': rows}


def bulk_witness(point_mm, coords, triangles, labels):
    """Optional closed-mesh parity witness with three deterministic ray directions."""
    tree = BVHTree.FromPolygons(coords.tolist(), triangles.tolist(), all_triangles=True)
    point = Vector(point_mm)
    _, _, nearest_triangle, nearest_distance = tree.find_nearest(point)
    epsilon = 1e-4
    limit = float(np.linalg.norm(coords.max(axis=0) - coords.min(axis=0)) * 4 + 1)
    rays = []
    for direction_tuple in ((1, .2137, .4173), (.3191, 1, .1731), (.2717, .3913, 1)):
        direction = Vector(direction_tuple).normalized()
        origin, remaining = point.copy(), limit
        hits = {}
        for _ in range(len(triangles) + 1):
            location, _, triangle, distance = tree.ray_cast(origin, direction, remaining)
            if location is None:
                break
            component = int(labels[triangles[triangle, 0]])
            hits[component] = hits.get(component, 0) + 1
            origin = location + direction * epsilon
            remaining -= distance + epsilon
            if remaining <= 0:
                break
        rays.append({'direction': list(direction), 'intersections_by_component': hits,
                     'inside_components_by_parity': sorted(k for k, value in hits.items() if value % 2)})
    main_votes = sum(0 in ray['inside_components_by_parity'] for ray in rays)
    ambiguous = nearest_distance is None or nearest_distance <= epsilon
    return {'point_mm': list(point_mm), 'near_boundary_tolerance_mm': epsilon,
            'nearest_surface_distance_mm': nearest_distance,
            'nearest_component': int(labels[triangles[nearest_triangle, 0]]) if nearest_triangle is not None else None,
            'rays': rays, 'inside_largest_component': bool(main_votes >= 2) if not ambiguous else None,
            'all_three_rays_agree_on_largest': main_votes in (0, 3),
            'limitation': 'Numerical parity witness for this point, not graph-root provenance or universal attachment proof.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scene', required=True, type=Path)
    parser.add_argument('--pose', required=True, choices=['whole', 'plane', 'bite', 'plane_moved', 'bite_moved', 'plane_rotated'])
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--expect-scene-sha256')
    parser.add_argument('--expect-R-sha256')
    parser.add_argument('--expect-GBA-sha256')
    parser.add_argument('--expect-BA-sha256')
    parser.add_argument('--atlas-name', action='append')
    parser.add_argument('--required-attribute', action='append', help='Repeat to override the default fruit_rest and v8_vascular_intensity requirements for cut poses.')
    parser.add_argument('--surface-distance', action='store_true')
    parser.add_argument('--bulk-witness-mm', type=float, nargs=3)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    required_attributes = args.required_attribute or ['fruit_rest', 'v8_vascular_intensity']
    source = args.scene.expanduser().resolve(strict=True)
    report = {'schema': 'strawberry-independent-pose-qa/v1', 'scene': str(source), 'pose': args.pose,
              'scene_sha256': digest_file(source), 'source_size_bytes': source.stat().st_size,
              'scientific_status': 'ARTIST parameters; no histological validation',
              'visual_status': 'NOT_ASSESSED_BY_THIS_SCRIPT'}
    bpy.context.preferences.filepaths.use_scripts_auto_execute = False
    before_load = time.perf_counter()
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    after_load = time.perf_counter()
    scene = bpy.context.scene
    mm_per_bu = float(scene.unit_settings.scale_length) * 1000
    frame = 1 if args.pose == 'whole' else 40 if args.pose.startswith('bite') else 20
    before_frame = time.perf_counter()
    scene.frame_set(frame)
    after_frame = time.perf_counter()
    cutter = None if args.pose == 'whole' else bpy.data.objects[BITE if args.pose.startswith('bite') else PLANE]
    original_transform = list(map(list, cutter.matrix_world)) if cutter else None
    if args.pose == 'plane_moved':
        cutter.location.y += 3.0
        cutter.rotation_euler.x += 0.1745329252
    elif args.pose == 'bite_moved':
        cutter.location.x -= 4.0
        cutter.scale *= 1.13
    elif args.pose == 'plane_rotated':
        cutter.rotation_euler.y += math.radians(20)
        cutter.rotation_euler.z += math.radians(30)
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    graph.update()
    name = WHOLE if args.pose == 'whole' else 'SDF visible body | ' + ('bite' if args.pose.startswith('bite') else 'planar')
    obj = bpy.data.objects[name]
    evaluated = obj.evaluated_get(graph)
    mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=graph)
    mesh.calc_loop_triangles()
    after_evaluation = time.perf_counter()
    local, coords = world_vertices(mesh, evaluated.matrix_world, mm_per_bu)
    edges = get_array(mesh.edges, 'vertices', 2, np.int32)
    triangles = get_array(mesh.loop_triangles, 'vertices', 3, np.int32)
    if len(coords) == 0 or len(triangles) == 0:
        raise RuntimeError('Empty evaluated geometry; no engineering pass is possible')
    labels, counts = connected_labels(len(coords), edges)
    # Count incidences on original mesh edges; loop triangles additionally test area.
    loop_edges = get_array(mesh.loops, 'edge_index', 1, np.int32)
    incidence = np.bincount(loop_edges, minlength=len(edges))
    loop_vertices = get_array(mesh.loops, 'vertex_index', 1, np.int32)
    starts = get_array(mesh.polygons, 'loop_start', 1, np.int32)
    totals = get_array(mesh.polygons, 'loop_total', 1, np.int32)
    next_indices = np.roll(np.arange(len(mesh.loops)), -1)
    next_indices[starts + totals - 1] = starts
    orientation = np.where(loop_vertices < loop_vertices[next_indices], 1, -1)
    winding = np.bincount(loop_edges, weights=orientation, minlength=len(edges))
    bm = bmesh.new()
    bm.from_mesh(mesh)
    nonmanifold_vertices = sum(not v.is_manifold for v in bm.verts)
    bm.free()
    a, b, c = (coords[triangles[:, i]] for i in range(3))
    cross = np.cross(b - a, c - a)
    areas = np.linalg.norm(cross, axis=1) * 0.5
    origin = coords.mean(axis=0)
    volumes = np.einsum('ij,ij->i', a - origin, np.cross(b - origin, c - origin)) / 6.0
    triangle_components = labels[triangles[:, 0]]
    component_volumes = np.bincount(triangle_components, weights=volumes, minlength=len(counts))
    component_areas = np.bincount(triangle_components, weights=areas, minlength=len(counts))
    component_triangles = np.bincount(triangle_components, minlength=len(counts))
    mins = np.full((len(counts), 3), np.inf)
    maxes = np.full((len(counts), 3), -np.inf)
    np.minimum.at(mins, labels, coords)
    np.maximum.at(maxes, labels, coords)
    materials = {i: mat.name if mat else None for i, mat in enumerate(mesh.materials)}
    polygon_materials = get_array(mesh.polygons, 'material_index', 1, np.int32)
    triangle_materials = get_array(mesh.loop_triangles, 'material_index', 1, np.int32)
    source_local = get_array(obj.data.vertices, 'co', 3, np.float32)
    report.update(blender={'version': bpy.app.version_string, 'build_hash': bpy.app.build_hash.decode(),
                           'auto_execute_scripts': bpy.context.preferences.filepaths.use_scripts_auto_execute},
                  frame=frame, object=name, unit_system=scene.unit_settings.system,
                  mm_per_blender_unit=mm_per_bu, matrix_world=list(map(list, evaluated.matrix_world)),
                  cutter_original_matrix_world=original_transform,
                  cutter_test_matrix_world=list(map(list, cutter.matrix_world)) if cutter else None,
                  source_body={'vertices': len(source_local), 'local_vertices_sha256_float32_le': digest_array(source_local, '<f4')},
                  vertices=len(coords), edges=len(edges), polygons=len(mesh.polygons), triangles=len(triangles),
                  bounds_mm=[coords.min(axis=0).tolist(), coords.max(axis=0).tolist()],
                  evaluated_vertices_sha256_float32_le=digest_array(local, '<f4'),
                  evaluated_triangles_sha256_int32_le=digest_array(triangles, '<i4'),
                  connected_components=len(counts), component_vertex_counts=counts.tolist(),
                  largest_vertex_fraction=float(counts[0] / len(coords)),
                  components=[{'index': i, 'vertices': int(count), 'triangles': int(component_triangles[i]),
                               'signed_volume_mm3': float(component_volumes[i]), 'area_mm2': float(component_areas[i]),
                               'bounds_mm': [mins[i].tolist(), maxes[i].tolist()]} for i, count in enumerate(counts)],
                  boundary_edges=int((incidence == 1).sum()), wire_edges=int((incidence == 0).sum()),
                  edges_with_more_than_two_faces=int((incidence > 2).sum()),
                  nonmanifold_edges=int((incidence != 2).sum()), nonmanifold_vertices=nonmanifold_vertices,
                  inconsistent_winding_edges=int(((incidence == 2) & (winding != 0)).sum()),
                  signed_volume_mm3=float(volumes.sum()), surface_area_mm2=float(areas.sum()),
                  minimum_triangle_area_mm2=float(areas.min()), zero_area_triangles=int((areas <= 0).sum()),
                  tiny_area_threshold_mm2=AREA_LIMIT_MM2,
                  triangles_below_area_threshold=int((areas < AREA_LIMIT_MM2).sum()),
                  tiny_triangle_indices=np.flatnonzero(areas < AREA_LIMIT_MM2).tolist(),
                  material_counts=[{'slot': int(i), 'name': materials.get(i), 'polygons': int((polygon_materials == i).sum()),
                                    'triangles': int((triangle_materials == i).sum())} for i in sorted(set(polygon_materials))],
                  attributes={name: attribute_report(mesh, name) for name in required_attributes})
    after_geometry = time.perf_counter()
    images = [bpy.data.images[name] for name in args.atlas_name] if args.atlas_name else [
        image for image in bpy.data.images if tuple(image.size) == (3072, 2304)]
    report['atlases'] = [image_report(image) for image in images]
    after_atlas = time.perf_counter()
    if args.surface_distance:
        report['source_hull_distance'] = nearest_hull_by_material(obj, mm_per_bu, (a + b + c) / 3, triangle_materials, materials)
    if args.bulk_witness_mm:
        report['bulk_witness'] = bulk_witness(args.bulk_witness_mm, coords, triangles, labels)
    checks = {'blender_5_2_or_newer': bpy.app.version >= (5, 2, 0),
              'scripts_disabled': not bpy.context.preferences.filepaths.use_scripts_auto_execute,
              'one_mm_per_unit': math.isclose(mm_per_bu, 1.0, abs_tol=1e-6),
              'finite_vertices': bool(np.isfinite(coords).all()), 'one_connected_component': len(counts) == 1,
              'closed_manifold_edges': report['nonmanifold_edges'] == 0,
              'manifold_vertices': nonmanifold_vertices == 0,
              'consistent_edge_winding': report['inconsistent_winding_edges'] == 0,
              'positive_signed_volume': report['signed_volume_mm3'] > 0,
              'all_triangle_areas_at_least_1e_10_mm2': report['triangles_below_area_threshold'] == 0,
              'atlas_present': len(images) > 0, 'atlas_pixels_finite': all(im['finite_pixels'] for im in report['atlases'])}
    if args.pose != 'whole':
        checks['required_rest_attributes_present_and_finite'] = all(
            attr.get('present') and attr.get('finite') for attr in report['attributes'].values())
    for expected, key, field in ((args.expect_scene_sha256, 'source_sha_matches', None),
                                 (args.expect_R_sha256, 'atlas_R_sha_matches', 'R_sha256_float32_le'),
                                 (args.expect_GBA_sha256, 'atlas_GBA_sha_matches', 'GBA_sha256_float32_le'),
                                 (args.expect_BA_sha256, 'atlas_BA_sha_matches', 'BA_sha256_float32_le')):
        if expected:
            checks[key] = report['scene_sha256'] == expected if field is None else bool(report['atlases']) and all(im.get(field) == expected for im in report['atlases'])
    if args.bulk_witness_mm:
        checks['bulk_witness_inside_main_component'] = report['bulk_witness']['inside_largest_component'] is True
    report['checks'] = checks
    report['status'] = 'PASS_FOR_TESTED_POSE' if all(checks.values()) else 'FAIL'
    report['timing_seconds'] = {'from_script_start_including_open_and_updates': time.perf_counter() - START,
                                'open_mainfile': after_load - before_load, 'frame_set': after_frame - before_frame,
                                'pose_update_and_evaluated_mesh': after_evaluation - after_frame,
                                'mesh_analysis': after_geometry - after_evaluation,
                                'atlas_read_and_hash': after_atlas - after_geometry,
                                'optional_distance_and_witness': time.perf_counter() - after_atlas}
    report['timing_limit'] = 'Includes file open/frame changes/depsgraph evaluation, excludes Blender process startup and final JSON write; frame_set may evaluate multiple visible scene objects.'
    report['maxrss_kib_linux'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    evaluated.to_mesh_clear()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print('INDEPENDENT_QA', json.dumps({'pose': args.pose, 'status': report['status'], 'report': str(args.output),
          'components': report['connected_components'], 'tiny_triangles': report['triangles_below_area_threshold'],
          'failed_checks': [key for key, value in checks.items() if not value]}, ensure_ascii=False), flush=True)
    return 0 if all(checks.values()) else 2


if __name__ == '__main__':
    sys.exit(main())

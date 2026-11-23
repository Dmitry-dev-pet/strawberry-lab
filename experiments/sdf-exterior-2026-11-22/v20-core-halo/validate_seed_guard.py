"""Read-only v20B regression: evaluated seed vertices vs the actual cutter BVH.

Run in a fresh Blender process with --factory-startup --disable-autoexec.
Four finite poses only. The inherited -0.0002 cutter-local nearest-normal
threshold is preserved. This is not a triangle/triangle intersection test,
an exhaustive inside/outside proof, or a seed-to-body attachment test.

Optional --source compares raw seed mesh coordinates, topology, material
indices and achene_center attributes against the saved v19A input.
"""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

import bpy
import bmesh
import numpy as np
from mathutils.bvhtree import BVHTree


TOLERANCE_CUTTER_LOCAL = -0.0002
SEED_NAMES = ['SDF visible seeds | planar', 'SDF visible seeds | bite']
V19A_SHA256 = 'd89dd750f6f97bd7e85bce55eae0fb58af7d2a1dee9d07dc503932258a8b8110'


def file_sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def array_sha256(collection, field, width, dtype):
    values = np.empty(len(collection) * width, dtype=dtype)
    collection.foreach_get(field, values)
    return hashlib.sha256(values.tobytes()).hexdigest()


def raw_seed_inputs():
    result = {}
    for name in SEED_NAMES:
        obj = bpy.data.objects[name]
        assert obj.type == 'MESH', name
        mesh = obj.data
        center = mesh.attributes.get('achene_center')
        assert center is not None and center.data_type == 'FLOAT_VECTOR', name
        result[name] = {
            'vertices': len(mesh.vertices),
            'edges': len(mesh.edges),
            'polygons': len(mesh.polygons),
            'vertices_sha256_float32_le': array_sha256(mesh.vertices, 'co', 3, '<f4'),
            'edges_sha256_int32_le': array_sha256(mesh.edges, 'vertices', 2, '<i4'),
            'loop_vertices_sha256_int32_le': array_sha256(mesh.loops, 'vertex_index', 1, '<i4'),
            'polygon_starts_sha256_int32_le': array_sha256(mesh.polygons, 'loop_start', 1, '<i4'),
            'polygon_sizes_sha256_int32_le': array_sha256(mesh.polygons, 'loop_total', 1, '<i4'),
            'material_indices_sha256_int32_le': array_sha256(mesh.polygons, 'material_index', 1, '<i4'),
            'achene_center_domain': center.domain,
            'achene_center_count': len(center.data),
            'achene_center_sha256_float32_le': array_sha256(center.data, 'vector', 3, '<f4'),
        }
    return result


def open_without_scripts(path):
    bpy.context.preferences.filepaths.use_scripts_auto_execute = False
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False, use_scripts=False)
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scene', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--source', type=Path, help='Optional pinned original v19A scene for raw seed input comparison.')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    scene_path = args.scene.expanduser().resolve(strict=True)
    started = time.perf_counter()
    assert bpy.app.version >= (5, 2, 0), bpy.app.version_string
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute, 'Start Blender with --disable-autoexec'
    reference = None
    if args.source:
        source = args.source.expanduser().resolve(strict=True)
        digest = file_sha256(source)
        assert digest == V19A_SHA256, 'The optional source must be the pinned original v19A scene'
        open_without_scripts(source)
        assert bpy.context.scene.get('v19_variant') == 'a'
        reference = {'scene': str(source), 'sha256': digest, 'raw_seed_inputs': raw_seed_inputs()}
    open_without_scripts(scene_path)
    scene = bpy.context.scene
    assert scene.get('v20_variant') == 'b', 'This finite regression targets saved v20B'
    report = {
        'schema': 'strawberry-v20-seed-guard/v1',
        'scene': str(scene_path),
        'scene_sha256': file_sha256(scene_path),
        'variant': scene['v20_variant'],
        'blender': bpy.app.version_string,
        'build_hash': bpy.app.build_hash.decode(),
        'auto_execute_scripts': bpy.context.preferences.filepaths.use_scripts_auto_execute,
        'tolerance_cutter_local': TOLERANCE_CUTTER_LOCAL,
        'method': 'Every evaluated seed vertex queried against evaluated cutter BVH; nearest-surface normal signed dot product in cutter-local coordinates.',
        'limitations': [
            'Four specified cutter poses only; no universal cutter regression proof.',
            'Nearest-normal vertex test, not exhaustive inside/outside or triangle/triangle intersection proof.',
            'No seed-to-body attachment test; calyx and stem are outside this check.',
            'Tolerance is in cutter-local units, not a fixed world-space millimetre distance.',
        ],
        'raw_seed_inputs': raw_seed_inputs(),
        'reference': reference,
        'poses': {},
    }
    for tag, frame in [('planar', 20), ('bite', 40)]:
        cutter = bpy.data.objects['SDF cutter | ' + ('planar (move or rotate)' if tag == 'planar' else 'spherical bite (move or scale)')]
        seeds = bpy.data.objects['SDF visible seeds | ' + tag]
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        base_location = cutter.location.copy()
        base_rotation = cutter.rotation_euler.copy()
        base_scale = cutter.scale.copy()
        for pose in ('original', 'moved'):
            # Establish the animation frame BEFORE modifying the test cutter.
            scene.frame_set(frame)
            cutter.location = base_location
            cutter.rotation_euler = base_rotation
            cutter.scale = base_scale
            if pose == 'moved':
                if tag == 'planar':
                    cutter.location.y += 3.0
                    cutter.rotation_euler.x += 0.1745329252
                else:
                    cutter.location.x -= 4.0
                    cutter.scale *= 1.13
            bpy.context.view_layer.update()
            graph = bpy.context.evaluated_depsgraph_get()
            graph.update()
            evaluated_cutter = cutter.evaluated_get(graph)
            evaluated_seeds = seeds.evaluated_get(graph)
            cutter_mesh = evaluated_cutter.to_mesh()
            seed_mesh = evaluated_seeds.to_mesh()
            bm = bmesh.new()
            try:
                bm.from_mesh(cutter_mesh)
                bm.normal_update()
                assert len(bm.faces) and all(edge.is_manifold for edge in bm.edges), 'Cutter must be a closed manifold'
                tree = BVHTree.FromBMesh(bm)
                transform = evaluated_cutter.matrix_world.inverted_safe() @ evaluated_seeds.matrix_world
                checked = inside = 0
                minimum_signed = float('inf')
                for vertex in seed_mesh.vertices:
                    query = transform @ vertex.co
                    near = tree.find_nearest(query)
                    if near and near[0] is not None:
                        point, normal, _, _ = near
                        checked += 1
                        signed = (query - point).dot(normal)
                        minimum_signed = min(minimum_signed, signed)
                        if signed < TOLERANCE_CUTTER_LOCAL:
                            inside += 1
                key = tag + '_' + pose
                row = {
                    'frame': frame,
                    'evaluated_seed_vertices': len(seed_mesh.vertices),
                    'checked_seed_vertices': checked,
                    'strictly_inside_cutter_vertices': inside,
                    'minimum_signed_nearest_normal_cutter_local': minimum_signed if checked else None,
                    'evaluated_cutter_vertices': len(cutter_mesh.vertices),
                    'cutter_matrix_world': [list(row) for row in evaluated_cutter.matrix_world],
                    'seed_matrix_world': [list(row) for row in evaluated_seeds.matrix_world],
                }
                report['poses'][key] = row
                print('V20_SEED', key, checked, inside, flush=True)
            finally:
                bm.free()
                evaluated_cutter.to_mesh_clear()
                evaluated_seeds.to_mesh_clear()
        cutter.location = base_location
        cutter.rotation_euler = base_rotation
        cutter.scale = base_scale
        bpy.context.view_layer.update()
    report['checks'] = {
        'scripts_disabled': not bpy.context.preferences.filepaths.use_scripts_auto_execute,
        'four_poses_evaluated': len(report['poses']) == 4,
        'all_seed_vertices_checked': all(row['checked_seed_vertices'] == row['evaluated_seed_vertices'] and row['checked_seed_vertices'] > 0 for row in report['poses'].values()),
        'zero_vertices_inside_cutter_at_inherited_tolerance': all(row['strictly_inside_cutter_vertices'] == 0 for row in report['poses'].values()),
    }
    if reference:
        report['checks']['raw_seed_inputs_identical_to_pinned_v19a'] = reference['raw_seed_inputs'] == report['raw_seed_inputs']
    report['total_checked_seed_vertices'] = sum(row['checked_seed_vertices'] for row in report['poses'].values())
    report['status'] = 'PASS_FOR_FOUR_TESTED_POSES' if all(report['checks'].values()) else 'FAIL'
    report['seconds_including_loads_and_updates'] = time.perf_counter() - started
    report['maxrss_kib_linux'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print('V20_SEED_GUARD', report['status'], report['total_checked_seed_vertices'], flush=True)
    return 0 if all(report['checks'].values()) else 2


if __name__ == '__main__':
    sys.exit(main())

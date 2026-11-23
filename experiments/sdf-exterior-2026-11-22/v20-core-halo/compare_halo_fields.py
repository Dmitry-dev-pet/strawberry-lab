"""Export real Blender geometry, then independently test core/halo A/B causality.

Blender: --python compare_halo_fields.py -- export --scene S --pose plane
         --npz E.npz --report E.json [--reference-scene original.blend]
Python:  compare_halo_fields.py compare A.npz B.npz --report comparison.json
         [--reference-report first-export-with-reference.json]

Export never saves the input scene. It temporarily bypasses only the final Set
Position in memory to observe the actual undisplaced positions and normals.
Comparison needs NumPy only and never imports Blender.
"""
import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

ORIGINAL_ATLAS = 'V19 | rooted 264-seed graph 192^3 rest R (ARTIST)'
ORIGINAL_PACKED_SHA = '02d8abd338b590451e0396a2e453e443aa60bfa1656f1f01ab2c1edaad238d65'
ATTRIBUTES = {
    'rest': 'fruit_rest', 'core': 'v8_vascular_intensity', 'cell': 'v8_cell_height_mm',
    'halo': 'v20_halo', 'suppression': 'v20_cell_suppression',
    'ridge': 'v20_ridge_height_mm', 'total': 'v20_total_height_mm',
    'cap_rim': 'v20_cap_rim', 'stored_normal': 'v20_rest_normal',
}
POSITION_TOLERANCE_MM = 1e-5  # Float32 position writeback at a ~48 mm scene extent.
FIELD_TOLERANCE = 3e-7


def file_hash(path):
    sha = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            sha.update(chunk)
    return sha.hexdigest()


def array_hash(values):
    return hashlib.sha256(np.ascontiguousarray(values).tobytes()).hexdigest()


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def get_array(collection, property_name, width, dtype):
    result = np.empty(len(collection) * width, dtype=dtype)
    collection.foreach_get(property_name, result)
    return result.reshape(-1, width) if width > 1 else result


def mesh_arrays(mesh, with_attributes):
    result = {
        'positions': get_array(mesh.vertices, 'co', 3, np.float32),
        'normals': get_array(mesh.vertices, 'normal', 3, np.float32),
        'edges': get_array(mesh.edges, 'vertices', 2, np.int32),
        'loop_vertices': get_array(mesh.loops, 'vertex_index', 1, np.int32),
        'polygon_starts': get_array(mesh.polygons, 'loop_start', 1, np.int32),
        'polygon_sizes': get_array(mesh.polygons, 'loop_total', 1, np.int32),
    }
    if with_attributes:
        for key, name in ATTRIBUTES.items():
            attribute = mesh.attributes.get(name)
            if attribute is None:
                raise RuntimeError('Missing evaluated attribute: ' + name)
            if attribute.domain != 'POINT':
                raise RuntimeError('Expected POINT attribute: ' + name)
            width = 3 if attribute.data_type == 'FLOAT_VECTOR' else 1
            result[key] = get_array(attribute.data, 'vector' if width == 3 else 'value', width, np.float32)
    return result


def safe_value(value):
    if isinstance(value, (str, bool, int)) or value is None:
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if hasattr(value, 'name_full'):
        return {'id_name': value.name_full, 'id_type': value.bl_rna.identifier}
    try:
        return [safe_value(v) for v in value]
    except TypeError:
        return None


def material_snapshot(bpy):
    """Functional node properties, socket defaults, links and recursive groups."""
    groups = {}
    irrelevant = {'rna_type', 'type', 'dimensions', 'location', 'width', 'height', 'select',
                  'show_options', 'show_preview', 'show_texture', 'hide', 'label', 'color',
                  'use_custom_color', 'parent', 'warning_propagation'}

    def graph(tree, key):
        if key in groups:
            return key
        groups[key] = None
        nodes = []
        for node in tree.nodes:
            properties = {}
            for prop in node.bl_rna.properties:
                if prop.identifier in irrelevant or prop.is_readonly:
                    continue
                if prop.type in {'STRING', 'BOOLEAN', 'INT', 'FLOAT', 'ENUM'}:
                    properties[prop.identifier] = safe_value(getattr(node, prop.identifier))
            item = {'name': node.name, 'type': node.bl_idname, 'properties': properties,
                    'inputs': [(socket.identifier, safe_value(socket.default_value) if hasattr(socket, 'default_value') else None)
                               for socket in node.inputs]}
            if hasattr(node, 'image'):
                item['image'] = node.image.name if node.image else None
            if hasattr(node, 'color_ramp'):
                ramp = node.color_ramp
                item['ramp'] = {'interpolation': ramp.interpolation, 'color_mode': ramp.color_mode,
                                'hue_interpolation': ramp.hue_interpolation,
                                'elements': [(e.position, list(e.color)) for e in ramp.elements]}
            if getattr(node, 'node_tree', None):
                item['group'] = graph(node.node_tree, 'group:' + node.node_tree.name)
            nodes.append(item)
        groups[key] = {'nodes': sorted(nodes, key=lambda x: x['name']),
                             'links': sorted((link.from_node.name, link.from_socket.identifier,
                                              link.to_node.name, link.to_socket.identifier) for link in tree.links)}
        return key

    materials = {}
    for material in bpy.data.materials:
        materials[material.name] = {'use_nodes': material.use_nodes,
                                    'diffuse_color': list(material.diffuse_color),
                                    'metallic': material.metallic, 'roughness': material.roughness,
                                    'graph': graph(material.node_tree, 'material:' + material.name) if material.use_nodes else None}
    data = {'materials': materials, 'graphs': groups}
    return {'sha256': canonical_hash(data), 'material_count': len(materials), 'shader_tree_count': len(groups), 'data': data}


def packed_images(bpy):
    result = {}
    for image in bpy.data.images:
        if tuple(image.size) != (3072, 2304):
            continue
        result[image.name] = {'size': list(image.size), 'packed_sha256': hashlib.sha256(image.packed_file.data).hexdigest()
                              if image.packed_file else None, 'packed_bytes': image.packed_file.size if image.packed_file else None}
    return result


def native_route(group):
    output = next(node for node in group.nodes if node.bl_idname == 'NodeGroupOutput' and node.is_active_output)
    reachable = set()

    def visit(node):
        if node.name in reachable:
            return
        reachable.add(node.name)
        for socket in node.inputs:
            for link in socket.links:
                visit(link.from_node)
    visit(output)
    nodes = [group.nodes[name] for name in sorted(reachable)]
    grid = group.nodes.get('Grid to Mesh')
    native_boolean = grid is not None and grid.name in reachable and any(
        link.from_node.bl_idname == 'GeometryNodeSDFGridBoolean' and link.from_node.operation == 'DIFFERENCE'
        for link in grid.inputs['Grid'].links)
    return {'reachable_node_count': len(nodes), 'native_grid_to_mesh_from_sdf_difference': native_boolean,
            'reachable_volume_cube_or_to_mesh': [n.name for n in nodes if n.bl_idname in {'GeometryNodeVolumeCube', 'GeometryNodeVolumeToMesh'}],
            'reachable_v18_v19_operations': [n.name for n in nodes if n.name.startswith(('V18', 'V19')) or n.label.startswith(('V18', 'V19'))],
            'all_reachable_nodes': [(n.name, n.bl_idname) for n in nodes]}


def export(args):
    import bpy
    start = time.perf_counter()
    scene_path = args.scene.resolve(strict=True)
    bpy.context.preferences.filepaths.use_scripts_auto_execute = False
    bpy.ops.wm.open_mainfile(filepath=str(scene_path), use_scripts=False, load_ui=False)
    scene = bpy.context.scene
    scene.frame_set(20 if args.pose == 'plane' else 40)
    bpy.context.view_layer.update()
    tag = 'planar' if args.pose == 'plane' else 'bite'
    obj = bpy.data.objects['SDF visible body | ' + tag]
    group = bpy.data.node_groups['SDF cutter + rest-space | ' + tag]
    map_range = group.nodes['Map Range.001']
    metadata = {'schema': 'strawberry-halo-causality-export/v1', 'scene': str(scene_path), 'scene_sha256': file_hash(scene_path),
                'pose': args.pose, 'variant': str(scene.get('v20_variant', 'UNSET')), 'blender': bpy.app.version_string,
                'scripts_disabled': not bpy.context.preferences.filepaths.use_scripts_auto_execute,
                'mm_per_blender_unit': scene.unit_settings.scale_length * 1000,
                'matrix_world': list(map(list, obj.matrix_world)), 'native_route': native_route(group),
                'cell_strength': group.nodes['V8_CELL_STRENGTH'].outputs[0].default_value,
                'ridge_gain_mm': group.nodes['V20_RIDGE_GAIN_MM'].outputs[0].default_value,
                'broad_halo': group.nodes['V20_USE_BROAD_HALO'].boolean,
                'suppression_map': {'from_min': map_range.inputs['From Min'].default_value,
                                    'from_max': map_range.inputs['From Max'].default_value,
                                    'to_min': map_range.inputs['To Min'].default_value,
                                    'to_max': map_range.inputs['To Max'].default_value,
                                    'clamp': map_range.clamp, 'interpolation': map_range.interpolation_type},
                'images': packed_images(bpy), 'materials': material_snapshot(bpy)}

    def evaluate(with_attributes):
        graph = bpy.context.evaluated_depsgraph_get()
        graph.update()
        evaluated = obj.evaluated_get(graph)
        mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=graph)
        try:
            return mesh_arrays(mesh, with_attributes)
        finally:
            evaluated.to_mesh_clear()

    result = evaluate(True)
    output = next(node for node in group.nodes if node.bl_idname == 'NodeGroupOutput' and node.is_active_output)
    output_socket = output.inputs['Geometry']
    original_sources = [link.from_socket for link in output_socket.links]
    set_position = group.nodes['V8 | actual cut cell pillows']
    base_source = set_position.inputs['Geometry'].links[0].from_socket
    try:
        group.links.new(base_source, output_socket)
        group.update_tag()
        obj.update_tag()
        bpy.context.view_layer.update()
        base = evaluate(False)
    finally:
        for link in list(output_socket.links):
            group.links.remove(link)
        for socket in original_sources:
            group.links.new(socket, output_socket)
        group.update_tag()
        obj.update_tag()
    for key, value in base.items():
        result['base_' + key] = value
    metadata['all_arrays_finite'] = all(np.isfinite(value).all().item() for value in result.values())
    metadata['vertices'] = len(result['positions'])
    metadata['array_sha256'] = {key: array_hash(value) for key, value in result.items()}
    if args.reference_scene:
        reference = args.reference_scene.resolve(strict=True)
        bpy.ops.wm.open_mainfile(filepath=str(reference), use_scripts=False, load_ui=False)
        metadata['reference'] = {'scene': str(reference), 'scene_sha256': file_hash(reference),
                                  'images': packed_images(bpy), 'materials': material_snapshot(bpy)}
    metadata['elapsed_seconds_including_open_and_base_evaluation'] = time.perf_counter() - start
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.npz.parent.mkdir(parents=True, exist_ok=True)
    result['metadata_json'] = np.array(json.dumps(metadata, ensure_ascii=False, sort_keys=True))
    np.savez_compressed(args.npz, **result)
    args.report.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('FIELD_EXPORT', json.dumps({'scene': scene_path.name, 'pose': args.pose, 'vertices': metadata['vertices'],
                                     'npz': str(args.npz), 'seconds': metadata['elapsed_seconds_including_open_and_base_evaluation']}), flush=True)
    return 0


def max_abs(value):
    return float(np.max(np.abs(value))) if value.size else 0.0


def max_norm(value):
    return float(np.max(np.linalg.norm(value, axis=1))) if len(value) else 0.0


def map_expected(value, settings):
    t = (value.astype(np.float64) - settings['from_min']) / (settings['from_max'] - settings['from_min'])
    if settings['clamp'] or settings['interpolation'] in {'SMOOTHSTEP', 'SMOOTHERSTEP'}:
        t = np.clip(t, 0, 1)
    if settings['interpolation'] == 'SMOOTHSTEP':
        t = t * t * (3 - 2 * t)
    elif settings['interpolation'] == 'SMOOTHERSTEP':
        t = t ** 3 * (t * (t * 6 - 15) + 10)
    elif settings['interpolation'] != 'LINEAR':
        raise RuntimeError('Independent map evaluator does not support ' + settings['interpolation'])
    return settings['to_min'] + t * (settings['to_max'] - settings['to_min'])


def compare(args):
    with np.load(args.a, allow_pickle=False) as z:
        a = {key: z[key] for key in z.files}
    with np.load(args.b, allow_pickle=False) as z:
        b = {key: z[key] for key in z.files}
    ma, mb = (json.loads(str(x['metadata_json'])) for x in (a, b))
    reference = ma.get('reference') or mb.get('reference')
    if reference is None and args.reference_report:
        reference = json.loads(args.reference_report.read_text()).get('reference')
    checks = {'same_pose': ma['pose'] == mb['pose'], 'correct_A_B_toggle': not ma['broad_halo'] and mb['broad_halo'],
              'both_scripts_disabled': ma['scripts_disabled'] and mb['scripts_disabled'],
              'same_vertex_count': len(a['positions']) == len(b['positions']),
              'all_exported_arrays_finite': ma['all_arrays_finite'] and mb['all_arrays_finite'],
              'same_object_transform_and_scale': ma['matrix_world'] == mb['matrix_world'] and ma['mm_per_blender_unit'] == mb['mm_per_blender_unit'],
              'unchanged_cell_strength_one': ma['cell_strength'] == mb['cell_strength'] == 1.0,
              'same_ridge_gain_0_18': ma['ridge_gain_mm'] == mb['ridge_gain_mm'] and abs(ma['ridge_gain_mm'] - .18) < 1e-7,
              'same_suppression_map': ma['suppression_map'] == mb['suppression_map'],
              'same_original_and_geometry_atlases': ma['images'] == mb['images'],
              'original_packed_atlas_matches_verified_v19': all(m['images'][ORIGINAL_ATLAS]['packed_sha256'] == ORIGINAL_PACKED_SHA for m in (ma, mb)),
              'same_material_shader_graphs': ma['materials']['sha256'] == mb['materials']['sha256'],
              'materials_equal_to_original_reference': reference is not None and ma['materials']['sha256'] == reference['materials']['sha256'] == mb['materials']['sha256'],
              'native_SDF_no_resampled_volume_or_tube_union': all(m['native_route']['native_grid_to_mesh_from_sdf_difference'] and
                  not m['native_route']['reachable_volume_cube_or_to_mesh'] and not m['native_route']['reachable_v18_v19_operations'] for m in (ma, mb))}
    metrics = {}
    for key in ('edges', 'loop_vertices', 'polygon_starts', 'polygon_sizes', 'base_positions', 'base_normals',
                'rest', 'core', 'halo', 'ridge', 'cap_rim', 'stored_normal'):
        checks['identical_' + key] = np.array_equal(a[key], b[key])
    for prefix, values in (('A', a), ('B', b)):
        for key in ('edges', 'loop_vertices', 'polygon_starts', 'polygon_sizes'):
            checks[prefix + '_base_and_final_same_' + key] = np.array_equal(values[key], values['base_' + key])
    if not checks['same_vertex_count']:
        report = {'status': 'FAIL', 'checks': checks, 'reason': 'Vertex alignment cannot be assumed; scalar causality comparison skipped.'}
    else:
        normal = a['stored_normal'].astype(np.float64)
        matrix = np.asarray(ma['matrix_world'], np.float64)[:3, :3] * ma['mm_per_blender_unit']
        delta = b['positions'].astype(np.float64) - a['positions'].astype(np.float64)
        height_delta = b['cell'].astype(np.float64) - a['cell'].astype(np.float64)
        expected = normal * height_delta[:, None]
        delta_world = delta @ matrix.T
        expected_world = expected @ matrix.T
        height_gain_violation = np.abs(b['cell']) - np.abs(a['cell'])
        metrics.update(vertices=len(delta), max_cell_amplitude_A_mm=max_abs(a['cell']), max_cell_amplitude_B_mm=max_abs(b['cell']),
                       max_cell_amplitude_increase_B_mm=float(height_gain_violation.max()),
                       vertices_with_cell_amplitude_increase_over_1e_8=int((height_gain_violation > 1e-8).sum()),
                       maximum_position_change_mm=max_norm(delta_world),
                       maximum_predicted_change_mm=max_norm(expected_world),
                       maximum_displacement_causality_error_mm=max_norm(delta_world - expected_world),
                       maximum_scalar_norm_error_local_mm=max_abs(np.linalg.norm(delta, axis=1) * ma['mm_per_blender_unit'] - np.abs(height_delta)),
                       changed_vertices_over_1e_6_mm=int((np.linalg.norm(delta_world, axis=1) > 1e-6).sum()),
                       halo_minus_core_minimum=float((a['halo'] - a['core']).min()),
                       stored_vs_independent_base_normal_max_error=max_norm(normal - a['base_normals'].astype(np.float64)),
                       unsuppressed_cell_field_max_difference_mm=max_abs(a['cell'] / a['suppression'] - b['cell'] / b['suppression']))
        checks['halo_not_below_core'] = metrics['halo_minus_core_minimum'] >= -FIELD_TOLERANCE
        checks['B_never_increases_absolute_cell_height'] = metrics['vertices_with_cell_amplitude_increase_over_1e_8'] == 0
        checks['actual_nonzero_geometry_difference'] = metrics['maximum_position_change_mm'] > POSITION_TOLERANCE_MM
        checks['position_difference_explained_by_cell_suppression'] = metrics['maximum_displacement_causality_error_mm'] <= POSITION_TOLERANCE_MM
        checks['scalar_delta_norm_matches_cell_height_delta'] = metrics['maximum_scalar_norm_error_local_mm'] <= POSITION_TOLERANCE_MM
        checks['stored_normal_matches_independently_evaluated_base'] = metrics['stored_vs_independent_base_normal_max_error'] <= 1e-6
        checks['same_underlying_unsuppressed_cell_field'] = metrics['unsuppressed_cell_field_max_difference_mm'] <= 1e-7
        region = (a['halo'] > a['core'] + .05) & (a['cap_rim'] > .1) & (np.abs(a['cell']) > 1e-6)
        metrics['halo_region_vertices'] = int(region.sum())
        if np.any(region):
            ratios = np.abs(b['cell'][region]) / np.abs(a['cell'][region])
            metrics['halo_region_abs_height_ratio_B_over_A_median'] = float(np.median(ratios))
            metrics['halo_region_abs_height_ratio_B_over_A_mean'] = float(ratios.mean())
            metrics['halo_region_mean_abs_height_A_mm'] = float(np.abs(a['cell'][region]).mean())
            metrics['halo_region_mean_abs_height_B_mm'] = float(np.abs(b['cell'][region]).mean())
        for label, values, meta, selected in (('A', a, ma, a['core']), ('B', b, mb, b['halo'])):
            positions = values['positions'].astype(np.float64)
            base = values['base_positions'].astype(np.float64)
            predicted_total = values['stored_normal'].astype(np.float64) * values['total'].astype(np.float64)[:, None]
            errors = {'total_height_sum_error_mm': max_abs(values['total'] - values['cell'] - values['ridge']),
                      'ridge_formula_error_mm': max_abs(values['ridge'].astype(np.float64) - meta['ridge_gain_mm'] * values['core'] * values['cap_rim']),
                      'suppression_formula_error': max_abs(values['suppression'] - map_expected(selected, meta['suppression_map'])),
                      'total_displacement_error_mm': max_norm(((positions - base) - predicted_total) @ matrix.T),
                      'fruit_rest_vs_base_position_max_mm': max_norm((values['rest'].astype(np.float64) - base) @ matrix.T)}
            metrics[label] = errors
            checks[label + '_total_equals_cell_plus_ridge'] = errors['total_height_sum_error_mm'] <= 1e-7
            checks[label + '_ridge_matches_core_and_cap'] = errors['ridge_formula_error_mm'] <= 1e-7
            checks[label + '_suppression_matches_selected_field'] = errors['suppression_formula_error'] <= FIELD_TOLERANCE
            checks[label + '_actual_total_displacement_matches_reported_height'] = errors['total_displacement_error_mm'] <= POSITION_TOLERANCE_MM
        report = {'schema': 'strawberry-halo-causality-comparison/v1', 'pose': ma['pose'],
                  'source_A': {'scene': ma['scene'], 'sha256': ma['scene_sha256']},
                  'source_B': {'scene': mb['scene'], 'sha256': mb['scene_sha256']},
                  'status': 'PASS_FOR_TESTED_POSE' if all(checks.values()) else 'FAIL', 'checks': checks, 'metrics': metrics,
                  'tolerances': {'position_mm': POSITION_TOLERANCE_MM, 'field': FIELD_TOLERANCE},
                  'interpretation': 'A/B geometry difference is tested against exported fields and independently evaluated undisplaced geometry; this is not visual or biological acceptance.',
                  'limitations': 'Stored pre-normal is independently compared against base mesh normals. Material snapshot covers functional node properties, defaults, links and nested groups, not a rendered-color equivalence test. Float32 writeback bounds the positional tolerance.'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    print('FIELD_COMPARISON', json.dumps({'status': report['status'], 'pose': ma['pose'], 'failed_checks': [key for key, value in checks.items() if not value],
                                       'report': str(args.report), 'metrics': metrics}), flush=True)
    return 0 if all(checks.values()) else 2


def main():
    arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    e = sub.add_parser('export')
    e.add_argument('--scene', type=Path, required=True)
    e.add_argument('--pose', choices=['plane', 'bite'], required=True)
    e.add_argument('--npz', type=Path, required=True)
    e.add_argument('--report', type=Path, required=True)
    e.add_argument('--reference-scene', type=Path)
    c = sub.add_parser('compare')
    c.add_argument('a', type=Path)
    c.add_argument('b', type=Path)
    c.add_argument('--report', type=Path, required=True)
    c.add_argument('--reference-report', type=Path)
    args = parser.parse_args(arguments)
    return export(args) if args.command == 'export' else compare(args)


if __name__ == '__main__':
    sys.exit(main())

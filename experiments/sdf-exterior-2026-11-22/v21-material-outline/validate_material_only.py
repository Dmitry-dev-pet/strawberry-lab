"""Independent saved-scene regression for one existing material socket change.

Only the named scalar socket may differ in the inspected scene structure.
Exact evaluated body/seed signatures transfer previous geometric QA only for
the three tested poses; this does not establish realism or all-pose validity.
Scene provenance custom properties and editor layout are outside this contract.
The default target SHA pins the delivered artifact. For a rebuilt target, pass
--expected-target-sha with the independent SHA recorded in its build receipt;
the validator never derives an expected SHA from the file it is validating.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import resource
import sys
import time

import bpy
import numpy as np


SOURCE_SHA = '35fd1d81c51aea1cc8f4cd71c39a2815da87a1137056d32c3f78d4ab1cf649e4'
TARGET_SHA = '92e7e288f7851ec8c5e68897d5f7f19b5b5f73310a6d7d9084836f854c258a13'
MATERIAL = 'SDF v12 | continuous vascular fibers, restrained wetness (ARTIST)'
POSES = ('plane', 'bite', 'plane_rotated')
UI_PROPERTIES = {'rna_type', 'location', 'width', 'height', 'dimensions', 'select', 'hide', 'show_options', 'show_preview', 'show_texture', 'use_custom_color', 'color', 'bl_description', 'bl_label', 'bl_icon', 'bl_static_type'}


def file_digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def sha256_argument(value):
    if re.fullmatch(r'[0-9a-fA-F]{64}', value) is None:
        raise argparse.ArgumentTypeError('Expected exactly 64 hexadecimal characters')
    return value.lower()


def canonical(value):
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else repr(value)
    if isinstance(value, bpy.types.ID):
        return {'id_type': value.bl_rna.identifier, 'name': value.name}
    if isinstance(value, bpy.types.Node):
        return {'node': value.name}
    if hasattr(value, 'to_dict'):
        return {str(k): canonical(v) for k, v in value.to_dict().items()}
    if isinstance(value, dict):
        return {str(k): canonical(v) for k, v in value.items()}
    if isinstance(value, set):
        return sorted(canonical(v) for v in value)
    if hasattr(value, '__iter__'):
        return [canonical(v) for v in value]
    return {'rna_class': getattr(getattr(value, 'bl_rna', None), 'identifier', type(value).__name__)}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def primitive_properties(value, *, node_ui=False):
    result = {}
    for prop in value.bl_rna.properties:
        key = prop.identifier
        if prop.is_readonly or key == 'rna_type' or (node_ui and key in UI_PROPERTIES):
            continue
        if prop.type in {'BOOLEAN', 'INT', 'FLOAT', 'STRING', 'ENUM'}:
            result[key] = canonical(getattr(value, key))
        elif prop.type == 'POINTER':
            item = getattr(value, key)
            if item is None or isinstance(item, (bpy.types.ID, bpy.types.Node)):
                result[key] = canonical(item)
    return result


def array_digest(collection, field, width, dtype):
    values = np.empty(len(collection) * width, dtype=dtype)
    collection.foreach_get(field, values)
    return hashlib.sha256(values.tobytes()).hexdigest()


def mesh_signature(mesh, *, evaluated=False):
    result = {
        'vertices': len(mesh.vertices), 'edges': len(mesh.edges), 'polygons': len(mesh.polygons),
        'coords_f32': array_digest(mesh.vertices, 'co', 3, '<f4'),
        'edges_i32': array_digest(mesh.edges, 'vertices', 2, '<i4'),
        'loop_vertices_i32': array_digest(mesh.loops, 'vertex_index', 1, '<i4'),
        'polygon_starts_i32': array_digest(mesh.polygons, 'loop_start', 1, '<i4'),
        'polygon_sizes_i32': array_digest(mesh.polygons, 'loop_total', 1, '<i4'),
        'material_indices_i32': array_digest(mesh.polygons, 'material_index', 1, '<i4'),
        'materials': [material.name if material else None for material in mesh.materials],
    }
    # Named fields are hashed directly, not recomputed using the builder.
    fields = {'FLOAT': ('value', 1, '<f4'), 'FLOAT_VECTOR': ('vector', 3, '<f4'),
              'FLOAT_COLOR': ('color', 4, '<f4'), 'BYTE_COLOR': ('color', 4, '<f4'),
              'INT': ('value', 1, '<i4'), 'BOOLEAN': ('value', 1, '?'),
              'FLOAT2': ('vector', 2, '<f4'), 'INT32_2D': ('value', 2, '<i4')}
    attrs = {}
    for attr in mesh.attributes:
        if attr.name.startswith('.'):
            continue  # Blender internal caches are not source data in this contract.
        if attr.data_type not in fields:
            raise RuntimeError('Unsupported named mesh attribute type: ' + attr.data_type)
        field, width, dtype = fields[attr.data_type]
        attrs[attr.name] = {'type': attr.data_type, 'domain': attr.domain, 'count': len(attr.data),
                            'sha256': array_digest(attr.data, field, width, dtype)}
    result['named_attributes'] = attrs
    if evaluated:
        mesh.calc_loop_triangles()
        result['triangles'] = len(mesh.loop_triangles)
        result['triangles_i32'] = array_digest(mesh.loop_triangles, 'vertices', 3, '<i4')
    return result


def socket_signature(socket):
    result = {'name': socket.name, 'identifier': socket.identifier, 'type': socket.bl_idname,
              'linked': socket.is_linked, 'enabled': socket.enabled}
    if hasattr(socket, 'default_value'):
        result['default_value'] = canonical(socket.default_value)
    return result


def tree_signature(tree):
    nodes = {}
    for node in tree.nodes:
        row = {'type': node.bl_idname, 'properties': primitive_properties(node, node_ui=True),
               'inputs': [socket_signature(s) for s in node.inputs],
               'outputs': [socket_signature(s) for s in node.outputs]}
        if hasattr(node, 'color_ramp'):
            ramp = node.color_ramp
            row['color_ramp'] = {'settings': primitive_properties(ramp),
                                 'elements': [{'position': e.position, 'color': list(e.color)} for e in ramp.elements]}
        if hasattr(node, 'mapping') and hasattr(node.mapping, 'curves'):
            row['mapping'] = {'settings': primitive_properties(node.mapping),
                              'curves': [[{'location': list(p.location), 'handle_type': p.handle_type} for p in curve.points] for curve in node.mapping.curves]}
        nodes[node.name] = row
    links = sorted([link.from_node.name, link.from_socket.identifier, link.to_node.name, link.to_socket.identifier, link.is_muted] for link in tree.links)
    interface = []
    for item in tree.interface.items_tree:
        interface.append({'name': item.name, 'item_type': item.item_type,
                          'properties': primitive_properties(item)})
    return {'type': tree.bl_idname, 'nodes': nodes, 'links': links, 'interface': interface}


def structural_snapshot():
    scene = bpy.context.scene
    scene.frame_set(20)
    bpy.context.view_layer.update()
    objects = {}
    for obj in bpy.data.objects:
        modifiers = []
        for mod in obj.modifiers:
            row = {'name': mod.name, 'type': mod.type, 'properties': primitive_properties(mod)}
            if mod.type == 'NODES' and mod.node_group:
                values = {}
                for item in mod.node_group.interface.items_tree:
                    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                        value = getattr(mod.properties.inputs, item.identifier, None)
                        if value is not None and hasattr(value, 'value'):
                            values[item.identifier] = canonical(value.value)
                row['node_inputs'] = values
            modifiers.append(row)
        objects[obj.name] = {'type': obj.type, 'data': canonical(obj.data), 'parent': canonical(obj.parent),
                             'matrix_world': [list(row) for row in obj.matrix_world],
                             'matrix_parent_inverse': [list(row) for row in obj.matrix_parent_inverse],
                             'hide_render': obj.hide_render, 'hide_viewport': obj.hide_viewport,
                             'material_slots': [canonical(slot.material) for slot in obj.material_slots],
                             'modifiers': modifiers,
                             'constraints': [primitive_properties(c) for c in obj.constraints],
                             'action': canonical(obj.animation_data.action) if obj.animation_data else None}
    images = {}
    for image in bpy.data.images:
        if image.type in {'RENDER_RESULT', 'COMPOSITING'}:
            continue
        row = {'source': image.source, 'size': list(image.size), 'channels': image.channels,
               'colorspace': image.colorspace_settings.name, 'alpha_mode': image.alpha_mode,
               'packed': image.packed_file is not None}
        if image.packed_file:
            row['packed_sha256'] = hashlib.sha256(image.packed_file.data).hexdigest()
            row['packed_bytes'] = image.packed_file.size
        else:
            row['filepath'] = image.filepath
        images[image.name] = row
    return {
        'unit_scale': scene.unit_settings.scale_length,
        'objects': objects,
        'meshes': {mesh.name: mesh_signature(mesh) for mesh in bpy.data.meshes},
        'node_groups': {tree.name: tree_signature(tree) for tree in bpy.data.node_groups},
        'materials': {material.name: {'properties': primitive_properties(material), 'tree': tree_signature(material.node_tree) if material.use_nodes and material.node_tree else None} for material in bpy.data.materials},
        'images': images,
    }


def evaluated_pose(pose):
    scene = bpy.context.scene
    is_bite = pose == 'bite'
    scene.frame_set(40 if is_bite else 20)
    cutter = bpy.data.objects['SDF cutter | ' + ('spherical bite (move or scale)' if is_bite else 'planar (move or rotate)')]
    old_rotation = cutter.rotation_euler.copy()
    if pose == 'plane_rotated':
        cutter.rotation_euler.y += math.radians(20)
        cutter.rotation_euler.z += math.radians(30)
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    graph.update()
    tag = 'bite' if is_bite else 'planar'
    result = {'cutter_matrix_world': [list(row) for row in cutter.matrix_world]}
    for role, name in [('body', 'SDF visible body | ' + tag), ('seeds', 'SDF visible seeds | ' + tag)]:
        obj = bpy.data.objects[name].evaluated_get(graph)
        mesh = obj.to_mesh(preserve_all_data_layers=True, depsgraph=graph)
        try:
            result[role] = {'matrix_world': [list(row) for row in obj.matrix_world], 'mesh': mesh_signature(mesh, evaluated=True)}
        finally:
            obj.to_mesh_clear()
    cutter.rotation_euler = old_rotation
    return result


def differences(a, b, path=()):
    if isinstance(a, dict) and isinstance(b, dict):
        rows = []
        for key in sorted(set(a) | set(b)):
            rows += differences(a.get(key, '<ABSENT>'), b.get(key, '<ABSENT>'), path + (key,))
        return rows
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [item for i, (av, bv) in enumerate(zip(a, b)) for item in differences(av, bv, path + (i,))]
    return [] if a == b else [{'path': list(path), 'source': a, 'target': b}]


def selected_socket(snapshot):
    return snapshot['materials'][MATERIAL]['tree']['nodes']['Math.039']['inputs'][1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--target', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--expected-target-sha', type=sha256_argument, default=TARGET_SHA,
                        help='Expected target SHA from its build receipt; defaults to the exact delivered artifact.')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    assert bpy.app.version >= (5, 2, 0)
    t = time.perf_counter()
    snapshots, poses, actual_hashes = {}, {}, {}
    for label, path, expected in [('source', args.source, SOURCE_SHA), ('target', args.target, args.expected_target_sha)]:
        path = path.resolve(strict=True)
        actual_hashes[label] = file_digest(path)
        assert actual_hashes[label] == expected, label + ' file digest mismatch'
        bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False, use_scripts=False)
        assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
        assert bpy.context.scene.get('v20_variant') == 'b'
        snapshots[label] = structural_snapshot()
        poses[label] = {}
        for pose in POSES:
            poses[label][pose] = evaluated_pose(pose)
            print('MATERIAL_QA_EVALUATED', label, pose, flush=True)
    source_socket, target_socket = (selected_socket(snapshots[k]) for k in ('source', 'target'))
    socket_values = {'source': source_socket['default_value'], 'target': target_socket['default_value'],
                     'source_identifier': source_socket['identifier'], 'target_identifier': target_socket['identifier']}
    normalized = copy.deepcopy(snapshots)
    for snapshot in normalized.values():
        selected_socket(snapshot)['default_value'] = '<ONLY_ALLOWED_SHADER_CHANGE>'
    structural_diffs = differences(normalized['source'], normalized['target'])
    pose_diffs = {pose: differences(poses['source'][pose], poses['target'][pose]) for pose in POSES}
    checks = {
        'scripts_disabled': not bpy.context.preferences.filepaths.use_scripts_auto_execute,
        'expected_source_scalar': math.isclose(source_socket['default_value'], .10, rel_tol=1e-6, abs_tol=1e-8),
        'expected_target_scalar': math.isclose(target_socket['default_value'], .02, rel_tol=1e-6, abs_tol=1e-8),
        'edited_socket_unlinked': not source_socket['linked'] and not target_socket['linked'],
        'only_named_material_socket_differs_in_inspected_structure': not structural_diffs,
    }
    checks.update({pose + '_body_and_seeds_exactly_unchanged': not rows for pose, rows in pose_diffs.items()})
    report = {
        'schema': 'strawberry-v21-material-only-regression/v1',
        'status': 'PASS_FOR_INSPECTED_STRUCTURE_AND_THREE_POSES' if all(checks.values()) else 'FAIL',
        'source_scene': str(args.source.resolve()), 'target_scene': str(args.target.resolve()),
        'file_sha256': actual_hashes, 'blender': bpy.app.version_string, 'build_hash': bpy.app.build_hash.decode(),
        'expected_target_sha256': args.expected_target_sha,
        'allowed_change': {'material': MATERIAL, 'node': 'Math.039', 'input_index': 1, 'values': socket_values},
        'checks': checks,
        'structural_differences_after_masking_one_socket': structural_diffs,
        'pose_differences': pose_diffs,
        'structural_section_signatures': {label: {key: digest(value) for key, value in snapshot.items()} for label, snapshot in snapshots.items()},
        'structural_counts': {label: {key: len(value) for key, value in snapshot.items() if isinstance(value, dict)} for label, snapshot in snapshots.items()},
        'evaluated_poses': poses,
        'seconds_including_opens_updates_and_analysis': time.perf_counter() - t,
        'maxrss_kib_linux': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'limits': [
            'Exact geometry equality for three finite poses transfers previously measured v20 geometric properties for those poses; no universal cutter or realism claim.',
            'Scene provenance custom properties, editor node layout, internal dot-prefixed mesh caches and transient render-result images are intentionally excluded.',
            'Raw mesh geometry and named supported attributes, object references/transforms/modifiers/constraints/action references, GN/material node structure and packed image bytes are compared.',
            'Animation action contents and hidden curve control points are not exhaustively audited; tested evaluated meshes and cutter transforms must nevertheless match exactly.',
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print('MATERIAL_QA', report['status'], json.dumps(checks), flush=True)
    return 0 if all(checks.values()) else 2


if __name__ == '__main__':
    sys.exit(main())

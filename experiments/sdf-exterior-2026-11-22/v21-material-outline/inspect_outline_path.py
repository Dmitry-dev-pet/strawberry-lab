"""Read-only inspection of the owned v20B cell-color outline branch."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy

MATERIAL = 'SDF v12 | continuous vascular fibers, restrained wetness (ARTIST)'
SOURCE_SHA = '35fd1d81c51aea1cc8f4cd71c39a2815da87a1137056d32c3f78d4ab1cf649e4'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scene', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    source = args.scene.resolve(strict=True)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest == SOURCE_SHA
    bpy.context.preferences.filepaths.use_scripts_auto_execute = False
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    group = bpy.data.materials[MATERIAL].node_tree
    gain = group.nodes['Math.039']
    assert gain.operation == 'MULTIPLY' and not gain.inputs[1].is_linked
    assert abs(gain.inputs[1].default_value - .1) < 1e-7
    chosen = ['Attribute', 'Voronoi Texture', 'Map Range', 'Math.039', 'Mix (Legacy).004',
              'Separate Color', 'Math.033', 'Mix (Legacy).001', 'Mix (Legacy).002',
              'Mix (Legacy).003', 'Map Range.001', 'Bump', 'Bump.001',
              'Voronoi Texture.001', 'Voronoi Texture.002', 'Math.034', 'Math.035',
              'Math.036', 'Math.037', 'Math.038', 'Vector Math.001', 'Noise Texture',
              'Map Range.003', 'Math.040', 'Math.041', 'Principled BSDF']
    nodes = []
    for name in chosen:
        node = group.nodes[name]
        row = {'name': name, 'type': node.bl_idname, 'label': node.label}
        for prop in ['operation', 'blend_type', 'feature', 'voronoi_dimensions', 'interpolation_type', 'clamp', 'attribute_name']:
            if hasattr(node, prop):
                row[prop] = getattr(node, prop)
        row['inputs'] = []
        for index, socket in enumerate(node.inputs):
            value = getattr(socket, 'default_value', None)
            if value is not None and not isinstance(value, (str, bool, int, float)):
                value = list(value)
            row['inputs'].append({'index': index, 'identifier': socket.identifier,
                                  'value': value,
                                  'links': [(link.from_node.name, link.from_socket.identifier) for link in socket.links]})
        nodes.append(row)
    reached = set()
    visited = set()

    def downstream(node):
        if node.name in visited:
            return
        visited.add(node.name)
        for output in node.outputs:
            for link in output.links:
                if link.to_node.bl_idname == 'ShaderNodeBsdfPrincipled':
                    reached.add(link.to_socket.identifier)
                else:
                    downstream(link.to_node)
    downstream(gain)
    assert reached == {'Base Color'}, reached
    links = [(link.from_node.name, link.from_socket.identifier, link.to_node.name, link.to_socket.identifier)
             for link in group.links if link.from_node.name in chosen or link.to_node.name in chosen]
    output = {'source_scene': source.name, 'source_sha256': digest, 'blender': bpy.app.version_string,
              'scripts_disabled': True, 'material': MATERIAL, 'nodes': nodes, 'links': links,
              'gain_reaches_principled_inputs': sorted(reached),
              'candidate': {'node': 'Math.039', 'input_index': 1, 'input_identifier': gain.inputs[1].identifier,
                            'from': gain.inputs[1].default_value, 'to': .02,
                            'scope': '80% reduction of only the final cell-color overlay weight; ARTIST'},
              'original_atlas_users': [(n.name, n.image.name) for n in group.nodes
                                       if n.bl_idname == 'ShaderNodeTexImage' and n.image],
              'scene_was_saved': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print('OUTLINE_AUDIT', json.dumps({'source_sha256': digest, 'reachable_principled_inputs': sorted(reached),
                                      'candidate_gain': .02, 'output': str(args.output)}), flush=True)


if __name__ == '__main__':
    main()

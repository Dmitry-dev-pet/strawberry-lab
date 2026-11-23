"""Owned v21 color-outline ablation on the SHA-pinned, saved v20B scene.

Only one shader socket changes. This is an ARTIST material experiment,
not a measured cellular reconstruction. No reference assets are used.
"""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

import bpy

SOURCE_SHA = '35fd1d81c51aea1cc8f4cd71c39a2815da87a1137056d32c3f78d4ab1cf649e4'
MATERIAL = 'SDF v12 | continuous vascular fibers, restrained wetness (ARTIST)'
NODE = 'Math.039'
SOURCE_GAIN = 0.10
CANDIDATE_GAIN = 0.02


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
    start = time.perf_counter()
    assert bpy.app.version[:3] == (5, 2, 4), bpy.app.version_string
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    assert digest(a.source) == SOURCE_SHA, 'Unexpected source scene'
    assert not a.out.exists(), 'Refusing to overwrite a saved experiment'
    assert not a.out.with_suffix('.json').exists(), 'Existing build receipt'
    a.out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()), use_scripts=False)
    scene = bpy.context.scene
    material = bpy.data.materials[MATERIAL]
    nodes = material.node_tree.nodes
    node = nodes[NODE]
    assert node.bl_idname == 'ShaderNodeMath' and node.operation == 'MULTIPLY'
    assert len(node.inputs[0].links) == 1 and not node.inputs[1].is_linked
    incoming = node.inputs[0].links[0]
    assert incoming.from_node == nodes['Map Range']
    assert incoming.from_socket.name == 'Result'
    outgoing = list(node.outputs[0].links)
    assert len(outgoing) == 1
    assert outgoing[0].to_node == nodes['Mix (Legacy).004']
    assert outgoing[0].to_socket.identifier == 'Fac'
    old = float(node.inputs[1].default_value)
    assert abs(old - SOURCE_GAIN) < 1e-7, old
    assert nodes['Voronoi Texture'].feature == 'DISTANCE_TO_EDGE'
    assert abs(nodes['Voronoi Texture'].inputs['Scale'].default_value - 2.7) < 1e-6

    images_before = {
        image.name: hashlib.sha256(bytes(image.packed_file.data)).hexdigest()
        for image in bpy.data.images if image.packed_file is not None
    }
    node.inputs[1].default_value = CANDIDATE_GAIN
    scene['v21_variant'] = 'B | color-outline gain 0.02; source 0.10'
    scene['v21_source_sha256'] = SOURCE_SHA
    scene['v21_scope'] = 'One shader socket: pale cellular outline gain. ARTIST.'
    scene['v21_non_goals'] = 'No wet geometry, anatomy calibration or geometry changes.'
    bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()), check_existing=False)
    receipt = {
        'experiment': 'v21-material-outline',
        'hypothesis': 'Attenuating the explicit pale cell-color outline reduces the drawn polygonal appearance.',
        'status': 'built; independent validation and actual renders required',
        'classification': 'ARTIST / template-derived',
        'blender': bpy.app.version_string,
        'blender_build_hash': bpy.app.build_hash.decode(),
        'source': a.source.name,
        'source_sha256': SOURCE_SHA,
        'candidate': a.out.name,
        'candidate_sha256': digest(a.out),
        'bytes': a.out.stat().st_size,
        'changed_socket': {
            'material': MATERIAL, 'node': NODE, 'input_index': 1,
            'old': old, 'new': float(node.inputs[1].default_value),
        },
        'packed_images_before': images_before,
        'frame': scene.frame_current,
        'build_seconds': time.perf_counter() - start,
        'maxrss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    a.out.with_suffix('.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('V21_BUILD', json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Non-infringing Blender Geometry/Shader node inventory for architecture audits.

Run with Blender 5.2+:
  blender -b --factory-startup --python scripts/audit_node_architecture.py -- \
    --blend /path/to/reference.blend --output /tmp/inventory.json

Reports only aggregate node counts, public socket names and group dependencies.
No link topology, node logic, mesh data, materials, textures, or model assets are exported.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path

import bpy


def count_connected_upstream(group):
    """Return set of nodes that can reach an active group output."""
    inputs = collections.defaultdict(set)
    for link in group.links:
        inputs[link.to_node].add(link.from_node)
    pending = [node for node in group.nodes
               if node.bl_idname == "NodeGroupOutput" and getattr(node, "is_active_output", True)]
    reached = set()
    while pending:
        node = pending.pop()
        if node in reached:
            continue
        reached.add(node)
        pending.extend(inputs[node])
    return reached


def group_data(group):
    active = count_connected_upstream(group)
    counts = collections.Counter(node.bl_idname for node in active)
    depnames = sorted(set(node.node_tree.name for node in active
                          if node.bl_idname in ("GeometryNodeGroup", "ShaderNodeGroup")
                          and getattr(node, "node_tree", None) is not None))
    types_of_interest = [
        "GeometryNodeVolumeCube", "GeometryNodeGetNamedGrid",
        "GeometryNodeStoreNamedGrid", "GeometryNodeMeshGrid",
        "GeometryNodeMeshBoolean", "GeometryNodeMeshToSDFGrid",
        "GeometryNodeSDFGridBoolean", "GeometryNodeGridToMesh",
        "GeometryNodeSampleGrid", "GeometryNodeInstanceOnPoints",
        "GeometryNodeRealizeInstances", "GeometryNodeSubdivideMesh",
        "GeometryNodeCurveToMesh", "ShaderNodeTexVoronoi",
        "GeometryNodeStoreNamedAttribute",
    ]
    voronoi_dims = collections.Counter(getattr(n, 'voronoi_dimensions', 'unknown')
                                       for n in active if n.bl_idname == 'ShaderNodeTexVoronoi')
    # Input/output names are descriptive public interface metadata, NOT graph source.
    io = {}
    for direction in ('INPUT', 'OUTPUT'):
        io[direction.lower()] = [s.name for s in group.interface.items_tree
                                 if s.item_type == 'SOCKET' and s.in_out == direction]
    return {
        'name': group.name, 'tree_type': group.bl_idname,
        'node_count': len(group.nodes), 'active_node_count': len(active),
        'link_count': len(group.links), 'dependencies': depnames,
        'structural_features': {k: counts[k] for k in types_of_interest if counts[k]},
        'voronoi_dimensions': dict(sorted(voronoi_dims.items())),
        'interface': io,
    }


def main(argv):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--blend', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args(argv)
    if not args.blend.is_file():
        p.error('No input Blender file')
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve()))
    groups = [group_data(g) for g in bpy.data.node_groups
              if g.bl_idname in ('GeometryNodeTree', 'ShaderNodeTree')]
    groups.sort(key=lambda g: (g['tree_type'], g['name']))
    totals = collections.Counter(g['tree_type'] for g in groups)
    report = {
        'schema': 'strawberry-lab-architecture-inventory-v1',
        'blend_sha256': hashlib.sha256(args.blend.read_bytes()).hexdigest(),
        'blender_version': bpy.app.version_string,
        'scope': 'stored Blender node groups, NOT dynamically executed nodes or performance',
        'group_counts': dict(sorted(totals.items())),
        'group_total': len(groups),
        'node_total': sum(g['node_count'] for g in groups),
        'geometry_node_total': sum(g['node_count'] for g in groups if g['tree_type'] == 'GeometryNodeTree'),
        'shader_group_node_total': sum(g['node_count'] for g in groups if g['tree_type'] == 'ShaderNodeTree'),
        'groups': groups,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print('ARCHITECTURE_AUDIT_OK', json.dumps({
        'groups': report['group_counts'], 'nodes': report['node_total'],
        'file_sha256': report['blend_sha256'], 'out': str(args.output)
    }, ensure_ascii=False))


if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
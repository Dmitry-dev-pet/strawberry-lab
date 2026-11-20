#!/usr/bin/env python3
"""Validate saved M1d Blender scene has a LIVE GN achene SDF culling mask.

Run: blender -b strawberry-m1d-half.blend --python validate_live_cut.py
Evaluates both keyed poses after reopening exactly ONE .blend file.
"""
import bmesh
import bpy
import json
from mathutils import Vector

seed=bpy.data.objects.get('GN live achenes (with actual surface pits)')
body=bpy.data.objects.get('M1c | SDF cutter + rest-space tissue')
dbg=bpy.data.objects.get('M1d | LIVE anchor mask diagnostic (hidden)')
assert seed and body and dbg, 'Missing key objects'
scene=bpy.context.scene
cutter=bpy.data.objects.get(scene.get('m1d_cutter', ''))
assert cutter is not None, 'Missing live cutter object'
assert len(seed.data.vertices)==539, 'Full achene anchors were not restored'
assert len(dbg.data.vertices)==539, 'Debug group anchors were not restored'
assert all(n in seed.data.attributes for n in ['seed_euler','seed_size']), 'Achene point attributes missing'
g=[m.node_group for m in seed.modifiers if m.type=='NODES'][0]
assert g is not None
needed={'GeometryNodeMeshToSDFGrid','GeometryNodeSampleGrid','GeometryNodeDeleteGeometry','GeometryNodeInstanceOnPoints'}
assert needed.issubset({n.bl_idname for n in g.nodes}), 'Missing live SDF sampling nodes'
obj_infos=[n for n in g.nodes if n.bl_idname=='GeometryNodeObjectInfo' and n.inputs['Object'].default_value==cutter]
assert len(obj_infos)==1, 'Seed SDF group does not use same cutter object'
node_delete=next(n for n in g.nodes if n.bl_idname=='GeometryNodeDeleteGeometry')
node_instance=next(n for n in g.nodes if n.bl_idname=='GeometryNodeInstanceOnPoints')
assert node_instance.inputs['Points'].is_linked and node_instance.inputs['Points'].links[0].from_node==node_delete,'GN does not delete BEFORE instancing'

stats=[]
for frame in [1,15,30]:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    dep=bpy.context.evaluated_depsgraph_get();dep.update()
    def counts(o, manifold=False):
        e=o.evaluated_get(dep);me=e.to_mesh()
        n=len(me.vertices)
        nonmanifold=None
        if manifold:
            bm=bmesh.new();bm.from_mesh(me)
            nonmanifold=sum(not edge.is_manifold for edge in bm.edges)
            bm.free()
        e.to_mesh_clear()
        return n, nonmanifold
    ac,_=counts(dbg)
    sc,_=counts(seed)
    bc,bm=counts(body,True)
    assert ac*168==sc,f'Frame {frame}: seed instances inconsistent with anchors'
    assert 0<ac<=539,f'Frame {frame}: invalid seed count {ac}'
    assert bm==0,f'Frame {frame}: cut body mesh has {bm} non-manifold edges'
    stats.append(dict(frame=frame,visible_anchors=ac,evaluated_seed_vertices=sc,sdf_body_vertices=bc,nonmanifold_edges=bm,location=list(cutter.location)))
assert stats[0]['visible_anchors']!=stats[-1]['visible_anchors'], 'Moving cutter did not update seed count'
assert stats[0]['sdf_body_vertices']!=stats[-1]['sdf_body_vertices'], 'Moving cutter did not change body SDF'
scene.frame_set(1)
print('M1D_LIVE_REOPEN_PASS',json.dumps({'mode':scene.get('m1c_mode'),'original_anchors':539,'same_cutter':cutter.name,'pose_checks':stats}),flush=True)
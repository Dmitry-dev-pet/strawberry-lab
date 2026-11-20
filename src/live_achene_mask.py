#!/usr/bin/env python3
"""M1d: restore all achene anchors, dynamically mask by LIVE SDF cutter.

Independent Strawberry Lab implementation, Blender 5.2+. Open an M1c scene,
restore the full M1a seed-anchor mesh (539 points with seed_euler/seed_size),
insert a Geometry Nodes Delete Geometry driven by the SDF of the same editable
cutter object driving the M1c fruit-body Boolean. Keyframe the cutter to show
that BOTH body and seed instances respond on two different poses.

Commands:
 blender -b --python src/live_achene_mask.py -- \\
    --scene BASE-M1C.blend --anchors-from M1A-WHOLE.blend --out OUT-DIR \\
    --resolution 680 --samples 16

Does not copy commercial Frucht assets and does not re-bake tissues. The SDF
mask uses the cutter's actual transformed mesh, not its Python approximation.
"""
from __future__ import annotations
import argparse
import bmesh
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import bpy
from mathutils import Vector

P = argparse.ArgumentParser()
P.add_argument('--scene', type=Path, required=True, help='Editable M1c scene with cutter')
P.add_argument('--anchors-from', type=Path, required=True, help='M1a scene with ALL achenes')
P.add_argument('--out', type=Path, required=True)
P.add_argument('--samples', type=int, default=16)
P.add_argument('--resolution', type=int, default=680)
P.add_argument('--voxel', type=float, default=0.023, help='SDF voxel mask resolution; must be smaller than seed dimensions')
P.add_argument('--no-render', action='store_true')
P.add_argument('--no-glb', action='store_true')
args = P.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
if args.voxel <= 0 or args.voxel > .15: raise ValueError('Bad SDF sampling voxel')
for path in [args.scene, args.anchors_from]:
    if not path.is_file(): raise FileNotFoundError(path)
args.out.mkdir(parents=True, exist_ok=True)
T0=time.monotonic()

bpy.ops.wm.open_mainfile(filepath=str(args.scene.resolve()))
scene=bpy.context.scene
seed_obj=bpy.data.objects.get('GN live achenes (with actual surface pits)')
body=bpy.data.objects.get('M1c | SDF cutter + rest-space tissue')
if not seed_obj or not body: raise RuntimeError('M1c scene lacks body or seeds')
cutters=[o for o in bpy.data.objects if o.name.startswith('M1c | ') and 'cutter' in o.name.lower() and o is not body and o.type=='MESH']
if len(cutters)!=1: raise RuntimeError('Expected exactly one cutter, found '+str([o.name for o in cutters]))
cutter=cutters[0]
mode = str(scene.get('m1c_mode', 'half'))
if mode not in ('half','bite'): raise RuntimeError('Unsupported mode '+mode)

# Read the real unfiltered point geometry from the published M1a Blender scene.
# Keep the existing M1c seeds object, so no modifier/material/layout is lost.
with bpy.data.libraries.load(str(args.anchors_from.resolve()), link=False) as (source, dest):
    original_name='GN live achenes (with actual surface pits)'
    if original_name not in source.objects: raise RuntimeError('Original M1a anchor object not found')
    dest.objects=[original_name]
temporary=dest.objects[0]
if temporary is None or temporary.type!='MESH': raise RuntimeError('Unable to load original achene anchors')
full_mesh=temporary.data.copy()
full_mesh.name='M1d | original 539 achene anchor points — no baked clipping'
bpy.data.objects.remove(temporary,do_unlink=True)
if len(full_mesh.vertices)<500: raise RuntimeError('Original anchor mesh unexpectedly has <500 points')
for aname in ('seed_euler','seed_size'):
    if aname not in full_mesh.attributes: raise RuntimeError('Lost required achene attribute '+aname)
old_mesh=seed_obj.data
seed_obj.data=full_mesh

# Rewire the existing live-instancing Geometry Nodes graph, preserving Euler
# orientation and individual size fields. The deletion is point-domain before
# instancing, rather than baking a subset of the original point cloud in Python.
mod = next((m for m in seed_obj.modifiers if m.type=='NODES' and m.node_group),None)
if not mod: raise RuntimeError('No live achene instancing GN modifier')
node_group=mod.node_group.copy()
node_group.name='M1d | LIVE SDF achene culling — same cutter as fruit'
mod.node_group=node_group
N=node_group.nodes;L=node_group.links
input_node=next((n for n in N if n.bl_idname=='NodeGroupInput'),None)
inst=next((n for n in N if n.bl_idname=='GeometryNodeInstanceOnPoints'),None)
if not input_node or not inst: raise RuntimeError('Missing original GN instancing connection')
for old_link in list(inst.inputs['Points'].links):
    L.remove(old_link)

objinfo=N.new('GeometryNodeObjectInfo')
objinfo.name='M1d | same live cutter object'
objinfo.inputs['Object'].default_value=cutter
objinfo.transform_space='RELATIVE'
objinfo.location=(-950,-430)

sdf=N.new('GeometryNodeMeshToSDFGrid')
sdf.name='M1d | SDF of cutter in fruit coordinates'
sdf.inputs['Voxel Size'].default_value=args.voxel
sdf.inputs['Band Width'].default_value=5
sdf.location=(-730,-440)
L.new(objinfo.outputs['Geometry'],sdf.inputs['Mesh'])

pos=N.new('GeometryNodeInputPosition')
pos.location=(-530,-670)
sample=N.new('GeometryNodeSampleGrid')
sample.name='M1d | signed distance at every achene anchor'
sample.location=(-470,-425)
L.new(sdf.outputs['SDF Grid'],sample.inputs['Grid'])
L.new(pos.outputs['Position'],sample.inputs['Position'])

cmp=N.new('FunctionNodeCompare')
cmp.data_type='FLOAT';cmp.operation='LESS_THAN'
cmp.name='M1d | remove seed if strictly inside cutter'
cmp.inputs['B'].default_value=-args.voxel * .55
cmp.location=(-240,-430)
L.new(sample.outputs['Value'],cmp.inputs['A'])

delete=N.new('GeometryNodeDeleteGeometry')
delete.name='M1d | dynamic point mask before instancing'
delete.domain='POINT'
delete.mode='ALL'
delete.location=(-100,130)
L.new(input_node.outputs['Geometry'],delete.inputs['Geometry'])
L.new(cmp.outputs['Result'],delete.inputs['Selection'])
L.new(delete.outputs['Geometry'],inst.inputs['Points'])

# A second, LIGHTWEIGHT debug object has the same SDF pipeline but outputs
# the surviving original seed POINTS. This independently validates that the
# GN point mask, not a baked mesh or Python filter, drives the visible seeds.
dbg_mesh=full_mesh.copy()
dbg_mesh.name='M1d | debug original achene anchors'
debug=bpy.data.objects.new('M1d | LIVE anchor mask diagnostic (hidden)',dbg_mesh)
seed_obj.users_collection[0].objects.link(debug)
debug.hide_render=True
debug.hide_set(True)
dbg_group=bpy.data.node_groups.new('M1d | live anchor diagnostic', 'GeometryNodeTree')
dbg_group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
dbg_group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
dN=dbg_group.nodes;dL=dbg_group.links
i=dN.new('NodeGroupInput');o=dN.new('NodeGroupOutput')
inf=dN.new('GeometryNodeObjectInfo');inf.inputs['Object'].default_value=cutter;inf.transform_space='RELATIVE'
v=dN.new('GeometryNodeMeshToSDFGrid');v.inputs['Voxel Size'].default_value=args.voxel;v.inputs['Band Width'].default_value=5
a=dN.new('GeometryNodeInputPosition');b=dN.new('GeometryNodeSampleGrid')
c=dN.new('FunctionNodeCompare');c.data_type='FLOAT';c.operation='LESS_THAN';c.inputs['B'].default_value=-args.voxel*.55
d=dN.new('GeometryNodeDeleteGeometry');d.domain='POINT';d.mode='ALL'
dL.new(inf.outputs['Geometry'],v.inputs['Mesh']);dL.new(v.outputs['SDF Grid'],b.inputs['Grid']);dL.new(a.outputs['Position'],b.inputs['Position'])
dL.new(b.outputs['Value'],c.inputs['A']);dL.new(c.outputs['Result'],d.inputs['Selection'])
dL.new(i.outputs['Geometry'],d.inputs['Geometry']);dL.new(d.outputs['Geometry'],o.inputs['Geometry'])
md=debug.modifiers.new('M1d | SDF mask validation', 'NODES');md.node_group=dbg_group

# Numerical invariants: original GN prototype is a 168-vertex realized seed
# mesh, so evaluate counts of BOTH paths on each cutter pose and cross-check.
proto=bpy.data.objects.get('GN prototype | dry fruit / achene')
if not proto or proto.type!='MESH':raise RuntimeError('Original achene source mesh not found')
seed_verts_per_instance=len(proto.data.vertices)
if seed_verts_per_instance<40:raise RuntimeError('Unexpected seed prototype mesh')


def evaluate():
    bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get();deps.update()
    def cnt(obj,measure_nonmanifold=False):
        evaluated=obj.evaluated_get(deps)
        mesh=evaluated.to_mesh()
        result={'vertices':len(mesh.vertices),'faces':len(mesh.polygons)}
        if measure_nonmanifold:
            bm=bmesh.new();bm.from_mesh(mesh)
            result['nonmanifold_edges']=sum(not e.is_manifold for e in bm.edges)
            bm.free()
        evaluated.to_mesh_clear()
        return result
    anchor=cnt(debug)
    seed=cnt(seed_obj)
    b=cnt(body,True)
    if seed['vertices'] != anchor['vertices']*seed_verts_per_instance:
        raise RuntimeError('Mismatch GN seed instances and live surviving anchor points: '+repr([seed,anchor,seed_verts_per_instance]))
    if not 0 < anchor['vertices'] <= len(full_mesh.vertices):
        raise RuntimeError('SDF mask returned no seeds or more than original 539')
    if b['nonmanifold_edges'] != 0:raise RuntimeError('SDF body no longer watertight')
    return {'live_achenes':anchor['vertices'],'seed_evaluated_verts':seed['vertices'], 'body':b}

# Test two positions of exactly THE SAME cutter object and GN groups. Two
# keyframes are saved in a single .blend so scrubbing reproduces the result.
scene.frame_start=1;scene.frame_end=30
scene.frame_set(1)
pose0=tuple(float(v) for v in cutter.location)
stat0=evaluate()
if mode=='half':
    delta=Vector((0.20, 1.15, .25))
else:
    delta=Vector((-1.14, .90, .40))
# No keyframe interpolation during the direct evaluation: the moving cutter
# is updated first; keyframes are created only after both states were checked.
cutter.location=Vector(pose0)+delta
stat1=evaluate()
if stat0['live_achenes']==stat1['live_achenes']:
    raise RuntimeError('Moving cutter failed to change live achene count; masking is not dynamic')
if stat0['body']['vertices']==stat1['body']['vertices']:
    raise RuntimeError('Moving cutter failed to alter the SDF fruit body')
print('LIVE_POSE_INITIAL', json.dumps(stat0),flush=True)
print('LIVE_POSE_SHIFTED', json.dumps(stat1),flush=True)

# Preserve keyframe interpolated movement for opening the final file in Blender.
cutter.location=pose0;cutter.keyframe_insert(data_path='location',frame=1)
cutter.location=Vector(pose0)+delta;cutter.keyframe_insert(data_path='location',frame=30)
if cutter.animation_data and cutter.animation_data.action:
    try:
        for fc in cutter.animation_data.action.fcurves:
            for key in fc.keyframe_points:key.interpolation='LINEAR'
    except Exception:pass
scene['m1d_status']='Live SDF point culling 539 original achenes; move cutter and BOTH body and seeds update'
scene['m1d_cutter']=cutter.name
scene['m1d_restored_anchor_count']=len(full_mesh.vertices)
scene['m1d_seed_mask_threshold']=-args.voxel*.55
scene['m1d_currently_tested']='frame 1 vs frame 30, body and visible achene instance count changed by moving same cutter'
scene['m1d_not_frucht']='Independent implementation; source is M1a+M1c, not proprietary Frucht'

stem=args.out/('strawberry-m1d-'+mode)
scene.frame_set(1)
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=args.samples
scene.render.resolution_x=args.resolution;scene.render.resolution_y=args.resolution
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(stem)+'-frame01.png'
blend_path=str(stem)+'.blend'
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print('BLEND_SAVED',blend_path,flush=True)

if not args.no_render:
    for frame in [1,30]:
        scene.frame_set(frame)
        scene.render.filepath=str(stem)+f'-frame{frame:02d}.png'
        bpy.ops.render.render(write_still=True)
        print('RENDER_SAVED',scene.render.filepath,flush=True)

if not args.no_glb:
    # GLB snapshot of frame 1 only. The live cutter and its procedural texture
    # are Blender-native; GLB does not preserve Geometry Nodes/cutter animation.
    scene.frame_set(1)
    for ob in list(bpy.context.selected_objects):ob.select_set(False)
    for ob in (body,seed_obj):
        ob.hide_set(False);ob.select_set(True)
    bpy.context.view_layer.objects.active=body
    path=str(stem)+'-frame01.glb'
    bpy.ops.export_scene.gltf(filepath=path,export_format='GLB',use_selection=True,export_apply=True)
    print('GLB_SAVED',path,flush=True)

stats={'version':'m1d', 'mode':mode,'anchors_original':len(full_mesh.vertices),'seed_verts_per_instance':seed_verts_per_instance,
       'anchor_mask_voxel':args.voxel,'cutter_name':cutter.name,'cutter_pose0':pose0,'cutter_delta':list(delta),
       'frame01':stat0,'frame30':stat1,'blender_version':bpy.app.version_string,
       'tested_live_in_same_scene':True,'time_sec':round(time.monotonic()-T0,2),
       'note':'Seed mask driven by same cutter SDF mesh in Geometry Nodes; m1c voxel body cut remains unchanged.'}
stat_path=str(stem)+'-stats.json'
Path(stat_path).write_text(json.dumps(stats,indent=2)+'\n',encoding='utf-8')
print('M1D_DONE',json.dumps(stats),flush=True)
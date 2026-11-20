#!/usr/bin/env python3
"""Export a tested STATIC GLB snapshot of an evaluated M1d Blender frame.

Blender's glTF exporter can silently export the original frame when relying on
export_apply for linked Geometry Nodes. To make frames genuinely distinct, this
script bakes explicit evaluated meshes at the requested frame, checks that
achene vertex counts agree with the live GN point mask, and exports only those
temporary baked objects. The source .blend remains the editable/animated model.

Requires Blender 5.2+. Usage:
 blender -b scene.blend --python src/export_pose_glb.py -- --frame 30 --out build/
"""
import argparse,sys,json
from pathlib import Path
import bpy
p=argparse.ArgumentParser();p.add_argument('--frame',type=int,choices=[1,15,30],required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
a.out.mkdir(parents=True,exist_ok=True)
s=bpy.context.scene;s.frame_set(a.frame)
bpy.context.view_layer.update()
deps=bpy.context.evaluated_depsgraph_get();deps.update()
body=bpy.data.objects['M1c | SDF cutter + rest-space tissue']
seed=bpy.data.objects['GN live achenes (with actual surface pits)']
dbg=bpy.data.objects['M1d | LIVE anchor mask diagnostic (hidden)']
mask=dbg.evaluated_get(deps);am=mask.to_mesh();count=len(am.vertices);mask.to_mesh_clear()

baked=[];counts={}
for orig in [body,seed]:
    ev=orig.evaluated_get(deps)
    me=bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=deps)
    if me is None:raise RuntimeError('Unable to bake evaluated mesh '+orig.name)
    baked_obj=bpy.data.objects.new('GLB frame '+str(a.frame)+' '+('fruit' if orig==body else 'live achenes'),me)
    s.collection.objects.link(baked_obj)
    baked_obj.matrix_world=orig.matrix_world.copy()
    baked_obj.select_set(True)
    baked.append(baked_obj)
    counts[orig.name]={'vertices':len(me.vertices),'triangles':sum(len(p.vertices)-2 for p in me.polygons)}
if counts[seed.name]['vertices'] != count * 168:raise RuntimeError('GLB seed bake does not match live GN mask: '+str((count,counts[seed.name]['vertices'])))
for o in list(bpy.context.selected_objects):
    if o not in baked:o.select_set(False)
bpy.context.view_layer.objects.active=baked[0]
mode=s.get('m1c_mode','unknown')
f=a.out/f'strawberry-m1d-{mode}-frame{a.frame:02d}.glb'
bpy.ops.export_scene.gltf(filepath=str(f),export_format='GLB',use_selection=True,export_apply=False)
report={'frame':a.frame,'mode':mode,'live_seed_count':count,'baked':counts,'glb_size_bytes':f.stat().st_size,'glb_file':f.name,'note':'Geometry-only export of true evaluated frame; procedural Cycles shader/animation not retained by GLB'}
(a.out/f'strawberry-m1d-{mode}-frame{a.frame:02d}-export.json').write_text(json.dumps(report,indent=2)+'\n')
print('M1D_GLB_BAKED',json.dumps(report),flush=True)
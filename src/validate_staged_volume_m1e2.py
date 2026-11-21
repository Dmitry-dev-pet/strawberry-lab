#!/usr/bin/env python3
"""Independent sanity test of a staged SourceVolume / Cut Blender scene."""
import bpy, bmesh, json, time, sys, argparse
from pathlib import Path
T=time.perf_counter()
ap=argparse.ArgumentParser()
ap.add_argument('--out',required=True,type=Path)
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
out=args.out.parent;out.mkdir(parents=True,exist_ok=True)
s=bpy.context.scene
body=bpy.data.objects['M1c | SDF cutter + rest-space tissue']
source=bpy.data.objects['M1e2 | 3D SourceVolume (outer minus cavity)']
knife=bpy.data.objects['M1e | independently moving knife (cube half space)']
cavity=bpy.data.objects['M1e | persistent internal cavity (separate 3D mesh)']
seeds=bpy.data.objects['GN live achenes (with actual surface pits)']
assert all(x is not None for x in [body,source,knife,cavity,seeds])
G=body.modifiers[0].node_group;C=source.modifiers[0].node_group
assert sum(n.bl_idname=='GeometryNodeMeshToSDFGrid' for n in G.nodes)==1
assert sum(n.bl_idname=='GeometryNodeSDFGridBoolean' for n in G.nodes)==1
assert sum(n.bl_idname=='GeometryNodeMeshToSDFGrid' for n in C.nodes)==2
assert sum(n.bl_idname=='GeometryNodeSDFGridBoolean' for n in C.nodes)==1
assert any(n.bl_idname=='GeometryNodeGetNamedGrid' and n.inputs['Name'].default_value=='fruit_solid' for n in G.nodes)
assert any(n.bl_idname=='GeometryNodeStoreNamedGrid' and n.inputs['Name'].default_value=='fruit_solid' for n in C.nodes)
rows=[]
for frame in (1,15,30):
 s.frame_set(frame)
 dg=bpy.context.evaluated_depsgraph_get();dg.update()
 eb=body.evaluated_get(dg);me=eb.to_mesh()
 if len(me.vertices)<1000:raise RuntimeError('EMPTY BODY at '+str(frame))
 bm=bmesh.new();bm.from_mesh(me)
 nonmanifold=sum(not e.is_manifold for e in bm.edges)
 unseen=set(bm.verts);comps=[]
 while unseen:
  root=unseen.pop();stack=[root];k=0
  while stack:
   v=stack.pop();k+=1
   for edge in v.link_edges:
    u=edge.other_vert(v)
    if u in unseen:unseen.remove(u);stack.append(u)
  comps.append(k)
 bm.free()
 mats={}
 for poly in me.polygons:mats[str(poly.material_index)]=mats.get(str(poly.material_index),0)+1
 r={'frame':frame,'body_vertices':len(me.vertices),'body_faces':len(me.polygons),'nonmanifold':nonmanifold,'components':len(comps),'component_vertices':sorted(comps,reverse=True),'material_faces':mats}
 eb.to_mesh_clear()
 es=seeds.evaluated_get(dg);ems=es.to_mesh();r['seed_mesh_vertices']=len(ems.vertices);es.to_mesh_clear()
 print('FRAME',json.dumps(r),flush=True)
 assert r['nonmanifold']==0
 rows.append(r)
assert rows[0]['components']==2
assert rows[-1]['components']==1
assert rows[0]['seed_mesh_vertices']>rows[-1]['seed_mesh_vertices']
json_file=args.out.resolve()
json_file.write_text(json.dumps({'result':'PASS','blender':bpy.app.version_string,'frames':rows,'wall_time_sec':time.perf_counter()-T},indent=2)+'\n')
print('STAGED_VOLUME_VALIDATION_PASS',str(json_file),flush=True)

#!/usr/bin/env python3
"""Validate the actual saved M1e4 Blender cut snapshot and its live 3D tubes."""
import bpy,bmesh,json,sys,math,time, argparse
from pathlib import Path
from mathutils.bvhtree import BVHTree
import random
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
t=time.perf_counter();s=bpy.context.scene
frame=int(s['m1e4_snapshot_frame']);s.frame_set(frame)
frozen=bpy.data.objects[f'M1e4 | local CutSurface SNAPSHOT frame {frame}']
body=bpy.data.objects['M1c | SDF cutter + rest-space tissue']
tubes=bpy.data.objects['M1e4 | LIVE 3D filament tubes, clipped by knife']
assert body.hide_render and not frozen.hide_render
assert frozen.type=='MESH' and tubes.type=='CURVE'
assert frozen.get('dynamic','').startswith('NO')
assert any(n.bl_idname=='GeometryNodeDeleteGeometry' for n in tubes.modifiers[0].node_group.nodes)
mod=frozen.modifiers[0];ng=mod.node_group
assert any(n.name=='M1e4 | expose 3D strand material only on cut' for n in ng.nodes)
assert ng.nodes['M1e3 | CutSurface true geometry'].inputs['Geometry'].links[0].from_node.bl_idname=='NodeGroupInput'
assert ng.nodes['M1e3 | 3D irregular cell-boundary field'].voronoi_dimensions=='3D'
DG=bpy.context.evaluated_depsgraph_get();DG.update()
obj=frozen.evaluated_get(DG);me=obj.to_mesh()
bm=bmesh.new();bm.from_mesh(me)
nonman=sum(not e.is_manifold for e in bm.edges)
unseen=set(bm.verts);parts=[]
while unseen:
 v=unseen.pop();pending=[v];ct=0
 while pending:
  w=pending.pop();ct+=1
  for ed in w.link_edges:
   u=ed.other_vert(w)
   if u in unseen:unseen.remove(u);pending.append(u)
 parts.append(ct)
bm.free()
assert nonman==0,nonman
assert len(parts)==(2 if frame==1 else 1),(frame,len(parts))
attr=me.attributes.get('fruit_rest');field=me.attributes.get('m1e4_fiber')
assert attr and field, [(x.name,x.domain,x.data_type) for x in me.attributes]
vals=[field.data[i].value for i in range(len(field.data))]
positive=sum(v>.11 for v in vals)
if frame != 1:assert positive>1000,(frame,positive)
assert len(me.vertices)<250000,len(me.vertices)
materials={}
for poly in me.polygons:
 m=me.materials[poly.material_index] if poly.material_index<len(me.materials) else None
 k=m.name if m else 'NULL'
 materials[k]=materials.get(k,0)+1
if frame != 1:assert any('M1e4 | strawberry cut flesh' in m for m in materials),materials

# The separate source network remains coherent 3D curves, and the tubes have
# an actual evaluated mesh which changes with cutter movement.
t_obj=tubes.evaluated_get(DG);tm=t_obj.to_mesh();tube_vertices=len(tm.vertices)
assert tube_vertices>1000,(frame,tube_vertices)
all_nets=bpy.data.objects['M1e4 | persistent 3D curved fibers (source)']
assert len(all_nets.data.splines)==135
assert all(len(sp.points)>6 for sp in all_nets.data.splines)
# Skin check against the original still-live M1e3 geometry at the SAME pose.
be=body.evaluated_get(DG);orig_me=be.to_mesh()
skin_indices={i for i,m in enumerate(orig_me.materials) if m and m.name.startswith('Strawberry M1a')}
incident=[set() for _ in orig_me.vertices]
for poly in orig_me.polygons:
 for vid in poly.vertices:incident[vid].add(poly.material_index)
skin_candidates=[i for i,mset in enumerate(incident) if mset and mset.issubset(skin_indices)]
assert len(skin_candidates)>=2000
skin_faces=[list(poly.vertices) for poly in me.polygons if me.materials[poly.material_index] and me.materials[poly.material_index].name.startswith('Strawberry M1a')]
skin_bvh=BVHTree.FromPolygons([tuple(v.co) for v in me.vertices],skin_faces,all_triangles=False)
rng=random.Random(101+frame)
checks=rng.sample(skin_candidates,min(2500,len(skin_candidates)))
skin_nearest=[skin_bvh.find_nearest(orig_me.vertices[i].co)[3] for i in checks]
skin_max=max(skin_nearest)
skin_median=sorted(skin_nearest)[len(skin_nearest)//2]
print('SKIN_SURFACE_DISTANCE',frame,'max',skin_max,'median',skin_median,'gt1e-5',sum(d>1e-5 for d in skin_nearest),flush=True)
assert skin_max<.005, skin_max
be.to_mesh_clear()
res={'status':'PASS','frame':frame,'snapshot_vertices':len(me.vertices),'snapshot_faces':len(me.polygons),
     'nonmanifold_edges':nonman,'original_skin_sample_n':len(checks),'original_skin_sample_max_offset':round(skin_max,8),'components':len(parts),'component_vertices':sorted(parts,reverse=True),
     'strand_field_vertices_gt_point11':positive,'fiber_field_minmax':[round(min(vals),4),round(max(vals),4)],
     'tube_geometry_vertices':tube_vertices,'tube_source_splines':len(all_nets.data.splines),
     'cut_and_skin_material_counts':materials,'elapsed_seconds':round(time.perf_counter()-t,3),
     'limitations':['snapshot only at this cutter pose','no guarantee no self-intersections','all 3D fibers artistic']}
obj.to_mesh_clear();t_obj.to_mesh_clear()
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(res,indent=2)+'\n')
print('M1E4_SAVED_SCENE_VALIDATED',json.dumps(res),flush=True)

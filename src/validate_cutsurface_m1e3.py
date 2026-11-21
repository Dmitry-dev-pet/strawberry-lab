#!/usr/bin/env python3
"""Independent saved-scene CutSurface validator; checks actual mesh vs M1e2.

Usage: blender -b strawberry-m1e3-cutsurface.blend --python validate_cutsurface.py
       -- --baseline original-m1e2.blend --out validation.json
"""
import sys,json,time,math,bmesh,random,argparse
from pathlib import Path
from mathutils.kdtree import KDTree
import bpy

p=argparse.ArgumentParser()
p.add_argument('--baseline',required=True,type=Path)
p.add_argument('--out',required=True,type=Path)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
start=time.perf_counter()
s=bpy.context.scene
body=bpy.data.objects['M1c | SDF cutter + rest-space tissue']
ng=body.modifiers[0].node_group
need=['M1e3 | true cut-surface mesh refinement','M1e3 | actual cut material only','M1e3 | actual inner cavity material only','M1e3 | rest-space source coordinates','M1e3 | CutSurface true geometry','M1e3 | real cavity wall geometry','M1e3 | no motion at skin rim','M1e3 | no motion at cavity rim','M1e3 | no motion at cavity opening rim','M1e3 | 3D irregular cell-boundary field']
for name in need:assert name in ng.nodes,name
sub=ng.nodes[need[0]]
assert sub.inputs['Level'].default_value in (1,2)
assert ng.nodes[need[3]].inputs['Name'].default_value=='fruit_rest'
assert ng.nodes[need[-1]].voronoi_dimensions=='3D'
assert ng.nodes[need[-1]].feature=='DISTANCE_TO_EDGE'
assert ng.nodes[need[1]].inputs['Material'].default_value.name.startswith('M1c | rest-space')
assert ng.nodes[need[2]].inputs['Material'].default_value.name.startswith('M1e | shadowy')
# Verify *both* separate geometry operations are wired after subdivision.
cut=ng.nodes['M1e3 | CutSurface true geometry'];cav=ng.nodes['M1e3 | real cavity wall geometry']
assert cut.inputs['Geometry'].links[0].from_node.name==sub.name
assert cav.inputs['Geometry'].links[0].from_node.name==cut.name
assert any(l.from_node.name==cav.name and l.to_node.bl_idname=='NodeGroupOutput' for l in ng.links)

report={'schema':'strawberry-lab.m1e3.cutsurface.1','blender':bpy.app.version_string,
  'source':'M1e2 source volume; independent M1e3 geometry, no third party node graph',
  'subdivision_level':sub.inputs['Level'].default_value,'frames':[]}
new_kdtree=None
for frame in (1,15,30):
 s.frame_set(frame)
 t=time.perf_counter();dg=bpy.context.evaluated_depsgraph_get();dg.update()
 e=body.evaluated_get(dg);me=e.to_mesh()
 bm=bmesh.new();bm.from_mesh(me)
 nonmanifold=sum(not edge.is_manifold for edge in bm.edges)
 unseen=set(bm.verts);cc=[]
 while unseen:
  root=unseen.pop();stack=[root];count=0
  while stack:
   v=stack.pop();count+=1
   for edge in v.link_edges:
    u=edge.other_vert(v)
    if u in unseen:unseen.remove(u);stack.append(u)
  cc.append(count)
 bm.free()
 assert nonmanifold==0,(frame,nonmanifold)
 assert len(cc)==(2 if frame==1 else 1)
 attr=me.attributes.get('fruit_rest')
 assert attr and attr.data_type=='FLOAT_VECTOR' and attr.domain=='POINT'
 matnames=[m.name if m else '' for m in me.materials]
 cut_ids=[i for i,x in enumerate(matnames) if x.startswith('M1c | rest-space')]
 cav_ids=[i for i,x in enumerate(matnames) if x.startswith('M1e | shadowy')]
 skin_ids=[i for i,x in enumerate(matnames) if x.startswith('Strawberry M1a')]
 assert cut_ids and cav_ids and skin_ids
 counts={'cut':0,'cavity':0,'skin':0}
 for pol in me.polygons:
  k=pol.material_index
  if k in cut_ids:counts['cut']+=1
  elif k in cav_ids:counts['cavity']+=1
  elif k in skin_ids:counts['skin']+=1
 assert counts['cavity']>1000 and counts['skin']>1000
 if frame>=15:assert counts['cut']>1000
 # Index valid re-opened named rest coords.
 random.seed(11+frame)
 for _ in range(100):
  idx=random.randrange(len(me.vertices))
  r=attr.data[idx].vector
  assert all(math.isfinite(x) for x in r)
 if frame==15:
  new_kdtree=KDTree(len(me.vertices))
  for i,v in enumerate(me.vertices):new_kdtree.insert(v.co,i)
  new_kdtree.balance()
 row={'frame':frame,'vertices':len(me.vertices),'faces':len(me.polygons),
     'surface_components':len(cc),'nonmanifold_edges':nonmanifold,
     'material_faces':counts,'evaluated_seconds':round(time.perf_counter()-t,4)}
 e.to_mesh_clear()
 report['frames'].append(row)
 print('M1E3_FRAME_VALID',json.dumps(row),flush=True)

# Open old saved M1e2; inspect old geometry and compare to actual M1e3 at same cutter pose.
bpy.ops.wm.open_mainfile(filepath=str(a.baseline.resolve()))
bpy.context.scene.frame_set(15)
old=bpy.data.objects['M1c | SDF cutter + rest-space tissue']
dg=bpy.context.evaluated_depsgraph_get();dg.update()
e=old.evaluated_get(dg);mesh=e.to_mesh()
matnames=[m.name if m else '' for m in mesh.materials]
skinidx={i for i,n in enumerate(matnames) if n.startswith('Strawberry M1a')}
cutidx={i for i,n in enumerate(matnames) if n.startswith('M1c | rest-space')}
cavidx={i for i,n in enumerate(matnames) if n.startswith('M1e | shadowy')}
vertex_type=[set() for _ in mesh.vertices]
for face in mesh.polygons:
 for i in face.vertices:vertex_type[i].add(face.material_index)
all_skin_only=[i for i,t in enumerate(vertex_type) if t and t.issubset(skinidx)]
all_cut_only=[i for i,t in enumerate(vertex_type) if t and t.issubset(cutidx)]
all_cav_only=[i for i,t in enumerate(vertex_type) if t and t.issubset(cavidx)]
assert len(all_skin_only)>2000 and len(all_cut_only)>400 and len(all_cav_only)>1000
rng=random.Random(47)
def sample_nearest(ids,n=2500):
 ids=rng.sample(ids,min(n,len(ids)))
 ds=[new_kdtree.find(mesh.vertices[i].co)[2] for i in ids]
 ds.sort()
 return {'samples':len(ds),'max':round(ds[-1],8),'median':round(ds[len(ds)//2],8),
  'mean':round(sum(ds)/len(ds),8),'over_0_001':sum(x>.001 for x in ds)}
comparison={'skin_untouched_vertices':sample_nearest(all_skin_only),
            'cut_displaced_vertices':sample_nearest(all_cut_only),
            'cavity_displaced_vertices':sample_nearest(all_cav_only)}
# All baseline skin vertices not touching any cut/cavity faces must still be
# present exactly (tiny Blender float roundoff tolerated) in the new refined mesh.
assert comparison['skin_untouched_vertices']['max']<1e-5,comparison
# Verify a *substantial number* of cut and cavity vertices were truly moved.
assert comparison['cut_displaced_vertices']['over_0_001']>int(.25*comparison['cut_displaced_vertices']['samples']),comparison
assert comparison['cavity_displaced_vertices']['over_0_001']>int(.15*comparison['cavity_displaced_vertices']['samples']),comparison
report['baseline_geometry_comparison_frame15']=comparison
report['time_seconds_total']=round(time.perf_counter()-start,3)
report['status']='PASS'
a.out.parent.mkdir(parents=True,exist_ok=True)
a.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
e.to_mesh_clear()
print('M1E3_CUTSURFACE_INDEPENDENT_PASS',json.dumps(comparison),flush=True)

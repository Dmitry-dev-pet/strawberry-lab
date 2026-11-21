#!/usr/bin/env python3
"""Independent Blender 5.2 M1e6 GN-only selected edge geometry audit."""
import bpy,bmesh,json,sys,time,math,random
from pathlib import Path
from mathutils.bvhtree import BVHTree
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
out=Path(args[0] if args else '/mnt/data/strawberry-m1e6/validation.json')
s=bpy.context.scene
body=bpy.data.objects['M1c | SDF cutter + rest-space tissue']
helper=bpy.data.objects['M1e5 | live SDF source for localized mesh']
knife=bpy.data.objects['M1e | independently moving knife (cube half space)']
cavity=bpy.data.objects['M1e | persistent internal cavity (separate 3D mesh)']
network=bpy.data.objects['M1e4 | persistent 3D curved fibers (source)']
snap=bpy.data.objects['M1e5 | EXACT live-local CutSurface']
ng=body.modifiers[0].node_group
assert any(n.bl_idname=='GeometryNodeMeshBevel' for n in ng.nodes)
assert all(n.bl_idname!='GeometryNodeSubdivideMesh' for n in ng.nodes)
assert len(body.modifiers)==1, 'Unsafe experimental island-cleanup modifier is not in production scene'
assert any(n.name=='M1e6 | live strand field on cut' for n in ng.nodes)
assert not body.hide_render and snap.hide_render
assert s['m1e5_mode']=='FAST_GN_ALWAYS_LIVE'
assert not any(fn.__name__.startswith('_on_depsgraph') or fn.__name__.startswith('_on_frame') for fn in bpy.app.handlers.depsgraph_update_post+bpy.app.handlers.frame_change_post)

rows=[]
def check(tag, need_comp=None, skin=False):
  t=time.perf_counter();dg=bpy.context.evaluated_depsgraph_get();dg.update()
  ev=body.evaluated_get(dg);me=ev.to_mesh()
  bm=bmesh.new();bm.from_mesh(me)
  bad=sum(not ed.is_manifold for ed in bm.edges)
  verts=set(bm.verts);parts=[]
  while verts:
   root=verts.pop();st=[root];k=0
   while st:
    x=st.pop();k+=1
    for ed in x.link_edges:
     u=ed.other_vert(x)
     if u in verts:verts.remove(u);st.append(u)
   parts.append(k)
  bm.free()
  assert bad==0,(tag,bad)
  if need_comp is not None:assert len(parts)==need_comp,(tag,parts)
  names=[mat.name if mat else '' for mat in me.materials]
  skin_idxs={i for i,n in enumerate(names) if n.startswith('Strawberry M1a')}
  cut_idxs={i for i,n in enumerate(names) if 'rest-space pith/cortex' in n or 'strawberry cut flesh' in n}
  cavity_idxs={i for i,n in enumerate(names) if 'shadowy wet cavity walls' in n}
  counts={'skin':0,'cut':0,'cavity':0}
  for f in me.polygons:
   if f.material_index in skin_idxs:counts['skin']+=1
   if f.material_index in cut_idxs:counts['cut']+=1
   if f.material_index in cavity_idxs:counts['cavity']+=1
  assert counts['skin']>1000 and counts['cavity']>1000
  if need_comp==1:assert counts['cut']>1000,(tag,counts)
  rest=me.attributes.get('fruit_rest');fiber=me.attributes.get('m1e4_fiber')
  assert rest and rest.data_type=='FLOAT_VECTOR' and fiber and fiber.data_type=='FLOAT'
  vals=[x.value for x in fiber.data]
  assert vals and max(vals)>.15 if need_comp==1 else bool(vals)
  positive=sum(x>.11 for x in vals)
  row={'label':tag,'frame':s.frame_current,'vertices':len(me.vertices),'faces':len(me.polygons),'components':len(parts),'nonmanifold_edges':bad,'materials':counts,'fiber_gt_0_11':positive,'fiber_max':round(max(vals),5)}
  if skin:
   # Nearest *surface*, not nearest vertex; compare skin-only points of the
   # original, independently live unrefined GN helper against final geometry.
   orig_ev=helper.evaluated_get(dg);old=orig_ev.to_mesh()
   onames=[m.name if m else '' for m in old.materials]
   oskin={i for i,n in enumerate(onames) if n.startswith('Strawberry M1a')}
   incident=[set() for _ in old.vertices]
   for p in old.polygons:
    for vid in p.vertices:incident[vid].add(p.material_index)
   candidates=[i for i,t in enumerate(incident) if t and t.issubset(oskin)]
   assert len(candidates)>2000
   selected=random.Random(42).sample(candidates,min(2500,len(candidates)))
   sf=[list(f.vertices) for f in me.polygons if f.material_index in skin_idxs]
   bvh=BVHTree.FromPolygons([tuple(v.co) for v in me.vertices],sf,all_triangles=False)
   ds=[bvh.find_nearest(old.vertices[i].co)[3] for i in selected]
   row['skin_surface_max_distance']=round(max(ds),8)
   row['skin_surface_mean_distance']=round(sum(ds)/len(ds),8)
   row['skin_surface_samples']=len(ds)
   assert max(ds)<.005,(tag,max(ds))
   orig_ev.to_mesh_clear()
  ev.to_mesh_clear()
  row['evaluated_seconds']=round(time.perf_counter()-t,3)
  rows.append(row);print('M1E6_GN_ONLY_QA',json.dumps(row),flush=True)
  return row

for frame,comp in [(1,2),(15,1),(21,1),(30,1)]:
 s.frame_set(frame)
 check(f'timeline-{frame}',comp,skin=True)
# No Python handler is active; manual moving changes the GN result regardless.
s.frame_set(21)
orig=knife.location.copy()
knife.location.y+=.3
bpy.context.view_layer.update()
translated=check('manual-knife-y-plus-0.3',1)
assert translated['vertices'] != rows[2]['vertices']
knife.location=orig
bpy.context.view_layer.update()
restored=check('knife-restored',1)
assert restored['vertices']==rows[2]['vertices']
ori=knife.rotation_euler.copy()
knife.rotation_euler.z+=math.radians(18)
bpy.context.view_layer.update()
rot=check('knife-rotated-18deg',1)
assert rot['vertices'] != rows[2]['vertices']
knife.rotation_euler=ori
bpy.context.view_layer.update()
# Source filament network is genuinely read via object-info in Blender GN.
rest=check('fiber-origin',1)
p0=network.location.copy()
network.location.x+=.5
bpy.context.view_layer.update()
shift=check('fiber-source-shifted-x-0.5',1)
assert shift['fiber_gt_0_11'] != rest['fiber_gt_0_11'] or shift['fiber_max'] != rest['fiber_max'],(shift,rest)
network.location=p0
bpy.context.view_layer.update()
# The persistent cavity itself is an actual independently editable 3D object;
# native GN source SDF must invalidate on source geometry transforms.
p0=cavity.location.copy()
cavity.location.x+=.18
bpy.context.view_layer.update()
changed=check('cavity-translated-x-0.18',None)
assert changed['vertices']!=rows[2]['vertices'] or changed['materials']['cavity']!=rows[2]['materials']['cavity'],changed
# KNOWN ISSUE: cavity motion creates small isolated closed 8-vertex islands;
# this is an observed failure of the underlying SDF stage, NOT a QA pass.
assert changed['components']>1,changed
cavity.location=p0
bpy.context.view_layer.update()
recovered=check('cavity-restored',1)
assert recovered['vertices']==rows[2]['vertices'],(recovered,rows[2])

payload={'status':'PASS','scene':bpy.data.filepath,'blender':bpy.app.version_string,'mode':body['m1e6_mode'],'segments':body['m1e6_bevel_segments'],'width':body['m1e6_bevel_width'],'tested':rows,'limitations':['Cavity edit +0.18 yields disconnected micro-islands even when nonmanifold=0; known bug, not production-ready for moving cavity','Selected bevel is NOT selected-face subdivision','zero nonmanifold edges does not exclude self-intersections','materials/fields artistic','no full 60 fps viewport claim']}
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n')
print('M1E6_PURE_GN_NOLIVEPYTHON_PASS',str(out.resolve()),flush=True)

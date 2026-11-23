"""Reopen with scripts disabled; exercise native GN drivers, cutters and fields."""
from pathlib import Path
import sys,json,time,resource,hashlib
import bpy,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from common import *
from build import PIN
from qa_inputs import parse_qa_inputs
p,out,source = parse_qa_inputs(sys.argv[sys.argv.index('--')+1:], PIN)
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);expected=digest_geometry();atlas=atlas_sha();bpy.ops.wm.open_mainfile(filepath=str(p),use_scripts=False);s=bpy.context.scene;b=s.objects[BODY];assert digest_geometry()==expected and atlas_sha()==atlas
assert len([o for o in s.objects if o.get('role')=='achene'])==264
assert all(m.type!='BOOLEAN' for o in s.objects for m in o.modifiers)
source_depth=pit_depths(b.data);rows=[]
for voxel in [.32,.20]:
 for mode,oblique,name in [(0,False,'whole'),(1,False,'plane-center'),(1,True,'plane-oblique'),(2,False,'sphere')]:
  start=time.perf_counter();state(mode,voxel,oblique);me=evaluated(b);elapsed=time.perf_counter()-start;metric=mesh_metrics(me)
  print('SDF_QA',voxel,name,metric,flush=True)
  assert metric['nonmanifold_edges']==metric['zero_edges']==metric['zero_render_triangles']==0 and metric['components']==1 and metric['signed_volume']>0
  visible=[];expected_visible=[];plane=s.objects[PLANE];sphere=s.objects[SPHERE]
  for o in s.objects:
   if o.get('role')!='achene':continue
   center=sum((v.co for v in o.data.vertices),Vector())/len(o.data.vertices)
   inside=((plane.matrix_world.inverted()@center).y<0) if mode==1 else (sphere.matrix_world.inverted()@center).length<1
   if mode==0 or not inside:expected_visible.append(o.name)
   seed=evaluated(o)
   if len(seed.vertices):visible.append(o.name)
   bpy.data.meshes.remove(seed)
  assert sorted(visible)==sorted(expected_visible),(len(visible),len(expected_visible))
  row={'physical_plane_matrix':[list(r) for r in s.objects[PLANE].matrix_world],'physical_sphere_matrix':[list(r) for r in s.objects[SPHERE].matrix_world],'voxel_mm':voxel,'state':name,'metrics':metric,'update_seconds':elapsed,'visible_achene_count':len(visible),'same_cutter_center_mask_matches':True,'max_process_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
  if mode:row['tissue_probes']=tissue_probes(me)
  else:
   row['pit_depths']=pit_depths(me)
   if voxel==.20:
    bodytree=BVHTree.FromPolygons([v.co for v in me.vertices],[f.vertices[:] for f in me.polygons],all_triangles=False);contacts=[]
    for seed in [o for o in s.objects if o.get('role')=='achene']:
     st=BVHTree.FromPolygons([v.co for v in seed.data.vertices],[f.vertices[:] for f in seed.data.polygons],all_triangles=False);contacts.append(len(bodytree.overlap(st)))
    row['actual_seed_mesh_contacts']={'intersecting_seeds':sum(n>0 for n in contacts),'min_triangle_pairs':min(contacts),'max_triangle_pairs':max(contacts)}
  row['geometry_digest']=hashlib.sha256(repr([v.co[:] for v in me.vertices]).encode()).hexdigest();rows.append(row);bpy.data.meshes.remove(me)
assert len({r['geometry_digest'] for r in rows if r['voxel_mm']==.20})==4
assert len({r['visible_achene_count'] for r in rows if r['voxel_mm']==.20})>=3
assert digest_geometry()==expected and atlas_sha()==atlas
# A second sphere position changes evaluated geometry without runtime callbacks.
state(2,.20);before=evaluated(b);s.objects[SPHERE].location.x+=.15;s.objects[SPHERE].update_tag();bpy.context.view_layer.update();after=evaluated(b);assert len(before.vertices)!=len(after.vertices);bpy.data.meshes.remove(before);bpy.data.meshes.remove(after)
out.write_text(json.dumps({'status':'PASS_NATIVE_SDF_TESTED_STATES','blender':bpy.app.version_string,'scripts_disabled':True,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scene_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_geometry_unchanged':True,'packed_atlas_sha256':atlas,'raw_source_pit_depths':source_depth,'rows':rows,'sphere_move_changed_mesh':True,'limitations':'Center culling only; inherited atlas artistic/template-derived; fixed profile in this slice; wetness shader-only.'},indent=2)+'\n')

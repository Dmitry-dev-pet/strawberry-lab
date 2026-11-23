"""Independent saved-scene native Blender QA for baked 3-bite cutter, including BVH seed intersection on actual non-spherical union."""
import bpy,bmesh,numpy as np,hashlib,json,time,sys,resource,argparse
from mathutils.bvhtree import BVHTree
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--scene',required=True,type=Path);p.add_argument('--pose',required=True,choices=['bite-032','bite-020','whole','plane']);p.add_argument('--out',required=True,type=Path);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);src=a.scene.resolve();out=a.out.resolve();pose=a.pose;assert src.is_file() and not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False);s=bpy.context.scene;body=s.objects['Receptacle | canonical PR29 hull'];cutter=s.objects['SDF | editable sphere bite'];plane=s.objects['SDF | editable plane halfspace'];seeds=[o for o in s.objects if o.get('role')=='achene'];assert len(seeds)==264
mode=0 if pose=='whole' else 1 if pose=='plane' else 2;vox=.20 if pose=='bite-020' else .32
body['sdf_mode']=mode;body['sdf_voxel_mm']=vox;body['sdf_use_broad_halo']=1;body['sdf_tissue_gain']=1;body['sdf_cell_surface_gain']=1;
cutter.location=(.82,-.70,-.42);cutter.scale=(1.04,)*3
start=time.monotonic();body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
evalobj=body.evaluated_get(dg);m=evalobj.to_mesh();xyz=np.zeros((len(m.vertices),3),np.float32);m.vertices.foreach_get('co',xyz.ravel());sha=hashlib.sha256(xyz.tobytes()).hexdigest()
bm=bmesh.new();bm.from_mesh(m);bad=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);bm.free();
mat=np.zeros(len(m.polygons),np.int32);m.polygons.foreach_get('material_index',mat);rec={'status':'UNVERIFIED','pose':pose,'scene_sha':hashlib.sha256(src.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'voxel':vox,'body_verts':len(m.vertices),'body_faces':len(m.polygons),'cap_faces':int((mat==2).sum()),'body_coords_sha':sha,'nonmanifold_edges':bad,'positive_volume':bool(vol>0),'body_seconds':round(time.monotonic()-start,3)};evalobj.to_mesh_clear()
assert bad==0 and vol>0,rec
print('BODY_PASS',pose,rec['body_verts'],rec['body_seconds'],flush=True)
if mode==2:
 ev=cutter.evaluated_get(dg);cm=ev.to_mesh();bmeshcut=bmesh.new();bmeshcut.from_mesh(cm);bvh=BVHTree.FromBMesh(bmeshcut)
 matrix=cutter.matrix_world.inverted();
 def inside(world):
  q,n,idx,d=bvh.find_nearest(matrix@world)
  return q is not None and ((matrix@world)-q).dot(n)<-1e-5
 t=time.monotonic();expected=0;visible=0;intruding=0
 for seed in seeds:
  orig_inside=any(inside(seed.matrix_world@v.co) for v in seed.data.vertices)
  if not orig_inside:expected+=1
  eva=seed.evaluated_get(dg);em=eva.to_mesh()
  if em.vertices:
   visible+=1
   intruding+=sum(inside(seed.matrix_world@v.co) for v in em.vertices)
  eva.to_mesh_clear()
 rec.update({'seeds_visible':visible,'seeds_expected':expected,'retained_seed_vertices_inside_actual_cutter':intruding,'guard_seconds':round(time.monotonic()-t,3),'cutter_verts':len(cm.vertices),'cutter_faces':len(cm.polygons)})
 bmeshcut.free();ev.to_mesh_clear()
 assert visible==expected and intruding==0,rec
rec['status']='PASS_REAL_CUTTER_AND_SEED_GUARD';rec['rss_kb']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
out.write_text(json.dumps(rec,indent=2));print('QA_SAVED_PASS',json.dumps(rec),flush=True)

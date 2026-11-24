"""Independent saved-scene cavity QA, distinguishes negative inward boundary from detached flesh."""
import bpy,bmesh,numpy as np,json,sys,hashlib
from pathlib import Path
src,scene,pose,helpers,out=sys.argv[sys.argv.index('--')+1:];out=Path(out);assert not out.exists();sys.path.insert(0,str(Path(helpers)/'juice-lab'));from qa_juice_surface import state,BODY,JUICE,juice_snap,body_snap
WALL='SL Lumen | moist inner wall ARTIST';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(src)=='361696819fd44733d560e3f59b101cd11f59862e7ebd7b7f83ce94fd07909963'
def snap(file):
 bpy.ops.wm.open_mainfile(filepath=file,use_scripts=False);s=bpy.context.scene;b=s.objects[BODY];mm=s.unit_settings.scale_length*1000;state(b,pose,.32,1.);br,p,cap,skin=body_snap(b);jr=juice_snap(s.objects[JUICE],mm,p,cap,skin)
 dg=bpy.context.evaluated_depsgraph_get();ev=b.evaluated_get(dg);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg);bm=bmesh.new();bm.from_mesh(me);non=sum(not e.is_manifold for e in bm.edges);bad_orient=sum(not e.is_contiguous for e in bm.edges);labels=np.full(len(p),-1,np.int32);cnt=0
 for v in bm.verts:
  if labels[v.index]>=0:continue
  labels[v.index]=cnt;stack=[v]
  while stack:
   for e in stack.pop().link_edges:
    for w in e.verts:
     if labels[w.index]<0:labels[w.index]=cnt;stack.append(w)
  cnt+=1
 bm.free();me.calc_loop_triangles();ids=np.empty(len(me.loop_triangles)*3,np.int32);me.loop_triangles.foreach_get('vertices',ids);ids=ids.reshape(-1,3);q=p[ids].astype(np.float64)*mm;tri_vol=np.einsum('ij,ij->i',q[:,0],np.cross(q[:,1],q[:,2]))/6.;cross=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);degen=int(np.sum(np.einsum('ij,ij->i',cross,cross)<1e-14));vol=np.bincount(labels[ids[:,0]],weights=tri_vol,minlength=cnt);wi=next((i for i,m in enumerate(me.materials) if m and m.name==WALL),-1);wall_count=0;wall_labels=set();wall_points=set()
 if wi>=0:
  for f in me.polygons:
   if f.material_index==wi:wall_count+=1;wall_labels.add(int(labels[f.vertices[0]]));wall_points.update(f.vertices)
 br.update(nonmanifold=non,orientation_edges=bad_orient,degenerate_triangles=degen,component_signed_volumes_mm3=vol.tolist(),wall_faces=wall_count,wall_component_ids=sorted(wall_labels),juice=jr)
 assert non==0 and bad_orient==0 and degen==0 and vol.sum()>0 and (vol>0).sum()==1,br
 if wall_points:assert not np.any(cap[np.array(list(wall_points))]&~skin[np.array(list(wall_points))]);br['wall_excluded_from_juice_cap_interior']=True
 ev.to_mesh_clear();return br,p[labels==int(np.argmax(vol))]
if pose=='whole': A,pa=snap(src)
else:
 old=json.loads((Path(helpers)/'ring-lab'/('qa-'+pose+'.json')).read_text());assert old['source_sha']==sha(src);A=dict(old['A'],component_signed_volumes_mm3=[old['A']['volume_mm3']],juice=old['juice_A']);pa=None
B,pb=snap(scene);assert sum(B['component_signed_volumes_mm3'])<sum(A['component_signed_volumes_mm3']) or pose=='bite';assert B['wall_faces']>0,B
r=dict(status='PASS',pose=pose,voxel_mm=.32,A=A,B=B,source_sha=sha(src),scene_sha=sha(scene))
if pose=='whole':
 def keys(x):return np.sort(np.ascontiguousarray(x).view(np.dtype((np.void,12))).ravel())
 assert len(B['component_signed_volumes_mm3'])==2 and min(B['component_signed_volumes_mm3'])<0 and len(B['wall_component_ids'])==1 and B['wall_component_ids'][0]==int(np.argmin(B['component_signed_volumes_mm3']));assert np.array_equal(keys(pa),keys(pb)),('exterior coordinate set changed',len(pa),len(pb));assert B['juice']['faces']==0;r['outer_coordinates_exactly_equal']=True
if pose=='plane':assert len(B['component_signed_volumes_mm3'])==1,'Expected plane-open lumen joined boundary'
out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)

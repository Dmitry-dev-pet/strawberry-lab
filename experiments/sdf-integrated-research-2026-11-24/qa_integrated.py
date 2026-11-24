"""Independent saved-scene checks of combined PR50 research. Reuses existing juice QA."""
import bpy,bmesh,numpy as np,json,sys,hashlib,time
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
scene,pose,voxel,helper,field,prior,out=sys.argv[sys.argv.index('--')+1:];voxel=float(voxel);out=Path(out);assert not out.exists();sys.path.insert(0,str(Path(helper).parent));from qa_juice_surface import state,body_snap,juice_snap,BODY,JUICE,attr,pos,sha
WALL='SL Lumen | moist inner wall ARTIST';CAP='SDF | inherited 150^3 tissue + own multiscale wetness';t=time.monotonic();bpy.ops.wm.open_mainfile(filepath=scene,use_scripts=False);s=bpy.context.scene;b=s.objects[BODY];j=s.objects[JUICE];mm=s.unit_settings.scale_length*1000;assert not j.visible_shadow
state(b,pose,voxel,1.);br,p,cap,skin=body_snap(b);dg=bpy.context.evaluated_depsgraph_get();ev=b.evaluated_get(dg);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg);bm=bmesh.new();bm.from_mesh(me);non=sum(not e.is_manifold for e in bm.edges);ori=sum(not e.is_contiguous for e in bm.edges);labels=np.full(len(p),-1,np.int32);cnt=0
for v in bm.verts:
 if labels[v.index]>=0:continue
 labels[v.index]=cnt;stack=[v]
 while stack:
  for e in stack.pop().link_edges:
   for w in e.verts:
    if labels[w.index]<0:labels[w.index]=cnt;stack.append(w)
 cnt+=1
bm.free();me.calc_loop_triangles();ids=np.empty(len(me.loop_triangles)*3,np.int32);me.loop_triangles.foreach_get('vertices',ids);ids=ids.reshape(-1,3);q=p[ids].astype(np.float64)*mm;tv=np.einsum('ij,ij->i',q[:,0],np.cross(q[:,1],q[:,2]))/6.;cross=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);degen=int(np.sum(np.einsum('ij,ij->i',cross,cross)<1e-14));vol=np.bincount(labels[ids[:,0]],weights=tv,minlength=cnt);wi=next(i for i,m in enumerate(me.materials) if m and m.name==WALL);wall=[f for f in me.polygons if f.material_index==wi];wp=np.array(sorted({i for f in wall for i in f.vertices}));assert len(wall)>0 and not np.any(cap[wp]&~skin[wp]);assert non==ori==degen==0 and sum(vol>0)==1 and sum(vol)>0
br.update(nonmanifold=non,orientation_edges=ori,degenerate_triangles=degen,component_signed_volumes_mm3=vol.tolist(),wall_faces=len(wall),wall_excluded_from_cap_interior=True)
if pose=='whole':
 assert len(vol)==2 and min(vol)<0;old=json.loads(Path(prior).read_text())['B'];assert br['coords_sha']==old['coords_sha'] and br['topology_sha']==old['topology_sha'];br['exact_whole_previous_protrusions']=True
else:
 if pose=='plane':assert len(vol)==1
 if pose=='bite':assert len(vol)==2 and min(vol)<0
 # Check actual R/H/B at cap samples against independent NumPy trilinear interpolation.
 rst=attr(me,'sdf_rest_position',True);ix=np.flatnonzero(cap&~skin);ix=ix[np.linspace(0,len(ix)-1,256,dtype=int)];xyz=rst[ix]*mm+np.array([0,0,27.]);coord=np.clip((xyz-np.array([-25.,-25.,-2.]))/np.array([50.,50.,54.])*191,0,191);lo=np.minimum(np.floor(coord).astype(int),190);f=coord-lo
 with np.load(field) as z:
  for attrname,key in [('sl_vascular_core','core'),('sl_vascular_halo','halo'),('sl_ring_relative','ring_relative')]:
   arr=z[key];val=np.zeros(len(ix));a=attr(me,attrname)[ix]
   for dx in [0,1]:
    for dy in [0,1]:
     for dz in [0,1]:val+=arr[lo[:,2]+dz,lo[:,1]+dy,lo[:,0]+dx]*((f[:,0] if dx else 1-f[:,0])*(f[:,1] if dy else 1-f[:,1])*(f[:,2] if dz else 1-f[:,2]))
   err=float(abs(a-val).max());assert err<.001,(attrname,err);br[attrname]={'max_error':err,'min':float(a.min()),'max':float(a.max()),'samples':len(ix)}
ev.to_mesh_clear();jr=juice_snap(j,mm,p,cap,skin);assert (jr['faces']==0)==(pose=='whole');br['juice']=jr
# Inspect only the original scene's stored seed policy; no claim of PR48 guard.
res=dict(status='PASS',pose=pose,voxel_mm=voxel,scene_sha=hashlib.sha256(Path(scene).read_bytes()).hexdigest(),body=br,elapsed_s=time.monotonic()-t,scope='body+wall+existing juice regression; no fresh seed/calyx or exhaustive self-intersection check')
out.write_text(json.dumps(res,indent=2)+'\n');print(json.dumps(res),flush=True)

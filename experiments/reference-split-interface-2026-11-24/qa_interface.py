"""Independent saved-scene A/B. Signed nearest-normal probes, not exact CSG proof."""
import sys,json,hashlib,time,math
from pathlib import Path
import numpy as np,bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
old,new,pose,voxel,helper,out=sys.argv[sys.argv.index('--')+1:];voxel=float(voxel);out=Path(out);assert not out.exists();sys.path.insert(0,str(Path(helper).resolve().parent))
from qa_split import setup,mesh_eval,co,polys,pa,top,sdf,stats,sha,ROOT,SKIN,SEEDS,FLESH,SOURCE,PLANE,SPHERE,CAP
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_interface import PIN,gitsha,SPLIT_SHA
assert sha(old)==PIN and gitsha(Path(helper).parent/'build_split.py')==SPLIT_SHA

def h(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def tri(me):
 me.calc_loop_triangles();a=np.empty(3*len(me.loop_triangles),np.int32);me.loop_triangles.foreach_get('vertices',a);return a.reshape(-1,3)
def attr_hash(me,name):return h(pa(me,name))
def geometry(name,attrs):
 ev,me=mesh_eval(name);r=dict(coords=h(co(me)),tri=h(tri(me)),attrs={a:attr_hash(me,a) for a in attrs});ev.to_mesh_clear();return r

def snapshot():
 return {SKIN:geometry(SKIN,['sl_rest_position','achene_pit']),SEEDS:geometry(SEEDS,['sl_rest_position','sl_anchor_index'])}
def signed(tree,points):
 r=[]
 for v in points:
  q,n,_,d=tree.find_nearest(Vector(v));assert q is not None
  r.append(float((Vector(v)-q).dot(n)))
 return np.array(r)

def inverse(p,root):
 p=p.astype(np.float64).copy();a,b,h0=[float(root[k]) for k in ('shape_a','shape_b','shape_h')];p[:,2]/=h0;t=p[:,2]/24-1;s=1+a*np.exp(-((t-.5)/.36)**2)+b*np.exp(-((t+.3)/.4)**2);p[:,:2]/=s[:,None];return p

def check_flesh(mode,rim,hull,root,check_attrs):
 ev,me=mesh_eval(FLESH);v=co(me);ts=tri(me);faces=polys(me);tp=top(me)[0];r={'mesh':tp,'coords':h(v),'tri':h(ts),'polygon_connectivity':hashlib.sha256(repr(faces).encode()).hexdigest()};assert tp['boundary_edges']==tp['wire_or_over_two_face_edges']==tp['inconsistent_edges']==tp['degenerate_triangles']==0,tp
 if not mode:assert not len(v);ev.to_mesh_clear();return r,v,ts
 assert tp['signed_volume_mm3']>0
 matnames=[m.name if m else None for m in me.materials];ci=matnames.index(CAP);cap=[f for f,p in zip(faces,me.polygons) if p.material_index==ci];assert cap
 alltree=BVHTree.FromPolygons(v.tolist(),faces);captree=BVHTree.FromPolygons(v.tolist(),cap)
 d=np.array([captree.find_nearest(Vector(x))[3] for x in rim]);sg=signed(alltree,rim)
 if mode==1:
  th=bpy.data.objects[PLANE].rotation_euler.z;n=np.tile(np.array([-math.sin(th),math.cos(th),0.]),(len(rim),1))
 else:
  n=rim-np.array(bpy.data.objects[SPHERE].location);n=n/np.linalg.norm(n,axis=1,keepdims=True)
 # A second probe 0.05mm toward retained tissue, independent of cap classification.
 r['seam']={'samples':len(rim),'nearest_cap_mm':stats(d),'over_0_10mm':int((d>.1).sum()),'rim_signed_flesh_mm':stats(sg),'rim_outside_gt_0_03mm':int((sg>.03).sum())}
 for offset in (.05,.15):
  sg2=signed(alltree,rim+n*offset);r['seam'][f'kept_side_{offset:.2f}_signed_mm']=stats(sg2);r['seam'][f'kept_side_{offset:.2f}_outside_gt_0_03mm']=int((sg2>.03).sum())
 # Sign convention: positive is outside uncut original skin (outward protrusion).
 cd=sdf(v,mode);outer=v[cd>1.5];op=signed(hull,outer[::max(1,len(outer)//8000)]);near=v[abs(cd)<.5];near=near[::max(1,len(near)//12000)];ns=signed(hull,near)
 r['outer']={'away_samples':len(op),'away_signed_mm':stats(op),'away_outside_gt_0_03mm':int((op>.03).sum()),'near_samples':len(ns),'near_signed_mm':stats(ns),'near_outside_gt_0_10mm':int((ns>.1).sum()),'min_analytic_cutter_margin_mm':float(cd.min())}
 if check_attrs:
  rest=pa(me,'sl_rest_position');ref=pa(me,'sl_reference_position');nor=pa(me,'sl_reference_normal');edge=pa(me,'sl_edge_distance_mm');off=pa(me,'sl_interface_offset_mm');expected=inverse(v,root);err=float(np.max(np.abs(rest-expected)));assert err<1e-4,err
  assert np.array_equal(ref,v);assert np.isfinite(edge).all() and np.isfinite(nor).all() and np.isfinite(off).all();assert np.min(edge)>=0 and np.max(np.abs(off))<=.200001
  indices=np.linspace(0,len(v)-1,min(1024,len(v)),dtype=int);exact=np.array([hull.find_nearest(Vector(v[i]))[3] for i in indices]);ee=float(np.max(np.abs(edge[indices]-exact)));assert ee<1e-4,ee
  r['rest']={'max_inverse_error_mm':err,'reference_position_exact':True,'normal_length_range':[float(np.linalg.norm(nor,axis=1).min()),float(np.linalg.norm(nor,axis=1).max())],'edge_samples':len(indices),'edge_distance_max_error_mm':ee,'edge_distance_range_mm':[float(edge.min()),float(edge.max())],'offset_range_mm':[float(off.min()),float(off.max())]}
 ev.to_mesh_clear();return r,v,ts

def setup_scene(path):
 bpy.ops.wm.open_mainfile(filepath=str(Path(path).resolve()),use_scripts=False);mode=setup(pose,voxel);root=bpy.data.objects[ROOT]
 # Whole evaluated hull, same shape as current cut.
 root['split_mode']=0;root.update_tag();bpy.context.view_layer.update();ev,me=mesh_eval(SKIN);hull=BVHTree.FromPolygons(co(me).tolist(),tri(me).tolist(),all_triangles=True);ev.to_mesh_clear();root['split_mode']=mode;root.update_tag();bpy.context.view_layer.update();ev,me=mesh_eval(SKIN);v=co(me);_,edges=top(me);rim=np.array([v[i] for i in sorted(set(i for e in edges for i in e))]);mid=np.array([(v[i]+v[j])*.5 for i,j in edges]);rim=np.concatenate([rim,mid]) if mode else np.empty((0,3));ev.to_mesh_clear();return mode,root,hull,rim

start=time.perf_counter();mode,root,hull,rim=setup_scene(old);base_ext=snapshot();base,bv,bt=check_flesh(mode,rim,hull,root,False);print('BASE',pose,base.get('seam'),flush=True)
mode,root,hull,rim=setup_scene(new);report={'pose':pose,'voxel_mm':voxel,'old_sha':sha(old),'new_sha':sha(new),'baseline':base,'candidates':[]}
for gain in (0.,1.):
 root['interface_gain']=gain;root.update_tag();bpy.context.view_layer.update();ext=snapshot();assert ext==base_ext,(pose,gain,'skin/seed changed');r,v,ts=check_flesh(mode,rim,hull,root,True);r['gain']=gain;r['skin_seeds_exact']=True;assert r['polygon_connectivity']==base['polygon_connectivity'];r['polygon_connectivity_exact']=True;r['render_triangles_exact']=bool(np.array_equal(ts,bt));r['max_displacement_mm']=float(np.linalg.norm(v-bv,axis=1).max()) if len(v) else 0
 if gain==0:assert np.array_equal(v,bv) and np.array_equal(ts,bt),(pose,r['max_displacement_mm'])
 report['candidates'].append(r);print('CANDIDATE',pose,gain,r.get('seam'),r.get('outer'),r.get('rest'),flush=True)
report.update(elapsed_seconds=time.perf_counter()-start,technical_geometry_pass=True);out.write_text(json.dumps(report,indent=2)+'\n')

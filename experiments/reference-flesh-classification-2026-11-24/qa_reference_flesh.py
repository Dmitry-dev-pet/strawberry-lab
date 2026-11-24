"""Reopen control/candidate and independently check provenance, displacement, and sampled interface."""
import sys,json,time,hashlib,math
from pathlib import Path
import numpy as np,bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
old,new,helper,pose,voxel,out=sys.argv[sys.argv.index('--')+1:];voxel=float(voxel);out=Path(out);assert not out.exists();sys.path.insert(0,str(Path(helper).resolve().parent))
from qa_split import setup,mesh_eval,co,polys,top,sdf,stats,ROOT,SKIN,SEEDS,FLESH,SOURCE,PLANE,SPHERE,CAP
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_reference_flesh import sha,gitsha,PIN,HELPER
assert sha(old)==PIN and gitsha(Path(helper).parent/'build_split.py')==HELPER

def h(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def tri(me):
 me.calc_loop_triangles();a=np.empty(3*len(me.loop_triangles),np.int32);me.loop_triangles.foreach_get('vertices',a);return a.reshape(-1,3)
def at(me,name):
 a=me.attributes[name];v=a.data_type=='FLOAT_VECTOR';dtype=np.float32 if v or a.data_type=='FLOAT' else np.bool_ if a.data_type=='BOOLEAN' else np.int32;out=np.empty(len(a.data)*(3 if v else 1),dtype);a.data.foreach_get('vector' if v else 'value',out);return out.reshape(-1,3) if v else out

def geom(name,attrs):
 ev,me=mesh_eval(name);r={'coords':h(co(me)),'tri':h(tri(me)),'attrs':{a:h(at(me,a)) for a in attrs}};ev.to_mesh_clear();return r

def tree(v,t):return BVHTree.FromPolygons(v.tolist(),t.tolist(),all_triangles=True)
def near(t,points):
 ds=[];sg=[]
 for x in points:
  p,n,_,d=t.find_nearest(Vector(x));assert p is not None;ds.append(float(d));sg.append(float((Vector(x)-p).dot(n)))
 return np.array(ds),np.array(sg)
DIRS=[Vector((.713,.391,.581)).normalized(),Vector((-.237,.841,.487)).normalized()]
def inside_one(t,x,d):
 p=Vector(x);hits=0
 for _ in range(64):
  loc,_,idx,dist=t.ray_cast(p,d,200.)
  if idx is None:return bool(hits%2)
  hits+=1;p=loc+d*0.00002
 return None

def inside(t,x):
 a,b=(inside_one(t,x,d) for d in DIRS);return a if a is not None and a==b else None

def inverse(p,r):
 q=p.astype(float).copy();a,b,h0=[float(r[k]) for k in ('shape_a','shape_b','shape_h')];q[:,2]/=h0;t=q[:,2]/24-1;s=1+a*np.exp(-((t-.5)/.36)**2)+b*np.exp(-((t+.3)/.4)**2);q[:,:2]/=s[:,None];return q

def cap_tri(me):
 ci=next(i for i,m in enumerate(me.materials) if m and m.name==CAP);me.calc_loop_triangles();return np.asarray([tuple(t.vertices) for t in me.loop_triangles if t.material_index==ci],np.int32),np.array([p.material_index==ci for p in me.polygons])

def probes(rim,hull,mode):
 if mode==1:
  th=bpy.data.objects[PLANE].rotation_euler.z;n=np.tile(np.array([-math.sin(th),math.cos(th),0.]),(len(rim),1))
 else:
  n=rim-np.array(bpy.data.objects[SPHERE].location);n=n/np.linalg.norm(n,axis=1,keepdims=True)
 result={}
 for offset in (.05,.15):
  q=rim+n*offset;d,_=near(hull,q);valid=[];uncertain=0
  for i,x in enumerate(q):
   if d[i]<.005:uncertain+=1;continue
   yes=inside(hull,x)
   if yes is None:uncertain+=1
   elif yes and sdf(q[i:i+1],mode)[0]>.005:valid.append(i)
  result[str(offset)]={'points':q[valid],'excluded':len(q)-len(valid),'uncertain_hull':uncertain}
 return result

def mesh_report(mode,rim,hull,valid):
 ev,m=mesh_eval(FLESH);v=co(m);t=tri(m);f=polys(m);r={'topology':top(m)[0],'coords_sha':h(v),'tri_sha':h(t),'polygon_sha':hashlib.sha256(repr(f).encode()).hexdigest()};tp=r['topology'];assert tp['boundary_edges']==tp['wire_or_over_two_face_edges']==tp['inconsistent_edges']==tp['degenerate_triangles']==0,tp
 if not mode:assert len(v)==0;return ev,m,r,v,f,None
 assert tp['signed_volume_mm3']>0;ct,mask=cap_tri(m);assert len(ct)>0
 alltree=tree(v,t);captree=tree(v,ct);d,_=near(captree,rim);_,signed=near(alltree,rim);r['rim']={'samples':len(rim),'nearest_cap_mm':stats(d),'over_0_10mm':int((d>.10).sum()),'approx_signed_outside_gt_0_03mm':int((signed>.03).sum())};r['hull_aware_probes']={}
 for key,data in valid.items():
  q=data['points'];ds,sg=near(alltree,q);outside=0;uncertain=0
  for x,d0 in zip(q,ds):
   if d0<.005:uncertain+=1;continue
   yes=inside(alltree,x)
   if yes is None:uncertain+=1
   elif not yes and d0>.03:outside+=1
  r['hull_aware_probes'][key]={'eligible':len(q),'excluded':data['excluded'],'uncertain_hull':data['uncertain_hull'],'uncertain_flesh':uncertain,'outside_flesh_gt_0_03mm':outside,'distance_to_flesh_mm':stats(ds)}
 c=sdf(v,mode);a=v[c>1.5];_,sign=near(hull,a[::max(1,len(a)//8000)]);r['outer_away']={'samples':len(sign),'outside_gt_0_03mm':int((sign>.03).sum()),'signed_mm':stats(sign)};r['cap_faces']=int(mask.sum());r['min_analytic_cutter_margin_mm']=float(c.min());return ev,m,r,v,f,mask

def open_scene(p):
 bpy.ops.wm.open_mainfile(filepath=str(Path(p).resolve()),use_scripts=False);mode=setup(pose,voxel);root=bpy.data.objects[ROOT];return mode,root

start=time.perf_counter();mode,root=open_scene(old);assert root['interface_gain']==0
root['split_mode']=0;root.update_tag();bpy.context.view_layer.update();ev,m=mesh_eval(SKIN);hull=tree(co(m),tri(m));ev.to_mesh_clear();root['split_mode']=mode;root.update_tag();bpy.context.view_layer.update()
ev,m=mesh_eval(SKIN);sv=co(m);_,edges=top(m);rim=np.concatenate([sv[sorted(set(i for e in edges for i in e))],np.array([(sv[i]+sv[j])*.5 for i,j in edges])]) if mode else np.empty((0,3));ev.to_mesh_clear();valid=probes(rim,hull,mode) if mode else {}
base_ext={SKIN:geom(SKIN,['sl_rest_position','achene_pit']),SEEDS:geom(SEEDS,['sl_rest_position','sl_anchor_index'])};ev,m,base,bv,bf,bmask=mesh_report(mode,rim,hull,valid);ev.to_mesh_clear()
root['flesh_recess_mm']=0.;root.update_tag();bpy.context.view_layer.update();ev,m=mesh_eval(FLESH);pre=co(m);assert polys(m)==bf;ev.to_mesh_clear();print('CONTROL',pose,voxel,base.get('rim'),flush=True)
mode,root=open_scene(new);ext={SKIN:geom(SKIN,['sl_rest_position','achene_pit']),SEEDS:geom(SEEDS,['sl_rest_position','sl_anchor_index'])};assert ext==base_ext,'skin or seeds changed';ev,m,r,v,f,mask=mesh_report(mode,rim,hull,valid);assert f==bf
if mode:
 p=at(m,'sl_pre_recess_position');n=at(m,'sl_pre_recess_normal');d=at(m,'sl_edge_distance_mm');sample=at(m,'sl_cutter_signed_mm');cut=at(m,'sl_cut_point');outer=at(m,'sl_outer_recess_point');rest=at(m,'sl_rest_position');ref=at(m,'sl_reference_position');assert np.array_equal(p,pre),'raw SDF positions changed';assert np.isfinite(sample).all() and np.isfinite(d).all();assert np.array_equal(cut,sample<np.float32(.8*voxel));assert np.array_equal(outer,(~cut)&(d<np.float32(voxel)));assert cut.any() and outer.any();delta=v-p;expected=-n*float(root['flesh_recess_mm'])*outer[:,None];err=float(np.max(np.abs(delta-expected)));assert err<1e-5,err;assert np.array_equal(v[cut],p[cut]);assert np.array_equal(v[~outer],p[~outer]);resterr=float(np.max(abs(rest-inverse(v,root))));assert resterr<1e-4 and np.array_equal(ref,v)
 se,sm=mesh_eval(SOURCE);refv=co(sm);reft=tri(sm);rt=tree(refv,reft);reftop=top(sm)[0];assert reftop['boundary_edges']==reftop['wire_or_over_two_face_edges']==reftop['inconsistent_edges']==reftop['degenerate_triangles']==0;se.to_mesh_clear();ii=np.linspace(0,len(p)-1,min(4096,len(p)),dtype=int);dr,_=near(rt,p[ii]);ed=float(np.max(np.abs(dr-d[ii])));assert ed<1e-4,ed
 analytic=sdf(p,mode);near_c=np.abs(analytic)<voxel*.75;serr=float(np.max(abs(sample[near_c]-analytic[near_c])));assert serr<voxel*.25,serr
 cent=np.asarray([p[list(q)].mean(axis=0) for q in f]);ac=sdf(cent,mode);dd,_=near(rt,cent);cc=(dd>1.5*voxel)&(abs(ac)<.4*voxel);oo=(dd<voxel)&(ac>1.5*voxel);assert oo.any();wide=(dd>1.5*voxel)&(abs(ac)<.75*voxel);assert wide.any()
 r['provenance']={'raw_grid_exact':True,'uncut_reference_topology':reftop,'edge_samples':len(ii),'edge_error_mm':ed,'cutter_sample_near_count':int(near_c.sum()),'analytic_cutter_max_error_mm':serr,'cap_points':int(cut.sum()),'recess_points':int(outer.sum()),'cap_points_unchanged':True,'max_displacement_equation_error_mm':err,'max_inverse_error_mm':resterr,'face_label_changed':int((mask!=bmask).sum()),'clear_cap_faces':int(cc.sum()),'clear_outer_faces':int(oo.sum()),'old_clear_cap_wrong':int((cc&~bmask).sum()) if cc.any() else None,'new_clear_cap_wrong':int((cc&~mask).sum()) if cc.any() else None,'wide_cap_probe_faces':int(wide.sum()),'wide_cap_old_wrong':int((wide&~bmask).sum()),'wide_cap_new_wrong':int((wide&~mask).sum()),'old_clear_outer_wrong':int((oo&bmask).sum()),'new_clear_outer_wrong':int((oo&mask).sum()),'unclassified_ambiguous_faces':int((~(cc|oo)).sum())}
ev.to_mesh_clear();report={'pose':pose,'voxel_mm':voxel,'baseline_sha':sha(old),'candidate_sha':sha(new),'skin_seed_exact':True,'baseline':base,'candidate':r,'geometry_gate_pass':True,'elapsed_seconds':time.perf_counter()-start};out.write_text(json.dumps(report,indent=2)+'\n');print('RESULT',json.dumps(report),flush=True)

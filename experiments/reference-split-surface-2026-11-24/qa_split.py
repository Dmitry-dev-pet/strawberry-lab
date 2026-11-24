"""Saved-scene QA; separate interface error from closed-flesh topology."""
import bpy,bmesh,numpy as np,sys,json,time,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_split import *
POSES={'whole':(0,(0,0,24),0,(0,0,1.)), 'plane':(1,(0,0,24),0,(0,0,1.)), 'tilted':(1,(0,1.7,24),.43,(.16,-.10,1.12)), 'bite':(2,(0,0,24),0,(0,0,1.))}
def setup(pose,voxel=.32):
 mode,loc,angle,shape=POSES[pose];r=bpy.data.objects[ROOT];r['split_mode']=mode;r['flesh_voxel_mm']=voxel
 for key,val in zip(('shape_a','shape_b','shape_h'),shape):r[key]=val
 p=bpy.data.objects[PLANE];p.location=loc;p.rotation_euler=(0,0,angle);r.update_tag();bpy.context.view_layer.update();return mode

def mesh_eval(name):
 o=bpy.data.objects[name];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();return ev,me

def co(me):
 a=np.empty(3*len(me.vertices),np.float32);me.vertices.foreach_get('co',a);return a.reshape(-1,3)
def polys(me):return [tuple(p.vertices) for p in me.polygons]
def pa(me,name):
 a=me.attributes[name];v=a.data_type=='FLOAT_VECTOR';dtype=np.float32 if v or a.data_type=='FLOAT' else np.int32;out=np.empty(len(a.data)*(3 if v else 1),dtype);a.data.foreach_get('vector' if v else 'value',out);return out.reshape(-1,3) if v else out

def top(me):
 bm=bmesh.new();bm.from_mesh(me);bm.verts.index_update();boundary=[(e.verts[0].index,e.verts[1].index) for e in bm.edges if len(e.link_faces)==1];adj={}
 for i,j in boundary:adj.setdefault(i,[]).append(j);adj.setdefault(j,[]).append(i)
 unseen=set(adj);loops=0
 while unseen:
  loops+=1;todo=[unseen.pop()]
  while todo:
   for j in adj[todo.pop()]:
    if j in unseen:unseen.remove(j);todo.append(j)
 res={'vertices':len(me.vertices),'faces':len(me.polygons),'boundary_edges':len(boundary),'boundary_components':loops,'boundary_bad_valence':sum(len(v)!=2 for v in adj.values()),'wire_or_over_two_face_edges':sum(len(e.link_faces) not in (1,2) for e in bm.edges),'inconsistent_edges':sum(len(e.link_faces)==2 and not e.is_contiguous for e in bm.edges),'signed_volume_mm3':float(bm.calc_volume(signed=True))};bm.free();me.calc_loop_triangles();res['degenerate_triangles']=sum(t.area<1e-9 for t in me.loop_triangles);return res,boundary

def sdf(p,mode):
 if mode==1:
  c=bpy.data.objects[PLANE];q=np.asarray(c.location);theta=c.rotation_euler.z;n=np.array([-math.sin(theta),math.cos(theta),0]);return (p-q)@n
 if mode==2:
  c=bpy.data.objects[SPHERE];return np.linalg.norm(p-np.asarray(c.location),axis=-1)-12*float(c.scale.x)
 return np.ones(len(p))*100

def stats(x):
 x=np.array(x);return {'min':float(x.min()),'median':float(np.median(x)),'p95':float(np.percentile(x,95)),'max':float(x.max())} if len(x) else None

def main():
 src,pose,out,*opts=sys.argv[sys.argv.index('--')+1:];out=Path(out);assert not out.exists();bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()),use_scripts=False);root=bpy.data.objects[ROOT];t=time.perf_counter();mode=setup(pose,float(opts[0]) if opts else .32);r={'source_sha':sha(src),'pose':pose,'shape':[root[k] for k in ('shape_a','shape_b','shape_h')],'voxel_mm':root['flesh_voxel_mm'],'stock_key':root['neutral_stock_key'],'anchor_digest':root['anchor_digest']}
 root['split_mode']=0;root.update_tag();bpy.context.view_layer.update();ev,ref=mesh_eval(SKIN);orig=co(ref);raw=co(bpy.data.objects[SKIN].data);rest=pa(ref,'sl_rest_position');ref_faces=polys(ref);assert np.array_equal(rest,raw);orig_pit=pa(ref,'achene_pit');ev.to_mesh_clear();ref_tree=BVHTree.FromPolygons(orig.tolist(),ref_faces)
 root['split_mode']=mode;root.update_tag();bpy.context.view_layer.update();ev,skin=mesh_eval(SKIN);sv=co(skin);skin_top,edges=top(skin);r['skin']=skin_top;assert skin_top['wire_or_over_two_face_edges']==skin_top['inconsistent_edges']==skin_top['boundary_bad_valence']==0,skin_top
 if mode==0:assert np.array_equal(sv,orig) and polys(skin)==ref_faces and not edges
 mask=sdf(orig,mode)>.5;safe=orig[mask];vs=set(map(tuple,sv));present=np.array([tuple(v) in vs for v in safe]);r['skin']['original_safe_vertices']=int(len(safe));r['skin']['exact_safe_vertices']=int(present.sum());r['skin']['exact_safe_fraction']=float(present.mean());r['skin']['position_sha']=hashlib.sha256(sv.tobytes()).hexdigest();r['skin']['pit_sha']=hashlib.sha256(pa(skin,'achene_pit').tobytes()).hexdigest();r['skin']['raw_unchanged']=bool(np.array_equal(co(bpy.data.objects[SKIN].data),raw));assert r['skin']['raw_unchanged'];rim=np.array([sv[i] for i in sorted(set(v for e in edges for v in e))]);r['skin']['rim_abs_cutter_distance_mm']=stats(np.abs(sdf(rim,mode))) if len(rim) else None
 r['skin']['safe_pit_vertex_count']=int(np.sum((orig_pit>.01)&mask));ap=pa(skin,'achene_pit');orig_vals={tuple(v):float(w) for v,w in zip(safe,orig_pit[mask])};diff=[abs(float(w)-orig_vals[tuple(v)]) for v,w in zip(sv,ap) if tuple(v) in orig_vals];r['skin']['retained_pit_attribute_max_error']=max(diff,default=None)
 ev2,seed=mesh_eval(SEEDS);se=co(seed);idx=pa(seed,'sl_anchor_index');r['seeds']={'kept_ids':int(len(set(idx))),'vertices':len(se),'min_analytic_cutter_margin_mm':float(sdf(se,mode).min()) if len(se) and mode else None};assert len(set(idx))==264 if mode==0 else np.all(sdf(se,mode)>=-1e-4);raw_ids=pa(bpy.data.objects[SEEDS].data,'sl_anchor_index');expected=np.bincount(raw_ids,minlength=264);got=np.bincount(idx,minlength=264);assert np.all((got==0)|(got==expected));r['seeds']['all_kept_solids_complete']=True;r['seeds']['position_sha']=hashlib.sha256(se.tobytes()).hexdigest()
 if mode==2:
  st=BVHTree.FromPolygons(se.tolist(),polys(seed));d=st.find_nearest(bpy.data.objects[SPHERE].location)[3]-12*float(bpy.data.objects[SPHERE].scale.x);r['seeds']['triangle_min_sphere_margin_mm']=float(d);assert d>=-1e-4
 ev3,flesh=mesh_eval(FLESH);fv=co(flesh);r['flesh']=top(flesh)[0];cap_faces=[]
 if mode:
  matnames=[m.name if m else None for m in flesh.materials];r['flesh']['materials']=matnames;cap_index=matnames.index(CAP);cap_faces=[tuple(p.vertices) for p in flesh.polygons if p.material_index==cap_index];r['flesh']['cap_faces']=len(cap_faces);assert cap_faces
  assert r['flesh']['boundary_edges']==r['flesh']['wire_or_over_two_face_edges']==r['flesh']['inconsistent_edges']==0 and r['flesh']['signed_volume_mm3']>0,r['flesh']
  cap_tree=BVHTree.FromPolygons(fv.tolist(),cap_faces);rim_samples=np.concatenate([rim,np.array([(sv[i]+sv[j])*.5 for i,j in edges])]);nearest=[cap_tree.find_nearest(Vector(v)) for v in rim_samples];dist=np.array([float(x[3]) for x in nearest]);r['seam']={'samples':len(dist),'rim_to_tissue_mm':stats(dist),'over_0_10mm':int((dist>.10).sum()),'over_0_32mm':int((dist>.32).sum()),'criterion':'proximity, not watertight combined topology'}
  sel=sdf(fv,mode)>1.5;sample=fv[sel][::max(1,int(sel.sum())//8000)];signed=[]
  for v in sample:
   p,n,_,_=ref_tree.find_nearest(Vector(v));signed.append(float((Vector(v)-p).dot(n)))
  r['flesh']['outer_samples']=len(signed);r['flesh']['outer_signed_distance_mm']=stats(signed);r['flesh']['outer_protrusions_over_0_03mm']=int(np.sum(np.array(signed)>.03))
 else:assert len(fv)==0
 r['elapsed_seconds']=time.perf_counter()-t;r['blender']=bpy.app.version_string;out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
 for e in (ev,ev2,ev3):e.to_mesh_clear()
if __name__=='__main__':main()

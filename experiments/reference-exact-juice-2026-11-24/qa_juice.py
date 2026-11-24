"""Independent saved-scene regression: immutable body, cap-only liquid patches."""
import bpy,bmesh,sys,json,time,hashlib,numpy as np
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE/'deps')]
from build_juice import EXACT,ROOT,JUICE,MAT,PIN,sha
from qa_split import setup,mesh_eval,co,SKIN,FLESH,SEEDS

def attr(me,k):
 a=me.attributes[k];vec=a.data_type=='FLOAT_VECTOR';dt=np.float32 if vec or a.data_type=='FLOAT' else np.bool_ if a.data_type=='BOOLEAN' else np.int32;v=np.empty(len(a.data)*(3 if vec else 1),dt);a.data.foreach_get('vector' if vec else 'value',v);return v.reshape(-1,3) if vec else v

def h(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def tri(m):
 m.calc_loop_triangles();v=np.empty(len(m.loop_triangles)*3,np.int32);m.loop_triangles.foreach_get('vertices',v);return v.reshape(-1,3)
def snap(name,keys=()):
 e,m=mesh_eval(name);r={'vertices':len(m.vertices),'faces':len(m.polygons),'pos':h(co(m)),'tri':h(tri(m)),'attr':{k:h(attr(m,k)) for k in keys if k in m.attributes},'material':h(np.array([p.material_index for p in m.polygons],np.int32))};e.to_mesh_clear();return r
KEYS={SKIN:['sl_rest_position','achene_pit'],SEEDS:['sl_rest_position','sl_anchor_index'],FLESH:['sl_cut_face','sl_rest_position','sl_edge_distance_mm','sl_reference_position','sl_reference_normal'],EXACT:['sl_cut_face','sl_cavity_wall_face','sl_rest_position','sl_reference_position','sl_reference_normal','sl_cell_interior','sl_cell_height_mm','sl_vascular_core','sl_vascular_halo','sl_vascular_ring_relative']}
def snapshot():return {n:snap(n,k) for n,k in KEYS.items()}
def update(r,**kw):
 for k,v in kw.items():r[k]=v
 r.update_tag();bpy.context.view_layer.update()
def load(path,pose,vox):
 bpy.ops.wm.open_mainfile(filepath=str(Path(path).resolve()),use_scripts=False);setup(pose,.32);r=bpy.data.objects[ROOT];update(r,exact_mode=1,exact_voxel_mm=vox,cap_refine_level=2,tissue_gain=1.);return r

def juicecheck():
 e,me=mesh_eval(JUICE);q=co(me);res={'vertices':len(q),'faces':len(me.polygons)}
 if not len(q):e.to_mesh_clear();return res
 src=attr(me,'sl_juice_tissue_position');base=attr(me,'sl_reference_position');n=attr(me,'sl_reference_normal');n=n/np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-8);level=attr(me,'sl_juice_final_level_mm');cl=attr(me,'sl_juice_clearance_mm');dist=attr(me,'sl_juice_protected_distance_mm');pure=attr(me,'sl_cell_interior')
 assert np.isfinite(q).all() and np.isfinite(cl).all() and pure.all();assert attr(me,'sl_cut_face').all() and not attr(me,'sl_cavity_wall_face').any();assert all(me.materials[p.material_index].name==MAT for p in me.polygons)
 ev,body=mesh_eval(EXACT);p=co(body);cap=attr(body,'sl_cut_face');p_cap=np.zeros(len(p),bool);non=np.zeros(len(p),bool)
 for i,f in enumerate(body.polygons):(p_cap if cap[i] else non)[list(f.vertices)]=True
 def packed(a):return np.ascontiguousarray(a).view(np.dtype((np.void,12))).ravel()
 matches=np.isin(packed(src),packed(p[p_cap&~non]));assert matches.all(),int((~matches).sum())
 ev.to_mesh_clear()
 err=float(np.max(abs(np.sum((q-src)*n,axis=1)-cl)));poserr=float(np.max(np.linalg.norm(q-(base+n*level[:,None]),axis=1)));assert err<1e-4 and poserr<1e-4,(err,poserr)
 bm=bmesh.new();bm.from_mesh(me);bm.verts.index_update();boundary=np.array([v.index for v in bm.verts if v.is_boundary],int);over=sum(len(ed.link_faces)>2 or len(ed.link_faces)==0 for ed in bm.edges);bad=sum(len(ed.link_faces)==2 and not ed.is_contiguous for ed in bm.edges);seen=set();components=0
 for v in bm.verts:
  if v in seen:continue
  components+=1;seen.add(v);stack=[v]
  while stack:
   for ed in stack.pop().link_edges:
    for x in ed.verts:
     if x not in seen:seen.add(x);stack.append(x)
 bm.free();me.calc_loop_triangles();deg=sum(t.area<1e-9 for t in me.loop_triangles);assert not over and not bad and not deg,(over,bad,deg)
 assert len(boundary)>0 and np.max(cl[boundary])<=-.0179,(len(boundary),float(np.max(cl[boundary])))
 visible=int((cl>.005).sum());buried=int((cl<-.005).sum());assert visible>0 and buried>0,(visible,buried)
 res.update(components=components,open_boundary_vertices=len(boundary),boundary_max_clearance_mm=float(cl[boundary].max()),visible_points=visible,buried_points=buried,max_clearance_mm=float(cl.max()),min_protected_distance_mm=float(dist.min()),over_two_face_or_wire_edges=over,inconsistent_edges=bad,degenerate_triangles=deg,source_pure_cap_match=True,normal_height_error_mm=err,position_error_mm=poserr,pos_sha=h(q),topology_sha=h(tri(me)));e.to_mesh_clear();return res

def main():
 base,new,pose,vox,out=sys.argv[sys.argv.index('--')+1:];vox=float(vox);out=Path(out);assert not out.exists() and sha(base)==PIN and sha(new)==json.loads(Path(new).with_suffix('.json').read_text())['scene_sha'];t=time.perf_counter();r=load(base,pose,vox);orig=snapshot();key=(r['neutral_stock_key'],r['anchor_digest'],r['sl_vascular_dependency_key']);print('BASE',orig[EXACT]['vertices'],flush=True)
 r=load(new,pose,vox);assert key==(r['neutral_stock_key'],r['anchor_digest'],r['sl_vascular_dependency_key']);update(r,juice_gain=0.);assert snapshot()==orig;assert juicecheck()['faces']==0
 update(r,juice_gain=1.);j=juicecheck();print('WET',json.dumps(j),flush=True);assert snapshot()==orig;assert (j['faces']==0)==(pose=='whole')
 update(r,juice_gain=0.);assert juicecheck()['faces']==0;update(r,juice_gain=1.);assert juicecheck()==j
 update(r,exact_mode=0);assert juicecheck()['faces']==0;update(r,exact_mode=1,tissue_gain=0.);assert juicecheck()['faces']==0
 report={'source_sha':PIN,'scene_sha':sha(new),'pose':pose,'voxel_mm':vox,'base_equal_with_juice_on_off':True,'juice':j,'toggle_roundtrip_equal':True,'fast_empty':True,'relief_disabled_empty':True,'gate':True,'elapsed_seconds':time.perf_counter()-t};out.write_text(json.dumps(report,indent=2)+'\n');print('RESULT',json.dumps(report),flush=True)
if __name__=='__main__':main()

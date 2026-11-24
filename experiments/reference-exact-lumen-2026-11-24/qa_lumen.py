"""Evaluate saved exact-lumen scene versus the pinned tissue baseline."""
import bpy,sys,json,time,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).parent))
from build_lumen import EXACT,ROOT,SKIN,WALL,PIN,sha
sys.path.insert(0,str(Path(__file__).parent/'deps'))
from qa_split import setup,mesh_eval,top,FLESH,SEEDS,CAP,co
base,new,pose,voxel,out=sys.argv[sys.argv.index('--')+1:]; voxel=float(voxel);out=Path(out)
receipt=json.loads(Path(new).with_suffix('.json').read_text());assert sha(base)==PIN and sha(new)==receipt['scene_sha'] and not out.exists()
def attr(me,k):
 a=me.attributes[k];dt=bool if a.data_type=='BOOLEAN' else np.int32 if a.data_type=='INT' else np.float32;n=3 if a.data_type=='FLOAT_VECTOR' else 1;v=np.empty(len(a.data)*n,dt);a.data.foreach_get('vector' if n==3 else 'value',v);return v.reshape(-1,3) if n==3 else v
def h(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def tris(m):
 m.calc_loop_triangles();a=np.empty(3*len(m.loop_triangles),np.int32);m.loop_triangles.foreach_get('vertices',a);return a.reshape(-1,3)
def snap(n,keys):
 e,m=mesh_eval(n);r=(h(co(m)),h(tris(m)),{k:h(attr(m,k)) for k in keys if k in m.attributes});e.to_mesh_clear();return r
keys={SKIN:['sl_rest_position','achene_pit'],SEEDS:['sl_rest_position','sl_anchor_index'],FLESH:['sl_cut_face','sl_rest_position','sl_edge_distance_mm','sl_reference_position','sl_reference_normal']}
def fast():return {n:snap(n,k) for n,k in keys.items()}
def update(r,**v):
 for k,val in v.items():r[k]=val
 r.update_tag();bpy.context.view_layer.update()
def load(p):
 bpy.ops.wm.open_mainfile(filepath=str(Path(p).resolve()),use_scripts=False);mode=setup(pose,.32);r=bpy.data.objects[ROOT];update(r,exact_mode=0,exact_voxel_mm=voxel,tissue_gain=0.);return r,mode
def snapshot():
 e,m=mesh_eval(EXACT);v=co(m);t=tris(m);names=[x.name if x else '' for x in m.materials];fm=np.array([p.material_index for p in m.polygons]);tf=np.array([q.polygon_index for q in m.loop_triangles]);f=[tuple(p.vertices) for p in m.polygons];aa={k:attr(m,k) for k in ['sl_cut_face','sl_cavity_wall_face','sl_exact_body_signed_mm','sl_exact_cutter_signed_mm','sl_cavity_signed_mm','sl_reference_position','sl_rest_position','sl_cell_interior','sl_cell_height_mm','sl_vascular_core','sl_vascular_halo','sl_vascular_ring_relative'] if k in m.attributes};r={'v':v,'t':t,'f':f,'names':names,'fm':fm,'tf':tf,'a':aa,'top':top(m)[0] if len(v) else None};e.to_mesh_clear();return r
def points_for(x,mask):return np.unique(np.concatenate([x['f'][j] for j in np.flatnonzero(mask)])) if mask.any() else np.empty(0,dtype=int)
def skinmask(x):return x['fm']==x['names'].index('Diagnostic clay | skin')
def components(x):
 v,t=x['v'],x['t'];parent=np.arange(len(v))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for a,b,c in t:
  ra,rb,rc=find(a),find(b),find(c);parent[rb]=ra;parent[rc]=ra
 labels=np.array([find(i) for i in range(len(v))]);u,cnt=np.unique(labels,return_counts=True);signed=np.einsum('ij,ij->i',v[t[:,0]].astype(float),np.cross(v[t[:,1]].astype(float),v[t[:,2]].astype(float)))/6
 return sorted([{'vertices':int(n),'signed_volume_mm3':float(signed[labels[t[:,0]]==k].sum())} for k,n in zip(u,cnt)],key=lambda d:-d['vertices'])
def pass_top(q):return all(q[k]==0 for k in ['boundary_edges','wire_or_over_two_face_edges','inconsistent_edges','degenerate_triangles']) and q['signed_volume_mm3']>0
def skin_faces(x):
 tm=x['t'][skinmask(x)[x['tf']]];return {tuple(sorted(tuple(float(k) for k in x['v'][i]) for i in q)) for q in tm}
t0=time.perf_counter();r,mode=load(base);fs=fast();raw=h(co(bpy.data.objects[SKIN].data));stock=(r['neutral_stock_key'],r['anchor_digest'],r['sl_vascular_dependency_key']);update(r,exact_mode=1);a=snapshot();seed=snap(SEEDS,keys[SEEDS]);print('BASE',len(a['v']),flush=True)
r,mode=load(new);assert stock==(r['neutral_stock_key'],r['anchor_digest'],r['sl_vascular_dependency_key']);assert raw==h(co(bpy.data.objects[SKIN].data));assert fs==fast();update(r,exact_mode=1);b=snapshot();assert snap(SEEDS,keys[SEEDS])==seed;print('CAVITY',len(b['v']),flush=True)
report={'pose':pose,'voxel_mm':voxel,'source_sha':sha(base),'scene_sha':sha(new),'fast_equal':True,'seed_mesh_equal':True,'raw_stock_equal':True}
if mode==0:
 assert not len(a['v']) and not len(b['v']);report['whole_display_bypass']=True;report['gate']=True
else:
 v=b['v'];s=b['a'];cap=s['sl_cut_face'];wall=s['sl_cavity_wall_face'];outer=skinmask(b);assert not np.any(cap&wall) and np.all(cap|wall|outer) and not np.any(outer&(cap|wall));assert np.array_equal(wall,b['fm']==b['names'].index(WALL));assert np.array_equal(cap,b['fm']==b['names'].index(CAP));u=-s['sl_exact_cutter_signed_mm'];c=-s['sl_cavity_signed_mm'];d=s['sl_exact_body_signed_mm'];assert np.array_equal(wall,(c>d)&(c>=u)) and np.array_equal(cap,u>np.maximum(d,c));assert wall.any()
 aa=skin_faces(a);bb=skin_faces(b);report['outer_skin_triangle_counts']=[len(aa),len(bb)];report['outer_skin_missing_triangles']=len(aa-bb);report['outer_skin_new_triangles']=len(bb-aa);skin_equal=aa==bb
 comp=components(b);positive=sum(x['signed_volume_mm3']>0 for x in comp);negative=sum(x['signed_volume_mm3']<0 for x in comp)
 cp=points_for(b,cap);wp=points_for(b,wall);sp=points_for(b,outer);noncap=np.union1d(wp,sp);pure=np.setdiff1d(cp,noncap);seam=np.intersect1d(cp,noncap);assert np.array_equal(np.flatnonzero(s['sl_cell_interior']),pure)
 update(r,tissue_gain=1.);g=snapshot();assert b['f']==g['f'];protected=np.array_equal(v[noncap],g['v'][noncap]);assert np.array_equal(g['a']['sl_cell_height_mm'][noncap],np.zeros(len(noncap),np.float32));assert np.array_equal(b['a']['sl_rest_position'],g['a']['sl_rest_position']);assert all(np.array_equal(b['a'][k],g['a'][k]) for k in ('sl_vascular_core','sl_vascular_halo','sl_vascular_ring_relative'))
 e,m=mesh_eval(SEEDS);sv=co(m);st=tris(m);sid=attr(m,'sl_anchor_index');e.to_mesh_clear();seedids=np.unique(sid);sf=sid[st[:,0]];tree=BVHTree.FromPolygons(g['v'].tolist(),g['t'][outer[g['tf']]].tolist(),all_triangles=True);contact=0
 for i in seedids:
  j=np.flatnonzero(sid==i);other=BVHTree.FromPolygons(sv[j].tolist(),np.searchsorted(j,st[sf==i]).tolist(),all_triangles=True);contact+=bool(tree.overlap(other))
 tip_probe=None
 if pose=='bite':
  walltree=BVHTree.FromPolygons(v.tolist(),b['t'][wall[b['tf']]].tolist(),all_triangles=True);tip_dist=[]
  for site in receipt['sites']:
   p=Vector(site['tip_mm']);q,n,_,_=walltree.find_nearest(p);tip_dist.append(float((q-p).dot(n)))
  tip_probe={'positive_inside_tissue':sum(d>0 for d in tip_dist),'total':len(tip_dist),'signed_tip_distances_mm':tip_dist,'note':'nearest actual oriented wall; centre sample, not complete protrusion survival'}
 report.update(body_topology_gain0=b['top'],body_topology_gain1=g['top'],components_gain0=comp,positive_components=positive,negative_components=negative,outer_skin_equal=skin_equal,wall_faces=int(wall.sum()),cap_faces=int(cap.sum()),protected_vertices=len(noncap),wall_vertices=len(wp),shared_cap_boundary_vertices=len(seam),protected_exactly_fixed=protected,seed_contacts=[contact,len(seedids)],tip_probe=tip_probe,volume_removed_mm3=a['top']['signed_volume_mm3']-b['top']['signed_volume_mm3']);report['gate']=bool(pass_top(b['top']) and pass_top(g['top']) and positive==1 and negative<=1 and skin_equal and protected and contact==len(seedids) and report['volume_removed_mm3']>0)
update(r,exact_mode=0);report['fast_roundtrip_equal']=fast()==fs;report['gate']=bool(report['gate'] and report['fast_roundtrip_equal']);report['elapsed_seconds']=time.perf_counter()-t0;out.write_text(json.dumps(report,indent=2)+'\n');print('RESULT',json.dumps(report),flush=True)

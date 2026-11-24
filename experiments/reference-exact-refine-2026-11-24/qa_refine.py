"""Independent cap-only geometry QA with reference comparison and new-point field sampling."""
import bpy,sys,json,time,hashlib
import numpy as np
from pathlib import Path
from collections import Counter,defaultdict
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent/'deps')]
from qa_split import setup,mesh_eval,co,top,ROOT,SKIN,FLESH,SEEDS,CAP
from build_refine import PIN,EXACT,sha
WALL='SL Exact | cavity wall ARTIST';SKIN_MAT='Diagnostic clay | skin'
base,new,field,pose,voxel,out=sys.argv[sys.argv.index('--')+1:];voxel=float(voxel);out=Path(out);assert sha(base)==PIN and sha(new)==json.loads(Path(new).with_suffix('.json').read_text())['scene_sha'] and not out.exists()
assert sha(field)=="0f6bbaa59a3a478c917a1c7bf69a41add5d9199f097c3ef8f0a2ebc984bb2c7e"
def h(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def attr(me,k):
 a=me.attributes[k];vec=a.data_type=='FLOAT_VECTOR';dt=np.float32 if vec or a.data_type=='FLOAT' else np.bool_ if a.data_type=='BOOLEAN' else np.int32;v=np.empty(len(a.data)*(3 if vec else 1),dt);a.data.foreach_get('vector' if vec else 'value',v);return v.reshape(-1,3) if vec else v
def tris(me):
 me.calc_loop_triangles();a=np.empty(3*len(me.loop_triangles),np.int32);me.loop_triangles.foreach_get('vertices',a);return a.reshape(-1,3)
def snap(name,keys):
 e,m=mesh_eval(name);r=(h(co(m)),h(tris(m)),{k:h(attr(m,k)) for k in keys if k in m.attributes});e.to_mesh_clear();return r
KEYS={SKIN:['sl_rest_position','achene_pit'],SEEDS:['sl_rest_position','sl_anchor_index'],FLESH:['sl_cut_face','sl_rest_position','sl_edge_distance_mm','sl_reference_position','sl_reference_normal']}
def fast():return {n:snap(n,k) for n,k in KEYS.items()}
def update(r,**v):
 for k,val in v.items():r[k]=val
 r.update_tag();bpy.context.view_layer.update()
def load(p):
 bpy.ops.wm.open_mainfile(filepath=str(Path(p).resolve()),use_scripts=False);mode=setup(pose,.32);r=bpy.data.objects[ROOT];update(r,exact_mode=0,exact_voxel_mm=voxel,tissue_gain=0.);return r,mode
def snapshot():
 e,m=mesh_eval(EXACT);v=co(m);t=tris(m);f=[tuple(p.vertices) for p in m.polygons];names=[x.name if x else '' for x in m.materials];fm=np.array([p.material_index for p in m.polygons]);tf=np.array([q.polygon_index for q in m.loop_triangles]);area=np.array([p.area for p in m.polygons]);aa={k:attr(m,k) for k in ['sl_cut_face','sl_cavity_wall_face','sl_reference_position','sl_reference_normal','sl_rest_position','sl_cell_interior','sl_cell_height_mm','sl_vascular_core','sl_vascular_halo','sl_vascular_ring_relative','sl_edge_distance_mm'] if k in m.attributes};r={'v':v,'t':t,'f':f,'names':names,'fm':fm,'tf':tf,'a':aa,'area':area,'top':top(m)[0] if len(v) else None};e.to_mesh_clear();return r
def equal(a,b):return np.array_equal(a['v'],b['v']) and a['f']==b['f'] and np.array_equal(a['t'],b['t']) and a['names']==b['names'] and np.array_equal(a['fm'],b['fm']) and all(np.array_equal(x,b['a'][k]) for k,x in a['a'].items())
def points_for(x,mask):return np.unique(np.concatenate([x['f'][j] for j in np.flatnonzero(mask)])) if mask.any() else np.empty(0,dtype=int)
def cap(x):return x['a']['sl_cut_face']
def protected(x):return points_for(x,~cap(x))
def triangle_keys(x,mat):
 t=x['t'][(x['fm']==x['names'].index(mat))[x['tf']]];return Counter(tuple(sorted(tuple(float(k) for k in x['v'][i]) for i in q)) for q in t)
def boundary_keys(x):
 edges=defaultdict(set)
 for j,f in enumerate(x['f']):
  c=bool(cap(x)[j]);
  for u,v in zip(f,f[1:]+f[:1]):edges[tuple(sorted((u,v)))].add(c)
 return {tuple(sorted((tuple(x['v'][u]),tuple(x['v'][v])))) for (u,v),vls in edges.items() if len(vls)==2}
def pass_top(q):return all(q[k]==0 for k in ['boundary_edges','wire_or_over_two_face_edges','inconsistent_edges','degenerate_triangles']) and q['signed_volume_mm3']>0
def components(x):
 parent=np.arange(len(x['v']));rank=np.zeros(len(parent),np.uint8)
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for a,b,c in x['t']:
  for u,v in ((a,b),(a,c)):
   u,v=find(u),find(v)
   if u!=v:
    if rank[u]<rank[v]:u,v=v,u
    parent[v]=u
    if rank[u]==rank[v]:rank[u]+=1
 labels=np.array([find(i) for i in range(len(parent))]);vv=x['v'].astype(float);t=x['t'];vs=np.einsum('ij,ij->i',vv[t[:,0]],np.cross(vv[t[:,1]],vv[t[:,2]]))/6;u,c=np.unique(labels,return_counts=True);return [{'vertices':int(n),'volume_mm3':float(vs[labels[t[:,0]]==j].sum())} for j,n in zip(u,c)]
def stats(x):
 a=x['area'][cap(x)];pure=np.setdiff1d(points_for(x,cap(x)),protected(x));eligible=np.zeros(len(x['v']),bool);eligible[pure]=True;sel=np.array([all(eligible[list(f)]) for f in x['f']]);sel&=cap(x);inner=x['area'][sel];return {'vertices':len(x['v']),'faces':len(x['f']),'cap_faces':int(cap(x).sum()),'cap_area_p95_mm2':float(np.percentile(a,95)),'cap_area_median_mm2':float(np.median(a)),'pure_cap_area_p95_mm2':float(np.percentile(inner,95)),'pure_cap_faces_above_limit':int((sel&(x['area']>.03)).sum()),'protected_vertices':len(protected(x))},sel

def trilinear(grid,pts,bounds):
 n=grid.shape[0];u=np.clip((pts-bounds[:,0])/(bounds[:,1]-bounds[:,0]),0,1)*(n-1);lo=np.floor(u).astype(int);hi=np.minimum(lo+1,n-1);f=u-lo;v=np.zeros(len(pts))
 for k in range(8):
  b=np.array([(k>>j)&1 for j in range(3)]);p=np.where(b,hi,lo);w=np.prod(np.where(b,f,1-f),axis=1);v+=w*grid[p[:,2],p[:,1],p[:,0]]
 return v
start=time.perf_counter();r,mode=load(base);fs=fast();raw=h(co(bpy.data.objects[SKIN].data));keys=(r['neutral_stock_key'],r['anchor_digest'],r['sl_vascular_dependency_key']);update(r,exact_mode=1);a=snapshot();seed=snap(SEEDS,KEYS[SEEDS]);print('BASE',len(a['v']),flush=True)
r,mode=load(new);assert keys==(r['neutral_stock_key'],r['anchor_digest'],r['sl_vascular_dependency_key']);assert raw==h(co(bpy.data.objects[SKIN].data));assert fs==fast();update(r,exact_mode=1,cap_refine_level=0);zero=snapshot();assert equal(a,zero);assert seed==snap(SEEDS,KEYS[SEEDS]);report={'pose':pose,'voxel_mm':voxel,'source_sha':sha(base),'scene_sha':sha(new),'field_sha':sha(field),'fast_equal':True,'level0_exact_equal':True,'seed_mesh_equal':True,'raw_stock_equal':True}
if mode==0:
 update(r,cap_refine_level=2,tissue_gain=1.);assert len(snapshot()['v'])==0;report['whole_bypass']=True;report['gate']=True
else:
 orig_skin=triangle_keys(a,SKIN_MAT);orig_wall=triangle_keys(a,WALL);orig_bound=boundary_keys(a);orig_comp=components(a);orig_stat,sel=stats(a);report['baseline']=orig_stat;print('BASE STATS',orig_stat,flush=True)
 prev=a;rows=[];gate=True
 for level in (1,2):
  oldstat,sel=stats(prev);expected=oldstat['pure_cap_faces_above_limit'];update(r,cap_refine_level=level,tissue_gain=0.);x=snapshot();xs,_=stats(x);new_count=len(x['v'])-len(prev['v']);px=set(map(tuple,x['v']));prev_pos=set(map(tuple,prev['v']));np_new=np.array([i for i,v in enumerate(x['v']) if tuple(v) not in prev_pos],dtype=int);pure=np.setdiff1d(points_for(x,cap(x)),protected(x));assert np.array_equal(np.flatnonzero(x['a']['sl_cell_interior']),pure);assert np.array_equal(x['v'],x['a']['sl_reference_position']);assert not np.any(x['a']['sl_cell_height_mm']);assert not np.any(cap(x)&x['a']['sl_cavity_wall_face']);assert np.array_equal(x['a']['sl_cavity_wall_face'],x['fm']==x['names'].index(WALL));assert np.array_equal(cap(x),x['fm']==x['names'].index(CAP));prot_ok=triangle_keys(x,SKIN_MAT)==orig_skin and triangle_keys(x,WALL)==orig_wall and boundary_keys(x)==orig_bound
  comp=components(x);count_ok=sum(c['volume_mm3']>0 for c in comp)==sum(c['volume_mm3']>0 for c in orig_comp) and sum(c['volume_mm3']<0 for c in comp)==sum(c['volume_mm3']<0 for c in orig_comp);old_preserved=prev_pos<=px;added_pure=set(np_new)<=set(pure);expected_count_ok=expected==new_count
  centers=np.array([prev['v'][list(f)].astype(float).mean(axis=0) for f,m,ar in zip(prev['f'],sel,prev['area']) if m and ar>.03]);err=None
  if len(centers) and len(np_new):
   tree=KDTree(len(np_new));
   for i in np_new:tree.insert(x['v'][i],int(i))
   tree.balance();err=float(max(tree.find(v)[2] for v in centers))
  i=np_new[np.linspace(0,len(np_new)-1,min(2048,len(np_new)),dtype=int)] if len(np_new) else np.array([],int);inv_err=0.;field_err={}
  if len(i):
   p=x['v'][i].astype(float);p[:,2]/=r['shape_h'];t=2*p[:,2]/48.-1;sc=1+r['shape_a']*np.exp(-((t-.5)/.36)**2)+r['shape_b']*np.exp(-((t+.3)/.4)**2);p[:,:2]/=sc[:,None];inv_err=float(np.max(abs(p-x['a']['sl_rest_position'][i])))
   with np.load(field) as d:
    for k in ('core','halo','ring_relative'):field_err[k]=float(np.max(abs(trilinear(d[k],p,d['bounds'])-x['a']['sl_vascular_'+k][i])))
  ok=bool(pass_top(x['top']) and prot_ok and count_ok and old_preserved and added_pure and expected_count_ok and (err is None or err<1e-4) and inv_err<1e-4 and max(field_err.values(),default=0)<.001)
  xs.update(level=level,new_vertices=new_count,expected_selected_faces=expected,face_count_expected_match=expected_count_ok,old_vertices_retained=old_preserved,new_vertices_cap_only=added_pure,protected_triangles_and_boundary_equal=prot_ok,components=comp,topology=x['top'],centroid_max_error_mm=err,new_point_inverse_max_error_mm=inv_err,field_samples=len(i),field_error=field_err,gate=ok);rows.append(xs);print('REFINE',json.dumps(xs),flush=True);gate&=ok;prev=x
 x=prev;update(r,tissue_gain=1.);g=snapshot();prot=protected(x);assert x['f']==g['f'];disp=g['v']-x['v'];assert np.array_equal(x['a']['sl_rest_position'],g['a']['sl_rest_position']);assert all(np.array_equal(x['a']['sl_vascular_'+k],g['a']['sl_vascular_'+k]) for k in ('core','halo','ring_relative'))
 e,m=mesh_eval(SEEDS);sv=co(m);st=tris(m);sid=attr(m,'sl_anchor_index');e.to_mesh_clear();seedids=np.unique(sid);sf=sid[st[:,0]];tree=BVHTree.FromPolygons(g['v'].tolist(),g['t'][(g['fm']==g['names'].index(SKIN_MAT))[g['tf']]].tolist(),all_triangles=True);contact=0
 for i in seedids:
  j=np.flatnonzero(sid==i);other=BVHTree.FromPolygons(sv[j].tolist(),np.searchsorted(j,st[sf==i]).tolist(),all_triangles=True);contact+=bool(tree.overlap(other))
 fixed=np.array_equal(x['v'][prot],g['v'][prot]);relief_ok=bool(pass_top(g['top']) and fixed and contact==len(seedids) and np.all(g['a']['sl_cell_height_mm'][prot]==0));report.update(levels=rows,protected_vertices_fixed_with_relief=fixed,relief_max_mm=float(np.linalg.norm(disp,axis=1).max()),relief_moved_vertices=int((np.linalg.norm(disp,axis=1)>1e-6).sum()),relief_topology=g['top'],seed_contacts=[contact,len(seedids)],gate=bool(gate and relief_ok));print('RELIEF',relief_ok,contact,len(seedids),flush=True)
update(r,exact_mode=0);report['fast_roundtrip_equal']=fast()==fs;report['gate']&=report['fast_roundtrip_equal'];report['elapsed_seconds']=time.perf_counter()-start;out.write_text(json.dumps(report,indent=2)+'\n');print('RESULT',json.dumps(report),flush=True)

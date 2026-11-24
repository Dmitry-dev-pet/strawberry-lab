"""Independent matched Exact tissue evaluation. No mutation of saved scenes."""
import bpy,bmesh,numpy as np,sys,json,time,hashlib
from pathlib import Path
from collections import defaultdict,Counter
from mathutils.bvhtree import BVHTree
from mathutils import Vector
H=Path(__file__).resolve().parent;sys.path[:0]=[str(H),str(H/'deps')]
from build_tissue import EXACT,ROOT,SKIN,SEEDS,PIN,sha,coords,attr
from qa_split import setup,mesh_eval,polys,top,FLESH,CAP,sdf
old,new,field,pose,vox,out=sys.argv[sys.argv.index('--')+1:];vox=float(vox);out=Path(out);assert not out.exists() and sha(old)==PIN
receipt=json.loads(Path(new).with_suffix('.json').read_text());assert sha(new)==receipt['scene_sha'] and sha(field)==receipt['field_sha']
def h(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def triangles(m):
 m.calc_loop_triangles();a=np.empty(3*len(m.loop_triangles),np.int32);m.loop_triangles.foreach_get('vertices',a);return a.reshape(-1,3)
def snap(n,attrs=()):
 e,m=mesh_eval(n);r={'coords':h(coords(m)),'tri':h(triangles(m)),'attrs':{a:h(attr(m,a)) for a in attrs if a in m.attributes},'n':len(m.vertices)};e.to_mesh_clear();return r
ATTRS={SKIN:['sl_rest_position','achene_pit'],SEEDS:['sl_rest_position','sl_anchor_index'],FLESH:['sl_cut_face','sl_rest_position','sl_edge_distance_mm','sl_cut_point','sl_outer_recess_point','sl_pre_recess_position','sl_cutter_signed_mm','sl_reference_position','sl_reference_normal']}
def fast():return {n:snap(n,a) for n,a in ATTRS.items()}
def update(r,**values):
 for k,v in values.items():r[k]=v
 r.update_tag();bpy.context.view_layer.update()
def load(p):
 bpy.ops.wm.open_mainfile(filepath=str(Path(p).resolve()),use_scripts=False);mode=setup(pose,.32);r=bpy.data.objects[ROOT];update(r,exact_mode=0,exact_voxel_mm=vox);return r,mode
KEYS=['sl_rest_position','sl_cut_face','sl_exact_body_signed_mm','sl_exact_cutter_signed_mm','sl_edge_distance_mm','sl_reference_position','sl_reference_normal','achene_pit']
FIELD=['sl_vascular_core','sl_vascular_halo','sl_vascular_ring_relative','sl_cell_interior','sl_cell_dome','sl_cell_edge_fade','sl_vascular_cell_multiplier','sl_vascular_ridge_mm','sl_cell_height_mm']
def exact_snapshot(fields=False):
 e,m=mesh_eval(EXACT);a={'v':coords(m),'t':triangles(m),'f':polys(m),'attrs':{k:attr(m,k) for k in KEYS+(FIELD if fields else []) if k in m.attributes},'top':top(m)[0]};e.to_mesh_clear();return a

def trilinear(grid,pts,bounds):
 n=grid.shape[0];u=np.clip((pts-bounds[:,0])/(bounds[:,1]-bounds[:,0]),0,1)*(n-1);lo=np.floor(u).astype(int);hi=np.minimum(lo+1,n-1);f=u-lo;v=np.zeros(len(pts))
 for k in range(8):
  b=np.array([(k>>j)&1 for j in range(3)]);p=np.where(b,hi,lo);w=np.prod(np.where(b,f,1-f),axis=1);v+=w*grid[p[:,2],p[:,1],p[:,0]]
 return v

def compare(a,b):return np.array_equal(a['v'],b['v']) and np.array_equal(a['t'],b['t']) and a['f']==b['f'] and all(np.array_equal(x,b['attrs'][k]) for k,x in a['attrs'].items())
start=time.perf_counter();r,mode=load(old);fs=fast();raw=h(coords(bpy.data.objects[SKIN].data));stock=(r['neutral_stock_key'],r['anchor_digest']);update(r,exact_mode=1);base=exact_snapshot();print('BASE',pose,len(base['v']),flush=True)
r,mode=load(new);assert stock==(r['neutral_stock_key'],r['anchor_digest']) and r['sl_vascular_dependency_key']==receipt['dependency_key'];assert h(coords(bpy.data.objects[SKIN].data))==raw;assert fast()==fs;img=bpy.data.images['SL Exact | new neutral vascular R H B'];assert img['dependency_key']==receipt['dependency_key'] and hashlib.sha256(bytes(img.packed_file.data)).hexdigest()==receipt['packed_image_sha'];update(r,exact_mode=1,tissue_gain=0.);a=exact_snapshot(True);assert compare(base,a),'gain zero changed Exact';assert snap(SEEDS,ATTRS[SEEDS])==fs[SEEDS];print('A',len(a['v']),flush=True)
report={'pose':pose,'voxel_mm':vox,'source_sha':sha(old),'scene_sha':sha(new),'field_sha':sha(field),'dependency_key':receipt['dependency_key'],'fast_before_equal':True,'gain0_exact_equal':True,'seed_hash_equal':True}
update(r,tissue_gain=1.);b=exact_snapshot(True)
if mode==0:
 assert len(a['v'])==len(b['v'])==0;report['whole_bypass']=True;report['gate']=True
else:
 assert a['f']==b['f'] and all(np.array_equal(a['attrs'][k],b['attrs'][k]) for k in KEYS);assert np.array_equal(a['attrs']['sl_rest_position'],b['attrs']['sl_rest_position']);v=a['v'];u=b['v'];x=b['attrs'];mask=x['sl_cut_face'];cap=np.zeros(len(v),bool);skin=np.zeros(len(v),bool)
 for fi,f in enumerate(a['f']):(cap if mask[fi] else skin)[list(f)]=True
 pure=cap&~skin;seam=cap&skin;assert pure.any() and seam.any();assert np.array_equal(x['sl_cell_interior'],pure),'cap point domain differs from adjacency'
 assert np.array_equal(v[skin],u[skin]),'skin or seam moved';assert np.array_equal(v,x['sl_reference_position']);assert np.array_equal(a['attrs']['sl_cell_height_mm'],np.zeros(len(v),np.float32));assert np.array_equal(x['sl_cell_height_mm'][~pure],np.zeros((~pure).sum(),np.float32));assert all(np.array_equal(a['attrs'][k],b['attrs'][k]) for k in FIELD if k!='sl_cell_height_mm')
 ids=np.flatnonzero(pure);ix=ids[np.linspace(0,len(ids)-1,min(4096,len(ids)),dtype=int)];rest=x['sl_rest_position'][ix].astype(float);err={};ranges={}
 with np.load(field) as data:
  for name in ('core','halo','ring_relative'):
   grid=data[name];assert h(grid)==receipt[{'core':'core_sha','halo':'halo_sha','ring_relative':'ring_sha'}[name]];y=x['sl_vascular_'+name];assert np.isfinite(y).all();p=trilinear(grid,rest,data['bounds']);err[name]=float(np.max(abs(p-y[ix])));ranges[name]=[float(y[pure].min()),float(y[pure].max())]
 assert max(err.values())<.001,err
 R,H,B=[x['sl_vascular_'+k] for k in ('core','halo','ring_relative')];assert (H+1e-5>=R).all();t=np.clip((H-.04)/.44,0,1);s=1-.88*t**3*(t*(6*t-15)+10);fade_t=np.clip((x['sl_edge_distance_mm']-.04)/1.01,0,1);fade=fade_t**3*(fade_t*(6*fade_t-15)+10);ridge=.12*R+.045*H;height=(.145*x['sl_cell_dome']*s+ridge)*fade*pure;he=float(np.max(abs(x['sl_cell_height_mm']-height)));assert he<1e-5,he
 normal=x['sl_reference_normal'];normal=normal/np.linalg.norm(normal,axis=1,keepdims=True);expected=normal*height[:,None];delta=u-v;de=float(np.max(abs(delta-expected)));assert de<1e-5,de;tp=b['top'];topok=bool(tp['boundary_edges']==tp['wire_or_over_two_face_edges']==tp['inconsistent_edges']==tp['degenerate_triangles']==0 and tp['signed_volume_mm3']>0)
 # Seed solids retained intact and still in contact with the unchanged skin-only faces.
 e,m=mesh_eval(SEEDS);sv=coords(m);st=triangles(m);sid=attr(m,'sl_anchor_index');e.to_mesh_clear()
 e,m=mesh_eval(EXACT);ci=[x.name if x else None for x in m.materials].index(CAP);skin_tri=np.array([tuple(q.vertices) for q in m.loop_triangles if q.material_index!=ci],np.int32);e.to_mesh_clear();tree=BVHTree.FromPolygons(u.tolist(),skin_tri.tolist(),all_triangles=True);contact=0;seedids=np.unique(sid);sf=sid[st[:,0]]
 for i in seedids:
  j=np.flatnonzero(sid==i);other=BVHTree.FromPolygons(sv[j].tolist(),np.searchsorted(j,st[sf==i]).tolist(),all_triangles=True);contact+=bool(tree.overlap(other))
 report.update(vertices=len(v),faces=len(a['f']),pure_cap_vertices=int(pure.sum()),shared_boundary_vertices=int(seam.sum()),moved_vertices=int((np.linalg.norm(delta,axis=1)>1e-6).sum()),max_skin_displacement_mm=0.,max_relief_mm=float(np.linalg.norm(delta,axis=1).max()),max_height_equation_error_mm=he,max_displacement_equation_error_mm=de,field_samples=len(ix),field_error=err,field_ranges=ranges,cell_multiplier_range=[float(s[pure].min()),float(s[pure].max())],max_ridge_mm=float(ridge[pure].max()),topology=tp,polygon_connectivity_equal=True,reference_attrs_equal=True,seed_contacts=[contact,len(seedids)],gate=bool(topok and contact==len(seedids)))
update(r,exact_mode=0);assert fast()==fs and snap(EXACT)['n']==0;report['fast_roundtrip_equal']=True;assert h(coords(bpy.data.objects[SKIN].data))==raw;report['raw_stock_equal']=True;report['elapsed_seconds']=time.perf_counter()-start;out.write_text(json.dumps(report,indent=2)+'\n');print('RESULT',json.dumps(report),flush=True)

"""Reopened scene quality routing, source preservation, common-body topology and pit/contact probes."""
import bpy,sys,math,hashlib,json,time,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from collections import defaultdict,Counter
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_exact import EXACT,PIN,HELPER,sha,gitsha
old,new,helper,pose,voxel,out=sys.argv[sys.argv.index('--')+1:];out=Path(out);voxel=float(voxel);assert not out.exists() and sha(old)==PIN and gitsha(Path(helper).parent/'build_split.py')==HELPER
sys.path.insert(0,str(Path(helper).resolve().parent))
from qa_split import setup,mesh_eval,co,polys,top,sdf,stats,ROOT,SKIN,SEEDS,FLESH,CAP
ANCHORS='SL Anchor Set'
ATTRS={SKIN:['sl_rest_position','achene_pit'],SEEDS:['sl_rest_position','sl_anchor_index'],FLESH:['sl_cut_face','sl_rest_position','sl_edge_distance_mm','sl_cut_point','sl_outer_recess_point','sl_pre_recess_position','sl_cutter_signed_mm','sl_reference_position','sl_reference_normal']}
def h(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def tri(m):
 m.calc_loop_triangles();a=np.empty(3*len(m.loop_triangles),np.int32);m.loop_triangles.foreach_get('vertices',a);return a.reshape(-1,3)
def at(m,n):
 a=m.attributes[n];vec=a.data_type=='FLOAT_VECTOR';dtype=np.float32 if vec or a.data_type=='FLOAT' else np.bool_ if a.data_type=='BOOLEAN' else np.int32;x=np.empty(len(a.data)*(3 if vec else 1),dtype);a.data.foreach_get('vector' if vec else 'value',x);return x.reshape(-1,3) if vec else x

def tree(v,t):return BVHTree.FromPolygons(v.tolist(),t.tolist(),all_triangles=True)
def snap(n,attrs=()):
 e,m=mesh_eval(n);v=co(m);t=tri(m);r={'vertices':len(v),'triangles':len(t),'coords':h(v),'tri':h(t),'attrs':{a:h(at(m,a)) for a in attrs if a in m.attributes}};e.to_mesh_clear();return r

def fast():return {n:snap(n,a) for n,a in ATTRS.items()}
def update(r,**p):
 for k,v in p.items():r[k]=v
 r.update_tag();bpy.context.view_layer.update()
def open_scene(p):
 bpy.ops.wm.open_mainfile(filepath=str(Path(p).resolve()),use_scripts=False);mode=setup(pose,.32);return mode,bpy.data.objects[ROOT]
def inverse(p,r):
 q=p.astype(float).copy();a,b,zscale=[float(r[k]) for k in ('shape_a','shape_b','shape_h')];q[:,2]/=zscale;t=q[:,2]/24-1;s=1+a*np.exp(-((t-.5)/.36)**2)+b*np.exp(-((t+.3)/.4)**2);q[:,:2]/=s[:,None];return q

def map_normal(p,n,r):
 a,b,hh=[float(r[k]) for k in ('shape_a','shape_b','shape_h')];t=p[:,2]/24-1;e1=np.exp(-((t-.5)/.36)**2);e2=np.exp(-((t+.3)/.4)**2);s=1+a*e1+b*e2;ds=(-2*a*(t-.5)/.36**2*e1-2*b*(t+.3)/.4**2*e2)/24;nn=n.astype(float).copy();nn[:,:2]/=s[:,None];nn[:,2]=(n[:,2]-ds*np.sum(p[:,:2]*nn[:,:2],axis=1))/hh;return nn/np.linalg.norm(nn,axis=1,keepdims=True)

def signed_probe(bvh,p):
 hit,n,_,d=bvh.find_nearest(Vector(p));assert hit is not None;return float(d),float((Vector(p)-hit).dot(n))

def contact_counts(v,t,ids,orig_tree,exact_tree):
 fids=ids[t[:,0]];assert np.all(ids[t]==fids[:,None]);rows=[]
 for i in np.unique(ids):
  ix=np.flatnonzero(ids==i);st=tree(v[ix],np.searchsorted(ix,t[fids==i]));rows.append((int(i),bool(orig_tree.overlap(st)),bool(exact_tree.overlap(st))))
 return {'retained':len(rows),'original_stock_contact':sum(x[1] for x in rows),'exact_skin_contact':sum(x[2] for x in rows),'exact_no_contact_ids':[x[0] for x in rows if not x[2]]}

start=time.perf_counter();mode,r=open_scene(old);baseline=fast();stock=(r['anchor_digest'],r['neutral_stock_key']);print('BASE FAST',pose,baseline[SKIN]['vertices'],flush=True)
mode,r=open_scene(new);update(r,exact_mode=0,exact_voxel_mm=voxel);assert fast()==baseline,'Fast changed on opening Exact candidate';assert snap(EXACT)['vertices']==0
raw_hash=h(co(bpy.data.objects[SKIN].data));assert stock==(r['anchor_digest'],r['neutral_stock_key']);assert bpy.data.objects[SKIN].data==bpy.data.objects[EXACT].data
update(r,split_mode=0);e,m=mesh_eval(SKIN);origv=co(m);origt=tri(m);orig_tree=tree(origv,origt);e.to_mesh_clear();anchor=bpy.data.objects[ANCHORS];rawa=co(anchor.data);rawnorm=at(anchor.data,'sl_rest_normal');anchor.hide_set(False);e,m=mesh_eval(ANCHORS);a=co(m);e.to_mesh_clear();anchor.hide_set(True);norm=map_normal(rawa,rawnorm,r);update(r,split_mode=mode,exact_mode=1);assert snap(SEEDS,ATTRS[SEEDS])==baseline[SEEDS]
report={'pose':pose,'exact_voxel_mm':voxel,'fast_voxel_mm':.32,'source_sha':sha(old),'scene_sha':sha(new),'stock_key':stock[1],'anchor_digest':stock[0],'fast_before_identical':True,'seed_hash_identical':True}
if mode==0:
 assert snap(EXACT)['vertices']==0 and fast()==baseline;report['whole_original_stock']=True
else:
 assert snap(SKIN)['vertices']==snap(FLESH)['vertices']==0,'Fast display not suppressed'
 e,m=mesh_eval(EXACT);v=co(m);t=tri(m);faces=polys(m);tp,bd=top(m);topology_gate=not bd and tp['wire_or_over_two_face_edges']==tp['inconsistent_edges']==tp['degenerate_triangles']==0 and tp['signed_volume_mm3']>0;degenerate=[{'face':int(x.polygon_index),'vertices':list(x.vertices),'area_mm2':float(x.area),'centroid_mm':v[list(x.vertices)].mean(axis=0).tolist()} for x in m.loop_triangles if x.area<1e-9]
 mask=at(m,'sl_cut_face');bs=at(m,'sl_exact_body_signed_mm');cs=at(m,'sl_exact_cutter_signed_mm');assert np.array_equal(mask,-cs>bs) and mask.any() and (~mask).any()
 mats=[x.name if x else None for x in m.materials];ci=mats.index(CAP);assert np.array_equal(mask,np.array([p.material_index==ci for p in m.polygons]));rest=at(m,'sl_rest_position');err=float(np.max(abs(rest-inverse(v,r))));assert err<1e-4 and np.array_equal(v,at(m,'sl_reference_position'));normal=at(m,'sl_reference_normal');assert np.isfinite(normal).all();normerr=float(np.max(abs(np.linalg.norm(normal,axis=1)-1)));assert normerr<1e-4
 # Incidence of actual edges on cap and skin faces. Also count total connected components of the body.
 adj=defaultdict(list);parent=list(range(len(v)))
 def find(x):
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 for fi,f in enumerate(faces):
  for i,j in zip(f,f[1:]+f[:1]):
   edge=tuple(sorted((i,j)));adj[edge].append(fi);u,w=find(i),find(j)
   if u!=w:parent[w]=u
 shared=[edge for edge,fs in adj.items() if len(fs)==2 and mask[fs[0]]!=mask[fs[1]]];assert shared
 component_sizes=Counter(find(i) for i in range(len(v)));conn=len(component_sizes);topology_gate=bool(topology_gate and conn==1)
 deg=Counter(i for edge in shared for i in edge);sadj=defaultdict(list)
 for i,j in shared:sadj[i].append(j);sadj[j].append(i)
 unvisited=set(sadj);loops=0
 while unvisited:
  loops+=1;todo=[unvisited.pop()]
  while todo:
   for j in sadj[todo.pop()]:
    if j in unvisited:unvisited.remove(j);todo.append(j)
 captris=np.array([tuple(q.vertices) for q in m.loop_triangles if q.material_index==ci],np.int32);skintris=np.array([tuple(q.vertices) for q in m.loop_triangles if q.material_index!=ci],np.int32);ct=tree(v,captris);st=tree(v,skintris);alltree=tree(v,t)
 centers=np.array([v[list(f)].mean(axis=0) for f in faces]);analytic=sdf(centers,mode);# independent sample of clear cap interiors, clear exterior
 ii=np.linspace(0,len(faces)-1,min(12000,len(faces)),dtype=int);dsg=np.array([signed_probe(orig_tree,centers[i]) for i in ii]);dd=dsg[:,0];ac=analytic[ii];mm=mask[ii];cc=(dd>1.5*voxel)&(abs(ac)<.8*voxel);oo=(dd<voxel)&(ac>1.5*voxel);assert cc.any() and oo.any()
 near=np.abs(analytic)<.75*voxel;serr=float(np.max(abs(cs[near]-analytic[near])));assert serr<.25*voxel,serr
 # Measure reference isosurface distance on actual independently evaluated uncut stock grid.
 # Use temporary in-memory reroute only, then restore the exact graph before further mode checks.
 stored=at(m,'sl_edge_distance_mm');pitfinite=bool(np.isfinite(at(m,'achene_pit')).all());e.to_mesh_clear()
 geo_group=bpy.data.objects[EXACT].modifiers[1].node_group;outnode=next(n for n in geo_group.nodes if n.type=='GROUP_OUTPUT');prev=outnode.inputs[0].links[0].from_socket;refnode=next((n for n in geo_group.nodes if n.label=='Physical uncut reference'),None);refsocket=refnode.outputs['Geometry'] if refnode else next(n for n in geo_group.nodes if n.label=='Uncut reference from same body grid').outputs['Mesh'];geo_group.links.new(refsocket,outnode.inputs[0]);bpy.context.view_layer.update();er,mr=mesh_eval(EXACT);rt=tree(co(mr),tri(mr));er.to_mesh_clear();geo_group.links.new(prev,outnode.inputs[0]);bpy.context.view_layer.update();ix=np.linspace(0,len(v)-1,min(4096,len(v)),dtype=int);dr=np.array([signed_probe(rt,v[i])[0] for i in ix]);ed=float(np.max(abs(dr-stored[ix])));assert ed<1e-4,ed
 # Captured actual geometry before rerouting, mesh evaluation lifetime held until read complete.
 report['exact']={'topology':tp,'coords_sha':h(v),'triangle_sha':h(t),'connected_components':conn,'component_vertex_counts':sorted(component_sizes.values(),reverse=True),'degenerate_triangles_detail':degenerate,'topology_gate':topology_gate,'skin_faces':int((~mask).sum()),'cap_faces':int(mask.sum()),'shared_material_edges':len(shared),'shared_edge_components':loops,'shared_edge_bad_valence':sum(x!=2 for x in deg.values()),'max_inverse_error_mm':err,'max_normal_length_error':normerr,'edge_distance_samples':len(ix),'edge_distance_error_mm':ed,'clear_cap_probes':int(cc.sum()),'clear_cap_wrong':int((cc&~mm).sum()),'clear_outer_probes':int(oo.sum()),'clear_outer_wrong':int((oo&mm).sum()),'cutter_signed_near_error_mm':serr,'minimum_analytic_cutter_margin_mm':float(sdf(v,mode).min()),'cap_vertices_analytic_distance_mm':stats(abs(sdf(v[np.unique(captris)],mode))),'reference_rim_abs_cutter_mm':stats(abs(sdf(v[sorted(deg)],mode))),'pit_mask_finite':pitfinite}
 # actual seed-solid contact in Exact skin, against same original stock and unaffected seed guard
 es,ms=mesh_eval(SEEDS);sv=co(ms);sti=tri(ms);ids=at(ms,'sl_anchor_index');es.to_mesh_clear();rawids=at(bpy.data.objects[SEEDS].data,'sl_anchor_index');cnt=np.bincount(ids,minlength=264);assert np.all((cnt==0)|(cnt==np.bincount(rawids,minlength=264)));assert np.all(sdf(sv,mode)>=-1e-4)
 report['seed_contact']=contact_counts(sv,sti,ids,orig_tree,st);report['seed_contact']['all_retained_complete']=True
 # Pit probes on kept seeds far enough from cutter to exclude rim effects.
 pd0=[];pd1=[];missing=[];eligible=[int(i) for i in np.unique(ids) if sdf(a[i:i+1],mode)[0]>2.0]
 for i in eligible:
  p=Vector(a[i]);n=Vector(norm[i]);x0=orig_tree.ray_cast(p+2*n,-n,5)[0];x1=st.ray_cast(p+2*n,-n,5)[0]
  if x0 is None or x1 is None:missing.append(i);continue
  pd0.append(float((p-x0).dot(n)));pd1.append(float((p-x1).dot(n)))
 report['pit_probes']={'eligible':len(eligible),'matched':len(pd0),'missing_ids':missing,'original_depth_mm':stats(pd0),'exact_depth_mm':stats(pd1),'median_relative_loss':float(1-np.median(pd1)/np.median(pd0)) if pd0 else None}
 # Complete technical invariants distinguish contact/pit loss and cutter approximation from topology.
 report['common_boundary_gate']=bool(topology_gate and loops==1 and not report['exact']['shared_edge_bad_valence'] and not report['exact']['clear_cap_wrong'] and not report['exact']['clear_outer_wrong']);report['seed_contact_gate']=report['seed_contact']['exact_skin_contact']==report['seed_contact']['retained']
update(r,exact_mode=0);assert fast()==baseline,'Fast changed on returning';assert snap(EXACT)['vertices']==0;assert raw_hash==h(co(bpy.data.objects[SKIN].data)) and stock==(r['anchor_digest'],r['neutral_stock_key']);report['fast_roundtrip_identical']=True;report['raw_stock_unchanged']=True;report['blender']=bpy.app.version_string;report['elapsed_seconds']=time.perf_counter()-start;out.write_text(json.dumps(report,indent=2)+'\n');print('RESULT',json.dumps(report),flush=True)

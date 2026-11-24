"""Saved-scene A/B: isolate skin clipping policy. Numerical probes, not a watertight seal proof."""
import bpy,numpy as np,sys,hashlib,json,time,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_fast_skin import sha,gitsha,PIN,HELPER
old,new,helper,pose,voxel,out=sys.argv[sys.argv.index('--')+1:];voxel=float(voxel);out=Path(out);assert not out.exists() and sha(old)==PIN and gitsha(Path(helper).parent/'build_split.py')==HELPER
sys.path.insert(0,str(Path(helper).resolve().parent));from qa_split import setup,mesh_eval,co,polys,top,sdf,stats,ROOT,SKIN,SEEDS,FLESH,PLANE,SPHERE,CAP

def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def attr(m,name):
 a=m.attributes[name];vec=a.data_type=='FLOAT_VECTOR';dtype=np.float32 if vec or a.data_type=='FLOAT' else np.bool_ if a.data_type=='BOOLEAN' else np.int32;v=np.empty(len(a.data)*(3 if vec else 1),dtype);a.data.foreach_get('vector' if vec else 'value',v);return v.reshape(-1,3) if vec else v

def tri(m):
 m.calc_loop_triangles();a=np.empty(len(m.loop_triangles)*3,np.int32);m.loop_triangles.foreach_get('vertices',a);return a.reshape(-1,3)
def tree(v,t):return BVHTree.FromPolygons(v.tolist(),t.tolist(),all_triangles=True)
def distances(t,p):return np.asarray([float(t.find_nearest(Vector(x))[3]) for x in p])
def rim(v,edges):return np.concatenate([v[sorted({i for e in edges for i in e})],np.asarray([(v[i]+v[j])*.5 for i,j in edges])]) if edges else np.empty((0,3),np.float32)
def skin_data():
 e,m=mesh_eval(SKIN);v=co(m);t=tri(m);f=polys(m);tp,edges=top(m);r=rim(v,edges);a={'v':v,'t':t,'f':f,'rim':r,'pit':attr(m,'achene_pit'),'rest':attr(m,'sl_rest_position'),'top':tp};
 if 'sl_fast_source_face' in m.attributes:a.update(face_id=attr(m,'sl_fast_source_face'),signed=attr(m,'sl_fast_face_signed_mm'))
 e.to_mesh_clear();return a

def other(name,attrs):
 e,m=mesh_eval(name);v=co(m);t=tri(m);a={n:attr(m,n) for n in attrs if n in m.attributes};tp=top(m)[0];cap=None
 if name==FLESH and len(t):
  ci=next(i for i,x in enumerate(m.materials) if x and x.name==CAP);cap=np.asarray([tuple(x.vertices) for x in m.loop_triangles if x.material_index==ci],np.int32);assert len(cap)
 result={'coords':digest(v),'triangles':digest(t),'attributes':{k:digest(x) for k,x in a.items()},'topology':tp};e.to_mesh_clear();return result,v,t,a,cap

def load(p):bpy.ops.wm.open_mainfile(filepath=str(Path(p).resolve()),use_scripts=False);return setup(pose,voxel),bpy.data.objects[ROOT]
def set_mode(root,m):root['split_mode']=m;root.update_tag();bpy.context.view_layer.update()
def seed_contacts(seed,skin_t,flesh_t):
 _,v,t,a,_=seed;ids=a['sl_anchor_index'];result=[];face_id=ids[t[:,0]];assert np.all(ids[t]==face_id[:,None]);
 for i in np.unique(ids):
  verts=np.flatnonzero(ids==i);faces=t[face_id==i];f=np.searchsorted(verts,faces);st=tree(v[verts],f);s=bool(skin_t.overlap(st));q=bool(flesh_t.overlap(st)) if flesh_t else False;result.append((int(i),s,q))
 return {'retained':len(result),'skin_contact':sum(x[1] for x in result),'skin_or_flesh_contact':sum(x[1] or x[2] for x in result),'no_surface_contact_ids':[x[0] for x in result if not(x[1] or x[2])]}
start=time.perf_counter();mode,root=load(old);set_mode(root,0);orig=skin_data();set_mode(root,mode);A=skin_data();sa=other(SEEDS,['sl_rest_position','sl_anchor_index']);fa=other(FLESH,['sl_cut_face','sl_rest_position','sl_edge_distance_mm','sl_cut_point','sl_outer_recess_point','sl_pre_recess_position','sl_cutter_signed_mm','sl_reference_position','sl_reference_normal']);stock=(root['anchor_digest'],root['neutral_stock_key']);print('A',pose,voxel,A['top']['vertices'],flush=True)
mode,root=load(new);assert stock==(root['anchor_digest'],root['neutral_stock_key']);B=skin_data();sb=other(SEEDS,['sl_rest_position','sl_anchor_index']);fb=other(FLESH,['sl_cut_face','sl_rest_position','sl_edge_distance_mm','sl_cut_point','sl_outer_recess_point','sl_pre_recess_position','sl_cutter_signed_mm','sl_reference_position','sl_reference_normal']);assert sa[0]==sb[0] and fa[0]==fb[0],'seed or flesh geometry/attributes changed'
report={'pose':pose,'voxel_mm':voxel,'baseline_sha':sha(old),'candidate_sha':sha(new),'stock_key':stock[1],'anchor_digest':stock[0],'flesh_seed_exact':True,'flesh':fb[0],'seeds':sb[0]}
orig_lookup={tuple(v):i for i,v in enumerate(orig['v'])};assert len(orig_lookup)==len(orig['v']);raw_idx=np.asarray([orig_lookup.get(tuple(x),-1) for x in B['v']]);assert np.all(raw_idx>=0),'new vertices introduced';assert np.array_equal(B['pit'],orig['pit'][raw_idx]) and np.array_equal(B['rest'],orig['rest'][raw_idx]);report['candidate_all_vertices_exact_source']=True
safe=sdf(orig['v'],mode)>.5
for k,x in [('A',A),('B',B)]:
 tp=x['top'];assert tp['wire_or_over_two_face_edges']==tp['inconsistent_edges']==tp['degenerate_triangles']==0,tp
 present=set(map(tuple,x['v']));exact=sum(tuple(v) in present for v in orig['v'][safe]);report[k]={'skin_topology':tp,'exact_safe_vertices':int(exact),'safe_vertices':int(safe.sum()),'position_sha':digest(x['v']),'pit_sha':digest(x['pit']),'triangle_sha':digest(x['t'])};assert exact==safe.sum(),(k,exact,safe.sum())
 if mode:
  r=x['rim'];c=sdf(r,mode);cap=tree(fb[1],fb[4]);cd=distances(cap,r);report[k]['rim']={'samples':len(r),'signed_cutter_mm':stats(c),'absolute_cutter_mm':stats(abs(c)),'inside_cutter_gt_0_03mm':int((c<-.03).sum()),'outside_cutter_gt_0_03mm':int((c>.03).sum()),'nearest_cap_mm':stats(cd),'over_0_10mm':int((cd>.10).sum())}
if not mode:
 assert np.array_equal(B['v'],A['v']) and B['f']==A['f'];report['whole_exact']=True
else:
 # Independently check source-face identity and diagnostic SDF values on the full pre-delete stock.
 mapped=[tuple(raw_idx[list(f)]) for f in B['f']];expected=[orig['f'][int(i)] for i in B['face_id']];assert mapped==expected,'retained face connectivity not original';assert len(set(B['face_id']))==len(B['f']) and (B['signed']>=0).all()
 g=bpy.data.objects[SKIN].modifiers[-1].node_group;outnode=next(n for n in g.nodes if n.type=='GROUP_OUTPUT');stored=next(n for n in g.nodes if n.bl_idname=='GeometryNodeStoreNamedAttribute' and n.inputs['Name'].default_value=='sl_fast_face_signed_mm');origlink=outnode.inputs[0].links[0].from_socket;g.links.new(stored.outputs['Geometry'],outnode.inputs[0]);bpy.context.view_layer.update();e,m=mesh_eval(SKIN);all_id=attr(m,'sl_fast_source_face');all_s=attr(m,'sl_fast_face_signed_mm');assert np.array_equal(all_id,np.arange(len(orig['f'])));assert np.array_equal(co(m),orig['v']);e.to_mesh_clear();g.links.new(origlink,outnode.inputs[0]);bpy.context.view_layer.update()
 assert np.array_equal(B['face_id'],np.flatnonzero(all_s>=0)), 'retained face set differs from signed rule';assert np.array_equal(B['signed'],all_s[B['face_id']]);centers=np.asarray([orig['v'][list(f)].mean(axis=0) for f in orig['f']]);analytic=sdf(centers,mode);clear=abs(analytic)>.05;near=abs(analytic)<voxel*.75;nearerr=float(np.max(abs(all_s[near]-analytic[near])));wrong=int(((all_s[clear]<0)!=(analytic[clear]<0)).sum());assert wrong==0 and nearerr<.25*voxel,(wrong,nearerr)
 report['face_rule']={'source_faces':len(all_s),'kept':len(B['face_id']),'removed':int((all_s<0).sum()),'exact_source_face_indices':True,'exact_signed_selection':True,'clear_analytic_centers':int(clear.sum()),'clear_wrong_labels':wrong,'near_cutter_sample_count':int(near.sum()),'near_cutter_max_error_mm':nearerr}
 # A's exact-clip rim is a common spatial comparator. Nearest skin probes are unsigned, not a proof of seal.
 ta=tree(A['v'],A['t']);tb=tree(B['v'],B['t']);ft=tree(fb[1],fb[2]);d=distances(tb,A['rim']);report['common_exact_rim_to_B_skin']={'samples':len(d),'distance_mm':stats(d),'over_0_10mm':int((d>.10).sum())}
 report['A']['seed_contacts']=seed_contacts(sa,ta,ft);report['B']['seed_contacts']=seed_contacts(sb,tb,ft)
 report['interface_gate_pass']=bool(report['B']['rim']['over_0_10mm']==0 and report['B']['rim']['inside_cutter_gt_0_03mm']==0 and report['common_exact_rim_to_B_skin']['over_0_10mm']==0 and B['top']['boundary_bad_valence']==0)
report.update(technical_invariants_pass=True,elapsed_seconds=time.perf_counter()-start,blender=bpy.app.version_string);out.write_text(json.dumps(report,indent=2)+'\n');print('RESULT',json.dumps({k:report.get(k) for k in ['pose','voxel_mm','A','B','face_rule','common_exact_rim_to_B_skin','interface_gate_pass','elapsed_seconds']}),flush=True)

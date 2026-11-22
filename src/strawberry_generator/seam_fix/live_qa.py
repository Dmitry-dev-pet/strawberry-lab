from pathlib import Path
import sys,json,hashlib
import bpy,numpy as np
import ast,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments/geometric-achene-pits-v1')]
from validate_pits import activate_runtime,body_mesh,topology,measure,pose_knife,KNIFE,activate,flush_callback
from validate_exact_cut import surface,assert_fast
sys.path.insert(0,str(ROOT/'experiments/profile-vascular-v1'))
from profile_probe import inverse
sys.path.insert(0,str(Path(__file__).parent))
from probe import metrics as zero_metrics
src=(ROOT/'experiments/nonlinear-cut-v1/check_field.py').read_text();fn=next(n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name=='evaluate');code=ast.get_source_segment(src,fn).replace("if n.type=='TEX_COORD':","if n.type in {'TEX_COORD','ATTRIBUTE'}:");shader_env={'math':math};exec(code,shader_env)
source,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(source.resolve()),use_scripts=False);s=bpy.context.scene;body=s.objects['Receptacle | canonical PR29 hull'];assert_fast(body)
def coords():
 return {o.name:np.array([tuple(v.co) for v in o.data.vertices] if o.type=='MESH' else [p.co[:3] for sp in o.data.splines for p in sp.points]) for o in s.objects if o.type in {'MESH','CURVE'} and not o.get('_strawberry_transient_exact')}
def rest_digest():
 r={}
 for o in s.objects:
  if o.get('_strawberry_transient_exact'):continue
  if o.type=='MESH' and 'nonlinear_source_rest' in o.data.attributes:r[o.name]=[tuple(p.vector) for p in o.data.attributes['nonlinear_source_rest'].data]
  if o.type=='CURVE' and 'nonlinear_source_points' in o:r[o.name]=o['nonlinear_source_points']
 return hashlib.sha256(repr(r).encode()).hexdigest()
initial=coords();rest=rest_digest();first=activate_runtime();r=activate_runtime();assert first['handler'] not in bpy.app.handlers.depsgraph_update_post
session=r['session'];env=session.refresh.__globals__;assert env['CURVES']==(('ARTIST | 28 trunks + 264 seed-linked terminals',292),)
reports=[]
for label,values in [('A',(.23,-.12,1.08)),('B',(-.12,.18,.96)),('A-return',(.23,-.12,1.08))]:
 for k,v in zip(['live_profile_a','live_profile_b','live_profile_h'],values):setattr(s,k,v)
 assert bpy.ops.strawberry.apply_profile()=={'FINISHED'};assert rest_digest()==rest
 if label=='A':initial=coords()
 if label=='A-return':
  final=coords();error=max(float(np.max(abs(final[n]-points))) for n,points in initial.items());assert error<5e-7;break
 body.data.calc_loop_triangles();tree=BVHTree.FromPolygons([v.co for v in body.data.vertices],[t.vertices[:] for t in body.data.loop_triangles],all_triangles=True);counts={}
 for o in s.objects:
  if o.get('role')!='achene':continue
  o.data.calc_loop_triangles();t=BVHTree.FromPolygons([v.co for v in o.data.vertices],[t.vertices[:] for t in o.data.loop_triangles],all_triangles=True);counts[o.name]=len(t.overlap(tree));assert counts[o.name]>0
 assert len(counts)==264
 graph=s.objects[env['CURVES'][0][0]];nodes=json.loads(graph['graph_manifest']);endpoint=[]
 for sp,n in zip(graph.data.splines,nodes):
  if 'seed_id' in n:endpoint.append(min((Vector(sp.points[-1].co[:3])-v.co).length for v in s.objects[n['seed_id']].data.vertices)*s.unit_settings.scale_length*1000)
 assert len(endpoint)==264 and max(endpoint)<1e-4
 activate(s,'matched');cuts=[]
 for pose in [(0,0,0),(.08,29,32)]:
  bpy.ops.strawberry.exact_quality(exact=False);pose_knife(s.objects[KNIFE],pose);bpy.context.view_layer.update();skin=surface(body_mesh(body));assert topology(body_mesh(body))>0
  fm=zero_metrics(body_mesh(body));assert fm['zero_edges_all']==fm['zero_render_triangles']==fm['zero_polygon_faces']==0
  bpy.ops.strawberry.exact_quality(exact=True)
  if bpy.app.timers.is_registered(r['timer']):flush_callback(r)
  else:session.refresh()
  assert session.error is None;mesh=body_mesh(body);assert surface(mesh)==skin;em=zero_metrics(mesh);assert em['zero_edges_all']==em['zero_render_triangles']==em['zero_polygon_faces']==0;m,profile=measure(s,body,mesh)
  cfg=json.loads(s['Nonlinear parameters']);params=cfg['a'],cfg['b'],cfg['h'];cap=sorted({i for face in mesh.polygons if face.material_index==1 for i in face.vertices});errors=[]
  node=next(n for n in session.material.node_tree.nodes if n.label=='Analytic nonlinear inverse: physical -> original PR29 rest')
  for i in cap[::max(1,len(cap)//3)][:3]:
   physical=Vector(mesh.attributes['strawberry_exact_rest'].data[i].vector);expected=Vector(inverse(physical,params));cpu=env['nonlinear_rest'](physical);shader=Vector(shader_env['evaluate'](node.outputs[0],physical));errors.extend([(expected-cpu).length,(expected-shader).length]);assert abs(session.atlas.sample_green(cpu)-session.atlas.sample_green(expected))<1e-6
  assert max(errors)<1e-6;m['shader_cpu_rest_max_error']=max(errors);cuts.append(m)
 # Same cap topology/pose, Vascular0 vs0.12. Other tissue controls fixed.
 vascular=s['strawberry_tissue_vascular_mm'];s['strawberry_tissue_vascular_mm']=0;session.refresh();_,zero=measure(s,body,body_mesh(body))
 s['strawberry_tissue_vascular_mm']=.12;session.refresh();_,on=measure(s,body,body_mesh(body));assert zero.keys()==on.keys();delta=max(on[k]-zero[k] for k in zero);assert delta>.01
 affected=[k for k in zero if on[k]-zero[k]>.001];near=[session.strands.distance(env['nonlinear_rest'](Vector(k)),1/(s.unit_settings.scale_length*1000))*(s.unit_settings.scale_length*1000) for k in affected];assert max(near)<1.001
 s['strawberry_tissue_vascular_mm']=vascular;session.refresh()
 for mode in ['whole','matched','flesh-only','fibers-only']:activate(s,mode)
 activate(s,'matched')
 reports.append({'state':label,'contacts':counts,'endpoint_max_mm':max(endpoint),'cuts':cuts,'vascular_max_added_mm':delta,'vascular_affected_vertices':len(affected),'max_affected_distance_to_new_graph_mm':max(near)})
# Leave a source-derived A scene in native Fast, proving no external disk rebuild needed.
bpy.ops.strawberry.exact_quality(exact=False);assert_fast(body)
out.write_text(json.dumps({'status':'PASS','states_same_process':reports,'A_B_A_max_coordinate_error':error,'rest_source_digest':rest,'rest_buffers_unchanged':True,'new_strand_source':env['CURVES'],'double_run':True,'UI_operator_used':True},indent=2)+'\n')

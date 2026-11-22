from pathlib import Path
import sys,json,hashlib,math
import bpy,numpy as np
import ast
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments/geometric-achene-pits-v1'),str(ROOT/'experiments/profile-vascular-v1')]
from validate_pits import activate_runtime,body_mesh,topology,measure,pose_knife,KNIFE,activate,flush_callback,immutable_snapshot,packed_atlas_digest
from validate_exact_cut import surface,assert_fast
from profile_probe import inverse
sys.path.insert(0,str(Path(__file__).parent))
from probe import metrics as zero_metrics
src=(ROOT/'experiments/nonlinear-cut-v1/check_field.py').read_text();tree=ast.parse(src);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='evaluate');code=ast.get_source_segment(src,fn).replace("if n.type=='TEX_COORD':","if n.type in {'TEX_COORD','ATTRIBUTE'}:");shader_env={'math':math};exec(code,shader_env)
p,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert not out.exists()
v=p.stem;source=ROOT.parent/'strawberry-generator/build/generator-v1-final'/v/'strawberry.blend'
def geometry():
 return {o.name:hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(f.vertices) for f in o.data.polygons]) if o.type=='MESH' else [[(tuple(p.co),p.radius,p.tilt) for p in sp.points] for sp in o.data.splines]).encode()).hexdigest() for o in bpy.context.scene.objects if o.type in {'MESH','CURVE'}}
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);before=geometry();atlas_digest=packed_atlas_digest();materials=immutable_snapshot(bpy.context.scene)['materials']
bpy.ops.wm.open_mainfile(filepath=str(p.resolve()),use_scripts=False);s=bpy.context.scene;assert geometry()==before and immutable_snapshot(s)['materials']==materials
body=s.objects['Receptacle | canonical PR29 hull'];assert_fast(body);activate(s,'matched');first=activate_runtime();r=activate_runtime();assert first['handler'] not in bpy.app.handlers.depsgraph_update_post
session=r['session'];env=session.refresh.__globals__;cfg=json.loads(s['Nonlinear parameters']);params=cfg['a'],cfg['b'],cfg['h'];poses=[]
for pose in [(0,0,0),(-.26,0,0),(.08,29,32)]:
 pose_knife(s.objects[KNIFE],pose);bpy.context.view_layer.update();fast=body_mesh(body);skin=surface(fast);assert topology(fast)>0
 fm=zero_metrics(fast);assert fm['zero_edges_all']==fm['zero_render_triangles']==fm['zero_polygon_faces']==0
 bpy.ops.strawberry.exact_quality(exact=True)
 if bpy.app.timers.is_registered(r['timer']):flush_callback(r)
 else:session.refresh()
 assert session.error is None,session.error
 mesh=body_mesh(body);assert surface(mesh)==skin;em=zero_metrics(mesh);assert em['zero_edges_all']==em['zero_render_triangles']==em['zero_polygon_faces']==0
 metrics,_=measure(s,body,mesh);metrics.update(Fast_zero_audit=fm,Exact_zero_audit=em,requested_pose=pose,physical_knife_matrix=[list(row) for row in s.objects[KNIFE].matrix_world],physical_rest_y_bias_mm=.001);assert metrics['max_displacement_mm']>.01
 mm=s.unit_settings.scale_length*1000;fade=.75/mm;boundary=env['Segments'](((Vector(a),Vector(b),0.,0.) for a,b in surface(mesh)[1]),fade)
 cap={i for face in mesh.polygons if face.material_index==1 for i in face.vertices};samples=[]
 for i in sorted(cap)[::max(1,len(cap)//3)][:3]:
  physical=Vector(mesh.attributes['strawberry_exact_rest'].data[i].vector);expected=Vector(inverse(physical,params));actual=env['nonlinear_rest'](physical)
  node=next(n for n in session.material.node_tree.nodes if n.label=='Analytic nonlinear inverse: physical -> original PR29 rest')
  shader_rest=Vector(shader_env['evaluate'](node.outputs[0],physical));assert (shader_rest-expected).length<1e-6
  assert tuple(params) in session.key[3]
  assert (actual-expected).length<1e-6
  assert abs(session.atlas.sample_green(actual)-session.atlas.sample_green(expected))<1e-6
  samples.append({'physical_source':list(physical),'reference_rest':list(expected),'atlas_green':session.atlas.sample_green(actual)})
 assert len(samples)==3
 for i in sorted(cap)[::max(1,len(cap)//7)][:7]:
  physical=Vector(mesh.attributes['strawberry_exact_rest'].data[i].vector);rest=Vector(inverse(physical,params));components=env['tissue_components'](rest,mm,session.atlas,session.strands);requested=sum(s[k]*value for (k,*_),value in zip(env['CONTROLS'],components));distance=boundary.distance(physical,fade);predicted=min(requested/mm,.45*distance)*env['smoothstep'](distance/fade)
  assert abs((mesh.vertices[i].co-physical).length-predicted)*mm<1e-5

 metrics.update(samples=samples,refresh_seconds=session.last['refresh_seconds']);poses.append(metrics)
 bpy.ops.strawberry.exact_quality(exact=False)
# Exercise actual scheduled refresh after translation/rotation while enabled.
bpy.ops.strawberry.exact_quality(exact=True);s.objects[KNIFE].location.y+=.03;s.objects[KNIFE].rotation_euler.x+=.02;bpy.context.view_layer.update();flush_callback(r);assert session.error is None;assert topology(body_mesh(body))>0
for mode in ['whole','matched','flesh-only','fibers-only']:activate(s,mode)
activate(s,'matched');bpy.ops.strawberry.exact_quality(exact=False);assert_fast(body)
assert geometry()==before and packed_atlas_digest()==atlas_digest
bpy.ops.strawberry.exact_quality(exact=True)
keys=[k for k,_,_,_ in env['CONTROLS']];settings=[s[k] for k in keys]
for k in keys:s[k]=0.0
session.refresh();zero,_=measure(s,body,body_mesh(body));assert zero['max_displacement_mm']<1e-5
for k,value in zip(keys,settings):s[k]=value
session.refresh()
original=env['make_mesh']
def broken(*args):raise ValueError('Injected nonlinear QA failure')
env['make_mesh']=broken
try:session.key=None;session.refresh()
finally:env['make_mesh']=original
assert not session.enabled and session.error=='Injected nonlinear QA failure';assert_fast(body)
bpy.ops.strawberry.exact_quality(exact=True)
saved=out.with_suffix('.saved.blend');assert not saved.exists();bpy.ops.wm.save_as_mainfile(filepath=str(saved.resolve()))
bpy.ops.wm.open_mainfile(filepath=str(saved.resolve()),use_scripts=False);assert_fast(bpy.context.scene.objects['Receptacle | canonical PR29 hull'])
out.write_text(json.dumps({'status':'PASS_NONLINEAR_EXACT','source_geometry_equal':True,'source_materials_equal':True,'double_activation':True,'callback_move_rotation':True,'four_layers':True,'zero_controls_flat':True,'error_fallback':True,'save_reopen_fast':True,'poses':poses,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},indent=2)+'\n')

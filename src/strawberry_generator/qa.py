"""Functional validation of independently regenerated Fast-only populations."""
import bpy,json,hashlib,ast,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from exterior_shape import AcheneAnchor,PitField
from validate_pits import topology,body_mesh,pose_knife,KNIFE,activate,packed_atlas_digest
ROOT=Path(__file__).resolve().parents[2]
def validate(scene,anchors):
 body=scene.objects['Receptacle | canonical PR29 hull'];mesh=body.data;mm=scene.unit_settings.scale_length*1000;field=PitField(anchors);errors=[];old_only=[]
 for v,base,normal,rest,mask,old in zip(mesh.vertices,mesh.attributes['pit_base_position'].data,mesh.attributes['pit_source_normal'].data,mesh.attributes['nonlinear_source_rest'].data,mesh.attributes['achene_pit'].data,mesh.attributes['generator_old_pit_mask'].data):
  depth,weight=field.sample(tuple(base.vector*mm));expected=base.vector-Vector(normal.vector).normalized()*(depth/mm);errors.append((expected-rest.vector).length)
  assert abs(mask.value-weight)<1e-6
  if old.value>.001 and weight==0:old_only.append((base.vector-rest.vector).length)
 assert max(errors)<1e-6 and old_only and max(old_only)<1e-6
 pit_error=max(errors)
 mesh.calc_loop_triangles();tree=BVHTree.FromPolygons([v.co for v in mesh.vertices],[t.vertices[:] for t in mesh.loop_triangles],all_triangles=True);contacts={}
 for obj in scene.objects:
  if obj.get('role')!='achene':continue
  obj.data.calc_loop_triangles();seed_tree=BVHTree.FromPolygons([v.co for v in obj.data.vertices],[t.vertices[:] for t in obj.data.loop_triangles],all_triangles=True);contacts[obj.name]=len(seed_tree.overlap(tree));assert contacts[obj.name]>0,obj.name
 assert len(contacts)==264
 graph=scene.objects['ARTIST | 28 trunks + 264 seed-linked terminals'];nodes=json.loads(graph['graph_manifest']);endpoint=[]
 for sp,n in zip(graph.data.splines,nodes):
  if 'seed_id' in n:endpoint.append(min((Vector(sp.points[-1].co[:3])-v.co).length for v in scene.objects[n['seed_id']].data.vertices)*mm)
 assert len(graph.data.splines)==292 and len(endpoint)==264 and max(endpoint)<1e-4
 cuts=[];activate(scene,'matched')
 for pose in [(0,0,0),(-.1,0,-23),(.08,29,32)]:
  pose_knife(scene.objects[KNIFE],pose);bpy.context.view_layer.update();cuts.append({'pose':pose,'positive_connected_manifold_volume':topology(body_mesh(body))})
 # Exercise Apply Profile on the new population without rewriting a file.
 before=np.array([tuple(v.co) for v in mesh.vertices]);cfg=json.loads(scene['Nonlinear parameters']);original=(cfg['a'],cfg['b'],cfg['h'])
 for values in [(-.12,.18,.96) if cfg['a']>0 else (.23,-.12,1.08),original]:
  for key,value in zip(['live_profile_a','live_profile_b','live_profile_h'],values):setattr(scene,key,value)
  assert bpy.ops.strawberry.apply_profile()=={'FINISHED'}
 error=float(np.max(abs(before-np.array([tuple(v.co) for v in mesh.vertices]))));assert error<5e-7
 for mode in ['whole','matched','flesh-only','fibers-only']:activate(scene,mode)
 activate(scene,'whole')
 # The actual saved shader inverse must still evaluate to the canonical atlas coordinates.
 src=(ROOT/'experiments/nonlinear-cut-v1/check_field.py').read_text();fn=next(n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name=='evaluate');env={'math':math};exec(ast.get_source_segment(src,fn),env)
 import sys
 sys.path.insert(0,str(ROOT/'experiments/profile-vascular-v1'))
 from profile_probe import forward
 errors=[]
 for mat in bpy.data.materials:
  if not mat.node_tree:continue
  for node in mat.node_tree.nodes:
   if node.label=='Analytic nonlinear inverse: physical -> original PR29 rest':
    for rest in [(0,0,.2),(.2,.1,-.3),(.3,-.4,.6)]:errors.append(float(np.linalg.norm(np.array(env['evaluate'](node.outputs[0],forward(rest,original)))-rest)))
 assert errors and max(errors)<1e-6
 from strawberry_generator.seam_fix.policy import validate_exact_caps
 exact=validate_exact_caps(scene)
 return {'status':'FAST_AND_EXACT_PASS_WITH_EXPLICIT_1UM_OFFSET','exact_validation':exact,'actual_triangle_contacts':contacts,'terminal_max_error_mm':max(endpoint),'new_pit_field_max_error_model_units':pit_error,'old_only_pit_vertices_cleared':len(old_only),'old_only_max_residual_model_units':max(old_only),'fast_cuts':cuts,'live_profile_roundtrip_error':error,'shader_inverse_error':max(errors),'atlas_digest':packed_atlas_digest(),'four_layers':True,'Exact':'Original CDT verified at physically offset blade poses; no fallback or epsilon change'}

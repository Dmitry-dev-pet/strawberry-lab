import os
"""Validate v5 genuine geometric cellular relief and conservation of live SDF cutters.
Uses Blender loaded with autoexecution disabled. Never overwrites the saved v5.
"""
import bpy, bmesh, numpy as np, json, time, hashlib, os
from pathlib import Path
from mathutils import Vector
P=Path(os.environ.get('STRAWBERRY_SDF_OUT',str(Path(__file__).resolve().parents[2]/'build/sdf-vertical-slice')))
BASE=P/'strawberry-sdf-vertical-slice-v5.blend'
bpy.ops.wm.open_mainfile(filepath=str(BASE),use_scripts=False)
sc=bpy.context.scene
assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
assert 'SDF proof v4 | 192^3 sparse volume and continuous branches' in bpy.data.images
info={'version':'v5','scripts_disabled':True,'scene_sha256':hashlib.sha256(BASE.read_bytes()).hexdigest(),'states':{},'started':time.time()}
def check(mode,frame,label):
 sc.frame_set(frame)
 t=time.perf_counter()
 obj=bpy.data.objects['Receptacle | sculpted skin and achene pits'] if mode=='whole' else bpy.data.objects['SDF visible body | '+mode]
 dg=bpy.context.evaluated_depsgraph_get();ev=obj.evaluated_get(dg);mesh=ev.to_mesh()
 n=len(mesh.vertices)
 bm=bmesh.new();bm.from_mesh(mesh)
 bm.normal_update()
 nonmanifold=sum(not e.is_manifold for e in bm.edges)
 signed=bm.calc_volume(signed=True)
 minarea=min((f.calc_area() for f in bm.faces),default=0)
 bm.free()
 row={'vertices':n,'faces':len(mesh.polygons),'nonmanifold_edges':nonmanifold,'signed_volume':round(signed,4),'min_face_area':minarea,'evaluation_seconds':round(time.perf_counter()-t,3)}
 if mode!='whole':
  assert 'fruit_rest' in mesh.attributes and 'v5_cut_cell_relief_mm' in mesh.attributes
  vals=np.empty(n,dtype='f4')
  mesh.attributes['v5_cut_cell_relief_mm'].data.foreach_get('value',vals)
  row.update({'relief_p01_mm':float(np.percentile(vals,1)),
              'relief_p50_mm':float(np.percentile(vals,50)),
              'relief_p99_mm':float(np.percentile(vals,99)),
              'relief_abs_gt_0_025_mm':int(np.sum(np.abs(vals)>.025)),
              'relief_abs_gt_0_005_mm':int(np.sum(np.abs(vals)>.005)),
              'max_abs_relief_mm':float(np.abs(vals).max())})
  assert row['relief_abs_gt_0_025_mm']>100,'Geometry relief not measurably present: '+repr(row)
  seed=bpy.data.objects['SDF visible seeds | '+mode]
  cutter=bpy.data.objects['SDF cutter | '+('planar (move or rotate)' if mode=='planar' else 'spherical bite (move or scale)')]
  s_eval=seed.evaluated_get(dg);s_mesh=s_eval.to_mesh()
  trans=cutter.matrix_world.inverted_safe()@seed.matrix_world
  intrusions=0
  for vert in s_mesh.vertices:
   q=trans@vert.co
   intrusions+=int(max(abs(q.x),abs(q.y),abs(q.z))<.999 if mode=='planar' else q.length<.999)
  row['visible_achene_solids']=len(s_mesh.vertices)//178
  row['achene_vertices_inside_cutter']=intrusions
  s_eval.to_mesh_clear()
  assert intrusions==0,repr(row)
 ev.to_mesh_clear()
 assert n>1000 and nonmanifold==0 and signed>0 and minarea>1e-9,'Cut manifold/volume failed: '+repr(row)
 info['states'][label]=row
 print('V5_QA',label,json.dumps(row),flush=True)

check('whole',1,'whole')
check('planar',20,'planar_base')
check('bite',40,'bite_base')
# Validate actual vertex displacement against same subdivided geometry at strength zero.
for mode,frame in (('planar',20),('bite',40)):
 sc.frame_set(frame)
 g=bpy.data.node_groups['SDF cutter + rest-space | '+mode]
 strength=g.nodes['V5_CELL_RELIEF_STRENGTH']
 def arr():
  bpy.context.view_layer.update()
  ev=bpy.data.objects['SDF visible body | '+mode].evaluated_get(bpy.context.evaluated_depsgraph_get())
  m=ev.to_mesh()
  a=np.empty(len(m.vertices)*3,dtype=np.float32)
  m.vertices.foreach_get('co',a)
  ev.to_mesh_clear()
  return a.reshape(-1,3)
 full=arr()
 strength.outputs['Value'].default_value=0.0
 bpy.context.view_layer.update()
 zero=arr()
 strength.outputs['Value'].default_value=1.0
 bpy.context.view_layer.update()
 delta=np.linalg.norm(full-zero,axis=1)
 assert len(full)==len(zero)
 item={'max_positional_change_mm':float(delta.max()),'p95_positional_change_mm':float(np.percentile(delta,95)),
 'vertices_changed_over_0_03mm':int(np.sum(delta>.03)),'vertices_identical_within_1e-5mm':int(np.sum(delta<1e-5))}
 info['states'][mode+'_geometry_AB']=item
 print('V5_GEOMETRY_NOT_JUST_BUMP',mode,json.dumps(item),flush=True)
 assert item['max_positional_change_mm']>.04 and item['vertices_changed_over_0_03mm']>100
# Motion recheck for two displaced poses; restore transforms in RAM only.
pc=bpy.data.objects['SDF cutter | planar (move or rotate)'];oldloc=pc.location.copy();oldrot=pc.rotation_euler.copy()
pc.location.y+=3.0;pc.rotation_euler.x+=.1745329252
check('planar',20,'planar_moved_and_rotated')
pc.location=oldloc;pc.rotation_euler=oldrot
bc=bpy.data.objects['SDF cutter | spherical bite (move or scale)'];bcloc=bc.location.copy();bcscale=bc.scale.copy()
bc.location.x-=4;bc.scale=bcscale*1.13
check('bite',40,'bite_moved_and_scaled')
bc.location=bcloc;bc.scale=bcscale
(P/'validation-v5.json').write_text(json.dumps(info,indent=2)+'\n')
print('V5_QA_PASS',flush=True)

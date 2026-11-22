# v3 — conservative seed/cutter exclusion, multi-pose validity check.
import bpy, bmesh, json, math, hashlib, time
from pathlib import Path
from mathutils import Vector
P=Path(__import__('os').environ.get('STRAWBERRY_SDF_OUT',str(Path(__file__).resolve().parents[2]/'build/sdf-vertical-slice')))
bpy.ops.wm.open_mainfile(filepath=str(P/'strawberry-sdf-vertical-slice-v4.blend'),use_scripts=False)
scene=bpy.context.scene
BODY='SDF visible body | '
SEED='SDF visible seeds | '
# Max source seed radius is 0.813mm; 0.95mm SDF guard removes full seeds on collision,
# instead of clipping partial achene meshes along cutter plane.
for mode in ('planar','bite'):
 grp=bpy.data.node_groups['SDF live achene center mask | '+mode]
 cmp=next(n for n in grp.nodes if n.bl_idname=='FunctionNodeCompare')
 old=cmp.inputs['B'].default_value
 cmp.inputs['B'].default_value=.95
 print('SEED_GUARD',mode,old,'->',cmp.inputs['B'].default_value,flush=True)
scene['achene_collision_policy']='Drop entire achene if signed distance of its center to cutter <= 0.95mm; max seed local radius 0.813mm'
scene['source_seed_max_radius_mm']=.813
report={}
def check(tag,mode,fr):
 scene.frame_set(fr)
 bpy.context.view_layer.update()
 dg=bpy.context.evaluated_depsgraph_get()
 obj=bpy.data.objects[BODY+mode]
 ev=obj.evaluated_get(dg);mesh=ev.to_mesh()
 bm=bmesh.new();bm.from_mesh(mesh)
 nm=sum(not e.is_manifold for e in bm.edges)
 bm.free()
 rec={'vertices':len(mesh.vertices),'nonmanifold_edges':nm}
 ev.to_mesh_clear()
 seed=bpy.data.objects[SEED+mode];s_eval=seed.evaluated_get(dg);smesh=s_eval.to_mesh()
 sv=len(smesh.vertices)
 rec['remaining_seed_solids']=sv//178
 cutter=bpy.data.objects['SDF cutter | '+('planar (move or rotate)' if mode=='planar' else 'spherical bite (move or scale)')]
 to_local=cutter.matrix_world.inverted_safe()@seed.matrix_world
 # Signed cutter membership check of every actual vertex (not only centres).
 intrusions=0
 for v in smesh.vertices:
  q=to_local@v.co
  if mode=='planar':
   inside=max(abs(q.x),abs(q.y),abs(q.z))<.999
  else:
   inside=q.length<.999
  intrusions+=int(inside)
 rec['achene_vertices_inside_cutter']=intrusions
 s_eval.to_mesh_clear()
 report[tag]=rec
 print('CHECK',tag,json.dumps(rec),flush=True)
 if nm!=0 or intrusions!=0:
  raise RuntimeError('Failed motion/collision test: '+tag+' '+repr(rec))
check('plane_base','planar',20)
pc=bpy.data.objects['SDF cutter | planar (move or rotate)']
p0=pc.location.copy();r0=pc.rotation_euler.copy()
pc.location.y+=3.0;pc.rotation_euler.x+=math.radians(10)
check('plane_moved_rotated','planar',20)
pc.location=p0;pc.rotation_euler=r0
check('bite_base','bite',40)
bc=bpy.data.objects['SDF cutter | spherical bite (move or scale)']
b0=bc.location.copy();s0=bc.scale.copy()
bc.location.x-=4.0;bc.scale=s0*1.13
check('bite_moved_scaled','bite',40)
bc.location=b0;bc.scale=s0
scene.frame_set(20)
(P/'validation-v4-motion.json').write_text(json.dumps(report,indent=2)+'\n')
print('VALIDATED_V4_MOTION',json.dumps(report),flush=True)

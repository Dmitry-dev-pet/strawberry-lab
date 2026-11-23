"""Read-only vertex-vs-cutter BVH containment check for v19B.
Not a proof of triangle/triangle intersections.
"""
import bpy,bmesh,json,os
from pathlib import Path
from mathutils.bvhtree import BVHTree
s=bpy.context.scene
assert s['v19_variant']=='b' and bpy.context.preferences.filepaths.use_scripts_auto_execute==False
root=Path(os.environ.get('STRAWBERRY_V19_OUT',str(Path(__file__).resolve().parent))).expanduser().resolve()
out={}
for tag,frame in [('planar',20),('bite',40)]:
 cut=bpy.data.objects['SDF cutter | '+('planar (move or rotate)' if tag=='planar' else 'spherical bite (move or scale)')]
 seeds=bpy.data.objects['SDF visible seeds | '+tag]
 bm=bmesh.new();bm.from_mesh(cut.data);bm.normal_update()
 assert all(e.is_manifold for e in bm.edges)
 tree=BVHTree.FromBMesh(bm)
 for pose in ('original','moved'):
  old_loc=cut.location.copy();old_rot=cut.rotation_euler.copy();old_scale=cut.scale.copy()
  if pose=='moved':
   if tag=='planar':cut.location.y+=3.;cut.rotation_euler.x+=.1745329252
   else:cut.location.x-=4.;cut.scale*=1.13
  s.frame_set(frame)
  ev=seeds.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
  tx=cut.matrix_world.inverted_safe()@seeds.matrix_world
  checked=inside=0
  for vert in m.vertices:
   q=tx@vert.co
   near=tree.find_nearest(q)
   if near and near[0] is not None:
    x,n,_,_=near;checked+=1
    if (q-x).dot(n)<-0.0002:inside+=1
  ev.to_mesh_clear();cut.location=old_loc;cut.rotation_euler=old_rot;cut.scale=old_scale
  out[f'{tag}_{pose}']={'checked_seed_vertices':checked,'strictly_inside_cutter_vertices':inside}
  print('V19_SEED',tag,pose,checked,inside,flush=True)
 bm.free()
assert all(v['strictly_inside_cutter_vertices']==0 for v in out.values()),out
(root/'v19b-seed-contact.json').write_text(json.dumps(out,indent=2)+'\n')
print('V19_SEED_GATE_PASS',flush=True)

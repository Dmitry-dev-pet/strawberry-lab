import os
import bpy,time,os
from mathutils import Vector
from pathlib import Path
P=Path(os.environ.get('STRAWBERRY_SDF_OUT',str(Path(__file__).resolve().parents[2]/'build/sdf-vertical-slice')))
bpy.ops.wm.open_mainfile(filepath=str(P/'strawberry-sdf-vertical-slice-v5.blend'),use_scripts=False)
sc=bpy.context.scene
mat=bpy.data.materials['SDF proof v5 | cell sculpt + restrained wet highlights']
bs=next(n for n in mat.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled')
bu=next(n for n in mat.node_tree.nodes if n.bl_idname=='ShaderNodeBump')
bu.inputs['Strength'].default_value=.09
bu.inputs['Distance'].default_value=.014
bs.inputs['Coat Weight'].default_value=.065
bs.inputs['Coat Roughness'].default_value=.24
sc.render.engine='CYCLES';sc.cycles.samples=20
sc.render.resolution_x=660;sc.render.resolution_y=660
sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'
for w in (.18,.34):
 for mode in ('planar','bite'):
  bpy.data.node_groups['SDF cutter + rest-space | '+mode].nodes['V5_CELL_RELIEF_STRENGTH'].outputs['Value'].default_value=w
 bpy.context.view_layer.update()
 for fr,kind in ((20,'plane'),(40,'bite')):
  sc.frame_set(fr)
  sc.render.filepath=str(P/(f'v6-preview-w{int(w*100):02d}-{kind}.png'))
  cam=sc.camera
  if kind=='plane':
   cam.data.ortho_scale=31.
   target=Vector((0,0,24))
   cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
  else:
   cam.data.ortho_scale=67.
   target=Vector((0,0,24))
   cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
  t=time.monotonic()
  bpy.ops.render.render(write_still=True)
  print('V6_PREVIEW',w,kind,round(time.monotonic()-t,2),os.path.getsize(sc.render.filepath),flush=True)
print('PREVIEW_COMPLETE',flush=True)

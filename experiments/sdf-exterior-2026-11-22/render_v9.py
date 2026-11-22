"""Real Cycles v9 scenes, controls fixed to match earlier v4.
Source unchanged. Renders from editable Blender scene, no image generation.
"""
import bpy,time,os
from pathlib import Path
from mathutils import Vector
P=Path(os.environ.get('STRAWBERRY_SDF_OUT',str(Path(__file__).resolve().parents[2]/'build/sdf-vertical-slice')))
bpy.ops.wm.open_mainfile(filepath=str(P/'strawberry-sdf-vertical-slice-v9.blend'),use_scripts=False)
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=36
scene.render.resolution_x=860
scene.render.resolution_y=860
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
for fr,name in ((20,'plane'),(40,'bite')):
 scene.frame_set(fr)
 scene.render.filepath=str(P/('sdf-v9-'+name+'.png'))
 start=time.monotonic();bpy.ops.render.render(write_still=True)
 print('V9_CYCLES',name,'render_s',round(time.monotonic()-start,2),'bytes',os.path.getsize(scene.render.filepath),flush=True)
scene.frame_set(20)
scene.camera.data.ortho_scale=31.0
target=Vector((0,0,24))
scene.camera.rotation_euler=(target-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(P/'sdf-v9-macro.png')
start=time.monotonic();bpy.ops.render.render(write_still=True)
print('V9_CYCLES macro','render_s',round(time.monotonic()-start,2),'bytes',os.path.getsize(scene.render.filepath),flush=True)
print('ALL_V9_CYCLES_COMPLETE',flush=True)

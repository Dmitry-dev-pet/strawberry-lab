import os
"""Real Cycles render v5 vs saved v4 fixed studio camera, 36 samples, no ImageGen."""
import bpy,os,time
from pathlib import Path
from mathutils import Vector
P=Path(os.environ.get('STRAWBERRY_SDF_OUT',str(Path(__file__).resolve().parents[2]/'build/sdf-vertical-slice')))
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=36
scene.render.resolution_x=860;scene.render.resolution_y=860
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
for frame,name in ((20,'plane'),(40,'bite')):
 scene.frame_set(frame)
 scene.render.filepath=str(P/('sdf-v5-'+name+'.png'))
 ts=time.monotonic()
 bpy.ops.render.render(write_still=True)
 print('V5_RENDER',name,'seconds',round(time.monotonic()-ts,2),'bytes',os.path.getsize(scene.render.filepath),flush=True)
scene.frame_set(20)
camera=scene.camera
camera.data.ortho_scale=31.0
target=Vector((0,0,24))
camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(P/'sdf-v5-macro.png')
ts=time.monotonic()
bpy.ops.render.render(write_still=True)
print('V5_RENDER macro','seconds',round(time.monotonic()-ts,2),'bytes',os.path.getsize(scene.render.filepath),flush=True)
print('V5_RENDER_ALL_COMPLETE',flush=True)

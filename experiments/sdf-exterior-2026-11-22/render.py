import bpy,time,os,json,bmesh
from pathlib import Path
from mathutils import Vector
P=Path(__import__('os').environ.get('STRAWBERRY_SDF_OUT',str(Path(__file__).resolve().parents[2]/'build/sdf-vertical-slice')))
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.device='CPU';scene.cycles.samples=26
scene.render.resolution_x=820;scene.render.resolution_y=820
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
for fr,tag in ((20,'plane'),(40,'bite')):
 scene.frame_set(fr)
 scene.render.filepath=str(P/('sdf-v3-'+tag+'.png'))
 bpy.ops.render.render(write_still=True)
 print('RENDER_V3',tag,os.path.getsize(scene.render.filepath),flush=True)
# camera-matched macro from same scene; no retouched/generated image.
scene.frame_set(20)
cam=scene.camera
cam.data.ortho_scale=31.0
target=Vector((0,0,24))
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(P/'sdf-v3-plane-macro.png')
bpy.ops.render.render(write_still=True)
print('RENDER_V3_MACRO',os.path.getsize(scene.render.filepath),flush=True)

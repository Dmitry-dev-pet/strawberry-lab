import json,hashlib,time
from pathlib import Path
import bpy
from mathutils import Vector
from validate_pits import activate,pose_knife,KNIFE

def render(scene,out):
 camera=scene.camera;camera.data.type='ORTHO';camera.data.ortho_scale=3.55;camera.data.dof.use_dof=False;camera.location=(3.5,-5.9,2.05);camera.rotation_euler=(Vector((0,0,.06))-camera.location).to_track_quat('-Z','Y').to_euler()
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.cycles.seed=1729;scene.cycles.use_denoising=True;scene.cycles.use_adaptive_sampling=False;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=scene.render.resolution_y=750;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
 for name in ['whole','cut']:
  activate(scene,'whole' if name=='whole' else 'matched')
  if name=='cut':pose_knife(scene.objects[KNIFE],(-.1,0,-23));bpy.context.view_layer.update()
  png=out/(name+'.png');assert not png.exists();scene.render.filepath=str(png.resolve());started=time.perf_counter();bpy.ops.render.render(write_still=True,layer=bpy.context.view_layer.name)
  png.with_suffix('.json').write_text(json.dumps({'frame':name,'recipe':json.loads(scene['Generator recipe']),'scene_sha256':hashlib.sha256((out/'strawberry.blend').read_bytes()).hexdigest(),'png_sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'resolution':750,'samples':12,'seed':1729,'camera':[list(row) for row in camera.matrix_world],'seconds':time.perf_counter()-started},indent=2)+'\n')

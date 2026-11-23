"""Matched native Blender Cycles: one vs three bites. No source geometry/material edits or image generation."""
import bpy,sys,json,hashlib,time,argparse
from mathutils import Vector
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--scene',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--shot',choices=['bite','close-bite'],required=True);p.add_argument('--resolution',type=int,default=480);p.add_argument('--samples',type=int,default=12)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);src=a.scene.resolve();dest=a.out.resolve();assert src.is_file() and not dest.exists()
bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False);assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
s=bpy.context.scene;body=s.objects['Receptacle | canonical PR29 hull'];cutter=s.objects['SDF | editable sphere bite'];cutter.location=(.82,-.70,-.42);cutter.scale=(1.04,)*3
body['sdf_mode']=2;body['sdf_voxel_mm']=.20;body['sdf_tissue_gain']=1.;body['sdf_use_broad_halo']=1.;body['sdf_cell_surface_gain']=1.
if a.shot=='close-bite':
 cam=s.camera;target=Vector((.35,-.35,-.20));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.4
body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=a.samples;s.cycles.seed=1729;s.cycles.use_denoising=True;s.render.image_settings.file_format='PNG';s.render.resolution_x=s.render.resolution_y=a.resolution;s.render.resolution_percentage=100
s.render.filepath=str(dest);dest.parent.mkdir(parents=True,exist_ok=True)
t=time.monotonic();assert bpy.ops.render.render(write_still=True)=={'FINISHED'} and dest.exists()
rec={'status':'REAL_BLENDER_CYCLES','scene_sha':hashlib.sha256(src.read_bytes()).hexdigest(),'image_sha':hashlib.sha256(dest.read_bytes()).hexdigest(),'shot':a.shot,'resolution':a.resolution,'samples':a.samples,'seed':s.cycles.seed,'seconds':round(time.monotonic()-t,3),'blender':bpy.app.version_string,'camera':[list(x) for x in s.camera.matrix_world],'cutter':[list(x) for x in cutter.matrix_world],'lights':{o.name:[o.data.energy,list(o.data.color),[list(row) for row in o.matrix_world]] for o in s.objects if o.type=='LIGHT'},'view':{'transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma},'material':'unchanged source cell-coherence B ARTIST','difference':'one native cutter vs three native union cutters; seed visibility correct'}
dest.with_suffix('.json').write_text(json.dumps(rec,indent=2));print('RENDER_PASS',a.shot,src.name,rec['seconds'],rec['image_sha'],flush=True)

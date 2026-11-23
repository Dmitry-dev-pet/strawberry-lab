"""Cycles matched A/B source-space SSS, one Blender 5.2.4 process per original PNG."""
import bpy,sys,argparse,hashlib,json,time
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--scene',type=Path,required=True);p.add_argument('--shot',choices=['plane','bite','macro','whole'],required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--resolution',type=int,default=640);p.add_argument('--samples',type=int,default=16)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);src=a.scene.resolve();out=a.out.resolve();assert src.is_file() and not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False);assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
sc=bpy.context.scene;body=sc.objects['Receptacle | canonical PR29 hull'];body['sdf_voxel_mm']=.20;body['sdf_mode']={'plane':1,'macro':1,'bite':2,'whole':0}[a.shot];body['sdf_tissue_gain']=1.;body['sdf_use_broad_halo']=1.
if a.shot=='bite':
 sph=sc.objects['SDF | editable sphere bite'];sph.location=(.82,-.70,-.42);sph.scale=(1.04,)*3
if a.shot=='macro':
 cam=sc.camera;target=Vector((.15,0,-.1));cam.location=target+(cam.location-target)*.42;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
body.update_tag();sc.frame_set(sc.frame_current);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=a.samples;sc.cycles.seed=1729;sc.cycles.use_denoising=True
sc.render.image_settings.file_format='PNG';sc.render.resolution_x=sc.render.resolution_y=a.resolution;sc.render.resolution_percentage=100;out.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(out)
t=time.monotonic();assert bpy.ops.render.render(write_still=True)=={'FINISHED'} and out.exists()
rec={'status':'CYCLES_PASS','source_scene_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'image_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'ss_optical_gain':float(body['sdf_optical_gain']),'shot':a.shot,'blender':bpy.app.version_string,'resolution':a.resolution,'samples':a.samples,'seed':1729,'render_seconds':round(time.monotonic()-t,2),'camera':[list(row) for row in sc.camera.matrix_world],'sphere':[list(row) for row in sc.objects['SDF | editable sphere bite'].matrix_world],'lights':{o.name:[o.data.energy,list(o.data.color),[list(row) for row in o.matrix_world]] for o in sc.objects if o.type=='LIGHT'},'view':{'transform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma},'note':'Original Blender Cycles; no generative-image visualization or image retouch'}
out.with_suffix('.json').write_text(json.dumps(rec,indent=2)+'\n');print('OPTICAL_CYCLES_PASS',a.shot,rec['ss_optical_gain'],rec['render_seconds'],rec['image_sha256'],flush=True)

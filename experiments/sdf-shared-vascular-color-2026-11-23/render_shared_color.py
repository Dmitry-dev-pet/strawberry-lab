"""Real matched Blender Cycles frame, exact A/B gain and geometry same."""
import bpy,sys,argparse,hashlib,json,time
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--scene',type=Path,required=True);p.add_argument('--shot',required=True,choices=['plane','bite','macro']);p.add_argument('--out',type=Path,required=True);p.add_argument('--resolution',type=int,default=640);p.add_argument('--samples',type=int,default=16)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert a.scene.is_file() and not a.out.exists()
bpy.ops.wm.open_mainfile(filepath=str(a.scene.resolve()),use_scripts=False);s=bpy.context.scene
body=s.objects['Receptacle | canonical PR29 hull']
body['sdf_mode']=1 if a.shot in ('plane','macro') else 2;body['sdf_voxel_mm']=.20;body['sdf_tissue_gain']=1.;body['sdf_use_broad_halo']=1.
if a.shot=='bite':
 sphere=s.objects['SDF | editable sphere bite'];sphere.location=(.82,-.70,-.42);sphere.scale=(1.04,)*3
if a.shot=='macro':
 cam=s.camera;target=Vector((.15,0,-.1));cam.location=target+(cam.location-target)*.42;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=a.samples;s.cycles.seed=1729;s.cycles.use_denoising=True
s.render.image_settings.file_format='PNG';s.render.resolution_x=s.render.resolution_y=a.resolution;s.render.resolution_percentage=100
s.render.filepath=str(a.out.resolve());a.out.parent.mkdir(parents=True,exist_ok=True)
t=time.monotonic();assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
rec={'shot':a.shot,'gain':float(body['sdf_v20_color_gain']),'source_scene_sha256':hashlib.sha256(a.scene.read_bytes()).hexdigest(),'image_sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'seed':1729,'resolution':a.resolution,'samples':a.samples,'seconds':round(time.monotonic()-t,2),'camera':[list(x) for x in s.camera.matrix_world],'lights':{o.name:[o.data.energy,list(o.data.color),[list(row) for row in o.matrix_world]] for o in s.objects if o.type=='LIGHT'},'cutter':[list(row) for row in s.objects['SDF | editable sphere bite'].matrix_world],'view':{'transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma}}
a.out.with_suffix('.json').write_text(json.dumps(rec,indent=2)+'\n');print('CYCLES_PASS',rec['shot'],rec['gain'],rec['seconds'],rec['image_sha256'],flush=True)

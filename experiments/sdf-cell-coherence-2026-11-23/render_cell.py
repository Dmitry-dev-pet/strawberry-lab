"""Original native Cycles image of the same shared cell domain A/B, one process per frame."""
import bpy,sys,argparse,hashlib,time,json
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--scene',type=Path,required=True);p.add_argument('--shot',required=True,choices=['plane','bite','macro','whole']);p.add_argument('--out',type=Path,required=True);p.add_argument('--samples',type=int,default=16);p.add_argument('--resolution',type=int,default=640)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert a.scene.is_file() and not a.out.exists()
bpy.ops.wm.open_mainfile(filepath=str(a.scene.resolve()),use_scripts=False);assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
s=bpy.context.scene;body=s.objects['Receptacle | canonical PR29 hull'];body['sdf_voxel_mm']=.20;body['sdf_mode']={'plane':1,'bite':2,'macro':1,'whole':0}[a.shot];body['sdf_tissue_gain']=1.;body['sdf_use_broad_halo']=1.
if a.shot=='bite':
 sph=s.objects['SDF | editable sphere bite'];sph.location=(.82,-.70,-.42);sph.scale=(1.04,)*3
if a.shot=='macro':
 cam=s.camera;target=Vector((.15,0,-.1));cam.location=target+(cam.location-target)*.42;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=a.samples;s.cycles.seed=1729;s.cycles.use_denoising=True
s.render.image_settings.file_format='PNG';s.render.resolution_x=s.render.resolution_y=a.resolution;s.render.resolution_percentage=100
a.out.parent.mkdir(parents=True,exist_ok=True);s.render.filepath=str(a.out.resolve());t=time.monotonic()
assert bpy.ops.render.render(write_still=True)=={'FINISHED'} and a.out.exists()
rec={'status':'CYCLES_PASS','variant_gain':float(body['sdf_cell_surface_gain']),'shot':a.shot,'scene_sha':hashlib.sha256(a.scene.read_bytes()).hexdigest(),'image_sha':hashlib.sha256(a.out.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'seed':1729,'resolution':a.resolution,'samples':a.samples,'cycles_seconds':round(time.monotonic()-t,3),'camera':[list(row) for row in s.camera.matrix_world],'cutter':[list(row) for row in s.objects['SDF | editable sphere bite'].matrix_world],'lights':{o.name:[o.data.energy,list(o.data.color),[list(row) for row in o.matrix_world]] for o in s.objects if o.type=='LIGHT'},'view':{'transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma}}
a.out.with_suffix('.json').write_text(json.dumps(rec,indent=2)+'\n');print('CELL_CYCLES_PASS',a.shot,rec['variant_gain'],rec['cycles_seconds'],rec['image_sha'],flush=True)

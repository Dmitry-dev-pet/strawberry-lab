"""Render true Cycles A/B with fixed camera, lights and seed; only shader gain differs."""
import bpy,hashlib,json,time,sys
from mathutils import Vector
from pathlib import Path
scene_path,shot,out_path,*args=sys.argv[sys.argv.index('--')+1:]
scene_path=Path(scene_path).resolve();out=Path(out_path).resolve();resolution=int(args[0]) if args else 720;samples=int(args[1]) if len(args)>1 else 20
assert shot in ('whole','plane','bite','macro') and not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(scene_path),use_scripts=False);s=bpy.context.scene;body=s.objects['Receptacle | canonical PR29 hull']
body['sdf_mode']={'whole':0,'plane':1,'macro':1,'bite':2}[shot];body['sdf_voxel_mm']=.20
if shot=='bite':
 sphere=s.objects['SDF | editable sphere bite'];sphere.location=(.82,-.70,-.42);sphere.scale=(1.04,)*3
if shot=='macro':
 cam=s.camera;target=Vector((.15,0,-.1));cam.location=target+(cam.location-target)*.42;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=samples;s.cycles.seed=1729;s.cycles.use_denoising=True
s.render.image_settings.file_format='PNG';s.render.resolution_x=s.render.resolution_y=resolution;s.render.resolution_percentage=100
s.render.filepath=str(out);start=time.monotonic();assert bpy.ops.render.render(write_still=True)=={'FINISHED'}

rec={'scene_sha256':hashlib.sha256(scene_path.read_bytes()).hexdigest(),'image_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'shot':shot,'mode':body['sdf_mode'],'voxel_mm':body['sdf_voxel_mm'],'gain':body.get('sdf_cut_relief_gain',0),'resolution':resolution,'samples':samples,'seed':1729,'render_seconds':time.monotonic()-start,'camera':[list(row) for row in s.camera.matrix_world],'lights':{o.name:[o.data.energy,list(o.data.color),[list(row) for row in o.matrix_world]] for o in s.objects if o.type=='LIGHT'},'cutter':[list(row) for row in s.objects['SDF | editable sphere bite'].matrix_world],'warning':'ARTIST only; shader microfibers, no real anatomical volume cells or liquid layer'}
out.with_suffix('.json').write_text(json.dumps(rec,indent=2)+'\n')
print('RENDER_PASS',shot,out.name,'seconds',round(rec['render_seconds'],2),flush=True)

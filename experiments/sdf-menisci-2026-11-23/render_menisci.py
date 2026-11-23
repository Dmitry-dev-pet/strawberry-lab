"""Matched original Blender Cycles, source A/B fruit unchanged; one meniscus toggle."""
from pathlib import Path
import bpy,argparse,sys,hashlib,json,time
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--scene',type=Path,required=True);p.add_argument('--shot',choices=['whole','plane','bite','macro'],required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--resolution',type=int,default=480);p.add_argument('--samples',type=int,default=12)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);src=a.scene.resolve();out=a.out.resolve();assert src.is_file() and not out.exists();out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False);s=bpy.context.scene;body=s.objects['Receptacle | canonical PR29 hull'];pool=s.objects['SDF | separate vascular-attached lens pockets']
body['sdf_voxel_mm']=.20;body['sdf_mode']={'whole':0,'plane':1,'macro':1,'bite':2}[a.shot]
if a.shot=='bite':
 sphere=s.objects['SDF | editable sphere bite'];sphere.location=(.82,-.70,-.42);sphere.scale=(1.04,)*3
if a.shot=='macro':
 cam=s.camera;target=Vector((.15,0,-.1));cam.location=target+(cam.location-target)*.42;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
obj=pool.evaluated_get(dg);me=obj.to_mesh();count=len(me.polygons);obj.to_mesh_clear()
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=a.samples;s.cycles.seed=1729;s.cycles.use_denoising=True
s.render.image_settings.file_format='PNG';s.render.resolution_x=s.render.resolution_y=a.resolution;s.render.resolution_percentage=100;s.render.filepath=str(out)
t=time.monotonic();result=bpy.ops.render.render(write_still=True);assert result=={'FINISHED'} and out.exists()
rec={'scene_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'image_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'shot':a.shot,'gain':body['sdf_meniscus_gain'],'lens_polygons':count,'blender':bpy.app.version_string,'resolution':a.resolution,'samples':a.samples,'seed':1729,'cycles_seconds':round(time.monotonic()-t,2),'camera':[list(row) for row in s.camera.matrix_world],'sphere':[list(row) for row in s.objects['SDF | editable sphere bite'].matrix_world],'lights':{o.name:[o.data.energy,list(o.data.color),[list(row) for row in o.matrix_world]] for o in s.objects if o.type=='LIGHT'},'view':{'transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma},'not_approved':'Original ARTIST convex menisci, not botanical measured wetness'}
out.with_suffix('.json').write_text(json.dumps(rec,indent=2)+'\n');print('MENISCI_RENDER_PASS',a.shot,body['sdf_meniscus_gain'],count,rec['cycles_seconds'],rec['image_sha256'],flush=True)

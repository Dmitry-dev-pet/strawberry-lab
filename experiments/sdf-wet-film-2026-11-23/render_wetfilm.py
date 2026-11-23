"""Render exact matched A/B from saved independent Blender scenes, no autoexec."""
import bpy,json,hashlib,argparse,sys,time
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--scene',required=True,type=Path);p.add_argument('--shot',required=True,choices=('plane','bite','macro','whole'));p.add_argument('--out',required=True,type=Path);p.add_argument('--resolution',type=int,default=640);p.add_argument('--samples',type=int,default=16)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert a.scene.is_file() and not a.out.exists()
bpy.ops.wm.open_mainfile(filepath=str(a.scene.resolve()),use_scripts=False)
s=bpy.context.scene;body=s.objects['Receptacle | canonical PR29 hull'];film=s.objects['SDF | live cut wet-film surface']
body['sdf_mode']={'whole':0,'plane':1,'macro':1,'bite':2}[a.shot];body['sdf_voxel_mm']=.20
body['sdf_tissue_gain']=1.0;body['sdf_use_broad_halo']=1.0
if a.shot=='bite':
 sphere=s.objects['SDF | editable sphere bite'];sphere.location=(.82,-.70,-.42);sphere.scale=(1.04,)*3
if a.shot=='macro':
 cam=s.camera;target=Vector((.15,0,-.1));cam.location=target+(cam.location-target)*.42;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
e=film.evaluated_get(dg);m=e.to_mesh();n=len(m.polygons);e.to_mesh_clear()
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=a.samples;s.cycles.seed=1729;s.cycles.use_denoising=True
s.render.image_settings.file_format='PNG';s.render.resolution_x=s.render.resolution_y=a.resolution;s.render.resolution_percentage=100
s.render.filepath=str(a.out.resolve());begin=time.monotonic()
status=bpy.ops.render.render(write_still=True);assert status=={'FINISHED'}
record={'variant_gain':float(body['sdf_wetfilm_gain']),'shot':a.shot,'blender':bpy.app.version_string,'scene_sha256':hashlib.sha256(a.scene.read_bytes()).hexdigest(),'image_sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'film_faces':n,'resolution':a.resolution,'samples':a.samples,'seed':1729,'render_seconds':round(time.monotonic()-begin,3),'camera':[list(row) for row in s.camera.matrix_world],'sphere':[list(row) for row in s.objects['SDF | editable sphere bite'].matrix_world],'lights':{o.name:[o.data.energy,list(o.data.color),[list(row) for row in o.matrix_world]] for o in s.objects if o.type=='LIGHT'},'color_management':{'view_transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma},'caveat':'ARTIST separate open cut film surface, not literal fluid volume'}
a.out.with_suffix('.json').write_text(json.dumps(record,indent=2)+'\n');print('CYCLES_WET_FILM',record,flush=True)

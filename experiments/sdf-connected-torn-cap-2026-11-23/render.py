"""Fresh-process original native Cycles proof for one torn-face topological extrusion control."""
import bpy,argparse,sys,json,hashlib,time
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--scene',required=True,type=Path);p.add_argument('--shot',required=True,choices=['bite','plane','whole','bite-macro']);p.add_argument('--out',required=True,type=Path);p.add_argument('--samples',type=int,default=16);p.add_argument('--resolution',type=int,default=640);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);src=a.scene.resolve();dst=a.out.resolve();assert src.is_file() and not dst.exists()
bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False);assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
s=bpy.context.scene;b=s.objects['Receptacle | canonical PR29 hull'];b['sdf_mode']=0 if a.shot=='whole' else 1 if a.shot=='plane' else 2;b['sdf_voxel_mm']=.20;b['sdf_tissue_gain']=1.;b['sdf_use_broad_halo']=1.;b['sdf_cell_surface_gain']=1.
if a.shot in ('bite','bite-macro'):
 sph=s.objects['SDF | editable sphere bite'];sph.location=(.82,-.70,-.42);sph.scale=(1.04,)*3
if a.shot=='bite-macro':
 cam=s.camera;target=Vector((.35,-.35,-.20));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.40
b.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();d=bpy.context.evaluated_depsgraph_get();d.update();m=b.evaluated_get(d).to_mesh();verts=len(m.vertices);faces=len(m.polygons)
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=a.samples;s.cycles.seed=1729;s.cycles.use_denoising=True;s.render.image_settings.file_format='PNG';s.render.resolution_x=s.render.resolution_y=a.resolution;s.render.resolution_percentage=100;dst.parent.mkdir(parents=True,exist_ok=True);s.render.filepath=str(dst)
t=time.monotonic();assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
r={'status':'ORIGINAL_CYCLES', 'scene_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'image_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'gain':b['sdf_torn_extrude_gain'],'shot':a.shot,'resolution':a.resolution,'samples':a.samples,'seed':s.cycles.seed,'verts':verts,'faces':faces,'seconds':round(time.monotonic()-t,3),'camera':[list(row) for row in s.camera.matrix_world],'cutter':[list(row) for row in s.objects['SDF | editable sphere bite'].matrix_world],'lights':{o.name:[o.data.energy,list(o.data.color),[list(row) for row in o.matrix_world]] for o in s.objects if o.type=='LIGHT'},'view':{'transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma}}
dst.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print('TORN_CYCLES_PASS',a.shot,r['gain'],r['seconds'],r['image_sha256'],flush=True)

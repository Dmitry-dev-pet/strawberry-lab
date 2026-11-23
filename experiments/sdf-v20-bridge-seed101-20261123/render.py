"""Matched native Cycles 3-way A/core/halo from saved editable .blend.

Only native GN live controls change between the variants; source video is not
embedded and no image generation/retouching is used.
"""
from pathlib import Path
import bpy,sys,json,hashlib,time,argparse
from mathutils import Vector
parser=argparse.ArgumentParser();parser.add_argument('--scene',required=True,type=Path);parser.add_argument('--outdir',required=True,type=Path);parser.add_argument('--shot',required=True);parser.add_argument('--variant',required=True,choices=['baseline','core','halo']);parser.add_argument('--resolution',type=int,default=640);parser.add_argument('--samples',type=int,default=16)
a=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);src=a.scene.resolve();shot=a.shot;only=a.variant;assert src.is_file()
assert shot in ('plane','macro','bite','whole')
out=a.outdir.resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False)
s=bpy.context.scene;body=s.objects['Receptacle | canonical PR29 hull']
body['sdf_voxel_mm']=.20;body['sdf_mode']={'plane':1,'macro':1,'bite':2,'whole':0}[shot]
if shot=='bite':
 o=s.objects['SDF | editable sphere bite'];o.location=(.82,-.70,-.42);o.scale=(1.04,)*3
if shot=='macro':
 cam=s.camera;target=Vector((.15,0,-.1));cam.location=target+(cam.location-target)*.42;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=a.samples;s.cycles.seed=1729;s.cycles.use_denoising=True;s.render.image_settings.file_format='PNG'
s.render.resolution_x=s.render.resolution_y=a.resolution;s.render.resolution_percentage=100
outputs=[]
for variant,gain,halo in [('baseline',0.,1.),('core',1.,0.),('halo',1.,1.)]:
 if only and variant != only: continue
 body['sdf_tissue_gain']=gain;body['sdf_use_broad_halo']=halo
 body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
 path=out/f'{shot}-{variant}.png';assert not path.exists();s.render.filepath=str(path)
 t=time.monotonic();assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
 record={'shot':shot,'variant':variant,'tissue_gain':gain,'use_broad_halo':halo,'image_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'scene_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'seconds':round(time.monotonic()-t,2),'blender':bpy.app.version_string,'samples':a.samples,'resolution':a.resolution,'seed':1729,'camera':[list(row) for row in s.camera.matrix_world],'cutter':[list(row) for row in s.objects['SDF | editable sphere bite'].matrix_world],'artist_magnitudes_not_botanical':True}
 path.with_suffix('.json').write_text(json.dumps(record,indent=2));outputs.append(record);print('V20_CYCLES_PASS',shot,variant,record['seconds'],record['image_sha256'],flush=True)

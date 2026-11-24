"""Matched original CPU Cycles exterior frames from pinned saved scenes."""
import bpy,sys,time,hashlib,json
from pathlib import Path
from mathutils import Vector
src,shot,out=sys.argv[sys.argv.index('--')+1:];s=bpy.context.scene
bpy.ops.wm.open_mainfile(filepath=src,use_scripts=False);s=bpy.context.scene;b=s.objects['Receptacle | canonical PR29 hull'];b['sdf_mode']=0;b['sdf_voxel_mm']=.32;b.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update()
if shot=='macro':
 from mathutils import Matrix
 old=s.camera;pos=old.matrix_world.translation.copy();target=Vector((.50,-.83,.44));location=target+(pos-target)*.28
 cam=bpy.data.objects.new('QA independent exterior macro camera',old.data.copy());s.collection.objects.link(cam);cam.location=location;cam.rotation_euler=(target-location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.05;s.camera=cam
if shot not in ('whole','macro'):raise ValueError(shot)
s.render.engine='CYCLES';s.cycles.device='CPU';s.render.resolution_x=s.render.resolution_y=640;s.render.resolution_percentage=100;s.cycles.samples=16;s.cycles.seed=1729;s.cycles.use_denoising=True;s.render.image_settings.file_format='PNG';s.render.filepath=out;s.render.threads_mode='FIXED';s.render.threads=4;bpy.context.view_layer.update()
assert not Path(out).exists();t=time.monotonic();assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();Path(out).with_suffix('.json').write_text(json.dumps({'shot':shot,'voxel_mm':.32,'resolution':640,'samples':16,'seed':1729,'camera':[list(x) for x in s.camera.matrix_world],'camera_type':s.camera.data.type,'ortho_scale':s.camera.data.ortho_scale,'elapsed':time.monotonic()-t,'source_sha':sha(src),'png_sha':sha(out)},indent=2)+'\n')

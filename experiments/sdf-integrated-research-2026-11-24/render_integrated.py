"""Real Cycles frame from the saved integrated scene. Controlled pigment gain."""
import bpy,sys,time,hashlib,json
from pathlib import Path
from mathutils import Vector
src,helper,shot,gain,out=sys.argv[sys.argv.index('--')+1:];gain=float(gain);sys.path.insert(0,str(Path(helper).resolve().parent));from qa_juice_surface import state,BODY,JUICE
bpy.ops.wm.open_mainfile(filepath=src,use_scripts=False);s=bpy.context.scene;b=s.objects[BODY];j=s.objects[JUICE];assert not j.visible_shadow;state(b,'plane' if shot=='macro' else shot,.32,1.)
cap=bpy.data.materials['SDF | inherited 150^3 tissue + own multiscale wetness'];cap.node_tree.nodes['SL Ring Pigment | A/B gain'].outputs[0].default_value=gain
if shot=='macro':
 cam=s.camera;target=Vector((.15,0,-.1));cam.location=target+(cam.location-target)*.56;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
s.render.engine='CYCLES';s.cycles.device='CPU';s.render.resolution_x=s.render.resolution_y=480;s.render.resolution_percentage=100;s.cycles.samples=8;s.cycles.seed=1729;s.cycles.use_denoising=True;s.render.image_settings.file_format='PNG';s.render.filepath=out;s.render.threads_mode='FIXED';s.render.threads=4
assert not Path(out).exists();t=time.monotonic();assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
Path(out).with_suffix('.json').write_text(json.dumps({'shot':shot,'pigment_gain':gain,'visible_shadow':False,'juice_gain':1.,'cell_gain':1.,'vascular_gain':1.,'voxel_mm':.32,'resolution':480,'samples':8,'seed':1729,'camera':[list(x) for x in s.camera.matrix_world],'elapsed':time.monotonic()-t,'source_sha':hashlib.sha256(Path(src).read_bytes()).hexdigest(),'png_sha':hashlib.sha256(Path(out).read_bytes()).hexdigest()},indent=2)+'\n')

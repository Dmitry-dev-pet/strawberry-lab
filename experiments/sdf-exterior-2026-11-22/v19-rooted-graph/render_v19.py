"""Matched original Cycles camera/light renders, no generative image."""
import bpy,sys,time,hashlib,json,os
from pathlib import Path
root=Path(os.environ.get('STRAWBERRY_V19_OUT',str(Path(__file__).resolve().parent))).expanduser().resolve()
args=sys.argv[sys.argv.index('--')+1:]
variant,shot=args
assert variant in ('a','b','af','bf') and shot in ('planar','bite','macro','whole')
s=bpy.context.scene
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=24
s.render.resolution_x=640;s.render.resolution_y=640;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.film_transparent=False
s.frame_set(40 if shot=='bite' else 1 if shot=='whole' else 20)
if shot=='macro':
 from mathutils import Vector
 s.camera.data.ortho_scale=31.
 target=Vector((0,0,24))
 s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler()
out=root/f'cycles-v19{variant}-{shot}-640px-24s.png'
assert not out.exists(),out
s.render.filepath=str(out)
t=time.perf_counter();bpy.ops.render.render(write_still=True)
rec={'variant':variant,'shot':shot,'frame':s.frame_current,'scene_file':Path(bpy.data.filepath).name,'source_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'render_sec':round(time.perf_counter()-t,2),'bytes':out.stat().st_size,'image_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'engine':'Cycles CPU','resolution':[640,640],'samples':24}
(root/f'render-v19{variant}-{shot}.json').write_text(json.dumps(rec,indent=2)+'\n')
print('V19_CYCLES_REAL',json.dumps(rec),flush=True)

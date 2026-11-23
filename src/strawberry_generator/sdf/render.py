"""One native Cycles frame per process; no modification of saved source scene."""
from pathlib import Path
import sys,json,time,hashlib
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from common import *
p,kind,png,*extra=sys.argv[sys.argv.index('--')+1:];voxel=float(extra[0]) if extra else .20;p=Path(p);png=Path(png);assert not png.exists();bpy.ops.wm.open_mainfile(filepath=str(p.resolve()),use_scripts=False);s=bpy.context.scene
mode={'whole':0,'plane':1,'oblique':1,'sphere':2,'macro':1}[kind];state(mode,voxel,kind=='oblique')
# Keep the inherited fixed camera/light for comparable whole/plane/sphere views.
if kind=='macro':
 cam=s.camera;target=Vector((.15,0,-.1));cam.location=target+(cam.location-target)*.56;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
s.render.filepath=str(png.resolve());s.render.resolution_percentage=100;s.render.resolution_x=s.render.resolution_y=900;s.cycles.samples=16;s.cycles.seed=1729;s.cycles.use_denoising=True
start=time.perf_counter();assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
receipt={'scene_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'kind':kind,'mode':mode,'voxel_mm':voxel,'resolution':900,'samples':16,'seed':1729,'camera':[list(r) for r in s.camera.matrix_world],'plane':[list(r) for r in s.objects[PLANE].matrix_world],'sphere':[list(r) for r in s.objects[SPHERE].matrix_world],'seconds':time.perf_counter()-start,'png_sha256':hashlib.sha256(png.read_bytes()).hexdigest()};png.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n')

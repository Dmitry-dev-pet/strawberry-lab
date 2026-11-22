# True Cycles A/B, fixed camera/lights/frames, independent Blender process per version
import bpy, sys, time, json, hashlib
from pathlib import Path
P=Path(__import__('os').environ.get('STRAWBERRY_SDF_OUT',str(Path(__file__).resolve().parents[2]/'build/sdf-vertical-slice')))
argv=sys.argv[sys.argv.index('--')+1:]
version,kind=argv
sc=bpy.context.scene
sc.render.engine='CYCLES'
sc.cycles.device='CPU'
sc.cycles.samples=36
sc.render.resolution_x=860
sc.render.resolution_y=860
sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'
sc.render.film_transparent=False
sc.frame_set(20 if kind=='plane' else 40)
if kind=='macro':
 sc.frame_set(20);sc.camera.data.ortho_scale=31.
 from mathutils import Vector
 target=Vector((0,0,24))
 sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler()
out=P/('sdf-'+version+'-matched-'+kind+'.png')
sc.render.filepath=str(out)
start=time.monotonic();bpy.ops.render.render(write_still=True)
print('RENDER_PROOF='+json.dumps({'version':version,'kind':kind,'samples':sc.cycles.samples,'resolution':[sc.render.resolution_x,sc.render.resolution_y],'frame':sc.frame_current,'seconds':round(time.monotonic()-start,2),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}),flush=True)

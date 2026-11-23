"""True Blender Cycles matched A/B visual evidence from independently saved v12/v19 scenes.
Camera/cutter matched except explicitly disclosed axial centered plane pose.
Does not save source scenes; does not use Frucht media as texture/render output.
"""
import bpy,sys,hashlib,json,time
from mathutils import Vector
from pathlib import Path
P=Path('/mnt/data/strawberry-v19')
a=sys.argv[sys.argv.index('--')+1:]
variant,shot=a
assert variant in ('v12','v19a','v19b')
assert shot in ('central','bite','central_macro','oblique')
sc=bpy.context.scene
sc.frame_set(40 if shot=='bite' else 20)
displaced_mm=0
if shot in ('central','central_macro'):
  knife=bpy.data.objects['SDF cutter | planar (move or rotate)']
  face=knife.data.polygons[1]
  normal=(knife.matrix_world.to_3x3().inverted().transposed()@face.normal).normalized()
  point=knife.matrix_world@knife.data.vertices[face.vertices[0]].co
  signed=float(normal.dot(Vector((0,0,25))-point))
  knife.location+=normal*signed
  displaced_mm=signed
  bpy.context.view_layer.update()
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=16
sc.render.resolution_x=640;sc.render.resolution_y=640;sc.render.resolution_percentage=100
sc.render.film_transparent=False;sc.render.image_settings.file_format='PNG'
if shot=='central_macro':
  sc.camera.data.ortho_scale=31.
  target=Vector((0,0,24.))
  sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler()
f=P/f'cycles-{variant}-{shot}-640px-16s.png'
assert not f.exists(),f
sc.render.filepath=str(f)
t0=time.monotonic();bpy.ops.render.render(write_still=True)
assert f.exists() and f.stat().st_size>1000
r={'version':variant,'shot':shot,'samples':16,'resolution':[640,640],'scene_frame':sc.frame_current,
   'center_plane_knife_offset_mm':round(displaced_mm,6),'cycles_render_seconds':round(time.monotonic()-t0,2),
   'blender':bpy.app.version_string,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size,
   'status':'ARTIST tissue demonstration, real Blender Cycles; no ImageGen or vendor source'}
(P/f'render-{variant}-{shot}.json').write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n')
print('V19_RENDER',json.dumps(r),flush=True)

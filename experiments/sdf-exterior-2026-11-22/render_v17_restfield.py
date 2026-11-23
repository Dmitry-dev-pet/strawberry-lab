"""Matched genuine Blender 5.2.4 CPU Cycles frames for v12/v17A/v17B.
Independent render per process, no source scene writes or Frucht reference assets.
"""
import bpy,sys,json,hashlib,time,os
from pathlib import Path
from mathutils import Vector
OUT=Path('/mnt/data/strawberry-v17')
argv=sys.argv[sys.argv.index('--')+1:]
version,kind=argv
assert version in ('v12','v17a','v17b') and kind in ('plane','bite','macro')
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=int(os.environ.get('STRAWBERRY_RENDER_SAMPLES','12'))
size=int(os.environ.get('STRAWBERRY_RENDER_SIZE','512'))
scene.render.resolution_x=size;scene.render.resolution_y=size;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.frame_set(40 if kind=='bite' else 20)
if kind=='macro':
    scene.camera.data.ortho_scale=31.
    target=Vector((0,0,24))
    scene.camera.rotation_euler=(target-scene.camera.location).to_track_quat('-Z','Y').to_euler()
png=OUT/f'cycles-{version}-{kind}-{size}px-{scene.cycles.samples}s.png'
assert not png.exists(),f'Refusing overwrite existing render {png}'
scene.render.filepath=str(png)
t0=time.monotonic();bpy.ops.render.render(write_still=True)
assert png.is_file() and png.stat().st_size>1000
row={'version':version,'kind':kind,'blender':bpy.app.version_string,'resolution':[size,size],
     'samples':scene.cycles.samples,'frame':scene.frame_current,'seconds':round(time.monotonic()-t0,2),
     'sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'bytes':png.stat().st_size,
     'not_an_imagegen_artifact':True}
(OUT/f'render-{version}-{kind}-{size}px-{scene.cycles.samples}s.json').write_text(json.dumps(row,indent=2)+'\n')
print('V17_CYCLES_RENDER='+json.dumps(row),flush=True)

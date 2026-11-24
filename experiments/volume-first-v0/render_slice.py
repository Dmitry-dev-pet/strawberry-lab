import bpy,sys,time
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
angle=int(args[0]) if args else 0
out=Path(__file__).resolve().parent/'outputs'
scene=bpy.context.scene
for ob in bpy.data.objects:
 if ob.name.startswith('CUT_'): ob.hide_render=(not ob.name.startswith(f'CUT_{angle:03d}'))
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=20
scene.render.resolution_x=840;scene.render.resolution_y=960
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.cycles.use_denoising=True
scene.render.filepath=str((out/f'slice-{angle:03d}.png').resolve())
t=time.perf_counter()
bpy.ops.render.render(write_still=True)
print('SLICE_CYCLES_OK',angle,'seconds',round(time.perf_counter()-t,1),flush=True)

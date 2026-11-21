"""Real Blender Cycles rendering of fixed-camera V2/V3 morphology variants."""
import bpy,sys,argparse,time
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--variant',choices=['v2','28-sag0.25','28-sag1.0','28-sag1.8','14-sag1.0','40-sag1.0'],default='28-sag1.0')
p.add_argument('--view',choices=['only','ghost','cut'],default='only')
p.add_argument('--resolution',type=int,default=680)
p.add_argument('--samples',type=int,default=12)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
sc=next(s for s in bpy.data.scenes if s.name.startswith({'only':'01 |','ghost':'02 |','cut':'03 |'}[a.view]))
if bpy.context.window:bpy.context.window.scene=sc
for ob in bpy.data.objects:
    if ob.name.startswith('V2 |') and ('core carriers' in ob.name or 'branches ending' in ob.name):
        ob.hide_render=a.variant!='v2'
    if ob.name.startswith('V3 |'):
        ob.hide_render=(f'| {a.variant} |' not in ob.name)
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=a.samples
sc.render.resolution_x=a.resolution;sc.render.resolution_y=int(a.resolution*920/820);sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.film_transparent=False
sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=4
sc.render.filepath=str(a.out.resolve());a.out.parent.mkdir(exist_ok=True,parents=True)
t=time.perf_counter();bpy.ops.render.render(write_still=True,scene=sc.name)
print('V3_REAL_BLENDER_CYCLES',a.view,a.variant,'seconds',round(time.perf_counter()-t,2),a.out.stat().st_size,flush=True)

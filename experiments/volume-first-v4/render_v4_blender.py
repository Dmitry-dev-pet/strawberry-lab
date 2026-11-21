"""Fixed-view Blender Cycles for V3 baseline and independent V4 variants."""
import bpy,sys,time,argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--variant',choices=['v3','0.35','0.85','1.5'],default='0.85');p.add_argument('--view',choices=['only','ghost'],default='only');p.add_argument('--samples',type=int,default=14);p.add_argument('--resolution',type=int,default=840);p.add_argument('--out',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
sc=next(s for s in bpy.data.scenes if s.name.startswith({'only':'01 |','ghost':'02 |'}[a.view]))
if bpy.context.window:bpy.context.window.scene=sc
for ob in bpy.data.objects:
 if ob.name.startswith('V2 |') and ('core carriers' in ob.name or 'branches ending' in ob.name):ob.hide_render=True
 if ob.name.startswith('V3 |'):ob.hide_render=True
 if ob.name.startswith('V4 |'):ob.hide_render=True
bpy.data.objects['V3 | 28-sag0.25 | CARRIERS'].hide_render=False
if a.variant=='v3':bpy.data.objects['V3 | 28-sag0.25 | BRANCHES'].hide_render=False
else:bpy.data.objects[f'V4 | hook{a.variant} | BRANCHES'].hide_render=False
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=a.samples
sc.render.resolution_x=a.resolution;sc.render.resolution_y=int(a.resolution*920/820);sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.film_transparent=False
sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=4
sc.render.filepath=str(a.out.resolve());a.out.parent.mkdir(exist_ok=True,parents=True)
t=time.perf_counter();bpy.ops.render.render(write_still=True,scene=sc.name)
print('V4_CYCLES_PASS',a.variant,a.view,round(time.perf_counter()-t,2),a.out.stat().st_size,flush=True)

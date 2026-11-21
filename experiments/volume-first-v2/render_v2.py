import bpy,sys,argparse,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--view',choices=('only','ghost','cut'),default='only');p.add_argument('--resolution',type=int,default=820);p.add_argument('--samples',type=int,default=12);p.add_argument('--out',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
n={'only':'01 |','ghost':'02 |','cut':'03 |'}[a.view]
scene=next(x for x in bpy.data.scenes if x.name.startswith(n))
bpy.context.window.scene=scene
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=a.samples
scene.render.resolution_x=a.resolution;scene.render.resolution_y=int(a.resolution*920/820);scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=False
scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4
p=a.out.resolve();p.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(p)
t=time.perf_counter();bpy.ops.render.render(write_still=True,scene=scene.name)
print('SEEDLINKED_V2_REAL_CYCLES',a.view,str(p),'seconds',round(time.perf_counter()-t,2),'bytes',p.stat().st_size,flush=True)

#!/usr/bin/env python3
"""Real CPU Cycles renders after auto-updating live M1e5 Exact via frame callbacks."""
import bpy,sys,argparse,time,importlib.util,json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--outdir',type=Path,required=True)
p.add_argument('--frames',type=str,default='15,21,30')
p.add_argument('--samples',type=int,default=16)
p.add_argument('--resolution',type=int,default=720)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
a.outdir.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('m1e5_live_exact',str(Path(__file__).parent/'m1e5_live_exact.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.register()
s=bpy.context.scene
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=a.samples
s.cycles.max_bounces=5;s.cycles.diffuse_bounces=3;s.cycles.glossy_bounces=2
s.render.threads_mode='FIXED';s.render.threads=4
s.render.resolution_x=s.render.resolution_y=a.resolution
s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
s.render.image_settings.color_mode='RGBA';s.render.film_transparent=False
results=[]
for f in [int(v) for v in a.frames.split(',')]:
    before=m._STATE['refresh_count']
    s.frame_set(f)
    if f!=15:assert m._STATE['refresh_count']>before
    assert m._STATE['last_result'] and m._STATE['last_result']['nonmanifold_edges']==0
    assert not bpy.data.objects[m.SNAP].hide_render and bpy.data.objects[m.BODY].hide_render
    dest=a.outdir/f'm1e5-live-exact-frame{f:02d}.png'
    s.render.filepath=str(dest.resolve())
    t=time.perf_counter()
    bpy.ops.render.render(write_still=True)
    info={'frame':f,'path':str(dest),'pixels':[a.resolution,a.resolution],
         'render_s':round(time.perf_counter()-t,3),'exact_mesh_vertices':m._STATE['last_result']['vertices'],
         'exact_mesh_update_s':m._STATE['last_seconds'],'file_bytes':dest.stat().st_size}
    results.append(info)
    print('M1E5_REAL_CYCLES_FRAME',json.dumps(info),flush=True)
m.unregister()
(a.outdir/'render-validation.json').write_text(json.dumps({'status':'PASS','frames':results},indent=2)+'\n')

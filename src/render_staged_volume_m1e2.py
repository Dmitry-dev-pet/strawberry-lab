#!/usr/bin/env python3
"""Render a chosen frame from the saved staged M1e2 scene, without image fabrication."""
import bpy, sys, argparse, time
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--frame',type=int,default=15)
p.add_argument('--samples',type=int,default=10)
p.add_argument('--resolution',type=int,default=640)
p.add_argument('--out',required=True,type=Path)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
a.out.parent.mkdir(parents=True,exist_ok=True)
s=bpy.context.scene;s.frame_set(a.frame)
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=a.samples
s.render.threads_mode='FIXED';s.render.threads=4
s.render.resolution_x=a.resolution;s.render.resolution_y=a.resolution
s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
s.render.image_settings.color_mode='RGBA';s.render.film_transparent=False
s.render.filepath=str(a.out.resolve())
t=time.perf_counter();bpy.ops.render.render(write_still=True)
print('STAGED_VOLUME_CYCLES_PASS',str(a.out.resolve()),round(time.perf_counter()-t,2),flush=True)

#!/usr/bin/env python3
"""Render one genuine Cycles frame of an existing M1d animated Blender scene.

Render a single frame per Blender process to bound memory in headless mode.
Usage: blender -b scene.blend --python src/render_pose.py -- --frame 15 --out build/ --resolution 720 --samples 12
"""
import argparse,sys
from pathlib import Path
import bpy
p=argparse.ArgumentParser()
p.add_argument('--frame',type=int,required=True)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--resolution',type=int,default=720)
p.add_argument('--samples',type=int,default=12)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
if a.resolution<64 or a.samples<1:raise ValueError('Invalid render parameters')
a.out.mkdir(parents=True,exist_ok=True)
s=bpy.context.scene;s.frame_set(a.frame)
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=a.samples
s.render.resolution_x=a.resolution;s.render.resolution_y=a.resolution;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
mode=s.get('m1c_mode','unknown')
s.render.filepath=str(a.out/f'strawberry-m1d-{mode}-frame{a.frame:02d}.png')
bpy.ops.render.render(write_still=True)
print('M1D_RENDER_DONE',s.render.filepath,flush=True)
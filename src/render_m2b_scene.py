#!/usr/bin/env python3
"""Render one saved Blender M2b scene in a fresh process (safe CPU memory)."""
import argparse,sys
from pathlib import Path
import bpy

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--name',required=True,choices=['cells','vascular'])
 p.add_argument('--out',required=True)
 p.add_argument('--samples',type=int,default=9)
 p.add_argument('--resolution-scale',type=float,default=1.)
 a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
 target='04 | M2b | 3D cell diameter proxies NOT histology' if a.name=='cells' else '05 | M2b | vascular graph QUALITATIVE'
 scene=bpy.data.scenes[target]
 bpy.context.window.scene=scene
 scene.render.engine='CYCLES';scene.cycles.samples=a.samples
 scene.render.resolution_percentage=round(100*a.resolution_scale)
 scene.render.filepath=str(Path(a.out).resolve())
 bpy.ops.render.render(write_still=True)
 print('M2B_CYCLES_RENDER_OK',a.name,scene.render.filepath)

if __name__=='__main__':main()
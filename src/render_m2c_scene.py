#!/usr/bin/env python3
"""Render real M2c Blender Cycles frames, independently per scene."""
import argparse,sys
from pathlib import Path
import bpy
p=argparse.ArgumentParser();p.add_argument('--mode',choices=('volume','sections','macro'),required=True)
p.add_argument('--out',required=True);p.add_argument('--samples',type=int,default=16)
p.add_argument('--resolution',type=float,default=.85)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
name={'volume':'06 | M2c | 3D CELL SOLIDS / source diameters',
      'sections':'07 | M2c | exact TWO ORTHOGONAL SECTIONS',
      'macro':'08 | M2c | mixed outer pericarp 3D macro'}[a.mode]
scene=bpy.data.scenes[name];bpy.context.window.scene=scene
scene.render.engine='CYCLES';scene.cycles.samples=a.samples
scene.render.resolution_percentage=round(100*a.resolution)
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
scene.render.filepath=str(Path(a.out).resolve())
scene.cycles.use_denoising=True
bpy.ops.render.render(write_still=True)
print('M2C_CYCLES_RENDER_OK',a.mode,scene.render.filepath)
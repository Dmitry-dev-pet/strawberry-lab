#!/usr/bin/env python3
"""Render an already-saved M1a anatomy .blend with Blender Workbench.

Run: blender -b /path/to/strawberry-m1a-anatomy.blend --python src/render_anatomy_workbench.py -- --output /path/anatomy.png
Workbench is intentionally a schematic viewport render, NOT a Cycles photo.
"""
import bpy
import sys
import argparse
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--output',type=Path,required=True)
p.add_argument('--resolution',type=int,default=720)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
a.output.parent.mkdir(parents=True,exist_ok=True)
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO'
sc.display.shading.color_type='MATERIAL'
sc.display.shading.show_shadows=True
sc.display.shading.show_cavity=True
sc.display.shading.cavity_type='BOTH'
sc.display.shading.curvature_ridge_factor=1.1
sc.display.shading.curvature_valley_factor=1.0
sc.display.shading.background_type='WORLD'
sc.render.resolution_x=a.resolution;sc.render.resolution_y=a.resolution;sc.render.resolution_percentage=100
for m in bpy.data.materials:
    if m.use_nodes:
        bs=m.node_tree.nodes.get('Principled BSDF')
        if bs:
            m.diffuse_color=bs.inputs['Base Color'].default_value
sc.render.filepath=str(a.output)
bpy.ops.render.render(write_still=True)
print('WORKBENCH_RENDER_SAVED',str(a.output),a.output.stat().st_size,flush=True)
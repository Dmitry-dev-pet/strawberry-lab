#!/usr/bin/env python3
"""Render authentic saved M2a Blender scenes (no generated images)."""
import bpy
import argparse
import sys
from pathlib import Path

ap=argparse.ArgumentParser();ap.add_argument('--out',required=True)
ap.add_argument('--samples',type=int,default=12)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
for name,file in (
    ('01 | Fruit Platform | 4 independent contexts','fruit-platform-m2a-overview.png'),
    ('02 | Cell size calibration, not histology','fruit-platform-m2a-cell-gauges.png')):
    scene=bpy.data.scenes[name]
    scene.render.engine='CYCLES'
    scene.cycles.samples=a.samples
    scene.render.filepath=str(out/file)
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    bpy.ops.render.render(scene=scene.name,write_still=True)
    assert (out/file).exists()
    print('FRUIT_PLATFORM_REAL_BLENDER_RENDER_OK',file,(out/file).stat().st_size)
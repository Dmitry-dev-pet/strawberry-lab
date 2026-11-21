#!/usr/bin/env python3
"""Render unchanged geometry from a closer diagnostic camera at frame 15."""
import bpy,argparse,sys,time
from mathutils import Vector
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--samples',type=int,default=6)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
s=bpy.context.scene;s.frame_set(15)
c=s.camera
c.location=(.65,-5.8,2.0)
target=Vector((-.16,-.45,.25))
c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler()
c.data.type='ORTHO';c.data.ortho_scale=2.65
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=a.samples
s.cycles.max_bounces=4;s.cycles.diffuse_bounces=2;s.cycles.glossy_bounces=2;s.cycles.transmission_bounces=1
s.render.threads_mode='FIXED';s.render.threads=4
s.render.resolution_x=520;s.render.resolution_y=520;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.film_transparent=False
s.render.filepath=str(a.out.resolve());a.out.parent.mkdir(parents=True,exist_ok=True)
t=time.perf_counter();bpy.ops.render.render(write_still=True)
print('CUTSURFACE_MACRO_RENDER_PASS',str(a.out),round(time.perf_counter()-t,2))

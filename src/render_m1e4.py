#!/usr/bin/env python3
import bpy,argparse,sys,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--resolution',type=int,default=720);p.add_argument('--samples',type=int,default=16);p.add_argument('--hide-tubes',action='store_true');p.add_argument('--macro',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
s=bpy.context.scene;s.frame_set(int(s['m1e4_snapshot_frame']))
if a.hide_tubes:bpy.data.objects['M1e4 | LIVE 3D filament tubes, clipped by knife'].hide_render=True
if a.macro:
 from mathutils import Vector
 c=s.camera;c.location=(.65,-5.8,2.0);target=Vector((-.16,-.45,.25));c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=2.65
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=a.samples
s.cycles.max_bounces=5;s.cycles.diffuse_bounces=3;s.cycles.glossy_bounces=2
s.render.threads_mode='FIXED';s.render.threads=4
s.render.resolution_x=a.resolution;s.render.resolution_y=a.resolution;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.film_transparent=False
s.render.filepath=str(a.out.resolve());a.out.parent.mkdir(parents=True,exist_ok=True)
t=time.perf_counter();bpy.ops.render.render(write_still=True)
print('M1E4_CYCLES',a.out,'seconds',round(time.perf_counter()-t,2),flush=True)

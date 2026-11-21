#!/usr/bin/env python3
"""Real CPU Cycles A/B: same scene/camera/light; v0 and v1 are separate meshes."""
import argparse,sys,time
from pathlib import Path
import bpy
from mathutils import Vector
p=argparse.ArgumentParser()
p.add_argument('--angle',type=int,choices=(0,32,82),default=0)
p.add_argument('--mode',choices=('baseline','fine'),default='fine')
p.add_argument('--macro',action='store_true')
p.add_argument('--clay',action='store_true',help='Replace only cut-face shader with uniform clay; prove true geometric relief')
p.add_argument('--samples',type=int,default=20)
p.add_argument('--resolution',type=int,default=840)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
s=bpy.context.scene
for obj in bpy.data.objects:
    if obj.name.startswith(('CUT_','V1_CUT_')):
        selected=f'CUT_{a.angle:03d}_' if a.mode=='baseline' else f'V1_CUT_{a.angle:03d}'
        obj.hide_render=not obj.name.startswith(selected)
        obj.hide_set(not obj.name.startswith(selected))
    if obj.name.startswith('V1_SOURCE'):obj.hide_render=True
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=a.samples
s.render.threads_mode='FIXED';s.render.threads=4
s.render.resolution_x=a.resolution;s.render.resolution_y=a.resolution if a.macro else int(a.resolution*960/840)
s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
s.render.image_settings.color_mode='RGBA';s.render.film_transparent=False
s.cycles.use_denoising=True
if a.macro:
    s.cycles.max_bounces=3;s.cycles.diffuse_bounces=2;s.cycles.glossy_bounces=1
if a.clay:
    clay=bpy.data.materials.new('DIAGNOSTIC UNIFORM CLAY, NO BUMP')
    clay.use_nodes=True
    sh=clay.node_tree.nodes.get('Principled BSDF')
    sh.inputs['Base Color'].default_value=(.58,.33,.27,1)
    sh.inputs['Roughness'].default_value=.53
    sh.inputs['Subsurface Weight'].default_value=0.0
    for ob in bpy.data.objects:
        if ob.name.startswith(('CUT_','V1_CUT_')) and not ob.hide_render:
            ob.data.materials[1]=clay
if a.macro:
    cam=s.camera
    cam.location=(0,-6.5,.28)
    aim=Vector((0,0,.19))
    cam.rotation_euler=(aim-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=1.8
else:
    s.camera.data.ortho_scale=2.69
p=a.out.resolve();p.parent.mkdir(parents=True,exist_ok=True)
s.render.filepath=str(p)
bpy.context.view_layer.update()
t=time.perf_counter();bpy.ops.render.render(write_still=True)
print('V1_REAL_CYCLES',a.mode,'angle',a.angle,'macro',a.macro,'seconds',round(time.perf_counter()-t,2),'bytes',p.stat().st_size,flush=True)

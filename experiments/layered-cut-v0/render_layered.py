#!/usr/bin/env python3
"""Render a saved layered scene with genuine Blender View Layer collection toggles."""
import argparse,sys,time,json
from pathlib import Path
import bpy
r=Path(__file__).resolve().parent
p=argparse.ArgumentParser()
p.add_argument('--mode',choices=('matched','flesh-only','fibers-only','no-seeds','core-only','no-core'),required=True)
p.add_argument('--size',type=int,default=550)
p.add_argument('--samples',type=int,default=8)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
mode='matched' if a.mode=='matched' else 'independent'
name='LAYER A | common cut y=0' if mode=='matched' else 'LAYER B | flesh-only cut y=0'
sc=bpy.data.scenes[name]
if bpy.context.window:bpy.context.window.scene=sc
sc.view_layers[0].update()
ly=sc.view_layers[0]

def layer_for(substr):
    def finder(node):
        if substr in node.collection.name:return node
        for child in node.children:
            res=finder(child)
            if res:return res
    return finder(ly.layer_collection)
keynames={
'flesh':'10 | FLESH', 'fullcore':'20 | CORE', 'clipcore':'21 | CORE',
'fullbranch':'30 | VASCULAR', 'clipbranch':'31 | VASCULAR',
'fullseed':'40 | SEED', 'clipseed':'41 | SEED', 'ghost':'50 | OUTLINE'}
include=['flesh','clipcore','clipbranch','clipseed'] if mode=='matched' else ['flesh','fullcore','fullbranch','fullseed']
if a.mode=='fibers-only':include=['fullcore','fullbranch','fullseed']
if a.mode=='no-seeds':include=['flesh','fullcore','fullbranch']
if a.mode=='core-only':include=['fullcore']
if a.mode=='no-core':include=['flesh','fullbranch','fullseed']
for key,label in keynames.items():
    l=layer_for(label)
    if l is None:raise RuntimeError('Missing layer '+label)
    l.exclude=key not in include
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=a.samples
sc.render.threads_mode='FIXED';sc.render.threads=4
sc.render.resolution_x=a.size;sc.render.resolution_y=round(a.size*785/690);sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'
sc.render.image_settings.color_mode='RGBA'
sc.cycles.use_denoising=True
out=a.output.resolve();out.parent.mkdir(exist_ok=True,parents=True)
sc.render.filepath=str(out)
print('BEGIN_LAYER_RENDER',a.mode,name,include,sc.render.resolution_x,sc.render.resolution_y,flush=True)
t=time.perf_counter();bpy.ops.render.render(write_still=True,scene=sc.name)
print('PASS_LAYER_RENDER',json.dumps({'mode':a.mode,'scene':sc.name,'resolution':[sc.render.resolution_x,sc.render.resolution_y],'samples':a.samples,'time_seconds':round(time.perf_counter()-t,2),'path':str(out),'size':out.stat().st_size,'included':include}),flush=True)

"""True Blender Cycles from one live shared-control scene; no generated imagery."""
import bpy,sys,argparse,math,time,json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--mode',choices=['matched','flesh-only','fibers-only','body-only','whole'],default='matched')
p.add_argument('--pose',choices=['center','deep','shallow','oblique'],default='center')
p.add_argument('--resolution',type=int,default=510)
p.add_argument('--samples',type=int,default=10)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
sc=bpy.data.scenes['LIVE MATCHED | shared movable plane' if a.mode=='matched' else 'LIVE FLESH ONLY | shared movable plane']
ctrl=bpy.data.objects['LIVE CUT | move or rotate this Empty']
poses={'center':(0.,0.),'deep':(.34,0.),'shallow':(-.26,0.),'oblique':(0.,32.)}
off,ang=poses[a.pose];ctrl.location.y=off;ctrl.rotation_euler.z=math.radians(ang)
if bpy.context.window:bpy.context.window.scene=sc
bpy.context.view_layer.update()

def layer(name):
 def scan(root):
  if name in root.collection.name:return root
  for child in root.children:
   v=scan(child)
   if v:return v
 return scan(sc.view_layers[0].layer_collection)
if a.mode=='fibers-only':layer('10 | FLESH cut').exclude=True
if a.mode=='body-only':
 layer('20 | 28 CORE').exclude=True
 layer('30 | 539 BRANCHES').exclude=True
 layer('40 | 539 MARKERS').exclude=True
if a.mode=='whole':
 layer('10 | FLESH cut').exclude=True
 layer('11 | FLESH whole').exclude=False
 layer('20 | 28 CORE').exclude=True
 layer('30 | 539 BRANCHES').exclude=True
 layer('40 | 539 MARKERS').exclude=True
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=a.samples
sc.cycles.transparent_max_bounces=192
sc.render.threads_mode='FIXED';sc.render.threads=4
sc.render.resolution_x=a.resolution;sc.render.resolution_y=round(a.resolution*785/690);sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.cycles.use_denoising=True;sc.render.film_transparent=False
out=a.out.resolve();out.parent.mkdir(exist_ok=True,parents=True);sc.render.filepath=str(out)
start=time.perf_counter()
print('RENDER_BEGIN',a.mode,a.pose,'resolution',sc.render.resolution_x,sc.render.resolution_y,flush=True)
bpy.ops.render.render(write_still=True,scene=sc.name)
print('RENDER_PASS',json.dumps({'mode':a.mode,'pose':a.pose,'seconds':round(time.perf_counter()-start,2),'bytes':out.stat().st_size,'file':str(out)},ensure_ascii=False),flush=True)

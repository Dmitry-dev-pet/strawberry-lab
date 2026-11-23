from pathlib import Path
import sys,json,hashlib,time
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments/geometric-achene-pits-v1')]
from validate_pits import activate_runtime,activate,pose_knife,KNIFE,flush_callback
p=ROOT/'build/live-profile-v1';source=p/'live-profile.blend';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();source_sha=sha(source)
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);s=bpy.context.scene;r=activate_runtime();session=r['session']
cam=s.camera;cam.data.type='ORTHO';cam.data.ortho_scale=3.55;cam.data.dof.use_dof=False;cam.location=(3.5,-5.9,2.05);cam.rotation_euler=(Vector((0,0,.06))-cam.location).to_track_quat('-Z','Y').to_euler()
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=12;s.cycles.seed=1729;s.cycles.use_denoising=True;s.cycles.use_adaptive_sampling=False;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=s.render.resolution_y=750;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
def render(name):
 png=p/(name+'.png');assert not png.exists();s.render.filepath=str(png);start=time.perf_counter();bpy.ops.render.render(write_still=True,layer=bpy.context.view_layer.name)
 png.with_suffix('.json').write_text(json.dumps({'source_sha256':source_sha,'frame':name,'profile':json.loads(s['Nonlinear parameters']),'vascular_mm':s['strawberry_tissue_vascular_mm'],'resolution':750,'samples':12,'seed':1729,'seconds':time.perf_counter()-start,'png_sha256':sha(png),'camera':[list(row) for row in cam.matrix_world],'knife':[list(row) for row in s.objects[KNIFE].matrix_world],'same_open_scene_process':True},indent=2)+'\n')
for label,values in [('A',(.23,-.12,1.08)),('B',(-.12,.18,.96))]:
 for key,value in zip(['live_profile_a','live_profile_b','live_profile_h'],values):setattr(s,key,value)
 assert bpy.ops.strawberry.apply_profile()=={'FINISHED'}
 if label=='B':
  target=p/'live-profile-B.blend';assert not target.exists();bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
 activate(s,'whole');render(label+'-whole')
 activate(s,'matched');pose_knife(s.objects[KNIFE],(-.1,0,-23));bpy.context.view_layer.update();bpy.ops.strawberry.exact_quality(exact=True)
 if bpy.app.timers.is_registered(r['timer']):flush_callback(r)
 else:session.refresh()
 assert session.error is None;render(label+'-exact-cut')
# Same B/oblique pose, only the Vascular control differs. Neutral clay hides curves.
pose_knife(s.objects[KNIFE],(.08,29,32));bpy.context.view_layer.update()
for obj in s.objects:
 if obj.type=='CURVE':obj.hide_render=True
mat=bpy.data.materials.new('Clay no bump');mat.use_nodes=True;bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.43,.43,.43,1);bsdf.inputs['Roughness'].default_value=.58;bpy.context.view_layer.material_override=mat
s['strawberry_tissue_cortex_mm']=s['strawberry_tissue_pith_mm']=0
for value,name in [(0,'vascular-zero-clay'),(.12,'vascular-on-clay')]:
 s['strawberry_tissue_vascular_mm']=value;session.refresh();assert session.error is None;render(name)
assert sha(source)==source_sha

"""Render fixed-camera native Cycles frames from an authenticated variant."""
from pathlib import Path
import sys,json,hashlib,time
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments/geometric-achene-pits-v1')]
from validate_pits import activate_runtime,activate,pose_knife,KNIFE,flush_callback
scene_path,quality,look,frame,png=sys.argv[sys.argv.index('--')+1:];png=Path(png);assert not png.exists()
source=Path(scene_path);digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source.resolve()),use_scripts=False)
s=bpy.context.scene
if frame=='whole':activate(s,'whole')
elif quality=='fast':activate(s,'matched');pose_knife(s.objects[KNIFE],(-.1,0,-23) if frame=='cut' else (.08,29,32));bpy.context.view_layer.update()
else:
    activate(s,'matched');r=activate_runtime();pose_knife(s.objects[KNIFE],(-.1,0,-23) if frame=='cut' else (.08,29,32));bpy.context.view_layer.update()
    bpy.ops.strawberry.exact_quality(exact=True)
    if bpy.app.timers.is_registered(r['timer']):flush_callback(r)
    else:r['session'].refresh()
    assert r['session'].error is None
cam=s.camera;cam.data.type='ORTHO';cam.data.ortho_scale=3.55;cam.data.dof.use_dof=False;cam.location=(3.5,-5.9,2.05)
cam.rotation_euler=(Vector((0,0,.06))-cam.location).to_track_quat('-Z','Y').to_euler()
if look=='clay':
    for obj in s.objects:
        if obj.type=='CURVE':obj.hide_render=True
    mat=bpy.data.materials.new('Uniform clay without bump');mat.use_nodes=True;bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.43,.43,.43,1);bsdf.inputs['Roughness'].default_value=.58;bpy.context.view_layer.material_override=mat
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=12;s.cycles.seed=1729;s.cycles.use_denoising=True;s.cycles.use_adaptive_sampling=False
s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=s.render.resolution_y=750;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.filepath=str(png.resolve());start=time.perf_counter()
bpy.ops.render.render(write_still=True,layer=bpy.context.view_layer.name)
png.with_suffix('.json').write_text(json.dumps({'source_sha256':digest,'frame':frame,'quality':quality,'look':look,'context':json.loads(s['Nonlinear parameters']),'resolution':750,'samples':12,'seed':1729,'seconds':time.perf_counter()-start,'camera':[list(row) for row in cam.matrix_world],'knife':[list(row) for row in s.objects[KNIFE].matrix_world],'png_sha256':hashlib.sha256(png.read_bytes()).hexdigest()},indent=2)+'\n')
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest

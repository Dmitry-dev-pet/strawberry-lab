"""Matched Workbench diagnostic frames for cap-local subdivision. Render only; never save scene changes."""
import bpy,sys,json,hashlib,time
from pathlib import Path
from mathutils import Vector
here=Path(__file__).resolve().parent;sys.path.insert(0,str(here/'deps'))
from qa_split import setup,ROOT
src,pose,gain,level,vox,out=sys.argv[sys.argv.index('--')+1:];gain=float(gain);level=int(level);vox=float(vox);out=Path(out);assert not out.exists();bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()),use_scripts=False);setup(pose,.32);r=bpy.data.objects[ROOT];r['exact_mode']=1;r['exact_voxel_mm']=vox;r['tissue_gain']=gain;r['cap_refine_level']=level;r.update_tag();bpy.context.view_layer.update();s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=s.render.resolution_y=700;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(out.resolve());cam=s.camera
# Same direct cut view in both frames; deliberately simple grey clay.
if pose=='plane':
 cam.location=(0,-120,24);cam.rotation_euler=(Vector((0,0,24))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=55
else:
 target=Vector((3,-7,38));cam.location+=target-Vector((0,0,24));cam.data.ortho_scale=23
bpy.context.view_layer.update();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();t=time.perf_counter();bpy.ops.render.render(write_still=True);assert out.exists();out.with_suffix('.json').write_text(json.dumps({'scene_sha':sha(src),'image_sha':sha(out),'pose':pose,'tissue_gain':gain,'exact_voxel_mm':vox,'cap_refine_level':level,'engine':s.render.engine,'resolution':[700,700],'camera_matrix':[list(x) for x in cam.matrix_world],'ortho_scale':cam.data.ortho_scale,'render_seconds':time.perf_counter()-t},indent=2)+'\n')

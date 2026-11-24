"""Matched Workbench rim diagnostics, no material/geometry changes."""
import bpy,sys,json,time,hashlib
from pathlib import Path
from mathutils import Vector
src,helper,pose,gain,out=sys.argv[sys.argv.index('--')+1:];out=Path(out);assert not out.exists();sys.path.insert(0,str(Path(helper).resolve().parent))
from qa_split import setup,ROOT
bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()),use_scripts=False);setup(pose,.32);root=bpy.data.objects[ROOT];root['interface_gain']=float(gain);root.update_tag();bpy.context.view_layer.update();s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=s.render.resolution_y=700;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(out.resolve());cam=s.camera
# Whole-object camera for tilted cut; a tighter physical camera on the bite rim.
if pose=='bite':
 target=Vector((3,-7,38));cam.location+=target-Vector((0,0,24));cam.data.ortho_scale=23
else:cam.data.ortho_scale=70
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();t=time.perf_counter();bpy.ops.render.render(write_still=True);assert out.exists();out.with_suffix('.json').write_text(json.dumps({'source_sha':sha(src),'image_sha':sha(out),'pose':pose,'gain':float(gain),'voxel_mm':.32,'engine':s.render.engine,'resolution':[700,700],'camera_matrix':[list(r) for r in cam.matrix_world],'camera_ortho_scale':cam.data.ortho_scale,'render_seconds':time.perf_counter()-t},indent=2)+'\n')

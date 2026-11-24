"""Matched diagnostic geometry views, not a photorealistic material test."""
import bpy,sys,json,time
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from qa_split import setup,sha,SKIN,FLESH
src,pose,out,*opts=sys.argv[sys.argv.index('--')+1:];out=Path(out);assert not out.exists();bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()),use_scripts=False);voxel=float(opts[0]) if opts else .32;setup(pose,voxel);s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=s.render.resolution_y=700;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(out.resolve());s.camera.data.ortho_scale=70
# Same physical camera for all shots; no rendering-specific geometry changes.
t=time.perf_counter();bpy.ops.render.render(write_still=True);assert out.exists();out.with_suffix('.json').write_text(json.dumps({'source_sha':sha(src),'image_sha':sha(out),'pose':pose,'voxel_mm':voxel,'engine':s.render.engine,'resolution':[700,700],'camera_matrix':[list(r) for r in s.camera.matrix_world],'camera_ortho_scale':70,'render_seconds':time.perf_counter()-t},indent=2)+'\n')

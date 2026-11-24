"""Diagnostic Workbench views of the native neutral-stock geometry."""
import bpy,sys,json,hashlib,time
from pathlib import Path
src,mode,out=sys.argv[sys.argv.index('--')+1:];src=Path(src);out=Path(out);assert mode in ('neutral','deformed') and not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False);s=bpy.context.scene;root=bpy.data.objects['SL Shape Controller | edit Custom Properties'];state=(0.,0.,1.) if mode=='neutral' else (.16,-.10,1.12)
for key,value in zip(('shape_a','shape_b','shape_h'),state):root[key]=value
root.update_tag();bpy.context.view_layer.update();s.render.image_settings.file_format='PNG';s.render.filepath=str(out.resolve());t=time.perf_counter();bpy.ops.render.render(write_still=True)
assert out.exists();r={'source_sha':hashlib.sha256(src.read_bytes()).hexdigest(),'image_sha':hashlib.sha256(out.read_bytes()).hexdigest(),'mode':mode,'shape':state,'engine':s.render.engine,'resolution':[s.render.resolution_x,s.render.resolution_y],'camera':[list(row) for row in s.camera.matrix_world],'camera_ortho_scale':s.camera.data.ortho_scale,'seconds':time.perf_counter()-t};out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print(r,flush=True)

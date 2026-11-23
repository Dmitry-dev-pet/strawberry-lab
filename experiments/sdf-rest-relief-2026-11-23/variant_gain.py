"""Create read-only source → new scene at bounded field gain."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy
p=argparse.ArgumentParser();p.add_argument('--source',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--gain',required=True,type=float)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert not a.out.exists() and 0<=a.gain<=1
bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()),use_scripts=False)
body=bpy.context.scene.objects['Receptacle | canonical PR29 hull']
assert 'sdf_cut_relief_gain' in body
body['sdf_cut_relief_gain']=a.gain;body.update_tag();bpy.context.scene.frame_set(bpy.context.scene.frame_current);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()),compress=True)
print('GAIN_VARIANT',json.dumps({'source_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),'scene_sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'gain':a.gain}))

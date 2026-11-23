"""Bounded single-control color gain variant from a SHA-pinned tested scene."""
import bpy,sys,argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--gain',type=float,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert a.source.is_file() and not a.out.exists() and 0<=a.gain<=1
assert hashlib.sha256(a.source.read_bytes()).hexdigest()=='84fc711db90d835b9d769c4fee438f9eafd55d3afcd0afa7ada90f729c130140'
bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()),use_scripts=False)
body=bpy.context.scene.objects['Receptacle | canonical PR29 hull'];body['sdf_v20_color_gain']=a.gain;body.update_tag();bpy.context.scene.frame_set(bpy.context.scene.frame_current);bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()),compress=True)
print('C_GAIN',json.dumps({'gain':a.gain,'scene_sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'bytes':a.out.stat().st_size}))

"""One-factor material follow-up: same real closed menisci, neutral near-clear water.

Geometry, distribution, vascular source, cutters and 150^3 tissue atlas unaltered.
"""
import bpy,hashlib,argparse,sys,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert a.source.is_file() and not a.out.exists()
expected='257a8f2296e98466ccbdbd053f44e150639157e5f988954d7235c15df1c478a0'
assert hashlib.sha256(a.source.read_bytes()).hexdigest()==expected
bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()),use_scripts=False)
mat=bpy.data.materials['ARTIST | attached reddish meniscus smooth liquid'];g=mat.node_tree
bs=next(n for n in g.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled')
assert abs(bs.inputs['Transmission Weight'].default_value-.12)<1e-6
bs.inputs['Base Color'].default_value=(.96,.92,.9,1)
bs.inputs['Transmission Weight'].default_value=.90
bs.inputs['Roughness'].default_value=.045
bs.inputs['Coat Weight'].default_value=.025
bs.inputs['Coat Roughness'].default_value=.08
bs.inputs['Subsurface Weight'].default_value=0
bpy.context.scene['meniscus_material_trial']='Neutral clear transmissive water (ARTIST), same exact GN lenses and source field, no body changes'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()),compress=True)
print('CLEAR_WATER_SCENE',json.dumps({'source':expected,'out_sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'bytes':a.out.stat().st_size}),flush=True)

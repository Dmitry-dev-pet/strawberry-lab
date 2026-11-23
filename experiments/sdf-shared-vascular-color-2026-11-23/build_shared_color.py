"""One-factor native shader A/B: use the SAME owned 192^3 vascular R field
for both actual GN cut displacement and (restrained) cut-flesh coloration.

No imported Frucht code; old 150^3 atlas, field, original geometry are untouched.
"""
import bpy,argparse,sys,json,hashlib
from pathlib import Path
SRC_SHA='0b79e33b0725f807524061b1afe79671f4fcf1c6b5c429bd8203cec8d6a21bd2'
BODY='Receptacle | canonical PR29 hull';MAT='SDF | inherited 150^3 tissue + own multiscale wetness';CORE='sdf_v20_core'
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--outdir',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert a.source.is_file() and hashlib.sha256(a.source.read_bytes()).hexdigest()==SRC_SHA and not a.outdir.exists()
a.outdir.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()),use_scripts=False);assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
s=bpy.context.scene;b=s.objects[BODY];g=bpy.data.materials[MAT].node_tree
assert bpy.app.version[:2]==(5,2)
atlas=bpy.data.images['LIVE | ORIGINAL V0 native RGB volume atlas (150^3)'];atlas_sha=hashlib.sha256(bytes(atlas.packed_file.data)).hexdigest()
# Confirm the field already exists on the GN output, not a speculative name.
assert any(n.bl_idname=='GeometryNodeStoreNamedAttribute' and n.inputs['Name'].default_value==CORE for n in b.modifiers[0].node_group.nodes)
base=next(n for n in g.nodes if n.type=='BSDF_PRINCIPLED');old=base.inputs['Base Color'].links[0]
assert old.from_node.name=='Hue/Saturation/Value'
original=old.from_socket;g.links.remove(old)

def node(t,name):
 x=g.nodes.new(t);x.name=x.label=name;return x
b['sdf_v20_color_gain']=0.
b.id_properties_ui('sdf_v20_color_gain').update(min=0,max=1,description='ARTIST 0 original source color, 1 warm vascular accents from current SAME 192^3 R field used by cut geometry')
gain=node('ShaderNodeValue','V20 actual vascular field → material A/B gain')
gain.outputs[0].default_value=0.
d=gain.outputs[0].driver_add('default_value').driver;v=d.variables.new();v.name='gain';v.targets[0].id=b;v.targets[0].data_path='["sdf_v20_color_gain"]';d.expression='gain'
attr=node('ShaderNodeAttribute','V20 actual GN core R seen by cap shader')
attr.attribute_name=CORE
remap=node('ShaderNodeMapRange','ARTIST warm vessels, core R 0.18 to 0.55')
remap.clamp=True;remap.interpolation_type='SMOOTHERSTEP';remap.inputs['From Min'].default_value=.18;remap.inputs['From Max'].default_value=.55
remap.inputs['To Min'].default_value=0.;remap.inputs['To Max'].default_value=1.
g.links.new(attr.outputs['Fac'],remap.inputs['Value'])
atten=node('ShaderNodeMath','V20 field only bounded color contribution');atten.operation='MULTIPLY';g.links.new(remap.outputs['Result'],atten.inputs[0]);atten.inputs[1].default_value=.25
amount=node('ShaderNodeMath','V20 live same-R color intensity');amount.operation='MULTIPLY';g.links.new(atten.outputs[0],amount.inputs[0]);g.links.new(gain.outputs[0],amount.inputs[1])
mix=node('ShaderNodeMixRGB','V20 owned core lightens only overlapping vascular surface');mix.blend_type='MIX';mix.use_clamp=True
mix.inputs[2].default_value=(.88,.46,.33,1.)  # ARTIST, not an original Frucht color
# The zero-gain A variant should retain the EXACT source color path.
g.links.new(amount.outputs[0],mix.inputs[0]);g.links.new(original,mix.inputs[1]);g.links.new(mix.outputs[0],base.inputs['Base Color'])
assert len([n for n in g.nodes if n.type=='TEX_IMAGE'])==2
assert hashlib.sha256(bytes(atlas.packed_file.data)).hexdigest()==atlas_sha
r=[]
for tag,value in [('A',0.),('B',1.)]:
 b['sdf_v20_color_gain']=value;b.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update()
 out=a.outdir/f'shared-vascular-color-{tag}.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()),compress=True)
 r.append({'variant':tag,'gain':value,'scene_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size})
receipt={'status':'BUILT_A_B_UNVERIFIED','source_sha256':SRC_SHA,'original_material_atlas_sha256':atlas_sha,'color_signal':'sdf_v20_core actual GN point-domain attribute','source_geometry_and_v20_field_unchanged':True,'max_artist_color_blend':.25,'n_saved':len(r),'variants':r}
(a.outdir/'build.json').write_text(json.dumps(receipt,indent=2)+'\n');print('SHARED_R_BUILD',json.dumps(r),flush=True)

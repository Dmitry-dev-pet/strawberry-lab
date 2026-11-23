"""Controlled shader-only 150^3 tissue atlas radial-core sampling A/B.

Own code, no Frucht nodes/assets. Only the CAP volume-color sampler receives a
radial, compactly supported rest-space warp. The source atlas and 192^3 vascular
geometry field stay untouched. This is an ARTIST color distribution experiment,
not a biological or true geometric reconstruction of the pith.
"""
import bpy,hashlib,json,sys,argparse
from pathlib import Path

PIN='0b79e33b0725f807524061b1afe79671f4fcf1c6b5c429bd8203cec8d6a21bd2'
BODY='Receptacle | canonical PR29 hull'
CAP='SDF | inherited 150^3 tissue + own multiscale wetness'
REST='sdf_rest_position'


def node(g,kind,name):
    n=g.nodes.new(kind);n.name=n.label=name;return n

def wire(g,out,inp):g.links.new(out,inp)

p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--outdir',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert a.source.is_file() and hashlib.sha256(a.source.read_bytes()).hexdigest()==PIN
assert not a.outdir.exists();a.outdir.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()),use_scripts=False)
assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
s=bpy.context.scene;body=s.objects[BODY];mat=bpy.data.materials[CAP];g=mat.node_tree
rest=next(n for n in g.nodes if n.type=='ATTRIBUTE' and n.attribute_name==REST)
sep=g.nodes.get('Separate XYZ');assert sep is not None
assert len(sep.inputs['Vector'].links)==1 and sep.inputs['Vector'].links[0].from_node==rest
assert len([n for n in g.nodes if n.type=='TEX_IMAGE'])==2
hue=g.nodes.get('Hue/Saturation/Value');assert hue is not None
bs=next(n for n in g.nodes if n.type=='BSDF_PRINCIPLED')
assert bs.inputs['Base Color'].links[0].from_node==hue
atlas=bpy.data.images['LIVE | ORIGINAL V0 native RGB volume atlas (150^3)']
original_atlas_sha=hashlib.sha256(bytes(atlas.packed_file.data)).hexdigest()
original_GN_count=len(body.modifiers[0].node_group.nodes)

body['sdf_pith_color_compact_gain']=0.
body.id_properties_ui('sdf_pith_color_compact_gain').update(min=0,max=1,description='ARTIST: 0 source color, 1 compact central pale color by local source atlas XY remapping; geometry unaffected')
value=node(g,'ShaderNodeValue','ARTIST | compact central pith COLOR only')
value.outputs[0].default_value=0.
driver=value.outputs[0].driver_add('default_value').driver
v=driver.variables.new();v.name='gain';v.targets[0].id=body;v.targets[0].data_path='["sdf_pith_color_compact_gain"]';driver.expression='gain'
# Source space is in Blender units, 22.22222 mm per BU.
radial=node(g,'ShaderNodeVectorMath','ARTIST | rest XY only, no Z warp');radial.operation='MULTIPLY';radial.inputs[1].default_value=(1.,1.,0.)
wire(g,rest.outputs['Vector'],radial.inputs[0])
length=node(g,'ShaderNodeVectorMath','ARTIST | radial distance from source axis');length.operation='LENGTH';wire(g,radial.outputs['Vector'],length.inputs[0])
taper=node(g,'ShaderNodeMapRange','ARTIST | local compact central zone')
taper.clamp=True;taper.interpolation_type='SMOOTHERSTEP';taper.inputs['From Min'].default_value=.10;taper.inputs['From Max'].default_value=.38
taper.inputs['To Min'].default_value=1.;taper.inputs['To Max'].default_value=0.
wire(g,length.outputs['Value'],taper.inputs['Value'])
amp=node(g,'ShaderNodeMath','ARTIST | bounded central radial compression strength');amp.operation='MULTIPLY'
wire(g,value.outputs[0],amp.inputs[0]);wire(g,taper.outputs['Result'],amp.inputs[1])
gain=node(g,'ShaderNodeMath','ARTIST | 1.55x pith color sample radial map');gain.operation='MULTIPLY';wire(g,amp.outputs[0],gain.inputs[0]);gain.inputs[1].default_value=.55
scale=node(g,'ShaderNodeMath','ARTIST | unit-plus-local-compression');scale.operation='ADD';scale.inputs[0].default_value=1.;wire(g,gain.outputs[0],scale.inputs[1])
xyz=node(g,'ShaderNodeCombineXYZ','ARTIST | cap-color XY resample, preserve Z')
wire(g,scale.outputs[0],xyz.inputs['X']);wire(g,scale.outputs[0],xyz.inputs['Y']);xyz.inputs['Z'].default_value=1.
warp=node(g,'ShaderNodeVectorMath','ARTIST | pith-color lookup only');warp.operation='MULTIPLY';wire(g,rest.outputs['Vector'],warp.inputs[0]);wire(g,xyz.outputs['Vector'],warp.inputs[1])
# Only the inherited RGB tissue samplers below Separate XYZ are affected;
# all three 3D wetness Voronoi nodes keep the original, unwarped rest.
g.links.remove(sep.inputs['Vector'].links[0]);wire(g,warp.outputs['Vector'],sep.inputs['Vector'])
assert len([n for n in g.nodes if n.type=='TEX_IMAGE'])==2
assert len(body.modifiers[0].node_group.nodes)==original_GN_count
assert hashlib.sha256(bytes(atlas.packed_file.data)).hexdigest()==original_atlas_sha

records=[]
for tag,ctrl in [('A',0.0),('B',1.0)]:
    body['sdf_pith_color_compact_gain']=ctrl
    body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update()
    out=a.outdir/f'pith-color-{tag}.blend'
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()),compress=True)
    records.append({'variant':tag,'gain':ctrl,'path':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'size_bytes':out.stat().st_size})
receipt={'status':'BUILT_UNVERIFIED','source_sha256':PIN,'blender':bpy.app.version_string,'source_150_atlas_sha256':original_atlas_sha,'source_GN_count':original_GN_count,'experiment':'local shader color-sampler XY warp only; not true PITH tissue redefinition','variants':records,'artist_values':{'sample_magnification_xy':1.55,'inner_radius_BU':.10,'outer_fade_BU':.38}}
(a.outdir/'build.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('PITH_AB_BUILT',json.dumps(records),flush=True)

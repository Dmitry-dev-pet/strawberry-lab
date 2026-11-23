"""Independent bounded A/B: same 3-D native cell-domes drive GEOMETRY and cap OPTICS.
Original Blender source: PR49 v20-bridge-portable SHA pinned; A reproduces source.
New morphology/cell sizes are ARTIST unmeasured; no copied Frucht assets/nodes.
"""
from pathlib import Path
import bpy, json, sys, hashlib, argparse

parser=argparse.ArgumentParser();parser.add_argument('--source',required=True,type=Path);parser.add_argument('--outdir',required=True,type=Path)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);SRC=args.source.resolve();DEST=args.outdir.resolve()
SHA='0b79e33b0725f807524061b1afe79671f4fcf1c6b5c429bd8203cec8d6a21bd2'
assert SRC.is_file() and hashlib.sha256(SRC.read_bytes()).hexdigest()==SHA
assert not DEST.exists();DEST.mkdir(parents=True)
assert bpy.app.version[:2]==(5,2)
bpy.ops.wm.open_mainfile(filepath=str(SRC),use_scripts=False)
assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
scene=bpy.context.scene
body=scene.objects['Receptacle | canonical PR29 hull']
g=body.modifiers[0].node_group
mat=bpy.data.materials['SDF | inherited 150^3 tissue + own multiscale wetness']
sh=mat.node_tree
bs=next(n for n in sh.nodes if n.type=='BSDF_PRINCIPLED')
old_color=bs.inputs['Base Color'].links[0].from_socket
old_rough=bs.inputs['Roughness'].links[0].from_socket
assert old_color.node.name=='Hue/Saturation/Value'
assert old_rough.node.name=='Math.059'
assert len(g.nodes)==79 and len(sh.nodes)==82
assert len([x for x in scene.objects if x.get('role')=='achene'])==264
core=g.nodes['V20 bridge: core and halo from same source 3D'].outputs['core']
vor=g.nodes['V20 bridge: own 3D source tissue cell field']
sup=g.nodes['V20 bridge: owned original cell suppression curve'].outputs['Result']
capmask=g.nodes['V20 bridge: active cut only'].outputs[0]
cellmm=g.nodes['V20 bridge: cell ARTIST mm']
old_cell_value=cellmm.outputs[0]
addcell=g.nodes['V20 bridge: cell+ridge shared displacement mm']
assert any(l.from_socket==old_cell_value and l.to_node==addcell for l in g.links)
store_height=g.nodes['V20 bridge: sdf_v20_height_mm']
prev=g.nodes['V20 bridge: sdf_v20_cell_suppression']
assert store_height.inputs['Geometry'].links[0].from_node==prev

def node(graph,id,label):
 x=graph.nodes.new(id);x.name=x.label=label;return x

def wire(graph,a,b):graph.links.new(a,b)

def math(graph,op,label,a,b=None):
 x=node(graph,'ShaderNodeMath',label);x.operation=op
 for i,v in enumerate([a,b]):
  if v is None:continue
  if isinstance(v,(int,float)):x.inputs[i].default_value=v
  else:wire(graph,v,x.inputs[i])
 return x.outputs[0]

def driver(graph,label):
 x=node(graph,'ShaderNodeValue',label);x.outputs[0].default_value=body['sdf_cell_surface_gain']
 d=x.outputs[0].driver_add('default_value').driver
 v=d.variables.new();v.name='gain';v.targets[0].id=body;v.targets[0].data_path='["sdf_cell_surface_gain"]';d.expression='gain'
 return x.outputs[0]

body['sdf_cell_surface_gain']=0.0
body.id_properties_ui('sdf_cell_surface_gain').update(min=0.,max=1.,description='Native co-registered cell geometry + color/roughness, 0 = original source; ARTIST unmeasured')

gain=driver(g,'CELL COHERENCE | LIVE body property')
# The very same original distance-to-edge field that shapes the native cap, no new random signal.
shape=node(g,'ShaderNodeMapRange','CELL COHERENCE | smooth original cell interior')
shape.clamp=True;shape.interpolation_type='SMOOTHERSTEP'
shape.inputs['From Min'].default_value=.019
shape.inputs['From Max'].default_value=.064
shape.inputs['To Min'].default_value=0
shape.inputs['To Max'].default_value=1
wire(g,vor.outputs['Distance'],shape.inputs['Value'])
# Suppress interior bulges near the already verified vascular halo and strictly on active cap.
interior=math(g,'MULTIPLY','CELL COHERENCE | cells × existing H suppress',shape.outputs['Result'],sup)
interior=math(g,'MULTIPLY','CELL COHERENCE | cut-only source interior',interior,capmask)
# Persist exactly the scalar field used by the actual new geometry response.
store=node(g,'GeometryNodeStoreNamedAttribute','CELL COHERENCE | store common material+shape field')
store.data_type='FLOAT';store.domain='POINT';store.inputs['Name'].default_value='sdf_cell_lobe_response'
g.links.remove(store_height.inputs['Geometry'].links[0]);wire(g,prev.outputs['Geometry'],store.inputs['Geometry']);wire(g,interior,store.inputs['Value']);wire(g,store.outputs['Geometry'],store_height.inputs['Geometry'])
# At gain=0 the exact previous geometry path is conserved. At B add <=0.055mm per-cell dome.
amp=math(g,'MULTIPLY','CELL COHERENCE | 0.055 mm response ARTIST',interior,.055)
amp=math(g,'MULTIPLY','CELL COHERENCE | one-factor gain to real cut mesh',amp,gain)
extra=math(g,'ADD','CELL COHERENCE | add to previous cell height ONLY',old_cell_value,amp)
g.links.remove(next(l for l in addcell.inputs[0].links if l.from_socket==old_cell_value));wire(g,extra,addcell.inputs[0])

# Cap material reads SAME captured evaluated GN point attribute rather than computing a second Voronoi.
optgain=driver(sh,'CELL COHERENCE | LIVE optical counterpart')
attr=node(sh,'ShaderNodeAttribute','CELL COHERENCE | exact GN cell lobe response')
attr.attribute_name='sdf_cell_lobe_response'
strength=math(sh,'MULTIPLY','CELL COHERENCE | shading mask with same gain',attr.outputs['Fac'],optgain)
# The cell interiors become slightly more red/matte (not white Voronoi edges); original shader remains exactly at A.
mix=node(sh,'ShaderNodeMixRGB','CELL COHERENCE | original warm cell pulp blend')
mix.blend_type='MIX';mix.use_clamp=True
colorfactor=math(sh,'MULTIPLY','CELL COHERENCE | cap color change <=0.10',strength,.10)
wire(sh,colorfactor,mix.inputs[0]);wire(sh,old_color,mix.inputs[1]);mix.inputs[2].default_value=(.40,.055,.045,1)
sh.links.remove(bs.inputs['Base Color'].links[0]);wire(sh,mix.outputs[0],bs.inputs['Base Color'])
# More diffuse cell bulk and slightly smooth intercellular spaces: +0.085 max roughness on bulges.
roughplus=math(sh,'MULTIPLY','CELL COHERENCE | interior roughness delta',strength,.085)
rough=math(sh,'ADD','CELL COHERENCE | preserve source roughness add subtle cell domain',old_rough,roughplus)
sh.links.remove(bs.inputs['Roughness'].links[0]);wire(sh,rough,bs.inputs['Roughness'])
assert bs.inputs['Subsurface Weight'].default_value==.08 or abs(bs.inputs['Subsurface Weight'].default_value-.08)<1e-5
assert len([n for n in sh.nodes if n.type=='TEX_IMAGE'])==2
scene['CELL COHERENCE']=('Original source 3D Voronoi cell interior stored on native SDF mesh; same point attr drives cap '+'roughness/color and extra 0.055mm mesh lift; limited test, ARTIST, no Frucht assets')
original_pack=hashlib.sha256(bytes(bpy.data.images['LIVE | ORIGINAL V0 native RGB volume atlas (150^3)'].packed_file.data)).hexdigest()
summary={'source_sha':SHA,'blender':bpy.app.version_string,'source_150_atlas_sha':original_pack,'original_nodes':{'GN':79,'MAT':82},'new_nodes':{'GN':len(g.nodes),'MAT':len(sh.nodes)},'extra_height_mm_upper_bound':.055,'shader_color_blend_upper_bound':.10,'roughness_add_upper_bound':.085,'field':'sdf_cell_lobe_response','variant':[]}
for tag,g in [('A',0.),('B',1.)]:
 body['sdf_cell_surface_gain']=g
 body.update_tag();scene.frame_set(scene.frame_current);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
 path=DEST/f'cell-coherent-{tag}.blend';assert not path.exists();bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
 summary['variant'].append({'name':tag,'gain':g,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
print('CELL_COHERENT_SCENE_CREATED',json.dumps(summary,ensure_ascii=False),flush=True)
(DEST/'build.json').write_text(json.dumps(summary,indent=2)+'\n')

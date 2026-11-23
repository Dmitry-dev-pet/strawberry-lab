"""Original Strawberry Lab test: physically attached extrusion of sparse cut-cell faces.
Unlike v14 normal displacement, creates real manifold side walls and raised top surfaces.
Source is saved original, script auto-execution OFF. ALL settings ARTIST, not botanical measurements.
"""
import bpy,sys,hashlib,json,argparse, pathlib
from pathlib import Path
P=argparse.ArgumentParser()
P.add_argument('--source',type=Path,required=True)
P.add_argument('--outdir',type=Path,required=True)
P.add_argument('--noise-threshold',type=float,default=.665)
P.add_argument('--height-mm',type=float,default=.62)
P.add_argument('--skin-mm',type=float,default=2.7)
P.add_argument('--seam-mm',type=float,default=.18)
P.add_argument('--islands',choices=('noise','voronoi'),default='noise')
P.add_argument('--scale',type=float,default=5.0)
a=P.parse_args(sys.argv[sys.argv.index('--')+1:]);src=a.source.resolve();o=a.outdir.resolve()
PIN='4732b465b103f9a0b4ab262dfeae51e26a8865aa586c3779d472d86eed845399'
assert hashlib.sha256(src.read_bytes()).hexdigest()==PIN
assert bpy.app.version[:2]==(5,2) and not o.exists()
bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False)
assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
s=bpy.context.scene; b=s.objects['Receptacle | canonical PR29 hull']; g=b.modifiers[0].node_group
assert len(g.nodes)==87 and s.unit_settings.scale_length>0
mm=s.unit_settings.scale_length*1000

def node(t,name):
 n=g.nodes.new(t);n.name=n.label=name;return n

def link(a,b):g.links.new(a,b)

def valmath(op,name,a,b):
 n=node('ShaderNodeMath',name);n.operation=op
 for i,x in enumerate((a,b)):
  if isinstance(x,(float,int)):n.inputs[i].default_value=x
  else:link(x,n.inputs[i])
 return n.outputs[0]

smooth=g.nodes['Set Shade Smooth'];out=g.nodes['Group Output']
assert out.inputs['Geometry'].links[0].from_node==smooth
g.links.remove(out.inputs['Geometry'].links[0])

b['sdf_torn_extrude_gain']=0.
b.id_properties_ui('sdf_torn_extrude_gain').update(min=0.,max=1.,description='Original ARTIST: 0 same geometry, 1 physical raised, connected bite flaps')
b['sdf_tear_parameters']=json.dumps({'patch_scale':a.scale,'patch_threshold':a.noise_threshold,'islands':a.islands,'seam_mm':a.seam_mm,'rim_skin_mm':a.skin_mm,'height_mm':a.height_mm,'non_measured':'ARTIST'})
active=node('ShaderNodeValue','TEAR | live gain driver')
active.outputs[0].default_value=0.
d=active.outputs[0].driver_add('default_value').driver
v=d.variables.new();v.name='gain';v.targets[0].id=b;v.targets[0].data_path='["sdf_torn_extrude_gain"]';d.expression='gain'
mode=node('ShaderNodeValue','TEAR | only sphere-bite mode')
mode.outputs[0].default_value=0.;md=mode.outputs[0].driver_add('default_value').driver
x=md.variables.new();x.name='mode';x.targets[0].id=b;x.targets[0].data_path='["sdf_mode"]';md.expression='mode'
modeon=valmath('GREATER_THAN','TEAR | mode is bite',mode.outputs[0],1.5)
tryon=valmath('GREATER_THAN','TEAR | gain enabled',active.outputs[0],.5)
engage=valmath('MULTIPLY','TEAR | gated ON only sphere',tryon,modeon)

matidx=node('GeometryNodeInputMaterialIndex','TEAR | face material index')
cap=valmath('GREATER_THAN','TEAR | only exposed flesh material index 2',matidx.outputs['Material Index'],1.5)
sep=node('GeometryNodeSeparateGeometry','TEAR | original exterior without cap');sep.domain='FACE'
link(smooth.outputs['Mesh'],sep.inputs['Geometry']);link(cap,sep.inputs['Selection'])
prox=node('GeometryNodeProximity','TEAR | evaluated-distance to live exterior skin');prox.target_element='FACES'
link(sep.outputs['Inverted'],prox.inputs['Target'])
# proximity query at a face center is domain-resolved on the selected cap faces
near=valmath('LESS_THAN','TEAR | within skin-adjacent band',prox.outputs['Distance'],a.skin_mm/mm)
not_on_seam=valmath('GREATER_THAN','TEAR | do not extrude seam itself',prox.outputs['Distance'],a.seam_mm/mm)
rest=node('GeometryNodeInputNamedAttribute','TEAR | same original rest coordinates');rest.data_type='FLOAT_VECTOR';rest.inputs['Name'].default_value='sdf_rest_position'
if a.islands=='noise':
 noise=node('ShaderNodeTexNoise','TEAR | sparse nonperiodic 3D tear islands');noise.noise_dimensions='3D'
 noise.inputs['Scale'].default_value=a.scale;noise.inputs['Detail'].default_value=2.;noise.inputs['Roughness'].default_value=.51
 link(rest.outputs['Attribute'],noise.inputs['Vector'])
 patch=valmath('GREATER_THAN','TEAR | sparse connected patches',noise.outputs['Fac'],a.noise_threshold)
else:
 noise=node('ShaderNodeTexVoronoi','TEAR | spaced 3D physical tissue islands');noise.voronoi_dimensions='3D';noise.feature='F1'
 noise.inputs['Scale'].default_value=a.scale;noise.inputs['Randomness'].default_value=0.7
 link(rest.outputs['Attribute'],noise.inputs['Vector'])
 patch=valmath('LESS_THAN','TEAR | non-overlapping local island centers',noise.outputs['Distance'],a.noise_threshold)
halo=node('GeometryNodeInputNamedAttribute','TEAR | existing vascular broad influence');halo.data_type='FLOAT';halo.inputs['Name'].default_value='sdf_v20_halo'
halo_gate=valmath('GREATER_THAN','TEAR | prefer near vascular branches',halo.outputs['Attribute'],.08)
selection=valmath('MULTIPLY','TEAR | selection cap × rim',cap,near)
selection=valmath('MULTIPLY','TEAR | seam excluded',selection,not_on_seam)
selection=valmath('MULTIPLY','TEAR | sparse patch field',selection,patch)
selection=valmath('MULTIPLY','TEAR | vascular-anchored',selection,halo_gate)
# save candidate signal to face attributes, without changing geometry when OFF
attr=node('GeometryNodeStoreNamedAttribute','TEAR | record selected candidate faces');attr.data_type='BOOLEAN';attr.domain='FACE';attr.inputs['Name'].default_value='sdf_torn_candidate'
link(smooth.outputs['Mesh'],attr.inputs['Geometry']);link(selection,attr.inputs['Value'])

extr=node('GeometryNodeExtrudeMesh','TEAR | actual connected tear flaps (not a normal bump)')
extr.mode='FACES';link(attr.outputs['Geometry'],extr.inputs['Mesh']);link(selection,extr.inputs['Selection'])
normal=node('GeometryNodeInputNormal','TEAR | face normals for attached extrusion');link(normal.outputs['Normal'],extr.inputs['Offset'])
extr.inputs['Offset Scale'].default_value=a.height_mm/mm
extr.inputs['Individual'].default_value=False
# Smooth shading on attached sidewalls and top.
shade=node('GeometryNodeSetShadeSmooth','TEAR | smooth surfaces of pulled-out tissue');shade.domain='FACE';link(extr.outputs['Mesh'],shade.inputs['Geometry'])
# the original mesh stays the exact same whenever gain=0, also candidate info is harmless.
switch=node('GeometryNodeSwitch','TEAR | editable A vs B native geometry switch');switch.input_type='GEOMETRY'
link(engage,switch.inputs['Switch']);link(attr.outputs['Geometry'],switch.inputs['False']);link(shade.outputs['Mesh'],switch.inputs['True']);link(switch.outputs['Output'],out.inputs['Geometry'])
# Record a separate GN property for easier forensic audit.
g['tear_contract']='connected cap-face extrusion on source rest-space sparse 3D patches near evaluated skin, only sphere, no body changes when OFF; ARTIST'
g['tear_node_count_added']=len(g.nodes)-87

# create variant scenes
records=[]
o.mkdir(parents=True)
for name,gain in [('A',0.),('B',1.)]:
 b['sdf_torn_extrude_gain']=gain;b.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
 p=o/f'torn-{name}.blend';bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(p),compress=True)
 records.append({'name':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
rep={'source_sha256':PIN,'mm_per_BU':mm,'blender':bpy.app.version_string,'settings':{'height_mm':a.height_mm,'rim_mm':a.skin_mm,'threshold':a.noise_threshold,'seam_mm':a.seam_mm,'islands':a.islands,'scale':a.scale},'added_nodes':len(g.nodes)-87,'variants':records}
(o/'build.json').write_text(json.dumps(rep,indent=2)+'\n');print('BUILT_TEAR',json.dumps(rep),flush=True)

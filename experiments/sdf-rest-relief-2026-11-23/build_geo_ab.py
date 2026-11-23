"""Independent, guarded native GN 3D cut relief experiment.

One owned rest-coordinate noise field, a controlled gain 0 vs 1, constant
core/hull/cutters/shader, fade to zero away from cutter, reduced at central pith.
3D cutter surface relief is ARTIST, not histological cell reconstruction.
"""
from pathlib import Path
import argparse,sys,hashlib,json
import bpy
PIN='bfecf691df67cafff020971368f1afc877f4bac1165e851520bdcc1773f85ce1'
BODY='Receptacle | canonical PR29 hull'

def node(g,typ,name):
 n=g.nodes.new(typ);n.name=name;n.label=name;return n

def wire(g,a,b):g.links.new(a,b)

def mathn(g,op,name,a,b=None):
 n=node(g,'ShaderNodeMath',name);n.operation=op
 for inp,v in zip(n.inputs,(a,b)):
  if v is None:continue
  if isinstance(v,(float,int)):inp.default_value=v
  else:wire(g,v,inp)
 return n.outputs[0]

def driver(g,body,key):
 n=node(g,'ShaderNodeValue',f'ARTIST controlled {key}')
 n.outputs[0].default_value=body[key]
 d=n.outputs[0].driver_add('default_value').driver
 v=d.variables.new();v.name='v';v.targets[0].id=body;v.targets[0].data_path=f'["{key}"]';d.expression='v'
 return n.outputs[0]

def add_nodes(s):
 body=s.objects[BODY];g=body.modifiers[0].node_group
 assert body['sdf_mode']==0
 orig=[n for n in g.nodes if n.bl_idname=='GeometryNodeSetMaterial' and 'Cut material' in n.name]
 assert len(orig)==1
 cut=orig[0];smooth=next(n for n in g.nodes if n.bl_idname=='GeometryNodeSetShadeSmooth')
 assert any(l.from_node==cut and l.to_node==smooth for l in g.links)
 # Different nodes connect old cut->smooth, only geometry field is rewired.
 for l in list(g.links):
  if l.from_node==cut and l.to_node==smooth:g.links.remove(l)
 pos=node(g,'GeometryNodeSetPosition','ARTIST native cut relief | one consistent 3D source')
 wire(g,cut.outputs['Geometry'],pos.inputs['Geometry'])
 wire(g,pos.outputs['Geometry'],smooth.inputs['Geometry'])
 rest=node(g,'GeometryNodeInputNamedAttribute','ARTIST source original rest xyz');rest.data_type='FLOAT_VECTOR';rest.inputs['Name'].default_value='sdf_rest_position'
 stretch=node(g,'ShaderNodeVectorMath','ARTIST elongated 3D tissue coordinate');stretch.operation='MULTIPLY';stretch.inputs[1].default_value=(45,42,12)
 wire(g,rest.outputs['Attribute'],stretch.inputs[0])
 noise=node(g,'ShaderNodeTexNoise','ARTIST bulk 3D cell relief variations');noise.noise_dimensions='3D';noise.inputs['Scale'].default_value=1.0;noise.inputs['Detail'].default_value=2.4;noise.inputs['Roughness'].default_value=.56;noise.inputs['Distortion'].default_value=.07
 wire(g,stretch.outputs['Vector'],noise.inputs['Vector'])
 shape=node(g,'ShaderNodeMapRange','ARTIST normalized signed source 3D relief');shape.clamp=True;shape.interpolation_type='SMOOTHERSTEP';shape.inputs['From Min'].default_value=.33;shape.inputs['From Max'].default_value=.67;shape.inputs['To Min'].default_value=-1;shape.inputs['To Max'].default_value=1
 wire(g,noise.outputs['Fac'],shape.inputs['Value'])
 # Core suppression: radial distance to z axis in stable source space, not a
 # claimed biologically measured vessel size. 0 at centre, 1 in outer tissue.
 ring=node(g,'ShaderNodeVectorMath','ARTIST radial tissue distance');ring.operation='MULTIPLY';ring.inputs[1].default_value=(1,1,0);wire(g,rest.outputs['Attribute'],ring.inputs[0])
 radius=node(g,'ShaderNodeVectorMath','ARTIST pith vs flesh radius');radius.operation='LENGTH';wire(g,ring.outputs['Vector'],radius.inputs[0])
 taper=node(g,'ShaderNodeMapRange','ARTIST suppress relief in visual core');taper.clamp=True;taper.interpolation_type='SMOOTHERSTEP';taper.inputs['From Min'].default_value=.08;taper.inputs['From Max'].default_value=.25;taper.inputs['To Min'].default_value=0;taper.inputs['To Max'].default_value=1;wire(g,radius.outputs['Value'],taper.inputs['Value'])
 # Proximity to active cutter is already in own SDF group; mask dies on uncut
 # skin and in WHOLE. Scales in physical mm -> model units, not guessed BU.
 prox=next(n for n in g.nodes if n.bl_idname=='GeometryNodeProximity')
 mm=s.unit_settings.scale_length*1000
 voxel=mathn(g,'DIVIDE','ARTIST voxel mm to scene BU',driver(g,body,'sdf_voxel_mm'),mm)
 normdist=mathn(g,'DIVIDE','ARTIST cutter distance in voxels',prox.outputs['Distance'],voxel)
 fade=node(g,'ShaderNodeMapRange','ARTIST cutter-local mask');fade.clamp=True;fade.interpolation_type='SMOOTHERSTEP';fade.inputs['From Min'].default_value=.05;fade.inputs['From Max'].default_value=1.6;fade.inputs['To Min'].default_value=1;fade.inputs['To Max'].default_value=0;wire(g,normdist,fade.inputs['Value'])
 active=mathn(g,'GREATER_THAN','ARTIST cut active',driver(g,body,'sdf_mode'),.5)
 gain=driver(g,body,'sdf_cut_relief_gain')
 fac=mathn(g,'MULTIPLY','ARTIST noise × radial domain',shape.outputs['Result'],taper.outputs['Result'])
 fac=mathn(g,'MULTIPLY','ARTIST masked by cutter proximity',fac,fade.outputs['Result'])
 fac=mathn(g,'MULTIPLY','ARTIST gated by cut active',fac,active)
 fac=mathn(g,'MULTIPLY','ARTIST bounded amplitude × gain',fac,gain)
 physical=mathn(g,'MULTIPLY','ARTIST relief 0.095mm in rest scene BU',fac,.095/mm)
 n=node(g,'GeometryNodeInputNormal','ARTIST evaluate surface normal')
 offs=node(g,'ShaderNodeVectorMath','ARTIST surface microdisplacement');offs.operation='SCALE';wire(g,n.outputs['Normal'],offs.inputs[0]);wire(g,physical,offs.inputs[3])
 wire(g,offs.outputs['Vector'],pos.inputs['Offset'])
 assert len(pos.inputs['Offset'].links)==1
 return g

ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--outdir',type=Path,required=True)
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source=args.source.resolve();outdir=args.outdir.resolve()
assert hashlib.sha256(source.read_bytes()).hexdigest()==PIN
assert not outdir.exists();outdir.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
s=bpy.context.scene;body=s.objects[BODY];body['sdf_cut_relief_gain']=0;body.id_properties_ui('sdf_cut_relief_gain').update(min=0,max=1)
g=add_nodes(s);reports=[]
for label,gain in [('A',0.0),('B',1.0)]:
 body['sdf_cut_relief_gain']=gain;body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
 p=outdir/f'pr49-rest-relief-{label}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(p),compress=True)
 reports.append({'variant':label,'gain':gain,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(outdir/'build-receipt.json').write_text(json.dumps({'status':'BUILT_UNVERIFIED','source_sha256':PIN,'blender':bpy.app.version_string,'variants':reports,'notes':['one native GN group plus one gain, rest-space cap relief','ARTIST 0.095mm peak amplitude; no measured tissue packing','same object geometry, material, cutter, camera source; validation to follow']},indent=2))
print('BUILT',json.dumps(reports),flush=True)

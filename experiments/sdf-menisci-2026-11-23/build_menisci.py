"""Owned original SDF cut meniscus proof: a few real closed, attached lens solids.

Source current PR49 v20 bridge; never alters the fruit/seed material or atlas.
A/B only toggles separate geometries. Artistic illustration, no measured droplets.
"""
from pathlib import Path
import argparse,sys,json,hashlib,math
import bpy

SOURCE_SHA='0b79e33b0725f807524061b1afe79671f4fcf1c6b5c429bd8203cec8d6a21bd2'
BODY='Receptacle | canonical PR29 hull'
FNAME='SDF | separate vascular-attached lens pockets'
NGEN='SDF | scattered attached menisci via real 3D vascular halo'
MAT='ARTIST | attached reddish meniscus smooth liquid'
TEMPLATE='SDF | original closed meniscus template (hidden)'


def node(g,t,label):
 n=g.nodes.new(t);n.name=n.label=label;return n

def wire(g,a,b):g.links.new(a,b)

def mathnode(g,op,label,a,b=None):
 n=node(g,'ShaderNodeMath',label);n.operation=op
 for i,val in enumerate([a,b]):
  if val is None:continue
  if isinstance(val,(int,float)):n.inputs[i].default_value=val
  else:wire(g,val,n.inputs[i])
 return n.outputs[0]


def make_material():
 m=bpy.data.materials.new(MAT);m.use_nodes=True;g=m.node_tree;g.nodes.clear()
 out=node(g,'ShaderNodeOutputMaterial','Only original lens material');bs=node(g,'ShaderNodeBsdfPrincipled','Thin reddish fluid no white cover')
 bs.inputs['Base Color'].default_value=(.36,.027,.015,1)
 bs.inputs['Roughness'].default_value=.085
 bs.inputs['IOR'].default_value=1.33
 bs.inputs['Transmission Weight'].default_value=.12
 bs.inputs['Coat Weight'].default_value=.08
 bs.inputs['Coat Roughness'].default_value=.095
 if 'Subsurface Weight' in bs.inputs:bs.inputs['Subsurface Weight'].default_value=.02
 wire(g,bs.outputs['BSDF'],out.inputs['Surface'])
 m['evidence']='Original ARTIST color/material; explicitly distinct from source strawberry 150-cube atlas and GPL Frucht'
 return m


def build_lens():
 # Surface of revolution, elliptical dome with closed, slightly submerged base.
 # All z in Blender units. 22.22222276mm per Blender unit.
 mm=bpy.context.scene.unit_settings.scale_length*1000
 radius=.31/mm;top=.082/mm;submerged=.034/mm
 S=32
 rings=[(1.0,-submerged),(.99,0.0),(.84,top*.48),(.57,top*.81),(.29,top*.975)]
 vertices=[];faces=[]
 for r,z in rings:
  for j in range(S):
   angle=2*math.pi*j/S;f=1+.052*math.cos(3*angle+.63)+.027*math.sin(5*angle-.21)
   vertices.append((radius*r*f*math.cos(angle),radius*r*f*math.sin(angle),z))
 for k in range(len(rings)-1):
  for j in range(S):
   a=k*S+j;b=k*S+(j+1)%S;c=(k+1)*S+(j+1)%S;d=(k+1)*S+j
   faces.append((a,b,c,d))
 cap_top=len(vertices);vertices.append((0,0,top))
 for j in range(S):faces.append(((len(rings)-1)*S+j,(len(rings)-1)*S+(j+1)%S,cap_top))
 cap_bottom=len(vertices);vertices.append((0,0,-submerged))
 for j in range(S):faces.append(((j+1)%S,j,cap_bottom))
 mesh=bpy.data.meshes.new('ARTIST convex puddle dome & intersecting closed base');mesh.from_pydata(vertices,[],faces);mesh.update()
 o=bpy.data.objects.new(TEMPLATE,mesh);bpy.context.scene.collection.objects.link(o)
 # Keep the source object from being independently rendered; ObjectInfo still reads mesh.
 o.hide_render=True
 return o


def create_group(body,lens):
 g=bpy.data.node_groups.new(NGEN,'GeometryNodeTree');g.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
 inp=node(g,'NodeGroupInput','Empty input surface');out=node(g,'NodeGroupOutput','Independent lens solids output')
 src=node(g,'GeometryNodeObjectInfo','Live evaluated SDF fruit body');src.inputs['Object'].default_value=body;src.transform_space='RELATIVE';src.inputs['As Instance'].default_value=False
 matidx=node(g,'GeometryNodeInputMaterialIndex','Original cut-face material index')
 cap=mathnode(g,'GREATER_THAN','Only cut tissue faces index 2',matidx.outputs['Material Index'],1.5)
 separate=node(g,'GeometryNodeSeparateGeometry','Exposed cut cap only');separate.domain='FACE'
 wire(g,src.outputs['Geometry'],separate.inputs['Geometry']);wire(g,cap,separate.inputs['Selection'])
 # The actual source vascular field: no new stochastic 3D noise and no 2D UV.
 core=node(g,'GeometryNodeInputNamedAttribute','Current PR49 source-vascular CORE');core.data_type='FLOAT';core.inputs['Name'].default_value='sdf_v20_core'
 halo=node(g,'GeometryNodeInputNamedAttribute','Current PR49 wide vascular HALO');halo.data_type='FLOAT';halo.inputs['Name'].default_value='sdf_v20_halo'
 # Density high next to vessels and absent in low-field cap areas.
 threshold=node(g,'ShaderNodeMapRange','Only field-associated liquid pockets');threshold.clamp=True;threshold.interpolation_type='SMOOTHSTEP';threshold.inputs['From Min'].default_value=.035;threshold.inputs['From Max'].default_value=.26;threshold.inputs['To Min'].default_value=0.;threshold.inputs['To Max'].default_value=1.
 wire(g,halo.outputs['Attribute'],threshold.inputs['Value'])
 density=mathnode(g,'MULTIPLY','Vascular-controlled distribution / BU^2',threshold.outputs['Result'],12.)
 points=node(g,'GeometryNodeDistributePointsOnFaces','Deterministic few cap lens anchors');points.distribute_method='POISSON';points.inputs['Distance Min'].default_value=.033 # ~0.56mm
 points.inputs['Density Max'].default_value=12.;points.inputs['Seed'].default_value=19011
 wire(g,separate.outputs['Selection'],points.inputs['Mesh']);wire(g,density,points.inputs['Density Factor'])
 inst=node(g,'GeometryNodeInstanceOnPoints','True lens solids on live surface');wire(g,points.outputs['Points'],inst.inputs['Points'])
 source=node(g,'GeometryNodeObjectInfo','Solid lens prototype');source.inputs['Object'].default_value=lens;source.transform_space='RELATIVE';source.inputs['As Instance'].default_value=False
 wire(g,source.outputs['Geometry'],inst.inputs['Instance']);wire(g,points.outputs['Rotation'],inst.inputs['Rotation'])
 rand=node(g,'FunctionNodeRandomValue','Puddle size variation');rand.data_type='FLOAT';rand.inputs['Min'].default_value=.78;rand.inputs['Max'].default_value=1.38;rand.inputs['Seed'].default_value=8081
 wire(g,rand.outputs['Value'],inst.inputs['Scale'])
 realize=node(g,'GeometryNodeRealizeInstances','Make editable evaluated solid lenses');wire(g,inst.outputs['Instances'],realize.inputs['Geometry'])
 # Live toggle body Custom Property, no embedded Python scripts.
 v=node(g,'ShaderNodeValue','SDF | live meniscus switch');v.outputs[0].default_value=body['sdf_meniscus_gain'];drv=v.outputs[0].driver_add('default_value').driver;dv=drv.variables.new();dv.name='value';dv.targets[0].id=body;dv.targets[0].data_path='["sdf_meniscus_gain"]';drv.expression='value'
 sw=node(g,'GeometryNodeSwitch','OFF / attached pools');sw.input_type='GEOMETRY';wire(g,mathnode(g,'GREATER_THAN','Menisci enabled',v.outputs[0],.5),sw.inputs['Switch']);wire(g,inp.outputs['Geometry'],sw.inputs['False']);wire(g,realize.outputs['Geometry'],sw.inputs['True']);wire(g,sw.outputs['Output'],out.inputs['Geometry'])
 g['contract']='Source cap + own 192^3 vascular HALO -> deterministic Poisson points -> closed shallow lens solids; no 3D Voronoi boundary sheets'
 return g


def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--outdir',type=Path,required=True);args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);src=args.source.resolve();outdir=args.outdir.resolve()
 assert src.is_file() and hashlib.sha256(src.read_bytes()).hexdigest()==SOURCE_SHA
 assert not outdir.exists();outdir.mkdir(parents=True)
 bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False)
 assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
 s=bpy.context.scene;b=s.objects[BODY];assert len([o for o in s.objects if o.get('role')=='achene'])==264
 assert b.get('sdf_use_broad_halo')==1.;b['sdf_meniscus_gain']=0.;b.id_properties_ui('sdf_meniscus_gain').update(min=0,max=1,description='0=none 1=small real attached closed lens pockets on v20 vascular halo. ARTIST')
 mat=make_material();templ=build_lens();templ.data.materials.append(mat)
 ob=bpy.data.objects.new(FNAME,bpy.data.meshes.new('Empty native GN input'));s.collection.objects.link(ob);ob.matrix_world=b.matrix_world.copy();g=create_group(b,templ)
 mod=ob.modifiers.new('ARTIST | source-anchored menisci, whole OFF','NODES');mod.node_group=g
 ob['model']='Closed slightly submerged lens volumes (NOT physical juice simulation), field-anchored with original core/halo'
 ob['art']='artist, unmeasured. original meshes, SDF engine, seed guards, source atlas untouched.'
 report={'source_sha':SOURCE_SHA,'blender':bpy.app.version_string,'license':'all new code and node graphs are own, no Frucht assets','template':{'radius_mm':.31,'height_mm':.082,'base_penetration_mm':.034,'segments':32},'results':[]}
 for tag,gain in [('A',0.),('B',1.)]:
  b['sdf_meniscus_gain']=gain;b['sdf_mode']=0;b['sdf_voxel_mm']=.32
  b.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();deps.update()
  ev=ob.evaluated_get(deps);m=ev.to_mesh();assert not len(m.vertices),len(m.vertices);ev.to_mesh_clear()
  path=outdir/f'menisci-{tag}.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
  report['results'].append({'variant':tag,'gain':gain,'bytes':path.stat().st_size,'sha':hashlib.sha256(path.read_bytes()).hexdigest()})
 (outdir/'build.json').write_text(json.dumps(report,indent=2));print('MENISCI_SCENES',json.dumps(report),flush=True)

if __name__=='__main__':main()

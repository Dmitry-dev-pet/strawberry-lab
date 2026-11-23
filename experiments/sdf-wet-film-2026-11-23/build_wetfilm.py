"""Independent Strawberry Lab wet-film surface A/B on the pinned seed101 v20 bridge.

Adds a separate native Geometry Nodes object that conforms to the exposed cut mesh.
The original SDF body, seed guards, 150^3 atlas and 192^3 vascular fields are not modified.
The coating is an open zero-volume offset surface; it is not literal simulated juice.
"""
from pathlib import Path
import sys, json, hashlib, argparse
import bpy

BODY='Receptacle | canonical PR29 hull'
PIN='0b79e33b0725f807524061b1afe79671f4fcf1c6b5c429bd8203cec8d6a21bd2'
MAT_NAME='SDF | separate cut wet film (ARTIST)'
OBJ_NAME='SDF | live cut wet-film surface'

def node(g,t,name):
 n=g.nodes.new(t);n.name=n.label=name;return n

def wire(g,a,b):g.links.new(a,b)

def mathn(g,operation,name,a,b=None):
 n=node(g,'ShaderNodeMath',name);n.operation=operation
 for i,value in enumerate((a,b)):
  if value is None:continue
  if isinstance(value,(int,float)):n.inputs[i].default_value=value
  else:wire(g,value,n.inputs[i])
 return n.outputs[0]

def make_material():
 m=bpy.data.materials.new(MAT_NAME);m.use_nodes=True;g=m.node_tree;g.nodes.clear()
 out=node(g,'ShaderNodeOutputMaterial','ARTIST | wet film output')
 mix=node(g,'ShaderNodeMixShader','ARTIST | transparent film coverage')
 trans=node(g,'ShaderNodeBsdfTransparent','ARTIST | underlying flesh remains visible')
 trans.inputs['Color'].default_value=(1,1,1,1)
 bs=node(g,'ShaderNodeBsdfPrincipled','ARTIST | damp reflective translucent tissue film')
 bs.inputs['Base Color'].default_value=(.92,.45,.42,1)
 bs.inputs['IOR'].default_value=1.33
 bs.inputs['Transmission Weight'].default_value=.40
 bs.inputs['Roughness'].default_value=.10
 bs.inputs['Coat Weight'].default_value=.32
 bs.inputs['Coat Roughness'].default_value=.08
 bs.inputs['Subsurface Weight'].default_value=0.0
 attr=node(g,'ShaderNodeAttribute','V20 | existing halo field');attr.attribute_name='sdf_v20_halo'
 # SAME owned vascular field as flesh: wet highlights vary near the vascular halo.
 halo=mathn(g,'MULTIPLY','ARTIST | halo highlights modulation',attr.outputs['Fac'],.22)
 fac=mathn(g,'ADD','ARTIST | transparent film mixing baseline',.24,halo)
 wire(g,fac,mix.inputs[0]);wire(g,trans.outputs['BSDF'],mix.inputs[1]);wire(g,bs.outputs['BSDF'],mix.inputs[2]);wire(g,mix.outputs[0],out.inputs['Surface'])
 # Vary roughness via existing cellular/suppression attributes, no new noise or UV.
 sup=node(g,'ShaderNodeAttribute','V20 | existing cellular suppression');sup.attribute_name='sdf_v20_cell_suppression'
 rough=mathn(g,'MULTIPLY','ARTIST | cellular roughness variation',sup.outputs['Fac'],.09)
 rough=mathn(g,'ADD','ARTIST | wet roughness .055..145',.055,rough)
 wire(g,rough,bs.inputs['Roughness'])
 m['provenance']='Independent ARTIST; physically separate cut-only open surface; same sdf_v20_halo and cell suppression attributes'
 return m

def make_film(body,mm):
 mat=make_material()
 mesh=bpy.data.meshes.new('SDF wet-film base empty mesh')
 ob=bpy.data.objects.new(OBJ_NAME,mesh)
 bpy.context.scene.collection.objects.link(ob)
 ob.matrix_world=body.matrix_world.copy()
 g=bpy.data.node_groups.new('SDF | separate native cut surface wet film','GeometryNodeTree')
 g.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
 g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
 inn=node(g,'NodeGroupInput','Empty source surface');out=node(g,'NodeGroupOutput','Wet-film geometry output')
 orig=node(g,'GeometryNodeObjectInfo','Live evaluated SDF body');orig.inputs['Object'].default_value=body;orig.transform_space='RELATIVE'
 if 'As Instance' in orig.inputs:orig.inputs['As Instance'].default_value=False
 matindex=node(g,'GeometryNodeInputMaterialIndex','Match active cut material index 2')
 cap=mathn(g,'GREATER_THAN','Cut cap faces only',matindex.outputs['Material Index'],1.5)
 sep=node(g,'GeometryNodeSeparateGeometry','Separate existing cut faces from skin');sep.domain='FACE'
 wire(g,orig.outputs['Geometry'],sep.inputs['Geometry']);wire(g,cap,sep.inputs['Selection'])
 off=node(g,'GeometryNodeSetPosition','ARTIST | sheet offset normal 0.025mm')
 wire(g,sep.outputs['Selection'],off.inputs['Geometry'])
 nor=node(g,'GeometryNodeInputNormal','Existing cut surface normal')
 scaled=node(g,'ShaderNodeVectorMath','Normal offset 0.025mm in scene units');scaled.operation='SCALE';wire(g,nor.outputs['Normal'],scaled.inputs[0]);scaled.inputs[3].default_value=.025/mm
 wire(g,scaled.outputs['Vector'],off.inputs['Offset'])
 setmat=node(g,'GeometryNodeSetMaterial','Independent film material');setmat.inputs['Material'].default_value=mat;wire(g,off.outputs['Geometry'],setmat.inputs['Geometry'])
 shade=node(g,'GeometryNodeSetShadeSmooth','Smooth thin wet surface');shade.domain='FACE';wire(g,setmat.outputs['Geometry'],shade.inputs['Geometry'])
 active=node(g,'ShaderNodeValue','ARTIST | wet film LIVE toggle');active.outputs[0].default_value=body['sdf_wetfilm_gain']
 d=active.outputs[0].driver_add('default_value').driver;v=d.variables.new();v.name='wet';v.targets[0].id=body;v.targets[0].data_path='["sdf_wetfilm_gain"]';d.expression='wet'
 ison=mathn(g,'GREATER_THAN','Wet layer gain > 0.5',active.outputs[0],.5)
 switch=node(g,'GeometryNodeSwitch','Enable/disable separate geometric film');switch.input_type='GEOMETRY'
 wire(g,ison,switch.inputs['Switch']);wire(g,inn.outputs['Geometry'],switch.inputs['False']);wire(g,shade.outputs['Geometry'],switch.inputs['True']);wire(g,switch.outputs['Output'],out.inputs['Geometry'])
 mod=ob.modifiers.new('Native independent cut film driven by source body','NODES');mod.node_group=g
 ob['film_description']='Independent, open cut-conforming surface offset by 0.025 mm; NOT volumetric juice; user toggle on SDF body.'
 ob['film_art_policy']='ARTIST, unmeasured; no Frucht source code/assets.'
 return ob,g,mat

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',required=True,type=Path);p.add_argument('--outdir',required=True,type=Path)
 args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
 src=args.source.resolve();dest=args.outdir.resolve()
 assert src.is_file() and hashlib.sha256(src.read_bytes()).hexdigest()==PIN,'Source mismatch'
 assert not dest.exists(),'Refuse to overwrite evidence'
 assert bpy.app.version[:2]==(5,2)
 dest.mkdir(parents=True)
 bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False)
 scene=bpy.context.scene;body=scene.objects[BODY]
 assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
 assert body['sdf_tissue_gain']==1 and body['sdf_use_broad_halo']==1
 mm=scene.unit_settings.scale_length*1000
 assert abs(mm-22.22222276)<1e-5
 body['sdf_wetfilm_gain']=0.0
 body.id_properties_ui('sdf_wetfilm_gain').update(min=0,max=1,description='0 hide real cut-only film geometry, 1 separate film. ARTIST not juice volume')
 obj,g,mat=make_film(body,mm)
 source_raw=hashlib.sha256(repr([(v.co[:]) for v in body.data.vertices]).encode()).hexdigest()
 result={'source_sha256':PIN,'source_raw_geometry':source_raw,'blender':bpy.app.version_string,'mode':'separate native cut-only sheet','geometry_node_count':len(g.nodes),'material_node_count':len(mat.node_tree.nodes),'offset_mm':.025,'independent_film_object':OBJ_NAME,'gain_property':'sdf_wetfilm_gain','variants':[],'limits':'separate open cap-following film, NOT closed fluid volume or physically simulated exudate'}
 for name,value in [('A',0.0),('B',1.0)]:
  body['sdf_wetfilm_gain']=value
  body.update_tag();scene.frame_set(scene.frame_current);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
  path=dest/f'wetfilm-{name}.blend'
  bpy.context.preferences.filepaths.save_version=0
  bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
  result['variants'].append({'name':name,'gain':value,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
 print('WET_FILM_CREATED',json.dumps(result),flush=True)
 (dest/'build-receipt.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()

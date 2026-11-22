"""Own M1c/M1d principles integrated with PR40 seed101. No Mesh Boolean/Exact."""
from pathlib import Path
import sys,json,hashlib,math,argparse
import bpy
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[3]
BODY='Receptacle | canonical PR29 hull';PLANE='SDF | editable plane halfspace';SPHERE='SDF | editable sphere bite';REST='sdf_rest_position'
PIN='156908ee46fd6be4cb7624d63d3f668f772abab2323d8c65ba3619dc45f63017'

def tree(name):
 g=bpy.data.node_groups.new(name,'GeometryNodeTree');g.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');return g

def node(g,kind,name=None):
 n=g.nodes.new(kind)
 if name:n.name=name;n.label=name
 return n

def wire(g,a,b):g.links.new(a,b)

def driven(g,body,key):
 n=node(g,'ShaderNodeValue',key);n.outputs[0].default_value=body[key];d=n.outputs[0].driver_add('default_value').driver;v=d.variables.new();v.name='value';v.targets[0].id=body;v.targets[0].data_path=f'["{key}"]';d.expression='value';return n.outputs[0]

def mathnode(g,op,a,b=None):
 n=node(g,'ShaderNodeMath');n.operation=op
 for i,v in enumerate([a,b]):
  if v is None:continue
  if isinstance(v,(int,float)):n.inputs[i].default_value=v
  else:wire(g,v,n.inputs[i])
 return n.outputs[0]

def inverse_nodes(g,pos,params):
 a,b,h=params;sep=node(g,'ShaderNodeSeparateXYZ');wire(g,pos,sep.inputs[0]);z=mathnode(g,'DIVIDE',sep.outputs['Z'],h)
 def gaussian(center,width,weight):
  q=mathnode(g,'DIVIDE',mathnode(g,'SUBTRACT',z,center),width);square=mathnode(g,'MULTIPLY',q,q);return mathnode(g,'MULTIPLY',mathnode(g,'EXPONENT',mathnode(g,'MULTIPLY',square,-1)),weight)
 scale=mathnode(g,'ADD',mathnode(g,'ADD',1,gaussian(.5,.36,a)),gaussian(-.3,.4,b));out=node(g,'ShaderNodeCombineXYZ','SDF inverse F | physical to original rest')
 for key,src in [('X',mathnode(g,'DIVIDE',sep.outputs['X'],scale)),('Y',mathnode(g,'DIVIDE',sep.outputs['Y'],scale)),('Z',z)]:wire(g,src,out.inputs[key])
 return out.outputs[0]

def info(g,obj):
 n=node(g,'GeometryNodeObjectInfo',obj.name);n.inputs['Object'].default_value=obj;n.transform_space='RELATIVE';return n

def cut_material(material):
 m=material.copy();m.name='SDF | inherited 150^3 tissue + own multiscale wetness';g=m.node_tree
 rest=node(g,'ShaderNodeAttribute',REST);rest.attribute_name=REST
 old=next(n for n in g.nodes if n.label=='Analytic nonlinear inverse: physical -> original PR29 rest')
 for link in list(old.outputs[0].links):target=link.to_socket;g.links.remove(link);wire(g,rest.outputs['Vector'],target)
 bs=next(n for n in g.nodes if n.type=='BSDF_PRINCIPLED');layers=[]
 for scale,weight in [(20,.5),(60,.3),(150,.2)]:
  vor=node(g,'ShaderNodeTexVoronoi',f'Own 3D wetness scale {scale}');vor.feature='DISTANCE_TO_EDGE';vor.voronoi_dimensions='3D';vor.inputs['Scale'].default_value=scale;wire(g,rest.outputs['Vector'],vor.inputs['Vector']);layers.append(mathnode(g,'MULTIPLY',vor.outputs['Distance'],weight))
 signal=mathnode(g,'ADD',mathnode(g,'ADD',layers[0],layers[1]),layers[2]);bump=node(g,'ShaderNodeBump','Soft wet surface | shader only');bump.inputs['Strength'].default_value=.13;bump.inputs['Distance'].default_value=.002;wire(g,signal,bump.inputs['Height']);wire(g,bump.outputs['Normal'],bs.inputs['Normal'])
 rough=mathnode(g,'ADD',.29,mathnode(g,'MULTIPLY',signal,.45));wire(g,rough,bs.inputs['Roughness']);bs.inputs['Coat Weight'].default_value=.10;bs.inputs['Coat Roughness'].default_value=.18;bs.inputs['Subsurface Weight'].default_value=.08
 if 'Subsurface Scale' in bs.inputs:bs.inputs['Subsurface Scale'].default_value=.012
 return m

def body_group(body,plane,sphere,params,skin,cap,mm):
 g=tree('SDF Generator | one fruit grid, two editable cutters');inp=node(g,'NodeGroupInput');out=node(g,'NodeGroupOutput');mode=driven(g,body,'sdf_mode');voxel=mathnode(g,'DIVIDE',driven(g,body,'sdf_voxel_mm'),mm)
 a=info(g,plane);b=info(g,sphere);choose=node(g,'GeometryNodeSwitch','1 plane / 2 sphere');choose.input_type='GEOMETRY';wire(g,mathnode(g,'GREATER_THAN',mode,1.5),choose.inputs['Switch']);wire(g,a.outputs['Geometry'],choose.inputs['False']);wire(g,b.outputs['Geometry'],choose.inputs['True'])
 fruit=node(g,'GeometryNodeMeshToSDFGrid','Fruit mesh to SDF');cutter=node(g,'GeometryNodeMeshToSDFGrid','Selected cutter to SDF')
 for n,geometry in [(fruit,inp.outputs['Geometry']),(cutter,choose.outputs[0])]:wire(g,geometry,n.inputs['Mesh']);wire(g,voxel,n.inputs['Voxel Size']);n.inputs['Band Width'].default_value=5
 boolean=node(g,'GeometryNodeSDFGridBoolean','SDF difference, no mesh seam triangulator');boolean.operation='DIFFERENCE';wire(g,fruit.outputs[0],boolean.inputs['Grid 1']);wire(g,cutter.outputs[0],boolean.inputs['Grid 2'])
 converted=[]
 for grid in [fruit.outputs[0],boolean.outputs['Grid']]:
  n=node(g,'GeometryNodeGridToMesh');n.inputs['Adaptivity'].default_value=0;n.inputs['Threshold'].default_value=0;wire(g,grid,n.inputs['Grid']);converted.append(n.outputs['Mesh'])
 select=node(g,'GeometryNodeSwitch','0 whole / cut');select.input_type='GEOMETRY';active=mathnode(g,'GREATER_THAN',mode,.5);wire(g,active,select.inputs['Switch']);wire(g,converted[0],select.inputs['False']);wire(g,converted[1],select.inputs['True'])
 pos=node(g,'GeometryNodeInputPosition');rest=inverse_nodes(g,pos.outputs[0],params);store=node(g,'GeometryNodeStoreNamedAttribute',REST);store.data_type='FLOAT_VECTOR';store.domain='POINT';store.inputs['Name'].default_value=REST;wire(g,select.outputs[0],store.inputs['Geometry']);wire(g,rest,store.inputs['Value'])
 sample=node(g,'GeometryNodeSampleNearestSurface','Transfer source skin pit mask');sample.data_type='FLOAT';attr=node(g,'GeometryNodeInputNamedAttribute');attr.data_type='FLOAT';attr.inputs['Name'].default_value='achene_pit';wire(g,inp.outputs['Geometry'],sample.inputs['Mesh']);wire(g,attr.outputs['Attribute'],sample.inputs['Value']);wire(g,pos.outputs[0],sample.inputs['Sample Position'])
 mask=node(g,'GeometryNodeStoreNamedAttribute');mask.data_type='FLOAT';mask.domain='POINT';mask.inputs['Name'].default_value='achene_pit';wire(g,store.outputs[0],mask.inputs['Geometry']);wire(g,sample.outputs['Value'],mask.inputs['Value'])
 base=node(g,'GeometryNodeSetMaterial');base.inputs['Material'].default_value=skin;wire(g,mask.outputs[0],base.inputs['Geometry'])
 prox=node(g,'GeometryNodeProximity');prox.target_element='FACES';wire(g,choose.outputs[0],prox.inputs['Target']);close=mathnode(g,'LESS_THAN',prox.outputs['Distance'],mathnode(g,'MULTIPLY',voxel,1.7));cutsel=mathnode(g,'MULTIPLY',active,close)
 cut=node(g,'GeometryNodeSetMaterial','Cut material by active cutter proximity');cut.inputs['Material'].default_value=cap;wire(g,base.outputs[0],cut.inputs['Geometry']);wire(g,cutsel,cut.inputs['Selection'])
 smooth=node(g,'GeometryNodeSetShadeSmooth');smooth.domain='FACE';wire(g,cut.outputs[0],smooth.inputs['Geometry']);wire(g,smooth.outputs[0],out.inputs['Geometry'])
 return g

def mask_group(body,plane,sphere):
 g=tree('SDF | same-cutter CENTER mask for solid seeds and crown');inp=node(g,'NodeGroupInput');out=node(g,'NodeGroupOutput');mode=driven(g,body,'sdf_mode');pos=node(g,'GeometryNodeInputPosition');mean=node(g,'GeometryNodeAttributeStatistic');mean.data_type='FLOAT_VECTOR';mean.domain='POINT';wire(g,inp.outputs[0],mean.inputs['Geometry']);wire(g,pos.outputs[0],mean.inputs['Attribute']);point=mean.outputs['Mean']
 a=info(g,plane);b=info(g,sphere)
 def subtract(x,y):
  n=node(g,'ShaderNodeVectorMath');n.operation='SUBTRACT';wire(g,x,n.inputs[0]);wire(g,y,n.inputs[1]);return n.outputs['Vector']
 vec=subtract(point,a.outputs['Location']);rotate=node(g,'ShaderNodeVectorRotate');rotate.rotation_type='EULER_XYZ';rotate.invert=True;wire(g,vec,rotate.inputs['Vector']);wire(g,a.outputs['Rotation'],rotate.inputs['Rotation']);xyz=node(g,'ShaderNodeSeparateXYZ');wire(g,rotate.outputs[0],xyz.inputs[0]);insideplane=mathnode(g,'LESS_THAN',xyz.outputs['Y'],0)
 length=node(g,'ShaderNodeVectorMath');length.operation='LENGTH';wire(g,subtract(point,b.outputs['Location']),length.inputs[0]);scale=node(g,'ShaderNodeSeparateXYZ');wire(g,b.outputs['Scale'],scale.inputs[0]);insidesphere=mathnode(g,'LESS_THAN',length.outputs['Value'],scale.outputs['X'])
 choose=node(g,'GeometryNodeSwitch');choose.input_type='BOOLEAN';wire(g,mathnode(g,'GREATER_THAN',mode,1.5),choose.inputs['Switch']);wire(g,insideplane,choose.inputs['False']);wire(g,insidesphere,choose.inputs['True']);active=mathnode(g,'GREATER_THAN',mode,.5);remove=mathnode(g,'MULTIPLY',active,choose.outputs[0]);delete=node(g,'GeometryNodeDeleteGeometry');delete.domain='POINT';wire(g,inp.outputs[0],delete.inputs['Geometry']);wire(g,remove,delete.inputs['Selection']);wire(g,delete.outputs[0],out.inputs[0]);return g

def main():
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert hashlib.sha256(args.input.read_bytes()).hexdigest()==PIN;assert not args.out.exists();args.out.parent.mkdir(parents=True,exist_ok=True)
 bpy.ops.wm.open_mainfile(filepath=str(args.input.resolve()),use_scripts=False);s=bpy.context.scene;body=s.objects[BODY];mm=s.unit_settings.scale_length*1000;cfg=json.loads(s['Nonlinear parameters']);params=cfg['a'],cfg['b'],cfg['h'];assert abs(mm-22.22222276)<1e-5
 # Remove legacy execution paths, not source organs. Never run old Exact/profile callbacks here.
 for text in list(bpy.data.texts):bpy.data.texts.remove(text)
 for o in s.objects:
  if o.type in {'MESH','CURVE'}:
   for m in list(o.modifiers):o.modifiers.remove(m)
 # One native layer. Original diagnostics remain stored, excluded from this slice.
 keep=s.view_layers.get('WHOLE');bpy.context.window.view_layer=keep
 for layer in list(s.view_layers):
  if layer!=keep:s.view_layers.remove(layer)
 keep.name='SDF | live';s.render.use_single_layer=True
 for child in keep.layer_collection.children:
  if child.name.startswith('Diagnostics') or child.name=='One shared knife':child.exclude=True
 coll=bpy.data.collections.new('SDF | native editable controls');s.collection.children.link(coll)
 def meshobj(name,vertices,faces):
  me=bpy.data.meshes.new(name);me.from_pydata(vertices,[],faces);me.update();o=bpy.data.objects.new(name,me);coll.objects.link(o);o.hide_render=True;o.display_type='WIRE';return o
 vertices=[(x,y,z) for z in [-2,2] for y in [-3,0] for x in [-2,2]];faces=[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]
 plane=meshobj(PLANE,vertices,faces)
 bpy.ops.mesh.primitive_uv_sphere_add(segments=96,ring_count=64,radius=1,location=(.60,-.70,.42));sphere=bpy.context.object;sphere.name=SPHERE
 for c in list(sphere.users_collection):c.objects.unlink(sphere)
 coll.objects.link(sphere);sphere.scale=(.65,.65,.65);sphere.hide_render=True;sphere.display_type='WIRE'
 body['sdf_mode']=0;body.id_properties_ui('sdf_mode').update(min=0,max=2,description='0 WHOLE; 1 PLANE; 2 SPHERE. Native drivers, no scripts needed.')
 body['sdf_voxel_mm']=.20;body.id_properties_ui('sdf_voxel_mm').update(min=.10,max=.6,description='Actual millimetres; divided by scene mm per model unit in GN')
 skin=body.data.materials[0].copy();skin.name='SDF | source skin at true rest_position';g=skin.node_tree;old=next(n for n in g.nodes if n.label=='Analytic nonlinear inverse: physical -> original PR29 rest');attr=node(g,'ShaderNodeAttribute',REST);attr.attribute_name=REST
 for link in list(old.outputs[0].links):target=link.to_socket;g.links.remove(link);wire(g,attr.outputs['Vector'],target)
 cap=cut_material(body.data.materials[1]);body.data.materials.clear();body.data.materials.append(skin);body.data.materials.append(cap);mod=body.modifiers.new('SDF engine | edit body Custom Properties mode / voxel mm','NODES');mod.node_group=body_group(body,plane,sphere,params,skin,cap,mm)
 group=mask_group(body,plane,sphere)
 for o in s.objects:
  if o.get('role') in {'achene','sepal','pedicel'}:o.modifiers.new('Same cutter | center cull, no solid clipping','NODES').node_group=group
 s['SDF slice provenance']='PR40 seed101 source hull/264 seeds/pits/ARTIST graph; original packed150^3 template-derived field. Own GN SDF pipeline; no Frucht assets.'
 s['SDF limitations']='Seed/crown CENTER culling only, no partial solid intersection. Source profile fixed; old live Python Exact/Profile removed. Diagnostics retained hidden, not clipped by SDF. Cut microtexture shader-only.'
 s['SDF controls']='Select canonical body > Object Custom Properties: sdf_mode 0/1/2; sdf_voxel_mm. Move/rotate SDF plane; move/uniform-scale sphere. No auto scripts.'
 s['SDF params']=json.dumps(params);s['SDF source_sha256']=PIN
 note=bpy.data.texts.new('SDF_SLICE__README.txt');note.write(s['SDF controls']+'\n'+s['SDF limitations']+'\nModes are geometry-node drivers. No Python execution required after reopening.')
 s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=16;s.cycles.use_denoising=True;s.cycles.seed=1729;s.render.resolution_x=s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
 # Evaluate before saving; source mesh stays the only body input.
 body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();assert len(me.vertices)>1000;print('SDF_INITIAL_VERTICES',len(me.vertices),flush=True);ev.to_mesh_clear()
 bpy.ops.wm.save_as_mainfile(filepath=str(args.out.resolve()),compress=True)
if __name__=='__main__':main()

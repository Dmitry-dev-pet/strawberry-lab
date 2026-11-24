"""Original two-path exterior/flesh prototype; no imported Frucht implementation.
Closed tissue stock and exact exterior clip share one editable cutter. ARTIST mm.
"""
import bpy, sys, math, json, hashlib
from pathlib import Path
from mathutils import Vector
PIN='d430ac081f5383148e4f6a6a81f0dfc89fdfc5e8fb7538dd76cf97598398026a'
SKIN='SL Neutral Skin'; SEEDS='SL Neutral Achenes'; ROOT='SL Shape Controller | edit Custom Properties'
SOURCE='SL Split | independent flesh source'; FLESH='SL Split | visible flesh'; CUTTER='SL Split | current cutter'; PLANE='SL Split | plane box'; SPHERE='SL Split | sphere bite'; CAP='SL Split | cut tissue'; MARK='SL Split | temporary cut marker'; INNER='SL Split | recessed tissue'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mat(name,rgb):
 m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);return m
class Graph:
 def __init__(self,name,root):
  self.g=bpy.data.node_groups.new(name,'GeometryNodeTree');self.root=root
  for direction in ['INPUT','OUTPUT']:self.g.interface.new_socket(name='Geometry',in_out=direction,socket_type='NodeSocketGeometry')
  self.input=self.node('NodeGroupInput').outputs[0];self.output=self.node('NodeGroupOutput').inputs[0]
 def node(self,t,label=''):
  n=self.g.nodes.new(t);n.label=label or t;return n
 def w(self,a,b):
  if isinstance(a,bpy.types.NodeSocket):self.g.links.new(a,b)
  else:b.default_value=a
 def math(self,op,a,b):
  n=self.node('ShaderNodeMath',op);n.operation=op;self.w(a,n.inputs[0]);self.w(b,n.inputs[1]);return n.outputs[0]
 def driven(self,key):
  n=self.node('ShaderNodeValue',key);n.outputs[0].default_value=self.root[key];d=n.outputs[0].driver_add('default_value').driver;d.type='AVERAGE';v=d.variables.new();v.name='value';v.type='SINGLE_PROP';v.targets[0].id=self.root;v.targets[0].data_path='["'+key+'"]';return n.outputs[0]
 def info(self,o):
  n=self.node('GeometryNodeObjectInfo',o.name);n.transform_space='RELATIVE';n.inputs['Object'].default_value=o;return n
 def switch(self,c,a,b):
  n=self.node('GeometryNodeSwitch','Conditional path');n.input_type='GEOMETRY';self.w(c,n.inputs['Switch']);self.w(a,n.inputs['False']);self.w(b,n.inputs['True']);return n.outputs[0]
 def sdf(self,geo,vox):
  n=self.node('GeometryNodeMeshToSDFGrid','Independent signed volume');self.w(geo,n.inputs['Mesh']);self.w(vox,n.inputs['Voxel Size']);n.inputs['Band Width'].default_value=3;return n.outputs[0]
 def attr(self,name,kind):
  n=self.node('GeometryNodeInputNamedAttribute',name);n.data_type=kind;n.inputs['Name'].default_value=name;return n.outputs['Attribute']
 def store(self,geo,name,kind,domain,value):
  n=self.node('GeometryNodeStoreNamedAttribute',name);n.data_type=kind;n.domain=domain;n.inputs['Name'].default_value=name;self.w(geo,n.inputs['Geometry']);self.w(value,n.inputs['Value']);return n.outputs[0]
 def material(self,geo,material,sel=True):
  n=self.node('GeometryNodeSetMaterial',material.name);self.w(geo,n.inputs['Geometry']);self.w(sel,n.inputs['Selection']);n.inputs['Material'].default_value=material;return n.outputs[0]
 def delete(self,geo,sel,domain):
  n=self.node('GeometryNodeDeleteGeometry','Remove selected '+domain);n.domain=domain;n.mode='ALL';self.w(geo,n.inputs['Geometry']);self.w(sel,n.inputs['Selection']);return n.outputs[0]
 def prox(self,geo):
  n=self.node('GeometryNodeProximity','Nearest triangle distance');n.target_element='FACES';self.w(geo,n.inputs['Geometry']);return n
 def finish(self,o,result):
  self.w(result,self.output)
  for i,n in enumerate(self.g.nodes):n.location=((i//7)*220,-(i%7)*180)
  mod=o.modifiers.new(self.g.name,'NODES');mod.node_group=self.g;return len(self.g.nodes)
def empty_mesh(name):
 o=bpy.data.objects.new(name,bpy.data.meshes.new(name));bpy.context.scene.collection.objects.link(o);return o
def hide(o):o.hide_render=True;o.hide_set(True);o.display_type='WIRE'
def main():
 src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)==PIN and not out.exists();bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False)
 s=bpy.context.scene;root=bpy.data.objects[ROOT];skin=bpy.data.objects[SKIN];seeds=bpy.data.objects[SEEDS]
 for key,val,lo,hi in [('split_mode',0,0,2),('flesh_voxel_mm',.32,.20,.60),('flesh_recess_mm',.20,0.,.5)]:root[key]=val;root.id_properties_ui(key).update(min=lo,max=hi)
 source=skin.copy();source.data=skin.data.copy();source.name=SOURCE;s.collection.objects.link(source);hide(source)
 # The two closed cutter meshes are shared, not separately approximated by each path.
 bpy.ops.mesh.primitive_cube_add(size=2,location=(0,-80,24));plane=bpy.context.object;plane.name=PLANE;plane.scale=(80,80,80);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);plane.data.transform(__import__('mathutils').Matrix.Translation((0,-80,0)));plane.location=(0,0,24);hide(plane)
 bpy.ops.mesh.primitive_uv_sphere_add(segments=96,ring_count=64,radius=12,location=(6,-13,30));sphere=bpy.context.object;sphere.name=SPHERE;hide(sphere)
 marker=mat(MARK,(.8,.2,.7));cap=mat(CAP,(.74,.70,.61));inner=mat(INNER,(.4,.38,.35));skin.data.materials[0].diffuse_color=(.46,.46,.46,1)
 cutter=empty_mesh(CUTTER);hide(cutter);g=Graph('SL Split | single cutter router',root);mode=g.driven('split_mode');geo=g.switch(g.math('GREATER_THAN',mode,1.5),g.info(plane).outputs['Geometry'],g.info(sphere).outputs['Geometry']);g.finish(cutter,geo)
 # Original skin: exact native mesh clipping, with cutter face material used as a provenance marker.
 g=Graph('SL Split | preserve original skin',root);cut=g.material(g.info(cutter).outputs['Geometry'],marker);b=g.node('GeometryNodeMeshBoolean','Clip original mesh; no SDF remesh');b.operation='DIFFERENCE';b.solver='MANIFOLD';g.w(g.input,b.inputs['Mesh 1']);g.w(cut,b.inputs['Mesh 2']);sel=g.node('GeometryNodeMaterialSelection','Remove only generated cut faces');sel.inputs['Material'].default_value=marker;open_skin=g.delete(b.outputs['Mesh'],sel.outputs[0],'FACE');g.finish(skin,g.switch(g.math('GREATER_THAN',g.driven('split_mode'),.5),g.input,open_skin))
 # Named reusable volume stock. Shape map still runs before this node group.
 g=Graph('SL Split | reusable named flesh grid',root);v=g.driven('flesh_voxel_mm');grid=g.sdf(g.input,v);store=g.node('GeometryNodeStoreNamedGrid','Store independent flesh stock');store.inputs['Name'].default_value='sl_flesh_volume';g.w(grid,store.inputs['Grid']);g.finish(source,store.outputs['Volume'])
 # Separate tissue: cutter subtraction, nearest-source classification, recession under skin.
 flesh=empty_mesh(FLESH);g=Graph('SL Split | flesh volume cut',root);src=g.info(source).outputs['Geometry'];get=g.node('GeometryNodeGetNamedGrid','Read reusable volume');get.data_type='FLOAT';get.inputs['Name'].default_value='sl_flesh_volume';g.w(src,get.inputs['Volume']);vox=g.driven('flesh_voxel_mm');cg=g.info(cutter).outputs['Geometry'];grid=g.sdf(cg,vox);bo=g.node('GeometryNodeSDFGridBoolean','Independent tissue difference');bo.operation='DIFFERENCE';g.w(get.outputs['Grid'],bo.inputs['Grid 1']);g.w(grid,bo.inputs['Grid 2']);gm=g.node('GeometryNodeGridToMesh','Tissue only remesh');g.w(bo.outputs['Grid'],gm.inputs['Grid']);geo=gm.outputs['Mesh'];d=g.prox(cg).outputs['Distance'];sel=g.math('LESS_THAN',d,g.math('MULTIPLY',vox,.8));geo=g.store(geo,'sl_cut_face','BOOLEAN','FACE',sel);geo=g.material(geo,inner);geo=g.material(geo,cap,g.attr('sl_cut_face','BOOLEAN'))
 ramp=g.node('ShaderNodeMapRange','Recess only away from cutter');ramp.clamp=True;ramp.interpolation_type='SMOOTHERSTEP';g.w(d,ramp.inputs['Value']);ramp.inputs['From Min'].default_value=.36;ramp.inputs['From Max'].default_value=.95;ramp.inputs['To Min'].default_value=0.;g.w(g.driven('flesh_recess_mm'),ramp.inputs['To Max']);normal=g.node('GeometryNodeInputNormal').outputs[0];vec=g.node('ShaderNodeVectorMath','Inward offset');vec.operation='SCALE';g.w(normal,vec.inputs[0]);g.w(g.math('MULTIPLY',ramp.outputs['Result'],-1),vec.inputs['Scale']);move=g.node('GeometryNodeSetPosition','Recess external tissue beneath original skin');g.w(geo,move.inputs['Geometry']);g.w(vec.outputs[0],move.inputs['Offset']);smooth=g.node('GeometryNodeSetShadeSmooth');smooth.domain='FACE';g.w(move.outputs[0],smooth.inputs['Geometry']);g.finish(flesh,g.switch(g.math('GREATER_THAN',g.driven('split_mode'),.5),g.input,smooth.outputs[0]))
 # Conservative whole-achene deletion based on all real vertices. Analytic cutter fields are valid only for the specified box/sphere types, margin 0.04 mm.
 g=Graph('SL Split | conservative achene solids',root);p=g.node('GeometryNodeInputPosition').outputs[0]
 def vec(op,a,b):n=g.node('ShaderNodeVectorMath',op);n.operation=op;g.w(a,n.inputs[0]);g.w(b,n.inputs[1]);return n.outputs['Value' if op in ('DISTANCE','DOT_PRODUCT') else 'Vector']
 pl=g.info(plane);delta=vec('SUBTRACT',p,pl.outputs['Location']);rot=g.node('ShaderNodeVectorRotate','Plane local frame');rot.rotation_type='EULER_XYZ';rot.invert=True;g.w(delta,rot.inputs['Vector']);g.w(pl.outputs['Rotation'],rot.inputs['Rotation']);sep=g.node('ShaderNodeSeparateXYZ');g.w(rot.outputs[0],sep.inputs[0]);pm=g.math('LESS_THAN',sep.outputs['Y'],.04)
 sp=g.info(sphere);radius=g.node('ShaderNodeSeparateXYZ');g.w(sp.outputs['Scale'],radius.inputs[0]);sm=g.math('LESS_THAN',vec('DISTANCE',p,sp.outputs['Location']),g.math('ADD',g.math('MULTIPLY',radius.outputs['X'],12),.04));mode=g.driven('split_mode');mask=g.math('ADD',g.math('MULTIPLY',pm,g.math('COMPARE',mode,1)),g.math('MULTIPLY',sm,g.math('COMPARE',mode,2))) if False else g.math('MAXIMUM',g.math('MULTIPLY',pm,g.math('MULTIPLY',g.math('GREATER_THAN',mode,.5),g.math('LESS_THAN',mode,1.5))),g.math('MULTIPLY',sm,g.math('GREATER_THAN',mode,1.5)))
 ac=g.node('GeometryNodeAccumulateField','All vertices per stable seed ID');ac.data_type='INT';ac.domain='POINT';g.w(mask,ac.inputs['Value']);g.w(g.attr('sl_anchor_index','INT'),ac.inputs['Group ID']);g.finish(seeds,g.delete(g.input,g.math('GREATER_THAN',ac.outputs['Total'],0),'POINT'))
 s['scope']='Split surface research: original skin clip, independent named SDF flesh; diagnostic only';bpy.context.view_layer.objects.active=root;root.select_set(True);bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True);print(json.dumps({'source_sha':PIN,'scene_sha':sha(out),'groups':{g.name:len(g.nodes) for g in bpy.data.node_groups if g.name.startswith('SL Split')}}),flush=True)
if __name__=='__main__':main()

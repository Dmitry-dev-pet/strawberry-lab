"""Independent source-consistent cut provenance, no reference code/graphs/presets."""
import bpy,sys,hashlib,json
from pathlib import Path
PIN='b46cc7492e3b42a5125147564c2aaabe42cd4e713e3c66c0de54ba43c32ab8e9'
HELPER='1fd07748a0bc668b81715d037e3ee5db8b6cad20'
ROOT='SL Shape Controller | edit Custom Properties'
SOURCE='SL Split | independent flesh source';FLESH='SL Split | visible flesh'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def gitsha(p):
 b=Path(p).read_bytes();return hashlib.sha1(('blob %d\0'%len(b)).encode()+b).hexdigest()
def one(g,label):
 ns=[n for n in g.nodes if n.label==label];assert len(ns)==1,(label,len(ns));return ns[0]
def connect(g,a,b):
 if not b.is_multi_input:
  for l in list(b.links):g.links.remove(l)
 g.links.new(a,b)
def prune(g):
 out=next(n for n in g.nodes if n.type=='GROUP_OUTPUT');keep={out};queue=[out]
 while queue:
  for sock in queue.pop().inputs:
   for l in sock.links:
    if l.from_node not in keep:keep.add(l.from_node);queue.append(l.from_node)
 for n in list(g.nodes):
  if n not in keep:g.nodes.remove(n)

def main():
 src,helper,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)==PIN and gitsha(helper)==HELPER and not out.exists();bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),use_scripts=False)
 root=bpy.data.objects[ROOT];source=bpy.data.objects[SOURCE];flesh=bpy.data.objects[FLESH]
 assert root['interface_gain']==0
 # Same named grid, extract its zero isosurface, not the high-resolution render skin.
 sg=source.modifiers[-1].node_group;join=one(sg,'Reference envelope and existing volume');grid=one(sg,'Independent signed volume');gm=sg.nodes.new('GeometryNodeGridToMesh');gm.label='Independent uncut flesh reference';connect(sg,grid.outputs[0],gm.inputs['Grid']);gm.inputs['Threshold'].default_value=0.
 for l in list(join.inputs['Geometry'].links):
  if l.from_node.type=='GROUP_INPUT':sg.links.remove(l)
 sg.links.new(gm.outputs['Mesh'],join.inputs['Geometry']);join.label='Named volume plus its uncut isosurface';gm.location=(420,-300)
 # Modify only the existing tissue display group. Keep same subtraction and voxel control.
 g=flesh.modifiers[0].node_group;N=g.nodes
 def node(t,label):n=N.new(t);n.label=label;return n
 def w(a,b):
  if isinstance(a,bpy.types.NodeSocket):connect(g,a,b)
  else:
   for l in list(b.links):g.links.remove(l)
   b.default_value=a
 def math(op,a,b):n=node('ShaderNodeMath',op);n.operation=op;w(a,n.inputs[0]);w(b,n.inputs[1]);return n.outputs[0]
 def st(geo,name,typ,domain,value):
  n=node('GeometryNodeStoreNamedAttribute',name);n.data_type=typ;n.domain=domain;n.inputs['Name'].default_value=name;w(geo,n.inputs['Geometry']);w(value,n.inputs['Value']);return n.outputs['Geometry']
 def at(name,typ):n=node('GeometryNodeInputNamedAttribute',name);n.data_type=typ;n.inputs['Name'].default_value=name;return n.outputs['Attribute']
 pos=node('GeometryNodeInputPosition','Unmoved cut-grid surface').outputs[0];normal=one(g,'GeometryNodeInputNormal').outputs[0]
 # Independent thresholds: keep former .8*voxel cap width, require outer surface within ONE voxel.
 cutter=one(g,'Independent signed volume').outputs[0];sample=node('GeometryNodeSampleGrid','Actual signed cutter sample');sample.data_type='FLOAT';w(cutter,sample.inputs['Grid']);w(pos,sample.inputs['Position'])
 srcinfo=one(g,SOURCE);sep=node('GeometryNodeSeparateComponents','Uncut grid reference mesh only');w(srcinfo.outputs['Geometry'],sep.inputs['Geometry']);prox=node('GeometryNodeProximity','Distance to uncut tissue isosurface');prox.target_element='FACES';w(sep.outputs['Mesh'],prox.inputs['Geometry']);w(pos,prox.inputs['Sample Position']);d=prox.outputs['Distance'];vox=one(g,'flesh_voxel_mm').outputs[0]
 cut=math('LESS_THAN',sample.outputs[0],math('MULTIPLY',vox,.8));eligible=math('MULTIPLY',math('SUBTRACT',1.,cut),math('LESS_THAN',d,vox))
 geo=one(g,'Tissue only remesh').outputs['Mesh']
 for name,typ,value in [('sl_pre_recess_position','FLOAT_VECTOR',pos),('sl_pre_recess_normal','FLOAT_VECTOR',normal),('sl_cutter_signed_mm','FLOAT',sample.outputs[0]),('sl_edge_distance_mm','FLOAT',d),('sl_cut_point','BOOLEAN',cut),('sl_outer_recess_point','BOOLEAN',eligible)]:geo=st(geo,name,typ,'POINT',value)
 # Face provenance is an explicit point-to-face adaptation of the pre-move cut mask.
 face=next(n for n in g.nodes if n.type=='STORE_NAMED_ATTRIBUTE' and n.label=='sl_cut_face');w(geo,face.inputs['Geometry']);w(at('sl_cut_point','BOOLEAN'),face.inputs['Value'])
 move=one(g,'Recess external tissue beneath original skin');w(at('sl_outer_recess_point','BOOLEAN'),move.inputs['Selection'])
 # Existing .20 mm recession magnitude, no extra tangent correction or parameter sweep.
 vec=one(g,'Inward offset');w(at('sl_pre_recess_normal','FLOAT_VECTOR'),vec.inputs[0]);w(math('MULTIPLY',one(g,'flesh_recess_mm').outputs[0],-1.),vec.inputs['Scale']);prune(g)
 # Keep exact existing inverse map and final pre-cell references. Remove old optional correction.
 ig=flesh.modifiers[-1].node_group;inp=next(n for n in ig.nodes if n.type=='GROUP_INPUT');rest=one(ig,'sl_rest_position');oldedge=one(ig,'sl_edge_distance_mm');ref=one(ig,'sl_reference_position');connect(ig,inp.outputs[0],rest.inputs['Geometry']);connect(ig,rest.outputs['Geometry'],ref.inputs['Geometry']);prune(ig);ig.name='SL Interface | verified inverse rest and final pre-cell references';del root['interface_gain']
 for group in (g,ig):
  for i,n in enumerate(group.nodes):n.location=((i//7)*220,-(i%7)*180)
 bpy.context.scene['scope']='Independent signed cutter and pre-recess uncut SDF reference; split skin; no weld or visual acceptance';bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()),compress=True)
 r={'source_sha':PIN,'scene_sha':sha(out),'helper_git_sha':HELPER,'cap_point_threshold_voxels':.8,'outer_reference_limit_voxels':1.,'existing_recess_mm':root['flesh_recess_mm'],'sample_interpolation':str(sample.inputs['Interpolation'].default_value),'groups':{x.name:len(x.nodes) for x in (sg,g,ig)},'anchor_digest':root['anchor_digest'],'stock_key':root['neutral_stock_key']};out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print('BUILT',json.dumps(r),flush=True)
if __name__=='__main__':main()

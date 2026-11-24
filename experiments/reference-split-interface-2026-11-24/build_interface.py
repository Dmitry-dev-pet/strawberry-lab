"""Original interface registration and inverse rest-coordinate experiment, ARTIST mm.
No author node graph, numerical presets, or assets. Preserve exact original skin.
"""
import sys,json,math,hashlib
from pathlib import Path
import bpy
PIN='6c614f51d9879589d8c57efbf1cb48cbd3dffb7d96b273d5c14e6c2ecdd6f839'
SPLIT_SHA='1fd07748a0bc668b81715d037e3ee5db8b6cad20'
def gitsha(path):
 b=Path(path).read_bytes();return hashlib.sha1(('blob %d\0'%len(b)).encode()+b).hexdigest()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def install(split):
 from build_split import Graph,ROOT,SOURCE,FLESH,CUTTER
 root=bpy.data.objects[ROOT];source=bpy.data.objects[SOURCE];flesh=bpy.data.objects[FLESH]
 # Keep the actual deformed mesh alongside the named grid, without rebuilding the skin.
 sg=source.modifiers[-1].node_group;inp=next(n for n in sg.nodes if n.type=='GROUP_INPUT');out=next(n for n in sg.nodes if n.type=='GROUP_OUTPUT');prior=out.inputs[0].links[0].from_socket
 j=sg.nodes.new('GeometryNodeJoinGeometry');j.label='Reference envelope and existing volume';j.location=(650,-300);sg.links.new(prior,j.inputs['Geometry']);sg.links.new(inp.outputs[0],j.inputs['Geometry']);sg.links.new(j.outputs[0],out.inputs[0])
 root['interface_gain']=0.;root.id_properties_ui('interface_gain').update(min=0.,max=1.,description='Research only: bounded near-rim tissue registration; 0 original geometry')
 g=Graph('SL Interface | rim registration and inverse rest',root);N=g.g.nodes
 def vec(op,a,b=None):
  n=g.node('ShaderNodeVectorMath',op);n.operation=op;g.w(a,n.inputs[0]);
  if b is not None:g.w(b,n.inputs['Scale'] if op=='SCALE' else n.inputs[1])
  return n.outputs['Value' if op in ('DOT_PRODUCT','DISTANCE','LENGTH') else 'Vector']
 def remap(x,lo,hi,a,b):
  n=g.node('ShaderNodeMapRange','Smooth bounded transition');n.clamp=True;n.interpolation_type='SMOOTHERSTEP';g.w(x,n.inputs['Value']);g.w(lo,n.inputs['From Min']);g.w(hi,n.inputs['From Max']);g.w(a,n.inputs['To Min']);g.w(b,n.inputs['To Max']);return n.outputs['Result']
 pos=g.node('GeometryNodeInputPosition','Physical tissue position').outputs[0];normal=g.node('GeometryNodeInputNormal','Surface normal').outputs[0]
 hull=g.info(source).outputs['Geometry'];cutter=g.info(bpy.data.objects[CUTTER]).outputs['Geometry'];hs=g.prox(hull);cs=g.prox(cutter)
 def sample_normal(geo,label):
  n=g.node('GeometryNodeSampleNearestSurface',label);n.data_type='FLOAT_VECTOR';g.w(geo,n.inputs['Mesh']);g.w(normal,n.inputs['Value']);g.w(pos,n.inputs['Sample Position']);return vec('NORMALIZE',n.outputs['Value'])
 hn=sample_normal(hull,'Envelope normal');cn=sample_normal(cutter,'Actual cutter normal')
 signed=vec('DOT_PRODUCT',vec('SUBTRACT',pos,hs.outputs['Position']),hn)
 tangent=vec('SUBTRACT',hn,vec('SCALE',cn,vec('DOT_PRODUCT',hn,cn)));direction=vec('NORMALIZE',tangent)
 projection=g.math('MAXIMUM',vec('DOT_PRODUCT',direction,hn),.45)
 # Signed radial registration towards a small overlap in the local tangent plane.
 # This is an independent approximation, not topological stitching.
 request=g.math('DIVIDE',g.math('SUBTRACT',.035,signed),projection)
 bounded=g.math('MINIMUM',g.math('MAXIMUM',request,-.20),.20)
 fade=g.math('MULTIPLY',remap(hs.outputs['Distance'],.10,.60,1.,0.),remap(cs.outputs['Distance'],.06,.38,1.,0.))
 amount=g.math('MULTIPLY',g.math('MULTIPLY',bounded,fade),g.driven('interface_gain'))
 # Save actual pre-offset diagnostic value; not re-evaluated on displaced geometry.
 geo=g.store(g.input,'sl_interface_offset_mm','FLOAT','POINT',amount)
 move=g.node('GeometryNodeSetPosition','Bounded near-rim tangential registration');g.w(geo,move.inputs['Geometry']);g.w(vec('SCALE',direction,g.attr('sl_interface_offset_mm','FLOAT')),move.inputs['Offset']);geo=move.outputs[0]
 # Map final pre-cell surface back to neutral rest using analytic inverse of our own map.
 # The map version is explicitly bound to the earlier neutral stock contract, not Frucht.
 xyz=g.node('ShaderNodeSeparateXYZ','Final physical position');g.w(pos,xyz.inputs[0]);x,y,z=(xyz.outputs[k] for k in ('X','Y','Z'));a,b,h=(g.driven(k) for k in ('shape_a','shape_b','shape_h'))
 zr=g.math('DIVIDE',z,h);t=g.math('SUBTRACT',g.math('MULTIPLY',zr,2/48.),1.)
 def bell(c,w):
  u=g.math('DIVIDE',g.math('SUBTRACT',t,c),w);return g.math('POWER',math.e,g.math('MULTIPLY',g.math('MULTIPLY',u,u),-1.))
 r=g.math('ADD',1.,g.math('ADD',g.math('MULTIPLY',a,bell(.5,.36)),g.math('MULTIPLY',b,bell(-.3,.4))))
 comb=g.node('ShaderNodeCombineXYZ','Independent analytic inverse map');g.w(g.math('DIVIDE',x,r),comb.inputs['X']);g.w(g.math('DIVIDE',y,r),comb.inputs['Y']);g.w(zr,comb.inputs['Z']);geo=g.store(geo,'sl_rest_position','FLOAT_VECTOR','POINT',comb.outputs[0])
 geo=g.store(geo,'sl_edge_distance_mm','FLOAT','POINT',hs.outputs['Distance']);geo=g.store(geo,'sl_reference_position','FLOAT_VECTOR','POINT',pos);geo=g.store(geo,'sl_reference_normal','FLOAT_VECTOR','POINT',normal)
 nodes=g.finish(flesh,geo)
 return dict(nodes=nodes,source_join=True,interface_gain_default=0.,map_version=root['shape_map_version'],anchor_digest=root['anchor_digest'])
if __name__=='__main__':
 src,split,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)==PIN and gitsha(split)==SPLIT_SHA and not out.exists();sys.path.insert(0,str(split.parent));bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False);r=install(split);bpy.context.scene['scope']='Split-interface research: gain 0 original geometry; inverse rest and bounded optional registration; not stitched';bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True);r.update(source_sha=PIN,scene_sha=sha(out),split_builder_git_sha=SPLIT_SHA);out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print('BUILT',json.dumps(r),flush=True)

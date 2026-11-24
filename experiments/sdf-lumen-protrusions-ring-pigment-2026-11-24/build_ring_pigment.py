"""Original diagnostic using the owned ring-relative atlas channel, no author code.
Changes only storage of an additional sampled field and the cap's Base Color.
All coefficients are ARTIST; no measured anatomy or color claim.
"""
import bpy,sys,hashlib,json
from pathlib import Path
PIN='0498a4bb9daf0fbdb15630a052539283e89f117bbe074c2b8762868ba0deb1b0'
BODY='Receptacle | canonical PR29 hull';CAP='SDF | inherited 150^3 tissue + own multiscale wetness';P='SL Ring Pigment | '
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def install():
 b=bpy.data.objects[BODY];g=next(m.node_group for m in b.modifiers if m.type=='NODES' and m.node_group.name.startswith('SL Cell Surface'))
 sample=g.nodes['Owned trilinear core and halo'];sg=sample.node_tree;N,L=sg.nodes,sg.links
 split=sorted((n for n in N if n.bl_idname=='FunctionNodeSeparateColor'),key=lambda n:n.name);assert len(split)==2
 out=next(n for n in N if n.bl_idname=='NodeGroupOutput')
 # Read the already-existing interpolation weights from the R-channel links.
 sumR=out.inputs['core'].links[0].from_node;terms=[x.links[0].from_node for x in sumR.inputs[:2]];assert all(x.operation=='MULTIPLY' for x in terms)
 weights=[]
 for i,t in enumerate(terms):
  assert t.inputs[0].links[0].from_node==split[i]
  weights.append(t.inputs[1].links[0].from_socket)
 sg.interface.new_socket(name='ring_relative',in_out='OUTPUT',socket_type='NodeSocketFloat')
 def math(op,a,b):
  n=N.new('ShaderNodeMath');n.name=P+op;n.operation=op;L.new(a,n.inputs[0]);L.new(b,n.inputs[1]);return n.outputs[0]
 L.new(math('ADD',math('MULTIPLY',split[0].outputs['Blue'],weights[0]),math('MULTIPLY',split[1].outputs['Blue'],weights[1])),out.inputs['ring_relative'])
 # Preserve all pre-existing geometry paths and values. Store B at the same
 # evaluation stage as R/G on the conformingly refined point geometry.
 N,L=g.nodes,g.links;old=N['sl_vascular_halo'];consumers=[l.to_socket for l in old.outputs['Geometry'].links];assert consumers
 st=N.new('GeometryNodeStoreNamedAttribute');st.name=P+'store';st.domain='POINT';st.data_type='FLOAT';st.inputs['Name'].default_value='sl_ring_relative';L.new(old.outputs['Geometry'],st.inputs['Geometry']);L.new(sample.outputs['ring_relative'],st.inputs['Value'])
 for sock in consumers:L.new(st.outputs['Geometry'],sock)
 mg=bpy.data.materials[CAP].node_tree;N,L=mg.nodes,mg.links;bs=next(n for n in N if n.type=='BSDF_PRINCIPLED');old=bs.inputs['Base Color'].links[0].from_socket
 def n(t,s):q=N.new(t);q.name=q.label=P+s;return q
 def w(a,s):
  if isinstance(a,(float,int,tuple)):s.default_value=a
  else:L.new(a,s)
 def attr(s):q=n('ShaderNodeAttribute',s);q.attribute_name=s;q.attribute_type='GEOMETRY';return q.outputs['Fac']
 def m(op,a,b,s):q=n('ShaderNodeMath',s);q.operation=op;w(a,q.inputs[0]);w(b,q.inputs[1]);return q.outputs[0]
 def mapv(a,lo,hi,x,y,s):
  q=n('ShaderNodeMapRange',s);q.interpolation_type='SMOOTHERSTEP';q.clamp=True;w(a,q.inputs['Value']);q.inputs['From Min'].default_value=lo;q.inputs['From Max'].default_value=hi;q.inputs['To Min'].default_value=x;q.inputs['To Max'].default_value=y;return q.outputs['Result']
 def mix(f,a,b,s):q=n('ShaderNodeMixRGB',s);q.blend_type='MIX';w(f,q.inputs[0]);w(a,q.inputs[1]);w(b,q.inputs[2]);return q.outputs[0]
 r=attr('sl_ring_relative');d=attr('sl_cell_dome');k=attr('sl_vascular_cell_multiplier');core=attr('sl_vascular_core');halo=attr('sl_vascular_halo')
 # Signed coordinate of the OWN ring, 0.5 on nominal ring. Continuous warm
 # inner zone transitions to red cortex; avoid hard white vascular outlines.
 outer=mapv(r,.36,.65,0.,1.,'Ring-relative regional transition')
 valley=mix(outer,(.57,.115,.073,1.),(.35,.019,.011,1.),'Regional valley palette')
 top=mix(outer,(.72,.235,.157,1.),(.57,.061,.032,1.),'Regional cell palette')
 cell=mapv(m('MULTIPLY',d,k,'Suppressed cell dome'),0.,.8,0.,1.,'Cell response')
 color=mix(cell,valley,top,'Pigment aligned to actual cells')
 h=mapv(halo,.12,.65,0.,.14,'Soft vascular tint')
 color=mix(h,color,(.62,.16,.095,1.),'Halo blend')
 c=mapv(core,.22,.72,0.,.12,'Subordinate core tint')
 color=mix(c,color,(.68,.21,.135,1.),'Core blend')
 color=mix(.20,color,old,'Retain atlas context');gain=n('ShaderNodeValue','A/B gain');gain.outputs[0].default_value=1.;L.new(mix(gain.outputs[0],old,color,'Diagnostic output'),bs.inputs['Base Color'])
 return {'new_shader_nodes':sum(n.name.startswith(P) for n in N),'source_atlas_fraction':.2,'only_shader_socket':'cap Base Color','ring_attribute':'sl_ring_relative','blue_channel_reuses_original_sampler_weights':True}
if __name__=='__main__':
 src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)==PIN and not out.exists();bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False);r=install();bpy.ops.wm.save_as_mainfile(filepath=str(out));r.update(source_sha=PIN,scene_sha=sha(out));out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)

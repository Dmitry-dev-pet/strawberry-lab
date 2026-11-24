"""Independent ARTIST spatial skin gloss hypothesis; original geometry preserved."""
import bpy,sys,hashlib,json
from pathlib import Path
PIN='790dc4adbd9025b56e7833c2cedb8ada83c0e9b738ac294f96889fbb52e0e215'
SKIN='SDF | source skin at true rest_position'
PREFIX='SL Skin Optics | '
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def install(mat):
 g=mat.node_tree;N,L=g.nodes,g.links;bs=N['Principled BSDF'];orig=bs.inputs['Roughness'].links[0].from_socket
 assert orig.node.name=='Color Ramp.003' and abs(bs.inputs['Coat Weight'].default_value-.13)<1e-6
 assert N['Attribute'].attribute_name=='achene_pit' and N['Map Range'].label=='Warm shoulder fade'
 assert not bs.inputs['Coat Weight'].is_linked
 def node(typ,name):
  x=N.new(typ);x.name=x.label=PREFIX+name;return x
 def wire(x,s):
  if isinstance(x,(float,int)):s.default_value=x
  else:L.new(x,s)
 def math(op,a,b,name):
  n=node('ShaderNodeMath',name);n.operation=op;wire(a,n.inputs[0]);wire(b,n.inputs[1]);return n.outputs[0]
 def remap(v,a,b,c,d,name):
  n=node('ShaderNodeMapRange',name);n.clamp=True;n.interpolation_type='SMOOTHERSTEP';wire(v,n.inputs['Value']);n.inputs['From Min'].default_value=a;n.inputs['From Max'].default_value=b;n.inputs['To Min'].default_value=c;n.inputs['To Max'].default_value=d;return n.outputs['Result']
 # One bounded hypothesis: varying gloss spatially rather than uniformly coating fruit.
 p=remap(N['Attribute'].outputs['Factor'],.08,.7,0.,1.,'Existing pit suppression mask')
 c=math('DIVIDE',N['Map Range'].outputs['Result'],.60,'Normalize existing shoulder fade')
 dry=math('MAXIMUM',p,c,'Dry / recess mask')
 noise=N['Noise Texture.001'].outputs['Fac']
 # Fine original cuticle noise; broader gloss modulation from existing ripening noise.
 broad=N['Noise Texture'].outputs['Fac']
 patch=remap(broad,.25,.75,.055,.225,'Spatially varied coat')
 suppress=math('SUBTRACT',1.,math('MULTIPLY',dry,.93,'Suppress at pit and shoulder'),'Remaining coat fraction')
 coat=math('MULTIPLY',patch,suppress,'Localized coat weight')
 increase=math('MULTIPLY',dry,.14,'Local roughness increase')
 rough=math('ADD',orig,increase,'Existing roughness plus dry region')
 # Live native 0/1 optical A/B; 0 recovers existing inputs exactly.
 gain=node('ShaderNodeValue','A/B gain');gain.outputs[0].default_value=1.
 def blend(a,b,name):
  d=math('SUBTRACT',b,a,name+' delta');v=math('MULTIPLY',d,gain.outputs[0],name+' weighted');return math('ADD',a,v,name+' final')
 L.new(blend(orig,rough,'Roughness'),bs.inputs['Roughness']);L.new(blend(.13,coat,'Coat Weight'),bs.inputs['Coat Weight'])
 for i,n in enumerate(x for x in N if x.name.startswith(PREFIX)):n.location=(700+(i//6)*210,-(i%6)*170)
 return len([x for x in N if x.name.startswith(PREFIX)])
if __name__=='__main__':
 src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)==PIN and not out.exists();bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False);n=install(bpy.data.materials[SKIN]);bpy.ops.wm.save_as_mainfile(filepath=str(out));out.with_suffix('.json').write_text(json.dumps({'source_sha':PIN,'scene_sha':sha(out),'new_nodes':n,'changed_sockets':['Roughness','Coat Weight'],'artist':True,'skin_material':SKIN},indent=2)+'\n');print('NEW NODES',n,flush=True)

"""Own rest-space pigment diagnostic, on the PR50 shadow-only baseline.
No Frucht nodes, code or palette imported. ARTIST coefficients; no histology claim.
Only cap Base Color is rewired. Old atlas is retained as gain=0 and a 12% context blend.
"""
import bpy,sys,json,hashlib
from pathlib import Path
PIN='361696819fd44733d560e3f59b101cd11f59862e7ebd7b7f83ce94fd07909963'
CAP='SDF | inherited 150^3 tissue + own multiscale wetness'; PREFIX='SL Pigment | '
PALETTE={'valley':(.38,.013,.009,1.),'dome':(.61,.052,.029,1.),'halo':(.67,.19,.105,1.),'core':(.72,.31,.20,1.),'pith':(.78,.42,.27,1.)}
def install():
 g=bpy.data.materials[CAP].node_tree; N,L=g.nodes,g.links; bs=next(n for n in N if n.type=='BSDF_PRINCIPLED'); target=bs.inputs['Base Color'];old=target.links[0].from_socket
 def n(t,s):
  a=N.new(t);a.name=a.label=PREFIX+s;return a
 def w(a,b):
  if isinstance(a,(int,float,tuple)):b.default_value=a
  else:L.new(a,b)
 def m(op,a,b,s):
  q=n('ShaderNodeMath',s);q.operation=op;w(a,q.inputs[0]);w(b,q.inputs[1]);return q.outputs[0]
 def attr(name,output='Fac'):
  q=n('ShaderNodeAttribute',name);q.attribute_name=name;q.attribute_type='GEOMETRY';return q.outputs[output]
 def remap(x,l,h,a,b,s):
  q=n('ShaderNodeMapRange',s);q.interpolation_type='SMOOTHERSTEP';q.clamp=True;w(x,q.inputs['Value']);q.inputs['From Min'].default_value=l;q.inputs['From Max'].default_value=h;q.inputs['To Min'].default_value=a;q.inputs['To Max'].default_value=b;return q.outputs['Result']
 def mix(f,a,b,s):
  q=n('ShaderNodeMixRGB',s);q.blend_type='MIX';w(f,q.inputs[0]);w(a,q.inputs[1]);w(b,q.inputs[2]);return q.outputs[0]
 dome=attr('sl_cell_dome');mult=attr('sl_vascular_cell_multiplier');core=attr('sl_vascular_core');halo=attr('sl_vascular_halo');rest=attr('sdf_rest_position','Vector')
 eff=m('MULTIPLY',dome,mult,'Actual suppressed cell dome');cell=remap(eff,0.,.85,0.,1.,'Cell interior pigment')
 col=mix(cell,PALETTE['valley'],PALETTE['dome'],'Cortex, same cells as relief')
 # Soft, subordinate vascular tint, not hard white spokes or detached tubes.
 hw=remap(halo,.10,.65,0.,.28,'Broad vascular halo weight');col=mix(hw,col,PALETTE['halo'],'Warm halo tint')
 cw=remap(core,.19,.72,0.,.32,'Narrow vascular core weight');col=mix(cw,col,PALETTE['core'],'Subtle core tint')
 # Independent ARTIST axial region, not a biological measurement: narrow smooth
 # spindle whose radius tapers at the ends. Existing R/H are not renamed as pith.
 xy=n('ShaderNodeVectorMath','Axis projection');xy.operation='MULTIPLY';w(rest,xy.inputs[0]);xy.inputs[1].default_value=(1.,1.,0.)
 rad=n('ShaderNodeVectorMath','Rest radius');rad.operation='LENGTH';w(xy.outputs['Vector'],rad.inputs[0]);z=n('ShaderNodeSeparateXYZ','Axial position');w(rest,z.inputs[0])
 dz=m('SUBTRACT',z.outputs['Z'],.02,'Axial centre offset');sq=m('MULTIPLY',dz,dz,'Squared axial distance');expo=m('MULTIPLY',sq,-1.6,'Spindle falloff exponent');taper=m('POWER',2.718281828459045,expo,'Smooth axial taper');radius=m('ADD',.055,m('MULTIPLY',taper,.125,'Spindle width'),'Pith radius BU');relative=m('DIVIDE',rad.outputs['Value'],radius,'Radius relative to spindle');pw=remap(relative,.40,1.40,.90,0.,'Reddish pith weight');col=mix(pw,col,PALETTE['pith'],'Narrow warm axial tissue')
 col=mix(.12,col,old,'Retain minor source atlas variation')
 gain=n('ShaderNodeValue','A/B gain');gain.outputs[0].default_value=1.;col=mix(gain.outputs[0],old,col,'Original or coherent pigment');L.new(col,target)
 for i,q in enumerate(n for n in N if n.name.startswith(PREFIX)):q.location=(-1400+(i//6)*210,-1500-(i%6)*175)
 return {'palette_linear_rgba':PALETTE,'source_input':[old.node.name,old.identifier],'new_nodes':len([n for n in N if n.name.startswith(PREFIX)]),'target':target.name,'source_atlas_fraction':.12,'attributes':['sdf_rest_position','sl_cell_dome','sl_vascular_cell_multiplier','sl_vascular_core','sl_vascular_halo']}
if __name__=='__main__':
 src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert not out.exists() and hashlib.sha256(src.read_bytes()).hexdigest()==PIN
 bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False);assert not bpy.data.objects['SL Juice | independent pool surface'].visible_shadow
 result=install();bpy.ops.wm.save_as_mainfile(filepath=str(out));result['source_sha']=PIN;result['scene_sha']=hashlib.sha256(out.read_bytes()).hexdigest();out.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

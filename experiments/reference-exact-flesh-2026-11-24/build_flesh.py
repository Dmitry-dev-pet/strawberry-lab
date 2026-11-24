"""Original ARTIST Exact cap material experiment. No Frucht code/assets/presets.
A: unchanged diagnostic material; B: shared rest-space pigment; C: B + spatial SSS.
Only the cap shader is changed; in Fast the original BSDF is selected exactly.
"""
import bpy,sys,json,hashlib,time
from pathlib import Path
PIN='d147164be18c2feecd170568b46df698ad3882c48f7f9645fc758d07fd81a0a0'
ROOT='SL Shape Controller | edit Custom Properties'; CAP='SL Split | cut tissue'
# Our uncalibrated sRGB artistic palette. Conversion to scene-linear is explicit.
PALETTE={'inner':'D76559','outer':'BF1825','halo':'E7A08B','core':'EBC2A0','rim':'9E1420'}
SSS_RANGE_MM=(.13,.65); SSS_WEIGHT=.58; SSS_RADIUS=(1.,.43,.24)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def linear(h):
 a=[int(h[i:i+2],16)/255 for i in (0,2,4)];return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in a)+(1.,)
def install():
 root=bpy.data.objects[ROOT]; mat=bpy.data.materials[CAP]; N,L=mat.node_tree.nodes,mat.node_tree.links
 root['flesh_material_mode']=0;root.id_properties_ui('flesh_material_mode').update(min=0,max=2,description='0 diagnostic baseline, 1 rest-space pigment, 2 same pigment + spatial SSS (Exact only)')
 out=next(n for n in N if n.bl_idname=='ShaderNodeOutputMaterial' and n.is_active_output);old=out.inputs['Surface'].links[0].from_socket;assert old.node.bl_idname=='ShaderNodeBsdfPrincipled'
 def node(t,label):n=N.new(t);n.name=n.label='Flesh | '+label;return n
 def w(x,s):
  if isinstance(x,bpy.types.NodeSocket):L.new(x,s)
  else:s.default_value=x
 def m(op,a,b,label):n=node('ShaderNodeMath',label);n.operation=op;w(a,n.inputs[0]);w(b,n.inputs[1]);return n.outputs[0]
 def attr(k,vec=False):n=node('ShaderNodeAttribute',k);n.attribute_type='GEOMETRY';n.attribute_name=k;return n.outputs['Vector' if vec else 'Fac']
 def remap(a,lo,hi,b,c,label):
  n=node('ShaderNodeMapRange',label);n.clamp=True;n.interpolation_type='SMOOTHERSTEP';w(a,n.inputs['Value']);w(lo,n.inputs['From Min']);w(hi,n.inputs['From Max']);w(b,n.inputs['To Min']);w(c,n.inputs['To Max']);return n.outputs['Result']
 def mix(f,a,b,label,op='MIX'):
  n=node('ShaderNodeMixRGB',label);n.blend_type=op;w(f,n.inputs[0]);w(a,n.inputs[1]);w(b,n.inputs[2]);return n.outputs[0]
 def driven(k):
  n=node('ShaderNodeValue',k);n.outputs[0].default_value=root[k];d=n.outputs[0].driver_add('default_value').driver;d.type='AVERAGE';v=d.variables.new();v.name='value';v.type='SINGLE_PROP';v.targets[0].id=root;v.targets[0].data_path='["'+k+'"]';return n.outputs[0]
 mode=driven('flesh_material_mode');exact=driven('exact_mode');enabled=m('MULTIPLY',m('GREATER_THAN',mode,.5,'colour enabled'),m('GREATER_THAN',exact,.5,'Exact only'),'select original for Fast')
 rest=attr('sl_rest_position',True);ring=attr('sl_vascular_ring_relative');core=attr('sl_vascular_core');halo=attr('sl_vascular_halo');dome=attr('sl_cell_dome');edge=attr('sl_edge_distance_mm')
 # Break radial uniformity with a low-frequency rest-space field. Ring position
 # is the common authored 3D atlas channel, not a painted cut-specific mask.
 noise=node('ShaderNodeTexNoise','coarse rest-space pigment variation');noise.noise_dimensions='3D';w(rest,noise.inputs['Vector']);noise.inputs['Scale'].default_value=.24;noise.inputs['Detail'].default_value=2.
 ring_perturbed=m('ADD',ring,m('MULTIPLY',m('SUBTRACT',noise.outputs['Fac'],.5,'centred mottling'),.18,'ring transition variation'),'vary ring transition')
 cortex=remap(ring_perturbed,.29,.74,0.,1.,'gradual inner to outer pigment')
 col=mix(cortex,linear(PALETTE['inner']),linear(PALETTE['outer']),'regional red pigment')
 # Keep vascular whitening restrained and subordinated to the tissue color.
 hmask=remap(halo,.06,.65,0.,.35,'soft vascular halo')
 col=mix(hmask,col,linear(PALETTE['halo']),'halo tint')
 cmask=remap(core,.08,.68,0.,.38,'narrow vascular tissue')
 col=mix(cmask,col,linear(PALETTE['core']),'vascular bundle tint')
 # Existing dome follows the actual geometry; this independent neutral-space
 # grain provides small color variations, not new histological cells.
 fine=node('ShaderNodeTexNoise','fine rest-space pigment grain');fine.noise_dimensions='3D';w(rest,fine.inputs['Vector']);fine.inputs['Scale'].default_value=3.2;fine.inputs['Detail'].default_value=2.
 cellbrightness=m('ADD',remap(dome,0.,1.,.87,1.02,'actual cell relief brightness'),m('MULTIPLY',m('SUBTRACT',fine.outputs['Fac'],.5,'centred fine grain'),.20,'fine variation'),'cell brightness factor')
 col=mix(1.,col,cellbrightness,'modulate cell pigment','MULTIPLY')
 rim=remap(edge,0.,.75,.70,0.,'thin red peripheral tint')
 col=mix(rim,col,linear(PALETTE['rim']),'outer cut rim')
 # Direction-independent radial scattering scale (rest space), separate from
 # pigmentation. Native Principled SSS, with shorter green/blue scatter.
 xy=node('ShaderNodeVectorMath','radial rest coordinates');xy.operation='MULTIPLY';w(rest,xy.inputs[0]);w((1.,1.,0.),xy.inputs[1]);rad=node('ShaderNodeVectorMath','distance from axis');rad.operation='LENGTH';w(xy.outputs['Vector'],rad.inputs[0]);scale=remap(rad.outputs['Value'],1.,14.,*SSS_RANGE_MM,'smaller scattering at axis')
 bs=node('ShaderNodeBsdfPrincipled','fresh pigmented tissue ARTIST');w(col,bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.43;bs.inputs['IOR'].default_value=1.42;bs.inputs['Subsurface Radius'].default_value=SSS_RADIUS
 w(scale,bs.inputs['Subsurface Scale']);w(m('MULTIPLY',m('GREATER_THAN',mode,1.5,'spatial SSS only in mode 2'),SSS_WEIGHT,'scattering weight'),bs.inputs['Subsurface Weight']);bs.inputs['Transmission Weight'].default_value=0.
 selector=node('ShaderNodeMixShader','original diagnostic or new tissue');w(enabled,selector.inputs[0]);w(old,selector.inputs[1]);w(bs.outputs[0],selector.inputs[2]);L.new(selector.outputs[0],out.inputs['Surface'])
 for i,n in enumerate(N):n.location=((i//7)*230,-(i%7)*185)
 root.update_tag();bpy.context.view_layer.update();return {'material':CAP,'palette_srgb':PALETTE,'sss_scale_mm':SSS_RANGE_MM,'sss_weight':SSS_WEIGHT,'sss_radius':SSS_RADIUS,'default_mode':0,'new_nodes':sum(n.name.startswith('Flesh | ') for n in N),'other_materials_unchanged_by_construction':True}
def main():
 src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)==PIN and not out.exists();t=time.perf_counter();bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),use_scripts=False);r=install();bpy.context.scene['scope']='Exact tissue pigment and radial scattering research; frozen geometry and juice; ARTIST';bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()),compress=True);r.update(source_sha=PIN,scene_sha=sha(out),elapsed_seconds=time.perf_counter()-t);out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print('BUILT',json.dumps(r),flush=True)
if __name__=='__main__':main()

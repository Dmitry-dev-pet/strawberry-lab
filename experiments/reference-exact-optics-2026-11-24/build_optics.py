"""Independent A/B/C optical comparison for our own thin Exact juice interfaces.
A: unchanged thin Fresnel/straight transmission. B: refractive dielectric.
C: B plus a normal-gap-dependent exponential tint proxy. All retain the original
transparent-shadow route. No commercial Frucht code, graph, or presets.
"""
import bpy,sys,json,hashlib
from pathlib import Path
PIN='250732d06c5c2cfbc24f531612cda2672755ba8cad50afddd0a2a894553954fb'
ROOT='SL Shape Controller | edit Custom Properties'; JUICE='SL Exact | independent juice pools'; MAT='SL Exact | thin wet interface ARTIST'
REFERENCE_TINT=(.96,.82,.75); REF_MM=.10; MAX_MM=.20

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def install():
 root=bpy.data.objects[ROOT];mat=bpy.data.materials[MAT];assert 'juice_optics_mode' not in root;root['juice_optics_mode']=0;root.id_properties_ui('juice_optics_mode').update(min=0,max=2,description='0 original thin optical interface; 1 refractive dielectric; 2 dielectric + thickness-dependent tint proxy')
 N,L=mat.node_tree.nodes,mat.node_tree.links
 output=next(n for n in N if n.bl_idname=='ShaderNodeOutputMaterial' and n.is_active_output);shadow=output.inputs['Surface'].links[0].from_node;assert shadow.bl_idname=='ShaderNodeMixShader' and shadow.inputs[0].links[0].from_socket.name=='Is Shadow Ray';assert shadow.inputs[2].links[0].from_node.bl_idname=='ShaderNodeBsdfTransparent'
 prior=shadow.inputs[1].links[0].from_socket;assert prior.node.bl_idname=='ShaderNodeMixShader'
 def node(t,label):n=N.new(t);n.name=n.label='Optics | '+label;return n
 def wire(x,s):
  if isinstance(x,bpy.types.NodeSocket):L.new(x,s)
  else:s.default_value=x
 def m(op,a,b,label):n=node('ShaderNodeMath',label);n.operation=op;wire(a,n.inputs[0]);wire(b,n.inputs[1]);return n.outputs[0]
 ctrl=node('ShaderNodeValue','mode 0 / 1 / 2');ctrl.outputs[0].default_value=0.;d=ctrl.outputs[0].driver_add('default_value').driver;d.type='AVERAGE';v=d.variables.new();v.name='value';v.type='SINGLE_PROP';v.targets[0].id=root;v.targets[0].data_path='["juice_optics_mode"]';mode=ctrl.outputs[0]
 attr=node('ShaderNodeAttribute','signed normal clearance in mm');attr.attribute_type='GEOMETRY';attr.attribute_name='sl_juice_clearance_mm'
 positive=m('MAXIMUM',attr.outputs['Fac'],0.,'ignore submerged negative gap');limited=m('MINIMUM',positive,MAX_MM,'bounded positive gap');exponent=m('DIVIDE',limited,REF_MM,'relative optical depth');use_tint=m('GREATER_THAN',mode,1.5,'tint only in mode 2');exponent=m('MULTIPLY',exponent,use_tint,'mode-gated optical depth')
 # Exponential channel attenuation is an artistic normal-gap proxy, not a
 # measurement of ray path through a closed liquid volume.
 rgb=node('ShaderNodeCombineColor','exponential linear-RGB attenuation');rgb.mode='RGB'
 for channel,base in zip(('Red','Green','Blue'),REFERENCE_TINT):wire(m('POWER',base,exponent,'attenuate '+channel),rgb.inputs[channel])
 dielectric=node('ShaderNodeBsdfPrincipled','refractive dielectric');wire(rgb.outputs['Color'],dielectric.inputs['Base Color']);dielectric.inputs['Metallic'].default_value=0.;dielectric.inputs['Roughness'].default_value=.12;dielectric.inputs['IOR'].default_value=1.333;dielectric.inputs['Transmission Weight'].default_value=1.
 select=node('ShaderNodeMixShader','original or dielectric');wire(m('GREATER_THAN',mode,.5,'refraction enabled'),select.inputs[0]);wire(prior,select.inputs[1]);wire(dielectric.outputs[0],select.inputs[2]);L.new(select.outputs[0],shadow.inputs[1]);assert shadow.inputs[2].links[0].from_node.bl_idname=='ShaderNodeBsdfTransparent'
 for i,n in enumerate(N):n.location=((i//5)*240,-(i%5)*180)
 root.update_tag();bpy.context.view_layer.update();return {'new_shader_nodes':sum(n.name.startswith('Optics | ') for n in N),'shader_total_nodes':len(N),'ior':1.333,'roughness':.12,'tint_at_0_10_mm_linear_rgb':REFERENCE_TINT,'max_gap_mm':MAX_MM,'reference_gap_mm':REF_MM,'default_mode':0,'shadow_route_preserved':True}

def main():
 src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)==PIN and not out.exists();bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),use_scripts=False);r=install();bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()),compress=True);r.update(source_sha=PIN,scene_sha=sha(out),scope='Only juice material alternative; open interfaces, ARTIST optical proxy; no geometry changes');out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print('BUILT',json.dumps(r),flush=True)
if __name__=='__main__':main()

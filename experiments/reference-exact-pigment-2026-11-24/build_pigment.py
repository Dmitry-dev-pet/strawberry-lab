"""Original source-informed warm tissue colour architecture. ARTIST, no author graph/presets.
Retain prior material and SSS; separate palette revision, shared skin foundation and grade.
"""
import bpy, sys, json, hashlib, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_flesh import ROOT, CAP, linear
PIN='7443e948ca2dc90e23a891f1262ff0afd68bb501f49c4a3d8f323fcff4f2a173'
WALL='SL Exact | cavity wall ARTIST'
P={'skin_deep':'A52510','skin_ripe':'D43815','skin_shoulder':'E49B55','cortex_deep':'C02B0C','cortex_light':'E24B20','pith':'E5A385','halo':'EFC3A7','bundle':'E9D1B8','grain':'EDAB89','stalk':'E7BD72','edge':'D75A2C'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Graph:
 def __init__(self,g,pre='Pigment v2 | '):self.g=g;self.N=g.nodes;self.L=g.links;self.pre=pre
 def n(self,t,k):n=self.N.new(t);n.name=n.label=self.pre+k;return n
 def w(self,x,s):
  if isinstance(x,bpy.types.NodeSocket):self.L.new(x,s)
  elif s.type=="RGBA" and isinstance(x,(int,float)):s.default_value=(x,x,x,1.)
  else:s.default_value=x
 def m(self,op,a,b,k):n=self.n('ShaderNodeMath',k);n.operation=op;self.w(a,n.inputs[0]);self.w(b,n.inputs[1]);return n.outputs[0]
 def remap(self,a,lo,hi,b,c,k):
  n=self.n('ShaderNodeMapRange',k);n.clamp=True;n.interpolation_type='SMOOTHERSTEP'
  for key,x in [('Value',a),('From Min',lo),('From Max',hi),('To Min',b),('To Max',c)]:self.w(x,n.inputs[key])
  return n.outputs['Result']
 def mix(self,f,a,b,k,op='MIX'):
  n=self.n('ShaderNodeMixRGB',k);n.blend_type=op;self.w(f,n.inputs[0]);self.w(a,n.inputs[1]);self.w(b,n.inputs[2]);return n.outputs[0]
 def xyz(self,v):n=self.n('ShaderNodeSeparateXYZ','rest components');self.w(v,n.inputs[0]);return n.outputs
 def vec(self,op,a,b,k):
  n=self.n('ShaderNodeVectorMath',k);n.operation=op;self.w(a,n.inputs[0]);self.w(b,n.inputs[1]);return n.outputs['Vector']
 def rad(self,v):
  n=self.n('ShaderNodeVectorMath','radial distance');n.operation='LENGTH';self.w(self.vec('MULTIPLY',v,(1.,1.,0.),'XY only'),n.inputs[0]);return n.outputs['Value']
 def noise(self,v,scale,k):n=self.n('ShaderNodeTexNoise',k);n.noise_dimensions='3D';self.w(v,n.inputs['Vector']);n.inputs['Scale'].default_value=scale;n.inputs['Detail'].default_value=2.;return n.outputs['Fac']
 def grp(self,g,k,values):
  n=self.n('ShaderNodeGroup',k);n.node_tree=g
  for name,v in values.items():self.w(v,n.inputs[name])
  return n.outputs[0]
 def attr(self,k,vec=False):n=self.n('ShaderNodeAttribute',k);n.attribute_type='GEOMETRY';n.attribute_name=k;return n.outputs['Vector' if vec else 'Fac']
 def drive(self,r,k):
  n=self.n('ShaderNodeValue',k);n.outputs[0].default_value=r[k];d=n.outputs[0].driver_add('default_value').driver;d.type='AVERAGE';v=d.variables.new();v.name='value';v.type='SINGLE_PROP';v.targets[0].id=r;v.targets[0].data_path='["'+k+'"]';return n.outputs[0]
 def layout(self):
  for i,n in enumerate(self.N):n.location=((i//8)*240,-(i%8)*185)
def group(name,ins):
 g=bpy.data.node_groups.new(name,'ShaderNodeTree');g.interface.new_socket(name='Color',in_out='OUTPUT',socket_type='NodeSocketColor')
 for k,t in ins:g.interface.new_socket(name=k,in_out='INPUT',socket_type=t)
 q=Graph(g);a=q.n('NodeGroupInput','Inputs');o=q.n('NodeGroupOutput','Output');return q,a.outputs,o.inputs['Color']
def C(k):return linear(P[k])
def skin_foundation():
 q,i,o=group('SL Pigment | shared warm skin foundation v2',[('Rest','NodeSocketVector')]);r=i['Rest'];z=q.xyz(r)['Z'];macro=q.noise(r,.16,'large ripeness variation');fine=q.noise(r,1.9,'pigment speckles')
 c=q.mix(q.remap(macro,.22,.80,0.,1.,'ripe patch weight'),C('skin_deep'),C('skin_ripe'),'ripe red patches');shoulder=q.remap(z,40.,48.,0.,.65,'lighter stem shoulder');c=q.mix(shoulder,c,C('skin_shoulder'),'stem colour');c=q.mix(1.,c,q.remap(fine,.1,.9,.85,1.10,'fine pigment variation'),'speckle multiplier','MULTIPLY');q.w(c,o);q.layout();return q.g
def pigment(skin):
 ins=[('Rest','NodeSocketVector')]+[(k,'NodeSocketFloat') for k in ('Ring','Core','Halo','Dome','Edge')];q,i,o=group('SL Pigment | regional tissue v2',ins);r=i['Rest'];z=q.xyz(r)['Z'];rad=q.rad(r);cloud=q.noise(r,.17,'low-frequency tissue clouds');grain=q.noise(r,2.7,'fine intercell pigment grain');streak=q.noise(q.vec('MULTIPLY',r,(1.,1.,.55),'elongated field'),.45,'nonuniform vascular whitening')
 # Spatially variable pith-to-cortex transition. Reduce paleness and whiteness near tip.
 ring=q.m('ADD',i['Ring'],q.m('MULTIPLY',q.m('SUBTRACT',cloud,.5,'centred cloud'),.38,'irregular transition'),'modulated ring');outer=q.remap(ring,.23,.60,0.,1.,'radial cortex')
 tip=q.remap(z,2.,19.,.18,1.,'less white toward tip');pith=q.m('MULTIPLY',q.m('SUBTRACT',1.,outer,'inside ring'),tip,'axial pith')
 cortex=q.mix(q.remap(cloud,.21,.82,0.,1.,'cortex mottling'),C('cortex_deep'),C('cortex_light'),'warm red cortex');col=q.mix(pith,cortex,C('pith'),'pith and cortex')
 variation=q.remap(streak,.18,.82,.30,.92,'local vessel intensity');white=q.m('MULTIPLY',tip,variation,'tip and strand variation');halo=q.m('MULTIPLY',q.remap(i['Halo'],.10,.70,0.,.22,'soft halo'),white,'local halo');core=q.m('MULTIPLY',q.remap(i['Core'],.14,.74,0.,.47,'bundle core'),white,'local bundle');col=q.mix(halo,col,C('halo'),'diffuse halo');col=q.mix(core,col,C('bundle'),'vessel bundle')
 brightness=q.m('ADD',q.remap(i['Dome'],0.,1.,.81,1.11,'actual cell variation'),q.m('MULTIPLY',q.m('SUBTRACT',grain,.5,'centred grain'),.32,'small pigment contrast'),'cell grain brightness');col=q.mix(1.,col,brightness,'cell pigment multiplier','MULTIPLY');flecks=q.m('MULTIPLY',q.remap(grain,.62,.88,0.,.19,'rare warm grains'),tip,'grain reduced at tip');col=q.mix(flecks,col,C('grain'),'subtle warm grains')
 # A localized artistic shoulder wedge. Different thresholds at different radii.
 threshold=q.m('ADD',36.5,q.m('MULTIPLY',rad,.33,'wedge radial taper'),'wedge start');span=q.m('ADD',threshold,8.,'wedge end');wedge=q.remap(z,threshold,span,0.,.28,'stalk wedge');col=q.mix(wedge,col,C('stalk'),'yellow stalk transition')
 # Reusable skin colour sampled at the same rest coordinate, not a second fixed red.
 skincol=q.grp(skin,'same skin pigment',{'Rest':r});col=q.mix(q.remap(i['Edge'],0.,1.8,.80,0.,'broad skin transition'),col,skincol,'skin pigment near cut rim');col=q.mix(q.remap(i['Edge'],0.,.27,.34,0.,'fine edge transition'),col,C('edge'),'narrow warm edge')
 # Selective colour grading in linear shader space; original independent coefficients.
 sep=q.n('ShaderNodeSeparateColor','saturation of regional pigment');sep.mode='HSV';q.w(col,sep.inputs['Color']);sat=q.remap(sep.outputs[1],.14,.76,.87,1.08,'retain pale tissue');h=q.n('ShaderNodeHueSaturation','regional colour correction');q.w(col,h.inputs['Color']);q.w(sat,h.inputs['Saturation']);h.inputs['Value'].default_value=.89;h.inputs['Hue'].default_value=.5
 col=q.mix(1.,h.outputs[0],q.remap(i['Edge'],0.,.20,1.13,1.,'light at cut edge'),'edge brightness','MULTIPLY');q.w(col,o);q.layout();return q.g
def global_grade(root):
 q,i,o=group('SL Pigment | fruit-wide colour grade',[('Color','NodeSocketColor')]);h=q.n('ShaderNodeHueSaturation','global grade');q.w(i['Color'],h.inputs['Color']);q.w(q.m('ADD',.5,q.m('DIVIDE',q.drive(root,'fruit_hue_degrees'),360.,'hue turns'),'neutral hue'),h.inputs['Hue']);q.w(q.drive(root,'fruit_saturation'),h.inputs['Saturation']);q.w(q.drive(root,'fruit_brightness'),h.inputs['Value']);q.w(h.outputs[0],o);q.layout();return q.g
def tissue_input(q,pg,wall=False):
 names={'Rest':q.attr('sl_rest_position',True),'Ring':q.attr('sl_vascular_ring_relative'),'Core':q.attr('sl_vascular_core'),'Halo':q.attr('sl_vascular_halo'),'Dome':q.attr('sl_cell_dome'),'Edge':q.attr('sl_edge_distance_mm')}
 # Interior walls aren't cut edges, even if an attribute is shared.
 if wall:names['Edge']=50.
 return q.grp(pg,'shared tissue pigment',names)
def install():
 r=bpy.data.objects[ROOT];r['pigment_revision']=0;r.id_properties_ui('pigment_revision').update(min=0,max=1,description='0 previous tissue pigment, 1 regional warm tissue v2; Exact and coloured mode only')
 for k,v,lo,hi in [('fruit_hue_degrees',0.,-45.,45.),('fruit_saturation',1.,.4,1.5),('fruit_brightness',1.,.5,1.5)]:r[k]=v;r.id_properties_ui(k).update(min=lo,max=hi)
 skin=skin_foundation();pg=pigment(skin);grade=global_grade(r)
 cap=bpy.data.materials[CAP];q=Graph(cap.node_tree);bs=q.N['Flesh | fresh pigmented tissue ARTIST'];prior=bs.inputs['Base Color'].links[0].from_socket;new=q.grp(grade,'apply shared grade',{'Color':tissue_input(q,pg)})
 enabled=q.m('GREATER_THAN',q.drive(r,'pigment_revision'),.5,'revision selected');q.w(q.mix(enabled,prior,new,'previous or revised tissue pigment'),bs.inputs['Base Color']);q.layout()
 wall=bpy.data.materials[WALL];q=Graph(wall.node_tree);o=next(n for n in q.N if n.type=='OUTPUT_MATERIAL' and n.is_active_output);prior=o.inputs['Surface'].links[0].from_socket;col=q.grp(grade,'apply shared grade',{'Color':tissue_input(q,pg,True)});col=q.mix(1.,col,.68,'darker moist cavity wall','MULTIPLY');bs=q.n('ShaderNodeBsdfPrincipled','wet cavity tissue');q.w(col,bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.34;bs.inputs['IOR'].default_value=1.42;bs.inputs['Subsurface Weight'].default_value=.35;bs.inputs['Subsurface Scale'].default_value=.20;bs.inputs['Subsurface Radius'].default_value=(1.,.43,.24)
 flag=q.m('MULTIPLY',q.m('GREATER_THAN',q.drive(r,'pigment_revision'),.5,'revision enabled'),q.m('MULTIPLY',q.m('GREATER_THAN',q.drive(r,'flesh_material_mode'),.5,'flesh colour enabled'),q.m('GREATER_THAN',q.drive(r,'exact_mode'),.5,'Exact only'),'coloured Exact'),'new wall only in revised Exact');mix=q.n('ShaderNodeMixShader','old or revised cavity wall');q.w(flag,mix.inputs[0]);q.w(prior,mix.inputs[1]);q.w(bs.outputs[0],mix.inputs[2]);q.w(mix.outputs[0],o.inputs['Surface']);q.layout()
 r.update_tag();bpy.context.view_layer.update();return {'palette_srgb_ARTIST':P,'new_groups':{g.name:len(g.nodes) for g in (skin,pg,grade)},'default_pigment_revision':0,'default_global_grade':[0.,1.,1.],'scope':'cap color and cavity wall only; shared future skin foundation; existing cap SSS fixed; no source presets copied'}
def main():
 src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)==PIN and not out.exists();t=time.perf_counter();bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),use_scripts=False);r=install();bpy.context.scene['scope']='Warm regional pigment v2; original ARTIST; frozen geometry and cap SSS';bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()),compress=True);r.update(source_sha=PIN,scene_sha=sha(out),elapsed_seconds=time.perf_counter()-t);out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print('BUILT',json.dumps(r),flush=True)
if __name__=='__main__':main()

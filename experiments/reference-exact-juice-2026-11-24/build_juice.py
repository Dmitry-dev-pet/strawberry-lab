"""Independent optical pool surfaces on current Exact. Reuses owned earlier pool principle.
No author code or assets. Artist thin reflective interfaces, not fluid simulation.
"""
import bpy,sys,json,hashlib,time
from pathlib import Path
PIN='0868e656bc1d4c68c1a0f2b555bb5443f5f2527e34ca8bab0e55a1ae9d656e67'
EXACT='SL Exact | common labelled body'; ROOT='SL Shape Controller | edit Custom Properties'; JUICE='SL Exact | independent juice pools'; MAT='SL Exact | thin wet interface ARTIST'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def install():
 s=bpy.context.scene;body=bpy.data.objects[EXACT];root=bpy.data.objects[ROOT]
 assert abs(s.unit_settings.scale_length-.001)<1e-8
 # Deliberately no second refracting medium or volume absorption through tissue.
 # A thin optical surface reflects using a water-like Fresnel; transmits without
 # bending. Shadow rays pass through. This is an artist approximation.
 mat=bpy.data.materials.new(MAT);mat.use_nodes=True;mat.diffuse_color=(.9,.91,.92,.45)
 n,l=mat.node_tree.nodes,mat.node_tree.links;n.clear()
 tr=n.new('ShaderNodeBsdfTransparent');tr.inputs['Color'].default_value=(1,1,1,1)
 gl=n.new('ShaderNodeBsdfAnisotropic');gl.inputs['Color'].default_value=(1,1,1,1);gl.inputs['Roughness'].default_value=.12
 fr=n.new('ShaderNodeFresnel');fr.inputs['IOR'].default_value=1.333
 mix=n.new('ShaderNodeMixShader');l.new(fr.outputs[0],mix.inputs[0]);l.new(tr.outputs[0],mix.inputs[1]);l.new(gl.outputs[0],mix.inputs[2])
 lp=n.new('ShaderNodeLightPath');shadow=n.new('ShaderNodeMixShader');l.new(lp.outputs['Is Shadow Ray'],shadow.inputs[0]);l.new(mix.outputs[0],shadow.inputs[1]);l.new(tr.outputs[0],shadow.inputs[2]);out=n.new('ShaderNodeOutputMaterial');l.new(shadow.outputs[0],out.inputs['Surface'])
 for i,q in enumerate(n):q.location=((i//3)*200,-(i%3)*180)
 obj=bpy.data.objects.new(JUICE,bpy.data.meshes.new('SL Exact juice empty source'));s.collection.objects.link(obj)
 root['juice_gain']=0.;root.id_properties_ui('juice_gain').update(min=0.,max=1.,description='0: no separate liquid; 1: artistic rest-space optical pools on Exact cuts with tissue relief')
 g=bpy.data.node_groups.new('SL Exact | native rest-space liquid pools','GeometryNodeTree')
 for d in ('INPUT','OUTPUT'):g.interface.new_socket(name='Geometry',in_out=d,socket_type='NodeSocketGeometry')
 N,L=g.nodes,g.links
 def node(typ,label):q=N.new(typ);q.name=q.label=label;return q
 def w(a,b):
  if isinstance(a,bpy.types.NodeSocket):L.new(a,b)
  else:b.default_value=a
 def m(op,a,b,label):q=node('ShaderNodeMath',label);q.operation=op;w(a,q.inputs[0]);w(b,q.inputs[1]);return q.outputs[0]
 def v(op,a,b=None,label=None):
  q=node('ShaderNodeVectorMath',label or op);q.operation=op;w(a,q.inputs[0]);
  if b is not None:w(b,q.inputs['Scale'] if op=='SCALE' else q.inputs[1])
  return q.outputs['Value' if op in ('DOT_PRODUCT','LENGTH','DISTANCE') else 'Vector']
 def attr(k,t='FLOAT'):q=node('GeometryNodeInputNamedAttribute','Read '+k);q.data_type=t;q.inputs['Name'].default_value=k;return q.outputs['Attribute']
 def store(geo,k,x,t='FLOAT',domain='POINT'):
  q=node('GeometryNodeStoreNamedAttribute',k);q.data_type=t;q.domain=domain;q.inputs['Name'].default_value=k;w(geo,q.inputs['Geometry']);w(x,q.inputs['Value']);return q.outputs['Geometry']
 def remap(x,lo,hi,a,b,label):
  q=node('ShaderNodeMapRange',label);q.clamp=True;q.interpolation_type='SMOOTHERSTEP';w(x,q.inputs['Value']);w(lo,q.inputs['From Min']);w(hi,q.inputs['From Max']);w(a,q.inputs['To Min']);w(b,q.inputs['To Max']);return q.outputs['Result']
 def drive(k):
  q=node('ShaderNodeValue','Control '+k);q.outputs[0].default_value=root[k];d=q.outputs[0].driver_add('default_value').driver;d.type='AVERAGE';va=d.variables.new();va.name='value';va.type='SINGLE_PROP';va.targets[0].id=root;va.targets[0].data_path='["'+k+'"]';return q.outputs[0]
 inp=node('NodeGroupInput','Empty source');out=node('NodeGroupOutput','Liquid only');gain=drive('juice_gain');cells=drive('tissue_gain');exact=drive('exact_mode');mode=drive('split_mode')
 info=node('GeometryNodeObjectInfo','Read actual refined Exact');info.transform_space='RELATIVE';info.inputs['Object'].default_value=body
 pos=node('GeometryNodeInputPosition','Actual tissue position').outputs[0];base=attr('sl_reference_position','FLOAT_VECTOR');normal=v('NORMALIZE',attr('sl_reference_normal','FLOAT_VECTOR'));rest=attr('sl_rest_position','FLOAT_VECTOR')
 # Native domains explicitly stored: no cap/wall/skin collar is selected.
 tagged=store(info.outputs['Geometry'],'sl_juice_pure_vertex_weight',attr('sl_cell_interior','BOOLEAN'))
 cap=attr('sl_cut_face','BOOLEAN');pure=m('GREATER_THAN',attr('sl_juice_pure_vertex_weight'),.999999,'All corners pure cap')
 sep=node('GeometryNodeSeparateGeometry','Cap versus protected skin and cavity');sep.domain='FACE';w(tagged,sep.inputs['Geometry']);w(cap,sep.inputs['Selection'])
 pr=node('GeometryNodeProximity','Distance to protected geometry');pr.target_element='FACES';w(sep.outputs['Inverted'],pr.inputs['Geometry']);w(base,pr.inputs['Sample Position']);dist=pr.outputs['Distance']
 edge=remap(dist,.60,1.45,0.,1.,'Avoid both skin and cavity walls')
 # Store distance and pure mask while full body is still present. Native face selection
 # uses this original point-domain tag, not a recalculated incidence on isolated patches.
 geo=store(tagged,'sl_juice_protected_distance_mm',dist)
 geo=store(geo,'sl_juice_edge_fade',edge)
 # Independent original three smooth pool scales. Work in mm (not old normalised units).
 noise=node('ShaderNodeTexNoise','Neutral spatial warp');noise.noise_dimensions='3D';w(rest,noise.inputs['Vector']);noise.inputs['Scale'].default_value=.22;noise.inputs['Detail'].default_value=2.
 warp=v('SCALE',v('SUBTRACT',noise.outputs['Color'],(.5,.5,.5)),.60,'Neutral gentle warp mm');coords=v('MULTIPLY',v('ADD',rest,warp),(1.,1.,.78),'Longitudinal pool variation')
 lobes=[]
 for i,(freq,weight,radius,shift) in enumerate([(.48,1.,.53,(.4,1.6,.7)),(.92,.78,.44,(1.3,.5,1.9)),(1.65,.52,.36,(.7,2.1,.3))]):
  vor=node('ShaderNodeTexVoronoi',f'Pool {i+1} smooth centres');vor.voronoi_dimensions='3D';vor.feature='SMOOTH_F1';w(v('ADD',coords,shift),vor.inputs['Vector']);vor.inputs['Scale'].default_value=freq;vor.inputs['Smoothness'].default_value=.24
  lobes.append(m('MULTIPLY',remap(vor.outputs['Distance'],.13,radius,1.,0.,f'Pool {i+1} envelope'),weight,f'Pool {i+1} weight'))
 env=m('MAXIMUM',m('MAXIMUM',lobes[0],lobes[1],'Combined coarse pools'),lobes[2],'All scales')
 rad=v('LENGTH',v('MULTIPLY',rest,(1.,1.,0.)));radial=remap(rad,2.,12.,.45,1.,'Reduced wetness near centre')
 env=m('MULTIPLY',m('MULTIPLY',env,attr('sl_juice_edge_fade'),'Protected edge fade'),radial,'Radial envelope')
 geo=store(geo,'sl_juice_envelope',env);env=attr('sl_juice_envelope')
 # Liquid height relative to the smooth pre-relief surface, with tissue crests exposed.
 level=m('SUBTRACT',m('MULTIPLY',m('MULTIPLY',env,remap(noise.outputs['Fac'],.24,.76,.11,.19,'ARTIST pool level mm'),'Envelope level'),gain,'Gain'),.025,'Submerged rim mm')
 geo=store(geo,'sl_juice_tissue_position',pos,'FLOAT_VECTOR');geo=store(geo,'sl_juice_level_mm',level)
 # Only original cap faces with all pure corners, and local wetness support.
 support=m('MULTIPLY',m('GREATER_THAN',env,.09,'Pool support'),m('GREATER_THAN',attr('sl_juice_edge_fade'),.20,'Exclude collar'),'Wet interior')
 select=m('MULTIPLY',m('MULTIPLY',cap,pure,'Only pure cap'),support,'Select pools')
 patch=node('GeometryNodeSeparateGeometry','Extract patches');patch.domain='FACE';w(geo,patch.inputs['Geometry']);w(select,patch.inputs['Selection'])
 nei=node('GeometryNodeInputMeshVertexNeighbors','Open-patch edge incidence');boundary=m('LESS_THAN',nei.outputs['Face Count'],nei.outputs['Vertex Count'],'Boundary vertices')
 height=v('DOT_PRODUCT',v('SUBTRACT',attr('sl_juice_tissue_position','FLOAT_VECTOR'),base),normal,'Actual tissue height mm');old=attr('sl_juice_level_mm');buried=m('MINIMUM',old,m('SUBTRACT',height,.018,'Buried patch edge mm'),'Edge below tissue')
 sw=node('GeometryNodeSwitch','Tuck only open border');sw.input_type='FLOAT';w(boundary,sw.inputs['Switch']);w(old,sw.inputs['False']);w(buried,sw.inputs['True'])
 geo=store(patch.outputs['Selection'],'sl_juice_final_level_mm',sw.outputs['Output']);geo=store(geo,'sl_juice_clearance_mm',m('SUBTRACT',attr('sl_juice_final_level_mm'),height,'Clearance mm'))
 move=node('GeometryNodeSetPosition','Smooth reference plus liquid height');w(geo,move.inputs['Geometry']);w(v('ADD',base,v('SCALE',normal,attr('sl_juice_final_level_mm'))),move.inputs['Position'])
 sm=node('GeometryNodeSetShadeSmooth','Smooth pool surface');sm.domain='FACE';w(move.outputs['Geometry'],sm.inputs['Geometry']);matn=node('GeometryNodeSetMaterial','Thin reflection material');matn.inputs['Material'].default_value=mat;w(sm.outputs['Geometry'],matn.inputs['Geometry'])
 enable=m('MULTIPLY',m('GREATER_THAN',gain,1e-6,'Juice on'),m('MULTIPLY',m('GREATER_THAN',exact,.5,'Exact on'),m('MULTIPLY',m('GREATER_THAN',mode,.5,'Cut on'),m('GREATER_THAN',cells,1e-6,'Tissue active'),'Cut and tissue'),'Exact cut and tissue'),'Enabled')
 sw=node('GeometryNodeSwitch','Disabled/whole/Fast empty');sw.input_type='GEOMETRY';w(enable,sw.inputs['Switch']);w(inp.outputs[0],sw.inputs['False']);w(matn.outputs['Geometry'],sw.inputs['True']);w(sw.outputs[0],out.inputs[0])
 for i,q in enumerate(N):q.location=((i//10)*220,-(i%10)*180)
 mod=obj.modifiers.new('SL Exact | separate optical pools','NODES');mod.node_group=g
 s['scope']='Research: independent Exact juice pools, thin reflection/straight transmission; diagnostic materials; no fluid simulation';root['juice_gain']=0.;root.update_tag();bpy.context.view_layer.update();return g

def main():
 src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)==PIN and not out.exists();start=time.perf_counter();bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),use_scripts=False);g=install();bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()),compress=True)
 r={'source_sha':PIN,'scene_sha':sha(out),'juice_nodes':len(g.nodes),'default_gain':0,'scope':'Separate Exact cut optical interfaces, original source body unmodified; ARTIST','elapsed_seconds':time.perf_counter()-start};out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print('BUILT',json.dumps(r),flush=True)
if __name__=='__main__':main()

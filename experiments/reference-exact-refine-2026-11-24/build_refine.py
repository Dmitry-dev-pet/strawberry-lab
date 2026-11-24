"""Independent native cap-local adaptive face-centre refinement, no author code.
Only selected cap faces are replaced by conforming triangle fans, no original edge
is split. Re-evaluate existing inverse/rest, edge distance, tissue field downstream.
"""
import bpy,sys,json,hashlib,time
from pathlib import Path
PIN='bbf897fd885725951e75e5ca4eda0301cbf38c0f1bd31a9f375f3d7ce58c72a8'
EXACT='SL Exact | common labelled body';ROOT='SL Shape Controller | edit Custom Properties'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)==PIN and not out.exists();t=time.perf_counter();bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),use_scripts=False)
 root=bpy.data.objects[ROOT];body=bpy.data.objects[EXACT];g=body.modifiers[1].node_group;N,L=g.nodes,g.links
 root['cap_refine_level']=0;root.id_properties_ui('cap_refine_level').update(min=0,max=2,description='0: baseline; 1/2: cap-only area-adaptive centroid subdivision passes')
 root['cap_refine_area_mm2']=.03;root.id_properties_ui('cap_refine_area_mm2').update(min=.005,max=.20,description='ARTIST maximum selected face area in square millimetres; boundary collar excluded')
 def node(t,label):q=N.new(t);q.label=q.name='Cap refine | '+label;return q
 def wire(a,b):
  if isinstance(a,bpy.types.NodeSocket):L.new(a,b)
  else:b.default_value=a
 def math(op,a,b,label):q=node('ShaderNodeMath',label);q.operation=op;wire(a,q.inputs[0]);wire(b,q.inputs[1]);return q.outputs[0]
 def attr(k,kind):q=node('GeometryNodeInputNamedAttribute',k);q.data_type=kind;q.inputs['Name'].default_value=k;return q.outputs['Attribute']
 def store(geo,k,domain,v,label):q=node('GeometryNodeStoreNamedAttribute',label);q.data_type='FLOAT';q.domain=domain;q.inputs['Name'].default_value=k;wire(geo,q.inputs['Geometry']);wire(v,q.inputs['Value']);return q.outputs['Geometry']
 def drive(k):
  q=node('ShaderNodeValue',k);q.outputs[0].default_value=root[k];d=q.outputs[0].driver_add('default_value').driver;d.type='AVERAGE';v=d.variables.new();v.name='value';v.type='SINGLE_PROP';v.targets[0].id=root;v.targets[0].data_path='["'+k+'"]';return q.outputs[0]
 level=drive('cap_refine_level');area_limit=drive('cap_refine_area_mm2');cap=attr('sl_cut_face','BOOLEAN')
 target=next(q for q in N if q.label=='achene_pit' and q.bl_idname=='GeometryNodeStoreNamedAttribute');assert len(target.inputs['Geometry'].links)==1;prior=target.inputs['Geometry'].links[0].from_socket;assert prior.node.label=='Lumen | separate diagnostic cavity wall';start=len(N)
 # Evaluate cap incidence explicitly on POINT then on FACE. The near-boundary
 # collar is left unrefined, and no original edge is ever split.
 def refine(geo,step):
  tagged=store(geo,'sl_refine_face_cap','FACE',cap,f'{step} float cap face mask');a=attr('sl_refine_face_cap','FLOAT');pure=math('GREATER_THAN',a,.999999,f'{step} exclusively cap vertices')
  tagged=store(tagged,'sl_refine_pure_vertex','POINT',pure,f'{step} float pure vertex mask');face=attr('sl_refine_pure_vertex','FLOAT');allpure=math('GREATER_THAN',face,.999999,f'{step} all vertices inside cap')
  area=node('GeometryNodeInputMeshFaceArea',f'{step} current face area').outputs['Area'];big=math('GREATER_THAN',area,area_limit,f'{step} area above limit')
  eligible=math('MULTIPLY',cap,math('MULTIPLY',allpure,big,f'{step} pure and large'),f'{step} only cut faces');active=math('GREATER_THAN',level,step-.5,f'{step} enabled')
  # Zero offset individual extrusion: each selected face is replaced by top +
  # sides. Collapse each individual top face to its own arithmetic centre,
  # then merge ONLY connected duplicated top vertices. The top face vanishes;
  # side faces become oriented triangles. No weld of original geometry.
  e=node('GeometryNodeExtrudeMesh',f'{step} individual face extrusion');e.mode='FACES';e.inputs['Individual'].default_value=True;e.inputs['Offset Scale'].default_value=0.;wire(tagged,e.inputs['Mesh']);wire(eligible,e.inputs['Selection'])
  s=node('GeometryNodeScaleElements',f'{step} collapse top to face centroid');s.domain='FACE';s.inputs['Scale'].default_value=0.;wire(e.outputs['Mesh'],s.inputs['Geometry']);wire(e.outputs['Top'],s.inputs['Selection'])
  m=node('GeometryNodeMergeByDistance',f'{step} merge duplicate top vertices only');m.inputs['Mode'].default_value='Connected';m.inputs['Distance'].default_value=1e-6;wire(s.outputs['Geometry'],m.inputs['Geometry']);wire(e.outputs['Top'],m.inputs['Selection'])
  sw=node('GeometryNodeSwitch',f'{step} exact bypass');sw.input_type='GEOMETRY';wire(active,sw.inputs['Switch']);wire(geo,sw.inputs['False']);wire(m.outputs['Geometry'],sw.inputs['True']);return sw.outputs[0]
 result=refine(refine(prior,1),2);L.new(result,target.inputs['Geometry'])
 for i,q in enumerate(N):q.location=((i//9)*220,-(i%9)*180)
 root['cap_refine_algorithm']='Original conforming adaptive face-centre triangle fans, no edge splitting; area threshold; pure cap collar';bpy.context.scene['scope']='Research Exact cap-only local area refinement; original skin/cavity/seed and Fast paths unchanged; visual pending';root['exact_mode']=0;root['split_mode']=0;root['tissue_gain']=0.;root.update_tag();bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()),compress=True)
 r={'source_sha':PIN,'scene_sha':sha(out),'nodes_total':len(N),'refinement_nodes':sum(q.label.startswith('Cap refine |') for q in N),'default_level':0,'default_face_area_mm2':.03,'max_passes':2,'algorithm':'area-selected pure cap face-centre fans; preserve every original edge; connected top-only collapse; no global subdivision','scope':'Exact cut path only; ARTIST threshold','elapsed_seconds':time.perf_counter()-t};out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print('BUILT',json.dumps(r),flush=True)
if __name__=='__main__':main()

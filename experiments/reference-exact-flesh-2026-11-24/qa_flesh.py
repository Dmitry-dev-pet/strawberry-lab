"""Saved-scene material-only regression. Independent actual mesh snapshots and driver observations."""
import bpy,sys,json,time,numpy as np
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE/'deps')]
from build_flesh import ROOT,CAP,PIN,sha,SSS_RANGE_MM
from qa_juice import load,update,snapshot,juicecheck,mesh_eval,attr,snap
EXACT='SL Exact | common labelled body'
JUICE='SL Exact | independent juice pools'
JKEYS=['sl_juice_clearance_mm','sl_reference_position','sl_reference_normal','sl_rest_position','sl_juice_tissue_position','sl_juice_final_level_mm']
def juice_snapshot():return snap(JUICE,JKEYS)
def value(x):
 if isinstance(x,(int,float,bool,str)):return x
 try:return list(x)
 except TypeError:return str(x)
def tree_inventory(m,original_only=False):
 g=m.node_tree;nodes={n.name:{'type':n.bl_idname,'inputs':[(s.identifier,value(s.default_value)) for s in n.inputs if hasattr(s,'default_value')],'outputs':[(s.identifier,value(s.default_value)) for s in n.outputs if hasattr(s,'default_value')],'attribute':getattr(n,'attribute_name',None),'operation':getattr(n,'operation',None)} for n in g.nodes if not original_only or not n.name.startswith('Flesh | ')}
 links=sorted((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in g.links if l.from_node.name in nodes and l.to_node.name in nodes)
 return {'nodes':nodes,'links':links}
def main():
 base,new,pose,out=sys.argv[sys.argv.index('--')+1:];out=Path(out);assert not out.exists() and sha(base)==PIN and sha(new)==json.loads(Path(new).with_suffix('.json').read_text())['scene_sha'];t=time.perf_counter()
 r=load(base,pose,.32);update(r,juice_gain=1.,juice_optics_mode=2);orig=snapshot();j=juice_snapshot();assert (j['faces']==0)==(pose=='whole')
 old={m.name:tree_inventory(m) for m in bpy.data.materials if m.node_tree};stock=tuple(r[k] for k in ('anchor_digest','neutral_stock_key','sl_vascular_dependency_key'))
 r=load(new,pose,.32);update(r,juice_gain=1.,juice_optics_mode=2);assert stock==tuple(r[k] for k in ('anchor_digest','neutral_stock_key','sl_vascular_dependency_key'));m=bpy.data.materials[CAP];N=m.node_tree.nodes
 assert {q.name:tree_inventory(q) for q in bpy.data.materials if q.node_tree and q.name!=CAP}=={k:v for k,v in old.items() if k!=CAP};prior=tree_inventory(m,True);assert prior['nodes']==old[CAP]['nodes'];assert len(old[CAP]['links'])==1 and not prior['links']
 selector=N['Flesh | original diagnostic or new tissue'];assert selector.inputs[1].links[0].from_node.name=='Principled BSDF';assert selector.inputs[2].links[0].from_node.name=='Flesh | fresh pigmented tissue ARTIST';assert selector.inputs[0].links[0].from_node.name=='Flesh | select original for Fast'
 rows=[]
 for mode in (0,2):
  update(r,flesh_material_mode=mode);assert snapshot()==orig and juice_snapshot()==j;g=m.node_tree.evaluated_get(bpy.context.evaluated_depsgraph_get());actual=g.nodes['Flesh | flesh_material_mode'].outputs[0].default_value;ex=g.nodes['Flesh | exact_mode'].outputs[0].default_value;assert abs(actual-mode)<1e-6 and ex==1.;rows.append({'mode':mode,'evaluated_driver':actual,'geometry_and_juice_equal':True})
 field={}
 if pose!='whole':
  e,me=mesh_eval(EXACT);mask=attr(me,'sl_cell_interior');rest=attr(me,'sl_rest_position')[mask].astype(float);assert len(rest)>0
  for k in ('sl_vascular_core','sl_vascular_halo','sl_vascular_ring_relative','sl_cell_dome','sl_edge_distance_mm'):
   a=attr(me,k)[mask];assert np.isfinite(a).all();field[k]=[float(a.min()),float(a.max())]
  x=np.clip((np.linalg.norm(rest[:,:2],axis=1)-1.)/13.,0,1);y=x**3*(x*(6*x-15)+10);scale=SSS_RANGE_MM[0]+(SSS_RANGE_MM[1]-SSS_RANGE_MM[0])*y;field['independent_sss_scale_mm']=[float(scale.min()),float(scale.max())];assert np.isfinite(scale).all();e.to_mesh_clear()
 # Compare Fast at both settings, including the actual driver feeding the bypass.
 update(r,exact_mode=0,flesh_material_mode=2);assert juice_snapshot()['faces']==0;g=m.node_tree.evaluated_get(bpy.context.evaluated_depsgraph_get());assert g.nodes['Flesh | exact_mode'].outputs[0].default_value==0.
 report={'pose':pose,'source_sha':PIN,'scene_sha':sha(new),'mode_checks':rows,'other_material_graphs_equal':True,'original_cap_nodes_equal':True,'fast_bypass_driver_verified':True,'field_ranges':field,'field_scope':'named mesh attributes and independent SSS formula, not per-pixel shader socket sampling','gate':True,'elapsed_seconds':time.perf_counter()-t};out.write_text(json.dumps(report,indent=2)+'\n');print('RESULT',json.dumps(report),flush=True)
if __name__=='__main__':main()

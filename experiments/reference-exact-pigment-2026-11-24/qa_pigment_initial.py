"""Reopen pinned and revised scenes. Geometry, inputs, driver and SSS invariants."""
import bpy,sys,json,time,numpy as np
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent/'deps')]
from build_pigment import PIN,ROOT,CAP,WALL,sha
from qa_juice import load,update,snapshot,mesh_eval,attr,snap,JUICE
from qa_flesh import tree_inventory
JKEYS=['sl_juice_clearance_mm','sl_reference_position','sl_reference_normal','sl_rest_position','sl_juice_tissue_position','sl_juice_final_level_mm']
EXACT='SL Exact | common labelled body'

def state(p,pose):
 r=load(p,pose,.32);update(r,juice_gain=1.,juice_optics_mode=2,flesh_material_mode=2);return r

def main():
 base,new,pose,out=sys.argv[sys.argv.index('--')+1:];out=Path(out);assert not out.exists() and sha(base)==PIN and sha(new)==json.loads(Path(new).with_suffix('.json').read_text())['scene_sha'];t=time.perf_counter()
 r=state(base,pose);a=snapshot();j=snap(JUICE,JKEYS);old={m.name:tree_inventory(m) for m in bpy.data.materials if m.node_tree};stock=tuple(r[k] for k in ('anchor_digest','neutral_stock_key','sl_vascular_dependency_key'))
 r=state(new,pose);assert stock==tuple(r[k] for k in ('anchor_digest','neutral_stock_key','sl_vascular_dependency_key'));m=bpy.data.materials[CAP];w=bpy.data.materials[WALL]
 assert {q.name:tree_inventory(q) for q in bpy.data.materials if q.node_tree and q.name not in (CAP,WALL)}=={k:v for k,v in old.items() if k not in (CAP,WALL)}
 for mat in (m,w):
  newtree=tree_inventory(mat);on=old[mat.name]['nodes'];nn=newtree['nodes'];assert all(nn[k]==v for k,v in on.items());links=[l for l in newtree['links'] if l[0] in on and l[2] in on];removed=set(old[mat.name]['links'])-set(links);assert len(removed)==1 and not (set(links)-set(old[mat.name]['links']));assert next(iter(removed))[3] in ('Base Color','Surface')
 assert m.node_tree.nodes['Flesh | fresh pigmented tissue ARTIST'].inputs['Base Color'].links[0].from_node.name=='Pigment v2 | previous or revised tissue pigment'
 assert bpy.data.node_groups['SL Pigment | regional tissue v2'].nodes['Pigment v2 | same skin pigment'].node_tree.name=='SL Pigment | shared warm skin foundation v2'
 for mat in (m,w):assert mat.node_tree.nodes['Pigment v2 | shared tissue pigment'].node_tree.name=='SL Pigment | regional tissue v2'
 rows=[]
 for rev in (0,1):
  update(r,pigment_revision=rev);assert snapshot()==a and snap(JUICE,JKEYS)==j;g=m.node_tree.evaluated_get(bpy.context.evaluated_depsgraph_get());actual=g.nodes['Pigment v2 | pigment_revision'].outputs[0].default_value;assert abs(actual-rev)<1e-6;rows.append({'revision':rev,'actual_driver':actual,'geometry_and_juice_equal':True})
 # Verify grade driver path separately, not claim optical measurement.
 gg=bpy.data.node_groups['SL Pigment | fruit-wide colour grade'];update(r,fruit_hue_degrees=10.,fruit_saturation=.8,fruit_brightness=.9);eg=gg.evaluated_get(bpy.context.evaluated_depsgraph_get());vals={k:eg.nodes['Pigment v2 | '+k].outputs[0].default_value for k in ('fruit_hue_degrees','fruit_saturation','fruit_brightness')};assert all(abs(vals[k]-r[k])<1e-6 for k in vals);update(r,fruit_hue_degrees=0.,fruit_saturation=1.,fruit_brightness=1.)
 # Independent check of axial modulation sampled on the actual rest-space cap.
 axial={}
 if pose!='whole':
  e,me=mesh_eval(EXACT);pure=attr(me,'sl_cell_interior');rest=attr(me,'sl_rest_position')[pure];z=rest[:,2].astype(float);t0=np.clip((z-2.)/17.,0,1);tip=.18+.82*t0**3*(t0*(6*t0-15)+10);axial={'tip_factor_range':[float(tip.min()),float(tip.max())],'rest_z_mm_range':[float(z.min()),float(z.max())],'samples':len(z)};assert np.isfinite(tip).all();e.to_mesh_clear()
 update(r,exact_mode=0);dg=bpy.context.evaluated_depsgraph_get();assert m.node_tree.evaluated_get(dg).nodes['Flesh | exact_mode'].outputs[0].default_value==0.;assert w.node_tree.evaluated_get(dg).nodes['Pigment v2 | exact_mode'].outputs[0].default_value==0.;assert snap(JUICE,JKEYS)['faces']==0
 result={'pose':pose,'source_sha':PIN,'scene_sha':sha(new),'revision_checks':rows,'old_material_nodes_and_sss_preserved':True,'other_materials_equal':True,'shared_tissue_and_skin_foundation_verified':True,'grade_driver_values':vals,'axial_field':axial,'fast_bypass_driver_verified':True,'gate':True,'elapsed_seconds':time.perf_counter()-t};out.write_text(json.dumps(result,indent=2)+'\n');print('RESULT',json.dumps(result),flush=True)
if __name__=='__main__':main()

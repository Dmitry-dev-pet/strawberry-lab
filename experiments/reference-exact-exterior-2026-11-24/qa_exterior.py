"""Independent saved-scene material-only gate; compares actual geometry and seed-local attrs."""
import bpy,sys,json,time,numpy as np
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path[:0]=[str(H),str(H/'deps')]
from build_exterior import PIN,ROOT,SKIN,SEED,SEED_OBJ,FOUNDATION,GRADE,FIELDS,sha,digest,attr
from qa_juice import load,update,snapshot,snap,JUICE,mesh_eval
from qa_flesh import tree_inventory
JKEYS=['sl_juice_clearance_mm','sl_reference_position','sl_reference_normal','sl_rest_position','sl_juice_tissue_position','sl_juice_final_level_mm']
def state(p,pose):
 r=load(p,pose,.32);update(r,juice_gain=1.,juice_optics_mode=2,flesh_material_mode=2,pigment_revision=1);return r
def main():
 old,new,pose,out=sys.argv[sys.argv.index('--')+1:];out=Path(out);rec=json.loads(Path(new).with_suffix('.json').read_text());assert sha(old)==PIN and sha(new)==rec['scene_sha'] and not out.exists();t=time.perf_counter();r=state(old,pose);orig=snapshot();j=snap(JUICE,JKEYS);graphs={m.name:tree_inventory(m) for m in bpy.data.materials if m.node_tree};keys=tuple(r[k] for k in ('anchor_digest','neutral_stock_key','sl_vascular_dependency_key'));groups=set(bpy.data.node_groups.keys());print('BASE',pose,flush=True)
 r=state(new,pose);assert keys==tuple(r[k] for k in ('anchor_digest','neutral_stock_key','sl_vascular_dependency_key')) and set(bpy.data.node_groups.keys())==groups
 for m in bpy.data.materials:
  if not m.node_tree:continue
  a=graphs[m.name];b=tree_inventory(m)
  if m.name not in (SKIN,SEED):assert a==b;continue
  assert all(b['nodes'][k]==v for k,v in a['nodes'].items());assert len(a['links'])==1 and not [l for l in b['links'] if l[0] in a['nodes'] and l[2] in a['nodes']];assert m.node_tree.nodes['Exterior | old or exterior'].inputs[1].links[0].from_node.name=='Principled BSDF'
  if m.name==SKIN:
   assert m.node_tree.nodes['Exterior | same pigment as flesh rim'].node_tree==bpy.data.node_groups[FOUNDATION];assert m.node_tree.nodes['Exterior | fruit-wide grade'].node_tree==bpy.data.node_groups[GRADE]
 stock=json.loads((H/'deps/stock264.json').read_text());raw=bpy.data.objects[SEED_OBJ].data;rawrest=attr(raw,'sl_rest_position');rawid=attr(raw,'sl_anchor_index');rawfields={k:attr(raw,k) for k in FIELDS};assert {k:digest(v) for k,v in rawfields.items()}==rec['attribute_sha'];assert digest(rawrest)==stock['objects'][SEED_OBJ]['rest_sha']
 # Independently recover each prototype local point from verified anchor basis and seating.
 err=0.;identities=[]
 for row in stock['anchor_rows']:
  i=row['index'];a=row['anchor'];mask=rawid==i;centre=np.array(row['seat_mm'])+.19*a['thickness_mm']*np.array(a['normal']);d=rawrest[mask].astype(float)-centre;expected=np.column_stack([d@np.array(a['side_axis'])/a['width_mm'],d@np.array(a['long_axis'])/a['length_mm'],d@np.array(a['normal'])/a['thickness_mm']]);err=max(err,float(np.max(abs(expected-rawfields[FIELDS[0]][mask]))));identities.append(float(rawfields[FIELDS[1]][mask][0]));assert np.ptp(rawfields[FIELDS[1]][mask])==0
 assert err<1e-6 and len(set(identities))==264
 modes=(0,1) if pose=='whole' else (1,);rows=[]
 for mode in modes:
  update(r,exterior_material_mode=mode);assert snapshot()==orig and snap(JUICE,JKEYS)==j
  dg=bpy.context.evaluated_depsgraph_get();vals={m:bpy.data.materials[m].node_tree.evaluated_get(dg).nodes['Exterior | exterior_material_mode'].outputs[0].default_value for m in (SKIN,SEED)};assert all(abs(v-mode)<1e-6 for v in vals.values())
  ev,me=mesh_eval(SEED_OBJ);ids=attr(me,'sl_anchor_index');rst=attr(me,'sl_rest_position');af={k:attr(me,k) for k in FIELDS};n=0
  for i in np.unique(ids):
   a=rawid==i;b=ids==i;assert a.sum()==b.sum();assert np.array_equal(rawrest[a],rst[b]);assert all(np.array_equal(rawfields[k][a],af[k][b]) for k in FIELDS);n+=1
  ev.to_mesh_clear();rows.append({'mode':mode,'geometry_equal':True,'seed_attribute_roundtrip_equal':True,'retained_seeds':n,'driver_values':vals});print('MODE',rows[-1],flush=True)
 result={'pose':pose,'source_sha':PIN,'scene_sha':rec['scene_sha'],'checks':rows,'seed_local_max_error':err,'other_materials_equal':True,'original_exterior_nodes_preserved':True,'shared_skin_foundation_and_grade_verified':True,'gate':True,'elapsed_seconds':time.perf_counter()-t};out.write_text(json.dumps(result,indent=2)+'\n');print('RESULT',json.dumps(result),flush=True)
if __name__=='__main__':main()

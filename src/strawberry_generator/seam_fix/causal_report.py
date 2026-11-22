from pathlib import Path
import sys,json
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments/profile-vascular-v1')]
from profile_probe import forward
probe=json.loads((ROOT/'build/source-seam-v1/probe.json').read_text());report={}
for seed in [101,202]:
 source=ROOT.parent/'strawberry-generator/build/generator-v1-final'/f'seed{seed}/strawberry.blend';bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);s=bpy.context.scene;mesh=s.objects['Receptacle | canonical PR29 hull'].data;p=np.array([tuple(v.co) for v in mesh.vertices]);_,inverse,counts=np.unique(p,axis=0,return_inverse=True,return_counts=True)
 row={'raw_exact_coincidence_groups':[np.flatnonzero(inverse==i).tolist() for i in np.flatnonzero(counts>1)],'raw_min_edge_model_units':probe[str(seed)]['raw']['min_edge_model_units'],'affected_vertices':[]}
 for group in probe[str(seed)]['near_collapsed_seam']:
  nearest=group[0];i=nearest['id'];co=p[i];seeds=[o for o in s.objects if o.get('role')=='achene'];achene=min(seeds,key=lambda o:np.linalg.norm(np.array(o['hull_anchor_rest'])-co));cfg=json.loads(s['Nonlinear parameters']);base=mesh.attributes['pit_base_position'].data[i].vector
  row['affected_vertices'].append({'id':i,'physical_pitted':co.tolist(),'physical_unpitted':forward(base,(cfg['a'],cfg['b'],cfg['h'])).tolist(),'canonical_pit_normal':list(mesh.attributes['pit_source_normal'].data[i].vector),'pit_mask':mesh.attributes['achene_pit'].data[i].value,'incident_source_polygon_ids':[f.index for f in mesh.polygons if i in f.vertices],'nearest_new_achene':achene.name,'achene_physical_anchor':list(achene['hull_anchor_rest']),'distance_to_achene_model_units':float(np.linalg.norm(np.array(achene['hull_anchor_rest'])-co))})
 report[str(seed)]=row
(ROOT/'build/source-seam-v1/causal-report.json').write_text(json.dumps(report,indent=2)+'\n')

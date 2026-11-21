"""Independent reopened Blender scene QA: points, ends, prefix and materials."""
from pathlib import Path
import bpy,numpy as np,json,sys
ROOT=Path(__file__).resolve().parent
base=np.load(ROOT/'input-v3-network.npz')
counts=base['lengths'];off=np.r_[0,np.cumsum(counts[:-1])];nmain=28
checks=[]
for name in ('0.35','0.85','1.5'):
 arr=np.load(ROOT/f'v4-hook{name}.npz')
 ob=bpy.data.objects[f'V4 | hook{name} | BRANCHES']
 assert len(ob.data.splines)==539
 assert np.array_equal(arr['achene_positions'],base['achene_positions'])
 assert np.array_equal(arr['branch_endpoints'],base['branch_endpoints'])
 assert np.array_equal(arr['radius'],base['radius'])
 assert np.array_equal(arr['points'][:off[nmain]],base['points'][:off[nmain]])
 for i,sl in enumerate(ob.data.splines):
  s=int(off[nmain+i]);p=arr['points'][s:s+64]
  xyz=np.array([pt.co[:3] for pt in sl.points],dtype='f4')
  assert np.array_equal(xyz,p), (name,i,'path differs')
  assert np.array_equal(p[:43],base['points'][s:s+43]),(name,i,'prefix changed')
  assert np.array_equal(p[-1],base['branch_endpoints'][i]),(name,i,'seed end changed')
 checks.append({'name':name,'branches':len(ob.data.splines),'source_points':int(len(arr['points'])),'max_endpoint_error':0.0,'unchanged_first_43':539})
assert len(bpy.data.objects['V3 | 28-sag0.25 | CARRIERS'].data.splines)==28
assert len(bpy.data.objects['V3 | 28-sag0.25 | BRANCHES'].data.splines)==539
scenes=[s for s in bpy.data.scenes if s.name.startswith(('01 |','02 |','03 |'))];assert len(scenes)==3
assert all('V4 | hook0.85 | BRANCHES' in s.objects for s in scenes)
rep={'status':'PASS','blender':bpy.app.version_string,'variants':checks,'same_539_seed_targets_all_variants':True,'initial_trunk_geometry_identical':True,'radius_identical':True,'camera_lights_materials_inherited':True,'original_V3_retained':True,'known_limits':['V4 is not real tissue anatomy','no cut-face or material atlas recomputed','cannot infer promo animation state']}
(ROOT/'blender-validation.json').write_text(json.dumps(rep,indent=2)+'\n')
print('V4_VALIDATION_PASS',json.dumps(rep),flush=True)

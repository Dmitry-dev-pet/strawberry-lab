"""Exact saved geometry and link verification, not visual fidelity claims."""
from pathlib import Path
import bpy,numpy as np,json,sys
root=Path(__file__).resolve().parent
baseline=np.load(root/'input-v2-network.npz')
scene_ids=('01 |','02 |','03 |')
scenes=[s for s in bpy.data.scenes if s.name.startswith(scene_ids)]
assert len(scenes)==3
variants=['28-sag0.25','28-sag1.0','28-sag1.8','14-sag1.0','40-sag1.0']
checks=[]
for name in variants:
    x=np.load(root/f'v3-profile{name}.npz')
    strands=int((x['kind']==0).sum())
    assert np.array_equal(x['achene_positions'],baseline['achene_positions'])
    assert np.array_equal(x['branch_endpoints'],baseline['branch_endpoints'])
    end_indices=np.cumsum(x['lengths'])[strands:]-1
    assert np.array_equal(x['points'][end_indices],baseline['branch_endpoints'])
    for typename,k in [('CARRIERS',strands),('BRANCHES',539)]:
        ob=bpy.data.objects[f'V3 | {name} | {typename}']
        assert ob.type=='CURVE' and len(ob.data.splines)==k
        assert all(ob.name in s.objects for s in scenes)
    ob=bpy.data.objects[f'V3 | {name} | BRANCHES']
    positions=np.array([sp.points[-1].co[:3] for sp in ob.data.splines],dtype='f4')
    error=np.linalg.norm(positions-baseline['branch_endpoints'],axis=1).max()
    assert error==0.0
    checks.append({'name':name,'carriers':strands,'branches':539,'endpoint_max_error':float(error),'points':len(x['points'])})
assert len(bpy.data.objects['V2 | 28 core carriers'].data.splines)==28
assert len(bpy.data.objects['V2 | 539 branches ending at achenes'].data.splines)==539
assert bpy.data.objects['V2 | 28 core carriers'].hide_render
report={'status':'PASS','blender':bpy.app.version_string,'variants':checks,'same_539_seed_targets_all_variants':True,'original_v2_curves_preserved':True,'three_original_camera_views_preserved':True,'limit':'Diagnostic source curves only; original Volume First cut mesh not recomputed'}
(root/'blender-validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
print('V3_SAVED_BLENDER_VALIDATION_PASS',json.dumps(report),flush=True)

"""Independent saved-scene and one-per-achene proof (Blender 5.2+)."""
import bpy,bmesh,numpy as np,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parent
f=np.load(root/'v2-seed-anchored-vascular-network.npz')
c14=np.load(root/'v2-control-14-strands.npz')
c40=np.load(root/'v2-control-40-strands.npz')
old=np.load(root/'m1a-539-actual-achene-centers.npz')
assert len(old['centers'])==len(old['curve_ends'])==539
assert len(np.unique(old['matched_index']))==539
assert np.max(old['nearest_distance'])<.0051
assert (f['kind']==0).sum()==28 and (f['kind']==1).sum()==539
for v,ct in [(c14,14),(c40,40)]:
 assert int((v['kind']==0).sum())==ct
 assert int((v['kind']==1).sum())==539
 assert np.array_equal(v['achene_positions'],f['achene_positions'])
 assert np.array_equal(v['branch_endpoints'],f['branch_endpoints'])
 assert np.array_equal(v['achene_idx'][ct:],np.arange(539))
main=bpy.data.objects['V2 | 28 core carriers']
branch=bpy.data.objects['V2 | 539 branches ending at achenes']
markers=bpy.data.objects['V2 | 539 seed positions and branch endpoints']
assert len(main.data.splines)==28 and len(branch.data.splines)==539
assert markers.type=='MESH' and len(markers.data.vertices)==539*6
assert len(markers.data.polygons)==539*8
starts=np.r_[0,np.cumsum(f['lengths'][:-1])]
ends=np.array([f['points'][j+n-1] for j,n in zip(starts[28:],f['lengths'][28:])])
curveends=np.array([tuple(sp.points[-1].co[:3]) for sp in branch.data.splines])
assert np.max(abs(ends-curveends))<1e-6
assert np.max(abs(curveends-f['branch_endpoints']))<1e-6
# Verify original 494 reference remains in the scene, without rendering over new results.
src=bpy.data.objects.get('V1_SOURCE | spatial filament paths (hidden)')
assert src and len(src.data.splines)==494
oldvis=[ob.name for ob in bpy.data.objects if ob.name.startswith(('FIBERS | original','FIBERS | additional')) and not ob.hide_render]
assert not oldvis,oldvis
scenes=[s for s in bpy.data.scenes if s.name.startswith(('01 |','02 |','03 |'))]
assert len(scenes)==3
for s in scenes:
 assert main.name in s.objects and branch.name in s.objects and markers.name in s.objects
report={'status':'PASS','blender':bpy.app.version_string,
 'source_m1a_seed_centers':539,'original_m1a_vascular_paths':539,'unique_match':539,
 'matched_original_seed_center_median_distance':float(np.median(old['nearest_distance'])),
 'matched_original_seed_center_max_distance':float(np.max(old['nearest_distance'])),
 'v2_central_strands':28,'v2_seed_ending_branches':539,'v2_markers':539,
 'controlled_main_strand_counts_tested':[14,28,40],
 'strands_changed_while_seed_terminal_positions_unchanged':True,
 'max_saved_blend_endpoint_error':float(np.max(abs(curveends-f['branch_endpoints']))),
 'old_494_curves_retained':True,'old_fiber_objects_visible_in_v2':False,
 'three_contexts':['only','translucent','original half-cut'],
 'limits':['Reprojected achene centers from M1a to volume-first hull','Diagnostic overlays, no new cut-surface tissue yet','Not the paid Frucht node graph','No independent botanical calibration']}
(root/'validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print('SEEDLINKED_V2_VALIDATION_PASS',json.dumps(report),flush=True)

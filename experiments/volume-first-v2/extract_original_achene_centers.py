"""Extract *our own* M1a seed instances and existing vascular endpoints from M1e5 scene.
No external Frucht code used. Creates a basis for Volume First v2 engineering comparison.
"""
import bpy, bmesh, numpy as np, json
from mathutils.kdtree import KDTree
from pathlib import Path
root=Path(__file__).resolve().parent
scene=bpy.context.scene;scene.frame_set(1)
seed=bpy.data.objects['GN live achenes (with actual surface pits)']
vas=bpy.data.objects['Vascular network | branches to every achene']
dg=bpy.context.evaluated_depsgraph_get();dg.update()
ev=seed.evaluated_get(dg); mesh=ev.to_mesh()
bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table()
remaining=set(bm.verts);comps=[]
while remaining:
    q=[remaining.pop()]; pts=[]
    while q:
        v=q.pop();pts.append(v)
        for e in v.link_edges:
            n=e.other_vert(v)
            if n in remaining:
                remaining.remove(n);q.append(n)
    comps.append(pts)
centers=np.array([np.array([tuple(v.co) for v in comp],dtype=np.float64).mean(axis=0) for comp in comps])
sizes=np.array([len(x) for x in comps]);bm.free();ev.to_mesh_clear()
endpoints=np.array([[p for p in s.points][-1].co[:3] for s in vas.data.splines],dtype=np.float64)
starts=np.array([[p for p in s.points][0].co[:3] for s in vas.data.splines],dtype=np.float64)
tree=KDTree(len(centers));[tree.insert(c,i) for i,c in enumerate(centers)];tree.balance()
match=[tree.find(x) for x in endpoints]
indices=np.array([m[1] for m in match]);dist=np.array([m[2] for m in match]);n_unique=len(set(indices))
# Save matched true achene centers in exactly the source path order. These are
# the seed instanced mesh actual centroids, not hand-guessed target locations.
np.savez_compressed(root/'m1a-539-actual-achene-centers.npz',centers=centers.astype('float32'),curve_ends=endpoints.astype('float32'),curve_starts=starts.astype('float32'),matched_center=centers[indices].astype('float32'),matched_index=indices.astype('int32'),nearest_distance=dist.astype('float32'),component_sizes=sizes.astype('int32'))
report={'blender':bpy.app.version_string,'source':'original owned M1a GN achenes and M1a Vascular network in archived M1e5',
 'frame':1,'achene_connected_components':len(comps),'source_vascular_curves':len(vas.data.splines),
 'seed_mesh_component_vertices_unique':sorted(set(int(x) for x in sizes)),
 'unique_matched_seed_centers':n_unique,'nearest_dist_min':float(min(dist)),'nearest_dist_median':float(np.median(dist)),'nearest_dist_max':float(max(dist)),
 'seed_z_range':[float(centers[:,2].min()),float(centers[:,2].max())],
 'is_1_to_1_seed_curve_mapping':len(comps)==len(endpoints)==n_unique,
 'note':'This establishes endpoint proximity to actual M1a seeds, not exact anatomical reality or Frucht internal nodes.'}
(root/'m1a-seed-anchor-extraction.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('M1A_ACTUAL_SEED_ENDS',json.dumps(report),flush=True)
assert len(comps)==len(endpoints)==n_unique, 'not bijection, need investigate before claiming anchor'

import json,hashlib
from pathlib import Path
root=Path('/mnt/data/strawberry_material_ab/qa');a=json.loads((root/'A.json').read_text());b=json.loads((root/'B.json').read_text());assert len(a['states'])==len(b['states'])==7
for x,y in zip(a['states'],b['states']):
 assert x['name']==y['name'] and x['voxel_mm']==y['voxel_mm']
 for key in ['body_verts','body_faces','cap_faces','body_coords_sha256','core_attr_sha256','cell_attr_sha256','nonmanifold_edges','positive_volume']:assert x[key]==y[key],(x['name'],key)
 assert x['nonmanifold_edges']==0 and x['positive_volume']
 assert abs(x['estimated_sss_weight_from_point_attributes']['min']-.08)<1e-5
assert a['source_mesh_sha256']==b['source_mesh_sha256'] and a['packed_150_sha256']==b['packed_150_sha256']
res={'status':'PASS_INDEPENDENT_A_B_SAME_GEOMETRY_AND_FIELDS','blender':a['blender'],'states':len(a['states']),'state_keys':[(x['voxel_mm'],x['name']) for x in a['states']],'original_packed_atlas':a['packed_150_sha256'],'source_raw_mesh':a['source_mesh_sha256'],'varying_sss_weight_B_plane_fine':next(x['estimated_sss_weight_from_point_attributes'] for x in b['states'] if x['name']=='plane' and x['voxel_mm']==.20),'peak_rss_kb':max(a['peak_rss_kb'],b['peak_rss_kb']),'SSS_in_whole_ignored':'whole uses separate skin material, not flesh cap shader','note':'Bounded actual meshes and one-factor material graph, not proof of image quality'}
(root/'compare.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps(res,indent=2))

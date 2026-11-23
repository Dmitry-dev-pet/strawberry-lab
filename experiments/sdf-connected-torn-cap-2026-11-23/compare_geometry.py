"""Compare independently reopened A/B GN meshes and original cell-coherent source QA."""
import json, pathlib, hashlib, argparse
p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,required=True);p.add_argument('--source-qa',type=pathlib.Path,required=True);p.add_argument('--source',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();r=a.root
assert not a.out.exists()
qa={}
for variant in ('A','B'):
 rows=[]
 for group in ['032','fine']:
  x=json.loads((r/f'qa-noise-{variant}-{group}.json').read_text());assert x['status']=='PASS_CLOSED_TESTED_POSES'
  rows.extend(x['poses'])
 assert len(rows)==7;qa[variant]=rows
original=json.loads(a.source_qa.read_text())
orig={(x['pose'],x['voxel_mm']):x['B_sha'] for x in original['states']}
normalize={'bite':'sphere','plane-fine':'plane_fine','edge-fine':'edge_fine'}
record=[]
for A,B in zip(qa['A'],qa['B']):
 assert (A['pose'],A['voxel_mm'])==(B['pose'],B['voxel_mm'])
 lookup=(normalize.get(A['pose'],A['pose']),A['voxel_mm'])
 assert A['xyz_sha']==orig[lookup],(A['pose'],'base sha')
 assert A['nonmanifold_edges']==B['nonmanifold_edges']==0
 assert A['connected_components']==B['connected_components']==1
 assert B['verts']>=A['verts'] and B['faces']>=A['faces']
 if A['pose'] in ('whole','plane','oblique','plane-fine'):assert A['xyz_sha']==B['xyz_sha']
 else:assert A['xyz_sha']!=B['xyz_sha'] and B['verts']>A['verts']
 record.append({'pose':A['pose'],'voxel_mm':A['voxel_mm'],'base_source_exact':True,'A_vertices':A['verts'],'B_vertices':B['verts'],'additional_vertices':B['verts']-A['verts'],'additional_faces':B['faces']-A['faces'],'base_sha':A['xyz_sha'],'torn_sha':B['xyz_sha'],'single_manifold_component_each':True})
res={'status':'PASS_EXPLICIT_A_B_SEVEN_TESTED_GEOMETRY_STATES','source_scene_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),'variants':{v:hashlib.sha256((r/'ab'/f'torn-{v}.blend').read_bytes()).hexdigest() for v in ['A','B']},'rows':record,'limit':'No exhaustive triangle-intersection proof; visual not accepted; validity scoped to tested poses.'}
a.out.write_text(json.dumps(res,indent=2)+'\n');print(json.dumps(res,indent=2))

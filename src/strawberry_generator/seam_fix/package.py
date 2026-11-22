"""Assemble authenticated owner-private delivery and public numeric evidence."""
from pathlib import Path
import hashlib,json,zipfile
root=Path(__file__).resolve().parents[3];p=root/'build/source-seam-v1';out=Path(__file__).parent
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
evidence={'base_PR':40,'base_head':'229826fe54d73a59702f0f22139d4db9e643b2ea','physical_rest_y_bias_mm':.001,'scope':'Tested recipes and poses only; nominal Y=0 without delta remains defective','tests':{'existing':124,'physical_metric_regressions':3},'seeds':{},'private_folder':'https://drive.google.com/drive/folders/1wcZlmCYQZ2hZ6qLhCetdhh8W-lgSoMs2'}
for seed in [101,202]:
 q=json.loads((p/f'seed{seed}-qa.json').read_text());r=json.loads((p/f'readback/seed{seed}-qa.json').read_text());assert q['sha256']==r['sha256']==sha(p/f'seed{seed}.blend')==sha(p/f'readback/seed{seed}.blend')
 for pose in q['poses']:
  for kind in ['Fast_zero_audit','Exact_zero_audit']:
   m=pose[kind];assert m['zero_edges_all']==m['zero_polygon_faces']==m['zero_render_triangles']==0 and m['closed_connected_positive']
 cli=json.loads((p/f'cli{seed}/receipt.json').read_text());old=json.loads((root.parent/f'strawberry-generator/build/generator-v1-final/seed{seed}/receipt.json').read_text())
 for key in ['anchor_digest','canonical_body_digest','body_vertices']:assert cli[key]==old[key]
 cq=json.loads((p/f'cli{seed}/qa.json').read_text());assert len(cq['actual_triangle_contacts'])==264 and min(cq['actual_triangle_contacts'].values())>0
 cross=p/('cross-layer101-retry' if seed==101 else 'cross-layer202-final')/'validation.json';c=json.loads(cross.read_text());assert all(v['pixels_identical'] for v in c.values())
 evidence['seeds'][str(seed)]={'sha256':sha(p/f'seed{seed}.blend'),'fully_downloaded_sha256':sha(p/f'readback/seed{seed}.blend'),'reopened_QA':r,'live_profile':json.loads((p/f'seed{seed}-live-qa.json').read_text()),'fresh_CLI_anchor_body_digests_match_PR40':True,'CLI_receipt':cli,'CLI_QA':cq,'cross_layer':c}
for name in ['probe.json','bias-probe.json','causal-report.json','code-parity.json','plate-qa.json']:
 evidence[name]=json.loads((p/name).read_text())
(p/'full-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
files={}
for seed in [101,202]:
 files[f'outputs/seed{seed}.blend']=p/f'seed{seed}.blend'
 files[f'inputs-pr40/seed{seed}/strawberry.blend']=root.parent/f'strawberry-generator/build/generator-v1-final/seed{seed}/strawberry.blend'
 for name in ['receipt.json','anchors.json','qa.json']:files[f'fresh-cli/seed{seed}/{name}']=p/f'cli{seed}/{name}'
files['inputs-pr39/live-profile.blend']=root.parent/'strawberry-live-profile/build/live-profile-v1/live-profile.blend'
for f in p.glob('*.png'):files['renders/'+f.name]=f
for f in p.glob('*.json'):files['qa/'+f.name]=f
for f in p.glob('tests*.log'):files['qa/'+f.name]=f
for seed,folder in [(101,'cross-layer101-retry'),(202,'cross-layer202-final')]:
 for f in (p/folder).glob('*'):
  if f.suffix in ['.png','.json']:files[f'qa/cross-layer{seed}/'+f.name]=f
 for f in (p/'readback').glob(f'seed{seed}-qa.json'):files['qa/readback/'+f.name]=f
for f in out.glob('*'):
 if f.suffix in ['.py','.md','.json']:files['source/seam_fix/'+f.name]=f
for f in (root/'src/strawberry_generator').glob('*.py'):files['source/strawberry_generator/'+f.name]=f
manifest={name:sha(f) for name,f in files.items()};(p/'delivery-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
archive=p/'strawberry-explicit-blade-offset-v1.zip';assert not archive.exists()
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
 for name,f in files.items():z.write(f,name)
 z.write(p/'delivery-manifest.json','manifest.json')
print({'archive_sha256':sha(archive),'files':len(manifest),'size_bytes':archive.stat().st_size})

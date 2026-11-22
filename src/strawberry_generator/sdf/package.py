"""Owner-private delivery. Reference comparison never enters the git tree."""
from pathlib import Path
import hashlib,json,zipfile
root=Path(__file__).resolve().parents[3];p=root/'build/sdf-slice-v1';final=p/'final';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();files={}
files['scene/strawberry-sdf.blend']=final/'strawberry-sdf.blend';files['inputs/pr40-seed101.blend']=root.parent/'strawberry-generator/build/generator-v1-final/seed101/strawberry.blend'
for f in final.iterdir():
 if f.suffix in ['.png','.json'] or f.name.startswith('tests'):files['renders-qa/'+f.name]=f
files['qa/full-downloaded-scene-qa.json']=p/'readback/qa.json'
for f in Path(__file__).parent.iterdir():
 if f.suffix in ['.py','.md','.json']:files['source/sdf/'+f.name]=f
for rel in ['experiments/profile-vascular-v1/profile_probe.py','experiments/exact-tissue-zones-v1/atlas.py','recipes/strawberry-101.json']:files['source/'+rel]=root/rel
files['lookdev-before/sphere.png']=p/'sphere.png';files['lookdev-before/sphere.json']=p/'sphere.json'
manifest={name:sha(f) for name,f in sorted(files.items())};(final/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');archive=final/'strawberry-technical-sdf-v1.zip';assert not archive.exists()
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
 for name,f in files.items():z.write(f,name)
 z.write(final/'manifest.json','manifest.json')
print({'archive_sha256':sha(archive),'members':len(manifest),'bytes':archive.stat().st_size})

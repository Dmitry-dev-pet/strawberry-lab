"""Exact matched Blender Cycles A/C, pixel effect (NOT photorealism score)."""
from pathlib import Path
from PIL import Image,ImageDraw
import argparse,json,hashlib,numpy as np
p=argparse.ArgumentParser();p.add_argument('--renders',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--report',required=True,type=Path)
a=p.parse_args();r=a.renders.resolve();assert not a.out.exists() and not a.report.exists()
rec={'meaning':'Image differences detect an actual material/geometry intervention, not realism','results':{},'caveats':['Changing denoised Cycles pixels is not independent quality proof','A and C scenes differ in lens visibility + C material, but source SDF body positions are identical']}
rows=[]
for shot in ['plane','bite','macro']:
 meta={};images={}
 for v in ('A','C'):
  path=r/f'{shot}-{v}-480.png';record=json.loads(path.with_suffix('.json').read_text());assert hashlib.sha256(path.read_bytes()).hexdigest()==record['image_sha256'];meta[v]=record;images[v]=Image.open(path).convert('RGB')
 for key in ('shot','resolution','samples','seed','camera','sphere','lights','view'):
  assert meta['A'][key]==meta['C'][key],(shot,key)
 aa=np.asarray(images['A'],np.int16);cc=np.asarray(images['C'],np.int16);delta=np.abs(aa-cc)
 rec['results'][shot]={'source_image_sha':meta['A']['image_sha256'],'menisci_image_sha':meta['C']['image_sha256'],'changed_fraction_gt2':float((delta.max(2)>2).mean()),'changed_fraction_gt10':float((delta.max(2)>10).mean()),'mean_absolute_rgb_255':float(delta.mean()),'render_seconds':{v:meta[v]['cycles_seconds'] for v in ('A','C')},'lens_polygons':{v:meta[v]['lens_polygons'] for v in ('A','C')}}
 rows.append((shot,images))
out=Image.new('RGB',(960,3*520),(23,24,28));d=ImageDraw.Draw(out)
for y,(shot,images) in enumerate(rows):
 for x,v in enumerate(('A','C')):
  out.paste(images[v],(x*480,y*520+40));d.text((x*480+12,y*520+12),f'{shot.upper()} | '+('baseline' if v=='A' else 'physically attached clear lens pockets'),fill='white')
out.save(a.out);a.report.write_text(json.dumps(rec,indent=2)+'\n');print('CYCLES_MATCHED',json.dumps({k:{'delta_gt10':v['changed_fraction_gt10'],'seconds':v['render_seconds']} for k,v in rec['results'].items()}),flush=True)

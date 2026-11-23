"""Independent unchanged-camera Cycles A/C contact and actual pixel intervention diagnostic."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib,argparse
p=argparse.ArgumentParser();p.add_argument('--a',type=Path,required=True);p.add_argument('--c',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
a=p.parse_args();assert not a.out.exists() and not a.report.exists();r={k:json.loads(x.with_suffix('.json').read_text()) for k,x in [('A',a.a),('C',a.c)]}
for key in ['shot','resolution','samples','seed','camera','cutter','lights','view']:
 assert r['A'][key]==r['C'][key],key
pix={}
for k,path in [('A',a.a),('C',a.c)]:
 assert hashlib.sha256(path.read_bytes()).hexdigest()==r[k]['image_sha'];pix[k]=Image.open(path).convert('RGB')
imgA=np.asarray(pix['A'],np.int16);imgC=np.asarray(pix['C'],np.int16);d=np.abs(imgA-imgC);mx=d.max(axis=2)
rec={'status':'NATIVE_CYCLES_MATCHED','settings':{k:r['A'][k] for k in ['shot','resolution','samples','seed']},'pixels_changed_gt2':float((mx>2).mean()),'pixels_changed_gt10':float((mx>10).mean()),'pixels_changed_gt25':float((mx>25).mean()),'mean_abs_RGB255':float(d.mean()),'seconds':{k:r[k]['seconds'] for k in ['A','C']},'image_sha256':{k:r[k]['image_sha'] for k in ['A','C']},'limitations':'Only measures visual intervention, NOT quality or Frucht match'}
out=Image.new('RGB',(960,520),(25,27,30));draw=ImageDraw.Draw(out)
for i,k in enumerate(['A','C']):
 out.paste(pix[k],(480*i,40));draw.text((480*i+15,12),('A | one spherical bite' if k=='A' else 'C | 3 bites, fixed seed guard'),fill='white')
out.save(a.out);a.report.write_text(json.dumps(rec,indent=2));print('COMPARE_PASS',rec)

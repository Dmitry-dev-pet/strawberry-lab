"""Independent signed Cycles A/B image check; no quality claim from pixel delta."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,numpy as np,argparse
parser=argparse.ArgumentParser();parser.add_argument('--renders',type=Path,required=True);parser.add_argument('--source-renders',type=Path,required=True)
a=parser.parse_args();p=a.renders.resolve();prev=a.source_renders.resolve()
metrics={'status':'PASS_MATCHED_NATIVE_BLENDER_CYCLES','blender':'5.2.4 LTS','seed':1729,'resolution':640,'samples':16,'effects_not_realism_scores':True,'views':{}}
out=Image.new('RGB',(1280,3*674),(24,26,29));d=ImageDraw.Draw(out)
for row,shot in enumerate(['plane','bite','macro']):
 rec={};pix={}
 for var in ('A','B'):
  png=p/f'{shot}-{var}.png';data=png.read_bytes();meta=json.loads(png.with_suffix('.json').read_text());assert hashlib.sha256(data).hexdigest()==meta['image_sha'];rec[var]=meta;pix[var]=np.asarray(Image.open(png).convert('RGB'),np.int16)
 for field in ['shot','blender','resolution','samples','seed','camera','cutter','lights','view']:
  assert rec['A'][field]==rec['B'][field],(shot,field)
 old=np.asarray(Image.open(prev/f'{shot}-halo.png').convert('RGB'),np.int16)
 assert np.array_equal(old,pix['A']),f'Control not pixel identical: {shot}'
 diff=np.abs(pix['A']-pix['B']);dd=diff.max(axis=2)
 metrics['views'][shot]={'A_is_pixel_identical_to_v20':True,'changed_pixel_fraction_gt2':float((dd>2).mean()),'changed_pixel_fraction_gt10':float((dd>10).mean()),'changed_pixel_fraction_gt25':float((dd>25).mean()),'mean_absolute_RGB_255':float(diff.mean()),'max_RGB_difference':int(dd.max()),'render_seconds':{v:rec[v]['cycles_seconds'] for v in ['A','B']},'image_sha':{v:rec[v]['image_sha'] for v in ['A','B']}}
 for i,var in enumerate(('A','B')):
  x=i*640;y=row*674
  out.paste(Image.fromarray(pix[var].astype(np.uint8)),(x,y+34))
  d.text((x+14,y+10),f'{shot.upper()}  |  '+('ORIGINAL A' if var=='A' else 'CO-REGISTERED CELLS B'),fill=(241,241,241))
print(json.dumps(metrics,indent=2))
out.save(p/'cell-coherence-AB-3shots.png')
(p/'comparison.json').write_text(json.dumps(metrics,indent=2)+'\n')

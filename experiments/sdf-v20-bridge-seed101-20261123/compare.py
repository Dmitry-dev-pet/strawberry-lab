"""Read signed Cycles PNG receipts, assert matching camera/cutter/seed/samples and report pixel differences (NOT quality)."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib,argparse
p=argparse.ArgumentParser();p.add_argument('--renders',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();r=a.renders.resolve();dest=a.out.resolve();assert not dest.exists()
result={'shots':{},'interpretation':'Pixel differences detect an intervention, NOT realism or owner visual approval'}
for shot,variants in [('plane',['baseline','core','halo']),('bite',['baseline','core','halo']),('macro',['baseline','halo'])]:
 records={v:json.loads((r/f'{shot}-{v}.json').read_text()) for v in variants}
 for k in ('shot','resolution','samples','seed','camera','cutter','scene_sha256'):
  assert len({json.dumps(rec[k],sort_keys=True) for rec in records.values()})==1,(shot,k)
 data={v:np.asarray(Image.open(r/f'{shot}-{v}.png').convert('RGB'),dtype=np.uint8) for v in variants}
 for v in variants:assert hashlib.sha256((r/f'{shot}-{v}.png').read_bytes()).hexdigest()==records[v]['image_sha256']
 pixels={};ref=data[variants[0]].astype(np.int16)
 for v in variants[1:]:
  diff=np.abs(data[v].astype(np.int16)-ref)
  pixels[f'{variants[0]}_vs_{v}']={'changed_frac_gt2':float((diff.max(axis=2)>2).mean()),'changed_frac_gt10':float((diff.max(axis=2)>10).mean()),'average_RGB_error_255':float(diff.mean())}
 if len(variants)==3:
  diff=np.abs(data['core'].astype(np.int16)-data['halo'].astype(np.int16));pixels['core_vs_halo']={'changed_frac_gt2':float((diff.max(2)>2).mean()),'changed_frac_gt10':float((diff.max(2)>10).mean()),'average_RGB_error_255':float(diff.mean())}
 sheet=Image.new('RGB',(640*len(variants),640+40),(23,25,29));d=ImageDraw.Draw(sheet)
 for i,v in enumerate(variants):
  sheet.paste(Image.fromarray(data[v]),(i*640,40));d.text((i*640+10,10),shot.upper()+' | '+v.upper(),fill='white')
 sheet.save(dest.parent/f'{shot}-comparable.png')
 result['shots'][shot]={'variants':variants,'pixels':pixels,'render_time_seconds':{v:records[v]['seconds'] for v in variants}}
# Combined editorial sheet (resize for quick overview; original image pixels preserved in individual frames)
order=['plane','bite','macro'];wide=960;cols=3;small=320;output=Image.new('RGB',(960,3*(320+34)),(22,24,29));d=ImageDraw.Draw(output)
for row,shot in enumerate(order):
 for col,v in enumerate(['baseline','core','halo']):
  if not (r/f'{shot}-{v}.png').exists():continue
  im=Image.open(r/f'{shot}-{v}.png').convert('RGB').resize((small,small),Image.Resampling.LANCZOS)
  x=col*small;y=row*(small+34);output.paste(im,(x,y+34));d.text((x+8,y+9),shot.upper()+' | '+v.upper(),fill='white')
output.save(dest.parent/'contact-sheet.png')
dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('MATCHED_COMPARISON',json.dumps(result['shots'],ensure_ascii=False))

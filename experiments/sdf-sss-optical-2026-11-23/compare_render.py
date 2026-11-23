"""A/B matched original Cycles, author reference excluded from image delta metrics."""
import json,hashlib,numpy as np
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
root=Path('/mnt/data/strawberry_material_ab');r=root/'renders';source=Path('/mnt/data/strawberry_work/v20bridge/renders');results={'schema':'sdf-cell-sss-optical-ab-2026-11-23','status':'PASS_MATCHED_CYCLES_IMAGE_RECEIPTS','settings':{'resolution':640,'samples':16,'seed':1729},'shots':{},'interpretation':'pixel change demonstrates real intervention, not resemblance to Frucht'}
canvas=Image.new('RGB',(1280,3*(640+36)),(24,26,30));draw=ImageDraw.Draw(canvas)
for row,shot in enumerate(['plane','bite','macro']):
 rec={v:json.loads((r/f'{shot}-{v}.json').read_text()) for v in ['A','B']}
 for v in ['A','B']:
  path=r/f'{shot}-{v}.png';assert hashlib.sha256(path.read_bytes()).hexdigest()==rec[v]['image_sha256']
  assert rec[v]['shot']==shot and rec[v]['samples']==16 and rec[v]['resolution']==640 and rec[v]['seed']==1729
 for key in ['camera','sphere','lights','view','resolution','samples','seed']:
  assert rec['A'][key]==rec['B'][key],(shot,key)
 pixels={v:np.asarray(Image.open(r/f'{shot}-{v}.png').convert('RGB'),dtype=np.int16) for v in ['A','B']}
 delta=np.abs(pixels['A']-pixels['B'])
 old=source/f'{shot}-halo.png';old_pixels=np.asarray(Image.open(old).convert('RGB'),dtype=np.int16)
 assert old_pixels.shape==pixels['A'].shape
 exact=bool(np.array_equal(old_pixels,pixels['A']))
 # visually controlled expected source identity, should succeed when all defaults match
 assert exact,(shot,'baseline deviates from signed source frame')
 results['shots'][shot]={'baseline_A_pixel_identical_to_prior_verified_v20':exact,'total_pixels':int(delta.shape[0]*delta.shape[1]),'fraction_changed_gt2':float((delta.max(axis=2)>2).mean()),'fraction_changed_gt10':float((delta.max(axis=2)>10).mean()),'mean_abs_RGB_255':float(delta.mean()),'max_channel_delta':int(delta.max()),'render_seconds':{v:rec[v]['render_seconds'] for v in ['A','B']},'image_sha256':{v:rec[v]['image_sha256'] for v in ['A','B']}}
 for i,v in enumerate(['A','B']):
  x=640*i;y=(640+36)*row
  canvas.paste(Image.fromarray(pixels[v].astype('uint8')),(x,y+36));draw.text((x+14,y+10),shot.upper()+'  |  '+('A · existing SSS' if v=='A' else 'B · tissue-linked SSS'),fill=(235,235,235))
print(json.dumps(results,indent=2));canvas.save(r/'optical-sss-AB-3shots.png');(r/'comparison.json').write_text(json.dumps(results,indent=2)+'\n')

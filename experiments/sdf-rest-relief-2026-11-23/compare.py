"""Compare original Blender-rendered A/C/B frames without any retouching.

All image differences indicate intervention effect, not visual-quality scores.
"""
import json,hashlib,sys,argparse
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,required=True,help='Output dir with renders/<shot>-<A,B,C>.png and receipts')
a=parser.parse_args()
root=a.root.resolve()
renders=root/'renders'
labels={'A':'A — 0 mm (old cut)','C':'C — 0.033 mm','B':'B — 0.095 mm'}
shots=('plane','macro','bite')
report={'settings':{'samples':20,'resolution':720,'seed':1729,'camera_matched':True},'pairs':{},'photos_meaning':'Image pixel difference, NOT photorealism or owner acceptance'}
for shot in shots:
 records={v:json.loads((renders/f'{shot}-{v}.json').read_text()) for v in 'ACB'}
 for key in ['mode','voxel_mm','resolution','samples','seed','camera','lights','cutter']:
  assert records['A'][key]==records['C'][key]==records['B'][key],(shot,key)
 imgs={v:np.asarray(Image.open(renders/f'{shot}-{v}.png').convert('RGB'),dtype=np.uint8) for v in 'ACB'}
 for v in 'CB':
  delta=np.abs(imgs['A'].astype(np.int16)-imgs[v].astype(np.int16))
  report['pairs'][f'{shot}_A_vs_{v}']={'changed_fraction_gt_2':float((delta.max(2)>2).mean()),'changed_fraction_gt_10':float((delta.max(2)>10).mean()),'mean_absolute_rgb_0_255':float(delta.mean()),'max_difference':int(delta.max()),'a_sha256':records['A']['image_sha256'],'candidate_sha256':records[v]['image_sha256']}
 w,h=imgs['A'].shape[1],imgs['A'].shape[0]
 out=Image.new('RGB',(3*w,h+46),(20,22,28));draw=ImageDraw.Draw(out)
 for i,v in enumerate('ACB'):
  out.paste(Image.fromarray(imgs[v]),(i*w,46));draw.text((i*w+12,13),f'{shot.upper()}: '+labels[v],fill='white')
 out.save(renders/f'{shot}-ACB.png')
# 3x3 compact view and preservation of unmodified pixel data via individual frames
w=720//2;h=w;composite=Image.new('RGB',(w*3,(h+35)*3),(20,23,28));dr=ImageDraw.Draw(composite)
for y,shot in enumerate(shots):
 for x,v in enumerate('ACB'):
  img=Image.open(renders/f'{shot}-{v}.png').convert('RGB').resize((w,h),Image.Resampling.LANCZOS)
  x0=x*w;y0=y*(h+35)
  composite.paste(img,(x0,y0+35));dr.text((x0+9,y0+10),f'{shot.upper()} {v}: '+(['0','0.033','0.095']['ACB'.index(v)])+' mm',fill='white')
composite.save(root/'cycles-a-c-b-matrix.png')
(root/'image-ab-diff.json').write_text(json.dumps(report,indent=2)+'\n')
print('COMPARISON',json.dumps(report['pairs'],indent=1)[:4500])

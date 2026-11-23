"""Verify matched Cycles camera/lights and compare A vs D. Pixel change is not quality."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--render-dir',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
a=p.parse_args();assert not a.out.exists() and not a.report.exists()
r=a.render_dir.resolve();rows=[];records={'shots':{},'meaning':'Changes measure effect, not realism'}
for shot in ('plane','bite'):
 images=[];rs=[]
 for variant in ('A','D'):
  src=r/f'{shot}-{variant}-480.png';rec=json.loads(src.with_suffix('.json').read_text());assert hashlib.sha256(src.read_bytes()).hexdigest()==rec['image_sha256'];rs.append(rec);images.append(Image.open(src).convert('RGB'))
 for k in ('shot','resolution','samples','seed','camera','sphere','lights','color_management'):assert rs[0][k]==rs[1][k],(shot,k)
 pix=np.abs(np.asarray(images[0],np.int16)-np.asarray(images[1],np.int16));records['shots'][shot]={'changed_pixel_fraction_gt10':float((pix.max(axis=2)>10).mean()),'changed_pixel_fraction_gt2':float((pix.max(axis=2)>2).mean()),'mean_absolute_RGB_255':float(pix.mean()),'render_seconds':{'A':rs[0]['render_seconds'],'D':rs[1]['render_seconds']},'wet_faces':{'A':rs[0]['film_faces'],'D':rs[1]['film_faces']},'image_sha256':{v:rs[i]['image_sha256'] for i,v in enumerate(('A','D'))}}
 rows.append((shot,images))
w=480;img=Image.new('RGB',(2*w,(480+34)*2),(23,24,29));d=ImageDraw.Draw(img)
for y,(shot,ims) in enumerate(rows):
 for x,im in enumerate(ims):
  img.paste(im,(x*w,y*514+34));d.text((x*w+10,y*514+10),shot.upper()+' '+('A / bare' if x==0 else 'D / localized film'),fill='white')
img.save(a.out);a.report.write_text(json.dumps(records,indent=2)+'\n');print(json.dumps(records,indent=2))

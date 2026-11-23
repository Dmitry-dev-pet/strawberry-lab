"""Compare independent original Cycles renders at identical settings; not perceptual score."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,hashlib,json
P=Path('/mnt/data/strawberry-v19')
source=Path('/mnt/data/strawberry-v17/cycles-v12-bite-640px-16s.png')
byshot={
 'central':{'v12':P/'cycles-v12-central-640px-16s.png','v19A':P/'cycles-v19a-central-640px-16s.png','v19B':P/'cycles-v19b-central-640px-16s.png'},
 'bite':{'v12':source,'v19A':P/'cycles-v19a-bite-640px-16s.png','v19B':P/'cycles-v19b-bite-640px-16s.png'}}
all_metrics={}
for shot,images in byshot.items():
 d={name:np.asarray(Image.open(path).convert('RGB')).astype(np.float32)/255 for name,path in images.items()}
 for left,right in [('v12','v19A'),('v19A','v19B'),('v12','v19B')]:
  diff=np.abs(d[left]-d[right])
  max_channel=diff.max(axis=-1)
  all_metrics[f'{shot}:{left}-{right}']={'mae':round(float(diff.mean()),7),'pixels_changed_gt_001_pct':round(float((max_channel>.01).mean()*100),3),
       'pixels_changed_gt_005_pct':round(float((max_channel>.05).mean()*100),3),'max_change':round(float(max_channel.max()),3)}
# 2x3 at 640 each + header; private reference frames NOT included.
w,h=640,640
canvas=Image.new('RGB',(3*w,2*h+95),'#101014')
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19)
draw=ImageDraw.Draw(canvas)
draw.text((22,10),'Strawberry Lab v19 — genuine Blender Cycles (640px / 16 samples)',font=font,fill='white')
for i,key in enumerate(['v12','v19A','v19B']):
 draw.text((i*w+20,53),key,font=font,fill='white')
for j,shot in enumerate(['central','bite']):
 for i,key in enumerate(['v12','v19A','v19B']):
  img=Image.open(byshot[shot][key]).convert('RGB')
  canvas.paste(img,(i*w,95+j*h))
  draw.text((i*w+20,100+j*h),('Centered axial plane' if shot=='central' else 'Spherical bite'),font=small,fill='white',stroke_fill='#161616',stroke_width=2)
contact=P/'comparison-v12-v19a-v19b-cycles.png'
assert not contact.exists()
canvas.save(contact,optimize=True)
rec={'source':'Blender 5.2.4 LTS CPU Cycles, same lighting camera samples and resolution','pixel_comparison':all_metrics,
     'contact_sheet':contact.name,'contact_sheet_sha256':hashlib.sha256(contact.read_bytes()).hexdigest(),
     'contact_sheet_bytes':contact.stat().st_size,'original_vendor_reference_included':False}
(P/'v19-pixel-comparison.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n')
print('V19_IMAGE_AB',json.dumps(all_metrics,ensure_ascii=False))

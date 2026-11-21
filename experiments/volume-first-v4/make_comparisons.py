"""Arrange actual source renders / private authentic video still; no AI imagery."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageEnhance
import numpy as np,json
D=Path(__file__).resolve().parent;O=D/'outputs'
items=[('only-v3.png','V3 | base 28-sag0.25'),('only-0.35.png','V4 | local hook 0.35'),('only-0.85.png','V4 | local hook 0.85'),('only-1.5.png','V4 | local hook 1.50')]
ims=[Image.open(O/p).convert('RGB') for p,_ in items]
assert all(x.size==ims[0].size for x in ims)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';big=ImageFont.truetype(font,24);small=ImageFont.truetype(font,16)
w,h=ims[0].size
full=Image.new('RGB',(w*2,h*2+96),(22,26,32));d=ImageDraw.Draw(full)
d.text((20,8),'V3 vs V4 | REAL Blender Cycles | identical 539 endpoints, 28 carriers, camera/light',font=big,fill='white')
for j,(im,(_,label)) in enumerate(zip(ims,items)):
 x=(j%2)*w;y=(j//2)*h+45;full.paste(im,(x,y));d.text((x+15,y+12),label,font=big,fill='white',stroke_width=2,stroke_fill='#2b3037')
d.text((15,full.height-34),'V4 updates only last 21 curve points. Not Frucht parity, not tissue morphology.',font=small,fill='white')
full.save(O/'ab-v3-v4-full.jpg',quality=92)
# Crop upper right where terminal markers are dense; identical crop in all scenes.
reg=(int(w*.55),int(h*.11),int(w*.93),int(h*.53))
crops=[x.crop(reg) for x in ims];cw,ch=crops[0].size
f=2
macro=Image.new('RGB',(cw*f*2,ch*f*2+90),(21,25,29));md=ImageDraw.Draw(macro)
md.text((12,8),'ENLARGED SAME VIEW: curve endings near markers',font=big,fill='white')
for j,(im,(_,name)) in enumerate(zip(crops,items)):
 x=(j%2)*cw*f;y=(j//2)*ch*f+44;macro.paste(im.resize((cw*f,ch*f),Image.Resampling.LANCZOS),(x,y));md.text((x+8,y+8),name,font=small,fill='white',stroke_width=2,stroke_fill='#272d36')
md.text((16,macro.height-34),'Cropping only. Same coordinates, scale, camera, and 12 Cycles samples.',font=small,fill='white')
macro.save(O/'ab-v3-v4-terminal-crop.jpg',quality=93)
A=np.array(ims[0],dtype='int16')
metrics={}
for j,(p,name) in enumerate(items[1:],1):
 B=np.array(ims[j],dtype='int16');diff=np.abs(A-B)
 metrics[p]={'mean_abs_rgb_difference':round(float(diff.mean()),4),'pixel_fraction_rgb_max_difference_gt_8':round(float(np.mean(diff.max(axis=2)>8)),4),'median_rgb_abs_diff':round(float(np.median(diff)),4)}
# private comparison with actual author video, clearly different frame and view.
ref=Image.open(D/'private-frucht-video-ref15.jpg').convert('RGB')
rw=int(w*.72);rh=h
panel=Image.new('RGB',(rw+w*2,rh+102),(19,22,27));pd=ImageDraw.Draw(panel)
pd.text((18,9),'REFERENCE VIDEO vs OWN 3D NETWORK | morphology ONLY',font=big,fill='white')
ref=ref.resize((rw,rh));panel.paste(ref,(0,46))
for i,k in enumerate((0,3)):
 panel.paste(ims[k],(rw+i*w,46))
 pd.text((rw+i*w+12,51),'V3 baseline' if k==0 else 'V4 local hook 1.50',font=big,fill='white',stroke_width=1,stroke_fill='#1c1e23')
pd.text((18,panel.height-36),'Frucht 00:15 VIDEO has different camera, crop and possibly animated/exploded fibers. NOT a pixel match.',font=small,fill='white')
panel.save(O/'private-author-v3-v4.jpg',quality=91)
(O/'render-difference-metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
print('V4_COMPARES_COMPLETED',metrics)

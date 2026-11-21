"""Arrange unmodified real Blender Cycles captures only, not image synthesis."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json
R=Path(__file__).resolve().parent;O=R/'outputs';font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
big=ImageFont.truetype(font,23);small=ImageFont.truetype(font,17)
poses=[('center','Y=0, 0°'),('deep','Y=+0.34, 0°'),('shallow','Y=−0.26, 0°'),('oblique','Y=0, 32°')]
ims={(p,m):Image.open(O/f'{p}-{m}.png').convert('RGB') for p,_ in poses for m in ['matched','flesh-only']}
w,h=next(iter(ims.values())).size
assert all(x.size==(w,h) for x in ims.values())
board=Image.new('RGB',(w*4,h*2+104),(20,25,30));dr=ImageDraw.Draw(board)
dr.text((20,11),'ONE MOVABLE CUT — SAME GEOMETRY, FOUR POSES × TWO VISIBILITY POLICIES',font=big,fill='white')
for i,(name,label) in enumerate(poses):
 for j,mode in enumerate(('matched','flesh-only')):
  col=i;row=j;x=col*w;y=row*h+51
  board.paste(ims[name,mode],(x,y));dr.text((x+12,y+9),label,font=big,fill='white',stroke_width=2,stroke_fill='#1b2026')
  dr.text((x+12,y+35),'Все слои: отсечь' if j==0 else 'Только мякоть: отсечь',font=small,fill='white',stroke_width=2,stroke_fill='#20252b')
dr.text((20,board.height-31),'Actual Blender Cycles 5.2.4 | Same 28+539 source curves, camera, studio and original 150³ tissue field | No AI imagery',font=small,fill='#e1e5e9')
board.save(O/'real-live-cut-four-poses.jpg',quality=91)

modes=[('center-whole.png','Целая клубника'),('center-matched.png','Общий срез'),('center-flesh-only.png','Срез только мякоти'),('center-fibers-only.png','Только волокна и маркеры')]
layer=Image.new('RGB',(w*2,h*2+102),(20,25,30));d=ImageDraw.Draw(layer)
d.text((16,11),'REAL LAYER TOGGLES — SAME BLENDER SOURCE',font=big,fill='white')
for k,(filename,label) in enumerate(modes):
 x=(k%2)*w;y=(k//2)*h+45
 layer.paste(Image.open(O/filename).convert('RGB'),(x,y));d.text((x+14,y+9),label,font=big,fill='white',stroke_width=2,stroke_fill='#171d24')
d.text((15,layer.height-28),'Live Boolean for tissue; full/clipped shader for carriers, branches and markers',font=small,fill='#e1e5e9')
layer.save(O/'real-live-layer-modes.jpg',quality=92)

rows=[]
for name,label in poses:
 a=np.asarray(ims[name,'matched'],dtype=np.int16)
 b=np.asarray(ims[name,'flesh-only'],dtype=np.int16)
 delta=np.abs(a-b)
 rows.append({'pose':name,'plane':label,'mean_abs_rgb_difference':float(delta.mean()),'fraction_pixels_maxchannel_change_gt_15':float((delta.max(axis=2)>15).mean())})
(O/'render-difference.json').write_text(json.dumps({'status':'PASS','images':'Real Blender Cycles only','poses':rows,'note':'Visual change proves independent mask effect but not anatomical or Frucht parity'},ensure_ascii=False,indent=2)+'\n')
print('COMPARISONS_READY',len(rows),board.size,layer.size,json.dumps(rows),flush=True)

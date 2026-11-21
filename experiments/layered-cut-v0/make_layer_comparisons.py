#!/usr/bin/env python3
"""Unmodified authentic Blender Cycles renders arranged for A/B display evidence."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import numpy as np,json
R=Path(__file__).resolve().parent;O=R/'outputs';F='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
big=ImageFont.truetype(F,22);sm=ImageFont.truetype(F,16)
A=Image.open(O/'matched.png').convert('RGB')
B=Image.open(O/'flesh-only.png').convert('RGB')
assert A.size==B.size
w,h=A.size
panel=Image.new('RGB',(w*2,h+115),(22,26,31))
d=ImageDraw.Draw(panel)
d.text((20,10),'SAME BODY / CUT / CAMERA / 539 BRANCHES',font=big,fill='white')
for i,(im,label) in enumerate([(A,'A  |  SHARED CLIP'),(B,'B  |  FLESH-ONLY CLIP')]):
    x=i*w
    panel.paste(im,(x,50))
    d.text((x+14,58),label,font=big,fill='white',stroke_width=2,stroke_fill='#262c34')
d.text((20,h+65),'Real Blender Cycles 5.2.4  |  clipping masks differ; anatomical paths unchanged',font=sm,fill='#d2d6dc')
panel.save(O/'real-ab-layer-clipping.jpg',quality=92)
images=[(B,'ALL  |  flesh + vasculature'),(Image.open(O/'fibers-only.png').convert('RGB'),'NO FLESH'),(Image.open(O/'no-seeds.png').convert('RGB'),'NO SEED MARKERS'),(Image.open(O/'core-only.png').convert('RGB'),'CENTRAL CARRIERS ONLY')]
for im,_ in images:assert im.size==(w,h)
board=Image.new('RGB',(w*2,h*2+105),(21,25,30));dd=ImageDraw.Draw(board)
dd.text((16,8),'FOUR INDEPENDENT LAYERS — REAL BLENDER VISIBILITY TOGGLES',font=big,fill='white')
for i,(im,label) in enumerate(images):
    x=i%2*w;y=i//2*h+40
    board.paste(im,(x,y));dd.text((x+13,y+9),label,font=big,fill='white',stroke_width=2,stroke_fill='#242933')
dd.text((20,2*h+60),'No invented curves or seed positions. Flesh is a prior, fixed V0 slice.',font=sm,fill='#d2d6dc')
board.save(O/'real-layer-toggle-grid.jpg',quality=91)
px=np.array(A,dtype=np.int16);py=np.array(B,dtype=np.int16);diff=np.abs(px-py)
report={'images':{'A':A.size,'B':B.size},'mean_abs_rgb_difference':round(float(np.mean(diff)),4),'fraction_pixels_max_channel_diff_gt_15':round(float(np.mean(np.max(diff,axis=2)>15)),4),'fraction_pixels_max_channel_diff_gt_40':round(float(np.mean(np.max(diff,axis=2)>40)),4),'comparison_is_perceptual_not_structural_truth':True}
(O/'render-difference.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('LAYER_AB_IMAGES',json.dumps(report),flush=True)

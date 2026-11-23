"""Arrange untouched Cycles PNGs with labels; never synthesize or retouch pixels."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=a.out.resolve()
font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def montage(rows,name,size,subtitle):
    header=72;band=44;footer=44
    canvas=Image.new('RGB',(size*2,header+len(rows)*(size+band)+footer),'#181b1e')
    draw=ImageDraw.Draw(canvas);font=ImageFont.truetype(font_path,20 if size==640 else 28)
    small=ImageFont.truetype(font_path,16 if size==640 else 23)
    draw.text((16,10),'V20 | A: CORE SUPPRESSION    B: BROAD HALO SUPPRESSION',font=font,fill='white')
    draw.text((16,40),subtitle,font=small,fill='#c6d5dc')
    sources=[]
    for row,shot in enumerate(rows):
        for col,var in enumerate(('a','b')):
            filename=f'cycles-v20{var}-{shot}.png';im=Image.open(root/filename).convert('RGB')
            assert im.size==(size,size),(filename,im.size)
            x=col*size;y=header+row*(size+band)
            draw.text((x+14,y+10),f'{var.upper()} | {shot.upper().replace("-"," ")}',font=font,fill='white')
            canvas.paste(im,(x,y+band))
            sources.append({'file':filename,'sha256':hashlib.sha256((root/filename).read_bytes()).hexdigest(),'image_resized':False})
    draw.text((16,canvas.height-footer+12),'Same core, ridge, material, camera and light. Only the cell-smoothing field changes.',font=small,fill='#c6d5dc')
    canvas.save(root/name)
    return {'sheet':name,'source_images':sources,'postprocessing':'labels and arrangement only; no image pixel edits or resizing'}

def difference(shot):
    xa=json.loads((root/f'cycles-v20a-{shot}.json').read_text());xb=json.loads((root/f'cycles-v20b-{shot}.json').read_text())
    assert xa['settings']==xb['settings'],f'Nonmatched camera/light/render settings: {shot}'
    A=np.asarray(Image.open(root/f'cycles-v20a-{shot}.png').convert('RGB'),dtype=np.float32)/255
    B=np.asarray(Image.open(root/f'cycles-v20b-{shot}.png').convert('RGB'),dtype=np.float32)/255
    D=np.abs(A-B)
    return {'shot':shot,'settings_identical':True,'mean_absolute_srgb_difference':float(D.mean()),'fraction_pixels_max_rgb_difference_gt_0_01':float((D.max(axis=2)>.01).mean()),'meaning':'Pixel difference only; NOT a realism score. Denoising can spread local differences.'}

results={'sheets':[
    montage(['plane','bite'],'v20-cycles-A-B-comparison.png',640,'Actual Blender 5.2.4 Cycles CPU | 640 px, 24 samples | independent ARTIST fields'),
    montage(['macro','macro-clay'],'v20-macro-A-B-comparison.png',1024,'Actual Cycles | 12 mm field of view | 1024 px, 32 samples | clay excludes shader bump')],
    'comparisons':[difference(s) for s in ['plane','bite','macro','macro-clay']]}
(root/'render_comparison_evidence.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))

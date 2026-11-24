from pathlib import Path
import hashlib,json,numpy as np
from PIL import Image,ImageDraw,ImageFont
import sys
baseline=Path(sys.argv[1]); work=Path(sys.argv[2]); out=work/'comparison.png'; assert not out.exists()
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';f=ImageFont.truetype(fontpath,18);h=ImageFont.truetype(fontpath,14)
shots=['plane','macro','bite'];variants=['A','B','C'];canvas=Image.new('RGB',(3*480,3*480+70),'#202124');d=ImageDraw.Draw(canvas)
for i,label in enumerate(['A  Shadow correction','B  Clearance-dependent tint','C  Radial scattering scale']):d.text((i*480+240,18),label,font=f,anchor='mm',fill='white')
report={}
for r,shot in enumerate(shots):
    paths=[baseline/f'{shot}-B.png',work/f'{shot}-B.png',work/f'{shot}-C.png']; images=[]; receipts=[]
    for c,p in enumerate(paths):
        rec=json.loads(p.with_suffix('.json').read_text());assert hashlib.sha256(p.read_bytes()).hexdigest()==rec['png_sha']; receipts.append(rec);im=Image.open(p).convert('RGB');assert im.size==(480,480);images.append(np.asarray(im,dtype=np.int16));canvas.paste(im,(c*480,36+r*480));
    keys=['shot','camera','seed','resolution','samples','voxel_mm','visible_shadow','juice_gain','cell_gain','vascular_gain'];assert all(all(q[k]==receipts[0][k] for k in keys) for q in receipts)
    report[shot]={}
    for c,v in enumerate(['B','C'],1):
        delta=np.abs(images[c]-images[0]);report[shot][v]={'pixels_gt2_pct':float(np.mean(delta.max(axis=2)>2)*100),'pixels_gt10_pct':float(np.mean(delta.max(axis=2)>10)*100),'mean_abs_rgb_change':float(delta.mean()),'A_png_sha':receipts[0]['png_sha'],'variant_png_sha':receipts[c]['png_sha'],'matched_settings':True}
    d.text((6,36+r*480+6),shot.upper(),font=h,fill='white',stroke_width=2,stroke_fill='black')
d.text((720,3*480+52),'Blender Cycles 480 x 480 | 8 samples | same geometry, cameras, lights and seed',font=h,fill='white',anchor='mm');canvas.save(out);(work/'render-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

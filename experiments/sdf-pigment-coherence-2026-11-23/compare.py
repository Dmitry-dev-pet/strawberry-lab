from pathlib import Path
import hashlib,json,numpy as np,sys
from PIL import Image,ImageDraw,ImageFont
baseline=Path(sys.argv[1]); work=Path(sys.argv[2]);out=work/'comparison.png';assert not out.exists()
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
canvas=Image.new('RGB',(960,3*480+70),'#202124');d=ImageDraw.Draw(canvas)
for i,label in enumerate(['A: Shadow correction (baseline)','B: Coherent tissue pigment']):d.text((i*480+240,18),label,font=font,anchor='mm',fill='white')
report={};keys=['shot','camera','seed','resolution','samples','voxel_mm','visible_shadow','juice_gain','cell_gain','vascular_gain']
for r,shot in enumerate(['plane','macro','bite']):
 ps=[baseline/f'{shot}-B.png',work/f'{shot}-B.png'];images=[];receipts=[]
 for c,p in enumerate(ps):
  rec=json.loads(p.with_suffix('.json').read_text());assert hashlib.sha256(p.read_bytes()).hexdigest()==rec['png_sha'];receipts.append(rec);im=Image.open(p).convert('RGB');assert im.size==(480,480);images.append(np.asarray(im,dtype=np.int16));canvas.paste(im,(c*480,36+r*480))
 assert all(receipts[0][k]==receipts[1][k] for k in keys);delta=np.abs(images[1]-images[0]);report[shot]={'pixels_gt2_pct':float(np.mean(delta.max(axis=2)>2)*100),'pixels_gt10_pct':float(np.mean(delta.max(axis=2)>10)*100),'mean_abs_rgb_change':float(delta.mean()),'A_receipt':receipts[0],'B_receipt':receipts[1],'matched_settings':True}
 d.text((6,42+r*480),shot.upper(),font=small,fill='white',stroke_width=2,stroke_fill='black')
d.text((480,3*480+52),'Blender Cycles 480 x 480 | 8 samples | same cameras, geometry, lights and seed',font=small,anchor='mm',fill='white');canvas.save(out);(work/'render-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print({k:{x:round(v[x],3) for x in ['pixels_gt2_pct','pixels_gt10_pct','mean_abs_rgb_change']} for k,v in report.items()})

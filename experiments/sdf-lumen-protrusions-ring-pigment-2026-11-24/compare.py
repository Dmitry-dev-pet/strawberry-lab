"""Compare matched native Cycles PNGs, not reference-fidelity scores."""
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,hashlib,sys
from pathlib import Path
root=Path(sys.argv[1]);out=Path(sys.argv[2]);
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[('Vascular ring: pigment',root/'ring-lab/plane-B.png',out/'ring-pigment-plane.png'),('Lumen: attached tissue',root/'lumen-lab/plane-B.png',out/'lumen-protrusions-plane.png')]
canvas=Image.new('RGB',(960,1060),(31,35,38));d=ImageDraw.Draw(canvas);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19);head=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',22);report={}
for i,(title,a,b) in enumerate(rows):
 ja=json.loads(a.with_suffix('.json').read_text());jb=json.loads(b.with_suffix('.json').read_text());assert digest(a)==ja['png_sha'] and digest(b)==jb['png_sha'];keys=['shot','visible_shadow','juice_gain','cell_gain','vascular_gain','voxel_mm','resolution','samples','seed','camera'];assert all(ja[k]==jb[k] for k in keys)
 ia=Image.open(a).convert('RGB');ib=Image.open(b).convert('RGB');x=np.abs(np.asarray(ia,dtype=np.int16)-np.asarray(ib,dtype=np.int16)).max(axis=2);report[title]={'A':ja,'B':jb,'changed_gt_2_255_percent':float((x>2).mean()*100),'changed_gt_10_255_percent':float((x>10).mean()*100),'matched_settings':keys};y=530*i;d.text((18,y+4),title,font=head,fill='white');d.text((18,y+29),'A - existing',font=font,fill='white');d.text((498,y+29),'B - new',font=font,fill='white');canvas.paste(ia,(0,y+50));canvas.paste(ib,(480,y+50))
canvas.save(out/'comparison.png');(out/'render-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:{x:v[x] for x in ('changed_gt_2_255_percent','changed_gt_10_255_percent')} for k,v in report.items()},indent=2))

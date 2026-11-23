from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,hashlib,sys
base,ring,lumen,out=map(Path,sys.argv[1:]);out.mkdir(exist_ok=True);sources=[base,ring,lumen];ims=[];rs=[]
for d in sources:
 p=d/'plane-B.png';r=json.loads(p.with_suffix('.json').read_text());assert hashlib.sha256(p.read_bytes()).hexdigest()==r['png_sha'];ims.append(Image.open(p).convert('RGB'));rs.append(r)
for r in rs[1:]:
 for k in ['camera','resolution','samples','seed','voxel_mm','juice_gain','cell_gain','vascular_gain','visible_shadow']:assert r[k]==rs[0][k],k
sheet=Image.new('RGB',(1440,530),(28,31,35));draw=ImageDraw.Draw(sheet);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
for i,(im,label) in enumerate(zip(ims,['A: Previous model','B: Vascular ring only','C: Inner cavity only'])):
 sheet.paste(im,(480*i,0));draw.text((480*i+15,494),label,font=font,fill=(240,240,240))
sheet.save(out/'comparison.png');a=np.asarray(ims[0],dtype=np.int16);result={}
for key,im in zip(['ring','cavity'],ims[1:]):
 d=np.max(np.abs(np.asarray(im,dtype=np.int16)-a),axis=2);result[key]={'changed_gt_2':float((d>2).mean()),'changed_gt_10':float((d>10).mean())}
(out/'render-comparison.json').write_text(json.dumps({'receipt':rs,'pixel_change_not_quality':result},indent=2)+'\n');print(result)

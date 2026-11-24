"""Matched diagnostic render sheet; no visual similarity metric."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from PIL import Image,ImageDraw
p=Path(sys.argv[1]);out=Image.new('RGB',(1100,1158),(245,245,245));d=ImageDraw.Draw(out);d.text((20,13),'A: previous unsigned classification',fill=(30,30,30));d.text((570,13),'B: signed SDF + reference surface',fill=(30,30,30));rows=[]
for i,pose in enumerate(('tilted','bite')):
 a,b=[p/f'{pose}-{x}.png' for x in ('A','B')];ra,rb=[json.loads(x.with_suffix('.json').read_text()) for x in (a,b)];sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();assert sha(a)==ra['image_sha'] and sha(b)==rb['image_sha'];assert all(ra[k]==rb[k] for k in ('pose','voxel_mm','engine','resolution','camera_matrix','camera_ortho_scale'));ims=[Image.open(x).convert('RGB') for x in (a,b)];diff=np.abs(np.asarray(ims[0],dtype=np.int16)-np.asarray(ims[1],dtype=np.int16)).max(axis=2);rows.append({'pose':pose,'A':ra,'B':rb,'changed_gt_2_percent':float((diff>2).mean()*100),'changed_gt_10_percent':float((diff>10).mean()*100)});y=30+i*560;d.text((20,y+2),pose,fill=(30,30,30));out.paste(ims[0].resize((536,536),Image.Resampling.LANCZOS),(8,y+20));out.paste(ims[1].resize((536,536),Image.Resampling.LANCZOS),(556,y+20))
out.save(p/'comparison.png');(p/'render-comparison.json').write_text(json.dumps(rows,indent=2)+'\n');print([(r['pose'],r['changed_gt_2_percent'],r['changed_gt_10_percent']) for r in rows])

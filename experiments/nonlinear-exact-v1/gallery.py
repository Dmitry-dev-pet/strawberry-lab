from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
p=Path('build/nonlinear-exact-v1');rows=[['shouldered-fast-beauty-cut','shouldered-exact-beauty-cut'],['waisted-fast-beauty-cut','waisted-exact-beauty-cut'],['shouldered-fast-clay-isolated','shouldered-exact-clay-isolated']]
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();c=Image.new('RGB',(1500,2370),(25,28,30));d=ImageDraw.Draw(c)
for row,names in enumerate(rows):
 for col,name in enumerate(names):
  f=p/(name+'.png');r=json.loads(f.with_suffix('.json').read_text());assert r['source_sha256']==sha(p/(name.split('-')[0]+'.blend')) and r['png_sha256']==sha(f) and r['quality']==['fast','exact'][col]
  assert r['look']==('clay' if row==2 else 'beauty') and r['frame']==('oblique' if row==2 else 'cut')
  c.paste(Image.open(f).convert('RGB'),(col*750,row*790+40));d.text((col*750+12,row*790+12),name+' | 750px 12samples',fill='white')
c.save(p/'comparison.png')

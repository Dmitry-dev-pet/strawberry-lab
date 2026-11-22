from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
p=Path('build/live-profile-v1');sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();rows=[['A-whole','B-whole'],['A-exact-cut','B-exact-cut'],['vascular-zero-clay','vascular-on-clay']]
c=Image.new('RGB',(1500,2370),(25,28,30));d=ImageDraw.Draw(c)
for row,names in enumerate(rows):
 for col,name in enumerate(names):
  f=p/(name+'.png');r=json.loads(f.with_suffix('.json').read_text());assert r['frame']==name and r['source_sha256']==sha(p/'live-profile.blend') and r['png_sha256']==sha(f)
  if row<2:assert abs(r['profile']['a']-[.23,-.12][col])<1e-6
  else:assert abs(r['vascular_mm']-[0,.12][col])<1e-6
  c.paste(Image.open(f).convert('RGB'),(col*750,row*790+40));d.text((col*750+12,row*790+12),name+' | same open scene | 750px 12samples',fill='white')
c.save(p/'comparison.png')

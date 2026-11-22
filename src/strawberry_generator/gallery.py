from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
p=Path('build/generator-v1-final');c=Image.new('RGB',(1500,1580),(25,28,30));d=ImageDraw.Draw(c);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
for row,frame in enumerate(['whole','cut']):
 for col,seed in enumerate([101,202]):
  folder=p/f'seed{seed}';f=folder/(frame+'.png');r=json.loads(f.with_suffix('.json').read_text());receipt=json.loads((folder/'receipt.json').read_text());assert r['frame']==frame and r['recipe']['seed']==seed and r['scene_sha256']==receipt['scene_sha256'] and r['png_sha256']==sha(f)
  c.paste(Image.open(f).convert('RGB'),(col*750,row*790+40));d.text((col*750+12,row*790+12),f'NEW scatter seed{seed} | {frame} | Fast only | 750px 12samples',fill='white')
c.save(p/'comparison.png')

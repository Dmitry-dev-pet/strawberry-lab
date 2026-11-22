from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw
p=Path('build/unified-context-v1');canvas=Image.new('RGB',(1500,2370),(27,30,32));d=ImageDraw.Draw(canvas)
for row,frame in enumerate(['whole','cut','oblique']):
 for col,v in enumerate(['elongated','round']):
  image=p/f'{v}-{frame}.png';r=json.loads(image.with_suffix('.json').read_text());m=json.loads((p/f'{v}.json').read_text())
  assert r['frame']==frame and r['source_sha256']==m['scene_sha256'] and r['png_sha256']==hashlib.sha256(image.read_bytes()).hexdigest()
  canvas.paste(Image.open(image).convert('RGB'),(col*750,row*790+40));d.text((col*750+15,row*790+12),f'{v.upper()} | {frame} | width {m["recipe"]["params"]["width_factor"]} / height {m["recipe"]["params"]["height_factor"]}',fill='white')
canvas.save(p/'comparison.png')

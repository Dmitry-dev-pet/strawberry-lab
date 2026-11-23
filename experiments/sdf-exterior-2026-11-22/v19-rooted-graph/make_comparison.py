"""Pair original Blender Cycles A/B images without modifying source pixels."""
import os,json,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np
ROOT=Path(os.environ.get('STRAWBERRY_V19_OUT',str(Path(__file__).resolve().parent))).expanduser().resolve()
src={(v,shot):ROOT/f'cycles-v19{v}-{shot}-640px-24s.png' for v in ('a','b') for shot in ('planar','bite')}
assert all(p.is_file() for p in src.values()),src
arr={(v,shot):np.asarray(Image.open(p).convert('RGB'),np.float32)/255 for (v,shot),p in src.items()}
report={}
for shot in ('planar','bite'):
 d=np.max(np.abs(arr['a',shot]-arr['b',shot]),axis=-1)
 report[shot]={'changed_pixels_gt_0_01_pct':round(100*float(np.mean(d>.01)),4),'mean_abs_rgb':round(float(np.mean(np.abs(arr['a',shot]-arr['b',shot]))),5),'max_rgb_difference':round(float(d.max()),5)}
(ROOT/'v19-cycles-pixels.json').write_text(json.dumps(report,indent=2)+'\n')
H=44;W=640
canvas=Image.new('RGB',(2*W,2*(W+H)),'#1b1d20')
draw=ImageDraw.Draw(canvas)
try: font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19)
except OSError:font=ImageFont.load_default()
for row,shot in enumerate(('planar','bite')):
 for col,v in enumerate(('a','b')):
  x=col*W;y=row*(W+H)
  draw.text((x+14,y+12),f"{shot.upper()} | v19{v.upper()} {'FIELD ONLY' if v=='a' else 'PHYSICAL TUBES'}",font=font,fill='white')
  canvas.paste(Image.open(src[v,shot]).convert('RGB'),(x,y+H))
out=ROOT/'v19-cycles-A-B-comparison.png'
canvas.save(out,optimize=True)
print('REAL_CYCLES_COMPARISON',out.stat().st_size,report)

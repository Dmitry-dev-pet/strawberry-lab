"""Arrange real Blender frames, and the user-supplied private author still.
No generative imagery, retouching or synthetic author frame."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
ROOT=Path(__file__).resolve().parent;O=ROOT/'outputs'
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
large=ImageFont.truetype(fontpath,25);small=ImageFont.truetype(fontpath,17)
W,H=680,int(680*920/820)
def make(paths, labels, title, name, footer):
 n=len(paths);canvas=Image.new('RGB',(n*W,H+125),'#181c24');d=ImageDraw.Draw(canvas)
 d.text((25,11),title,font=large,fill='#f9f9fb')
 for j,(path,label) in enumerate(zip(paths,labels)):
  im=Image.open(path).convert('RGB').resize((W,H))
  canvas.paste(im,(j*W,53))
  d.text((j*W+20,55),label,font=large,fill='#fffbf1',stroke_width=1,stroke_fill='#1c1f26')
 d.text((20,H+70),footer,font=small,fill='#e0e4e8')
 canvas.save(O/name,quality=91)
make([O/'only-v2.png',O/'only-28-sag0.25.png',O/'only-28-sag1.0.png',O/'only-28-sag1.8.png'],
 ['V2  |  radial','V3  |  Sag 0.25','V3  |  Sag 1.00','V3  |  Sag 1.80'],
 'ONE SET OF 539 ACHENE TARGETS — same camera & light',
 'real-ab-sag.jpg','100% authentic Blender Cycles 5.2.4; identical 539 seed positions; tissue cut not regenerated')
make([O/'only-14-sag1.0.png',O/'only-28-sag1.0.png',O/'only-40-sag1.0.png'],
 ['14 carriers','28 carriers','40 carriers'],'VESSEL STRANDS — all target points unchanged',
 'real-ab-strands.jpg','100% authentic Blender Cycles 5.2.4; fixed sag 1.0, camera, light, achene targets')
# Reference is a real video frame supplied by user; deliberately label incomparable camera/zoom.
author_path=ROOT/'private-frucht-video-ref15.jpg'
if not author_path.is_file():
 print('PRIVATE FRUCHT IMAGE NOT SUPPLIED: skipping author comparison');raise SystemExit(0)
author=Image.open(author_path).convert('RGB')
canvas=Image.new('RGB',(W*3,H+125),'#181c24');d=ImageDraw.Draw(canvas)
d.text((25,11),'REFERENCE / OUR BASELINE / V3 — morphology only',font=large,fill='white')
ref=author.resize((W,H))
for j,(im,label) in enumerate([(ref,'Frucht 00:15 | VIDEO'),(Image.open(O/'only-v2.png').convert('RGB'),'V2 | our actual 3D'),(Image.open(O/'only-28-sag1.0.png').convert('RGB'),'V3 | Bezier & profile')]):
 canvas.paste(im,(j*W,53));d.text((j*W+16,55),label,font=large,fill='white',stroke_width=1,stroke_fill='#202328')
d.text((20,H+70),'PRIVATE author video still; DIFFERENT camera/zoom/motion vs same-camera Blender V2/V3; NOT pixel parity',font=small,fill='#e0e4e8')
canvas.save(O/'private-frucht-v2-v3-comparison.jpg',quality=91)
print('COMPARISONS_FROM_REAL_IMAGES_ONLY',flush=True)

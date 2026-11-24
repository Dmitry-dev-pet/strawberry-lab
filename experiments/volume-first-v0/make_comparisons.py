from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parent;out=ROOT/'outputs'
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';big=ImageFont.truetype(font,23);small=ImageFont.truetype(font,15)
angles=[0,32,82]
imgs=[Image.open(out/f'slice-{x:03d}.png').convert('RGB') for x in angles]
W,H=imgs[0].size
montage=Image.new('RGB',(3*W,H+82),'#17191e');d=ImageDraw.Draw(montage)
for i,im in enumerate(imgs):
 montage.paste(im,(i*W,48));d.text((i*W+18,13),f'CUT {angles[i]:02d}° · same 150³ substrate',font=big,fill='white')
d.text((20,H+54),'Independent Blender 5.2.4 / Cycles / identical camera & light / 3D color, relief, pith & filaments',font=small,fill='#dde1e7')
montage.save(out/'three-cuts-one-volume.jpg',quality=91)
reference_path=Path(os.environ.get('STRAWBERRY_FRUCHT_FRAME',str(ROOT/'private-reference-frame.jpg')))
if not reference_path.exists():
 print('Optional Frucht comparison skipped; set STRAWBERRY_FRUCHT_FRAME=path to authorized reference frame')
 raise SystemExit(0)
reference=Image.open(reference_path).convert('RGB')
ref=reference.crop((146,250,870,1165)).resize((W,H),Image.Resampling.LANCZOS)
compare=Image.new('RGB',(W*2,H+82),'#17191e');dr=ImageDraw.Draw(compare)
compare.paste(ref,(0,48));compare.paste(imgs[0],(W,48))
dr.text((18,13),'Frucht video · 00:10.5 · reference',font=big,fill='white')
dr.text((W+18,13),'Strawberry Lab · static 3D POC 0°',font=big,fill='white')
dr.text((18,H+54),'Private video frame at left; actual Blender CPU Cycles at right; NOT visual parity',font=small,fill='#dde1e7')
compare.save(out/'frucht-versus-new-poc.jpg',quality=92)
print('MONTAGES_SAVED',montage.size,compare.size)

from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
root=Path('/mnt/data/strawberry-m1e6')
old=Path('/mnt/data/strawberry-m1e5/m1e5-live-exact-frame15.png')
frames=[(old,'M1e5  |  Python+BMesh Exact'),(root/'m1e6-PRODUCTION-F15.png','M1e6  |  Pure GN Beauty'),(root/'m1e6-nativeGN-FiberDiagnostic-F15.png','M1e6  |  GN Fiber Diagnostic')]
font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font=ImageFont.truetype(font_path,25)
small=ImageFont.truetype(font_path,17)
canvas=Image.new('RGB',(720*3,820),'#171b23');d=ImageDraw.Draw(canvas)
for ix,(path,label) in enumerate(frames):
 im=Image.open(path).convert('RGB')
 assert im.size==(720,720)
 canvas.paste(im,(ix*720,50))
 d.text((ix*720+22,12),label,font=font,fill='white')
d.text((24,781),'Source: authentic Blender 5.2.4 CPU Cycles · Frame 15 · 720×720 · 16 samples · identical camera and lights',font=small,fill='#e5e7eb')
canvas.save(root/'m1e6-real-three-way-compare.jpg',quality=92)
# Frame21 controlled comparison
f21=[(Path('/mnt/data/strawberry-m1e5/m1e5-live-exact-frame21.png'),'M1e5  |  Live Exact'),(root/'m1e6-nativeGN-Beauty-F21.png','M1e6  |  Pure GN')]
c2=Image.new('RGB',(1440,820),'#171b23');dr=ImageDraw.Draw(c2)
for ix,(p,lab) in enumerate(f21):
 im=Image.open(p).convert('RGB');assert im.size==(720,720);c2.paste(im,(ix*720,50));dr.text((ix*720+22,12),lab,font=font,fill='white')
dr.text((24,781),'Frame 21 · Blender CPU Cycles · 720px / 16 samples · fixed camera and lighting',font=small,fill='#e5e7eb')
c2.save(root/'m1e6-frame21-compare.jpg',quality=92)
print('MONTAGE_PASSED',canvas.size,c2.size)

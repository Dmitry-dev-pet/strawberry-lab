"""Compare actual owner-provided video still and authentic Blender renders only."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
ROOT=Path(__file__).resolve().parent
W,H=820,920
F='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font=ImageFont.truetype(F,22)
small=ImageFont.truetype(F,15)
old=Image.open(ROOT/'v1-original-494-only.png').convert('RGB')
new=Image.open(ROOT/'v2-only-539-anchored.png').convert('RGB')
ref=Image.open(ROOT/'private-frucht-video-ref15.jpg').convert('RGB')
# Original promo frame is taller than the matched Blender camera frame. Crop
# center only to preserve reference proportions; views remain *non-equivalent*.
crop_width=1080;crop_height=int(1080*H/W)
ref=ref.crop((0,max(0,(ref.height-crop_height)//2),1080,min(ref.height,(ref.height+crop_height)//2))).resize((W,H),Image.Resampling.LANCZOS)
assert old.size==new.size==(W,H)
images=[(ref,'FRUCHT  ~00:15  [VIDEO]'),(old,'V1  |  494 free ends'),(new,'V2  |  539 seed-linked ends')]
canvas=Image.new('RGB',(W*3,H+86),'#181c24');d=ImageDraw.Draw(canvas)
for i,(im,label) in enumerate(images):
 canvas.paste(im,(i*W,48))
 d.text((i*W+14,14),label,font=font,fill='#ffffff')
d.text((20,H+59),'Real author video / two authentic Blender 5.2.4 Cycles renders  •  Different scale and camera  •  PRIVATE reference',font=small,fill='#f1f3f7')
canvas.save(ROOT/'author-vs-v1-v2-real.jpg',quality=91)
imgs=[('v2-only-539-anchored.png','ONLY   |   539 anchor endings'),('v2-translucent-fruit.png','GHOST   |   body outline'),('v2-actual-cut-overlay.png','CUT   |   unchanged v1 cut')]
board=Image.new('RGB',(W*3,H+80),'#181c24');dr=ImageDraw.Draw(board)
for i,(name,label) in enumerate(imgs):
 board.paste(Image.open(ROOT/name).convert('RGB'),(i*W,45))
 dr.text((i*W+14,13),label,font=font,fill='#ffffff')
dr.text((20,H+53),'Same 28+539 3D source in three views. Actual Blender CPU Cycles. Body/cut remain unchanged.',font=small,fill='#f1f3f7')
board.save(ROOT/'v2-three-blender-views.jpg',quality=91)
print('COMPARE_REAL_IMAGES_PASS',canvas.size,board.size)

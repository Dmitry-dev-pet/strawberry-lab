"""Verify archived and fresh frame receipts, make a labeled original-render contact sheet."""
import json, hashlib, shutil, sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np
H=Path(__file__).resolve().parent
B=Path(sys.argv[1]);S='7443e948ca2dc90e23a891f1262ff0afd68bb501f49c4a3d8f323fcff4f2a173';NEW=json.loads((H/'exact-pigment.json').read_text())['scene_sha']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
keys=['pose','juice_gain','juice_optics_mode','flesh_material_mode','tissue_gain','exact_voxel_mm','cap_refine_level','engine','samples','seed','resolution','camera_matrix','ortho_scale','lights']
(H/'baseline').mkdir(exist_ok=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
img=Image.new('RGB',(1120,3*560+120),(26,29,33));d=ImageDraw.Draw(img);d.text((18,8),'A  Previous pigment',fill='white',font=font);d.text((578,8),'B  Warm regional pigment v2',fill='white',font=font)
report={}
for i,pose in enumerate(('plane','macro','bite')):
 a=B/f'{pose}-2.png';b=H/f'{pose}-1.png';ar=json.loads(a.with_suffix('.json').read_text());br=json.loads(b.with_suffix('.json').read_text());assert ar['scene_sha']==S and br['scene_sha']==NEW and br['pigment_revision']==1 and sha(a)==ar['image_sha'] and sha(b)==br['image_sha'];assert all(ar[k]==br[k] for k in keys),[(k,ar[k],br[k]) for k in keys if ar[k]!=br[k]]
 for p in (a,a.with_suffix('.json')):shutil.copyfile(p,H/'baseline'/p.name)
 ai=Image.open(a).convert('RGB');bi=Image.open(b).convert('RGB');y=40+i*586;img.paste(ai,(0,y));img.paste(bi,(560,y));d.text((12,y+560),pose.upper(),fill='white',font=small);delta=np.abs(np.array(ai,dtype=np.int16)-np.array(bi,dtype=np.int16));report[pose]={'a':ar,'b':br,'mean_abs_rgb_delta':float(delta.mean()),'percent_max_channel_gt_2':float((delta.max(2)>2).mean()*100),'percent_max_channel_gt_10':float((delta.max(2)>10).mean()*100)}
img.save(H/'comparison.png');(H/'render-comparison.json').write_text(json.dumps({'scope':'Archived A / fresh B, matched listed settings; pixels, not quality','rows':report},indent=2)+'\n');print([(k,round(v['percent_max_channel_gt_2'],2)) for k,v in report.items()])

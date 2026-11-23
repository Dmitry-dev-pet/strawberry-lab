"""Original Cycles paired comparison; checks exact camera, light, mode and SHA receipts."""
import json,hashlib,argparse
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--json',required=True,type=Path);a=p.parse_args();root=a.root;assert not a.out.exists() and not a.json.exists()
rows=[('BITE',480,16,'bite-A-480','bite-B-480'),('BITE MACRO',320,4,'bite-macro-A-320','bite-macro-B-320')]
records={'status':'PASS_MATCHED_NATIVE_CYCLES','disclaimer':'pixel changes are not realism/fidelity scores','comparisons':{}}
out=Image.new('RGB',(960,515+515),(24,26,30));d=ImageDraw.Draw(out)
for i,(label,res,samples,an,bn) in enumerate(rows):
 imgs=[];met=[]
 for name in [an,bn]:
  img=root/(name+'.png');rec=json.loads((root/(name+'.json')).read_text());assert hashlib.sha256(img.read_bytes()).hexdigest()==rec['image_sha256'];imgs.append(Image.open(img).convert('RGB'));met.append(rec)
 for field in ['blender','shot','resolution','samples','seed','camera','cutter','lights','view']:
  assert met[0][field]==met[1][field],(label,field)
 assert met[0]['gain']==0 and met[1]['gain']==1 and met[0]['resolution']==res and met[0]['samples']==samples
 ar=np.asarray(imgs[0],np.int16);br=np.asarray(imgs[1],np.int16);dt=np.abs(ar-br);mm=dt.max(2)
 records['comparisons'][label]={'pixels_gt2':float((mm>2).mean()),'pixels_gt10':float((mm>10).mean()),'pixels_gt25':float((mm>25).mean()),'mean_absolute_rgb255':float(dt.mean()),'max_channel_delta':int(mm.max()),'render_s':{'A':met[0]['seconds'],'B':met[1]['seconds']},'sizes':[met[0]['verts'],met[1]['verts']],'render_sha':[met[0]['image_sha256'],met[1]['image_sha256']]}
 for j,im in enumerate(imgs):
  if im.width!=480:im=im.resize((480,480),Image.Resampling.NEAREST)
  out.paste(im,(480*j,515*i+35));d.text((480*j+14,515*i+9),label+(' / A original' if j==0 else ' / B attached pull-out'),fill=(235,235,235))
print(json.dumps(records,indent=2));out.save(a.out);a.json.write_text(json.dumps(records,indent=2)+'\n')

import subprocess,json
from pathlib import Path
from PIL import Image,ImageChops
p=Path('build/live-profile-v1/cross-layer');p.mkdir(exist_ok=False);result={}
for layer in ['MATCHED','FLESH ONLY']:
 frames=[]
 for case in ['candidate','control']:
  png=p/(layer.lower().replace(' ','-')+'-'+case+'.png');frames.append(png)
  with png.with_suffix('.log').open('w') as f:subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender','-b','--factory-startup','--disable-autoexec','-t','4','--python-exit-code','1','--python','experiments/live-profile-seed-strands-v1/cross_frame.py','--','build/live-profile-v1/live-profile.blend',layer,case,str(png)],stdout=f,stderr=subprocess.STDOUT,check=True)
 assert ImageChops.difference(Image.open(frames[0]).convert('RGB'),Image.open(frames[1]).convert('RGB')).getbbox() is None
 result[layer]={'candidate':json.loads(frames[0].with_suffix('.json').read_text()),'control':json.loads(frames[1].with_suffix('.json').read_text()),'profile_A_to_B_in_WHOLE':True,'pixels_identical':True}
(p/'validation.json').write_text(json.dumps(result,indent=2)+'\n')

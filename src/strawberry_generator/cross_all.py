from pathlib import Path
import subprocess,json
from PIL import Image,ImageChops
p=Path('build/generator-v1-final/cross-layer');p.mkdir(exist_ok=False);result={}
for seed in [101,202]:
 result[str(seed)]={}
 for layer in ['MATCHED','FLESH ONLY']:
  frames=[]
  for case in ['candidate','control']:
   png=p/(f'{seed}-'+layer.lower().replace(' ','-')+'-'+case+'.png');frames.append(png)
   with png.with_suffix('.log').open('w') as f:subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender','-b','--factory-startup','--disable-autoexec','-t','4','--python-exit-code','1','--python','src/strawberry_generator/cross_frame.py','--',f'build/generator-v1-final/seed{seed}/strawberry.blend',layer,case,str(png)],stdout=f,stderr=subprocess.STDOUT,check=True)
  assert ImageChops.difference(Image.open(frames[0]).convert('RGB'),Image.open(frames[1]).convert('RGB')).getbbox() is None
  result[str(seed)][layer]={'pixels_identical':True,'cases':[json.loads(f.with_suffix('.json').read_text()) for f in frames]}
(p/'validation.json').write_text(json.dumps(result,indent=2)+'\n')

"""Run the existing cross-layer stale-cap regression against both variants."""
from pathlib import Path
import json,subprocess,sys
from PIL import Image,ImageChops
root=Path(__file__).resolve().parents[2];out=root/'build/nonlinear-exact-v1/cross-layer';out.mkdir(exist_ok=False)
blender='/Applications/Blender.app/Contents/MacOS/Blender'
result={}
for variant in ['shouldered','waisted']:
 result[variant]={}
 for layer in ['MATCHED','FLESH ONLY']:
  name=layer.lower().replace(' ','-');frames=[]
  for case in ['candidate','control']:
   png=out/f'{variant}-{name}-{case}.png';frames.append(png)
   with png.with_suffix('.log').open('w') as log:
    subprocess.run([blender,'-b','--factory-startup','--disable-autoexec','-t','4','--python-exit-code','1','--python',str(root/'experiments/geometric-achene-pits-v1/check_cross_layer.py'),'--',str(root/f'build/nonlinear-exact-v1/{variant}.blend'),layer,case,str(png)],stdout=log,stderr=subprocess.STDOUT,check=True)
  assert ImageChops.difference(Image.open(frames[0]).convert('RGB'),Image.open(frames[1]).convert('RGB')).getbbox() is None
  result[variant][layer]={'pixel_identical':True,'candidate':json.loads(frames[0].with_suffix('.json').read_text()),'control':json.loads(frames[1].with_suffix('.json').read_text())}
(out/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print('Both variants MATCHED/FLESH ONLY cross-layer render PASS')

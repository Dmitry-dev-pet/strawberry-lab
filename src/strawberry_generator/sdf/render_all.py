from pathlib import Path
import subprocess
p=Path('build/sdf-slice-v1/final')
for kind in ['whole','plane','sphere','macro','oblique']:
 with (p/f'{kind}.log').open('w') as f:subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender','-b','--factory-startup','--disable-autoexec','-t','4','--python-exit-code','1','--python','src/strawberry_generator/sdf/render.py','--',str(p/'strawberry-sdf.blend'),kind,str(p/(kind+'.png'))],stdout=f,stderr=subprocess.STDOUT,check=True)

from pathlib import Path
import subprocess
B='/Applications/Blender.app/Contents/MacOS/Blender';p=Path('build/nonlinear-exact-v1')
for v,q,l,pose in [(v,q,'beauty','cut') for v in ['shouldered','waisted'] for q in ['fast','exact']]+[('shouldered',q,'clay','oblique') for q in ['fast','exact']]:
 stem=f'{v}-{q}-{l}-'+('isolated' if l=='clay' else pose)
 with (p/f'{stem}.log').open('w') as f:subprocess.run([B,'-b','--factory-startup','--disable-autoexec','-t','4','--python-exit-code','1','--python','experiments/nonlinear-exact-v1/render.py','--',str(p/f'{v}.blend'),q,l,pose,str(p/f'{stem}.png')],stdout=f,stderr=subprocess.STDOUT,check=True)

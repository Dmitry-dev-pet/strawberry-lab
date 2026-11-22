from pathlib import Path
import subprocess
B='/Applications/Blender.app/Contents/MacOS/Blender';p=Path('build/nonlinear-final')
def run(script,args,log):
 with log.open('w') as f:subprocess.run([B,'-b','--factory-startup','--disable-autoexec','-t','4','--python-exit-code','1','--python',script,'--',*map(str,args)],stdout=f,stderr=subprocess.STDOUT,check=True)
run('experiments/nonlinear-cut-v1/qa.py',[p/'waisted.blend',p/'waisted-qa.json'],p/'waisted-qa.log')
for v in ['shouldered','waisted']:
 for frame in ['whole','cut','oblique']:run('experiments/nonlinear-cut-v1/render.py',[p/f'{v}.blend',frame,p/f'{v}-{frame}.png'],p/f'{v}-{frame}.log')

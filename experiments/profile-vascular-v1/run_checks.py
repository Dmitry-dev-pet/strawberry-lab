import subprocess
from pathlib import Path
B='/Applications/Blender.app/Contents/MacOS/Blender';p=Path('build/profile-vascular-final')
def run(script,args,log):
 with log.open('w') as f:subprocess.run([B,'-b','--factory-startup','--disable-autoexec','-t','4','--python-exit-code','1','--python',script,'--',*map(str,args)],stdout=f,stderr=subprocess.STDOUT,check=True)
for v in ['elongated','round']:
 run('experiments/profile-vascular-v1/validate_graph.py',[p/f'{v}.blend',p/f'{v}-graph-qa.json'],p/f'{v}-graph-qa.log')
 run('experiments/unified-strawberry-context-v1/validate_unified.py',['build/inputs/pr34-pits.blend',p/f'{v}.blend',p/f'{v}-cut-qa.json'],p/f'{v}-cut-qa.log')
 for frame in ['whole','cut','graph']:run('experiments/profile-vascular-v1/render_graph.py',[p/f'{v}.blend',frame,p/f'{v}-{frame}.png'],p/f'{v}-{frame}.log')

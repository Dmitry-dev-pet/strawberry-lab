from pathlib import Path
import subprocess
B='/Applications/Blender.app/Contents/MacOS/Blender';p=Path('build/source-seam-v1')
for seed,quality,look in [(s,'exact','beauty') for s in [101,202]]+[(s,q,'clay') for s in [101,202] for q in ['fast','exact']]:
 stem=f'seed{seed}-{quality}-{look}'
 with (p/(stem+'.log')).open('w') as f:subprocess.run([B,'-b','--factory-startup','--disable-autoexec','-t','4','--python-exit-code','1','--python','src/strawberry_generator/seam_fix/render.py','--',str(p/f'seed{seed}.blend'),quality,look,'cut',str(p/(stem+'.png'))],stdout=f,stderr=subprocess.STDOUT,check=True)

from pathlib import Path
import subprocess,sys,os
P=Path('/mnt/data/strawberry-v19');B='/mnt/data/blender-runtime/blender-5.2.4-linux-x64/blender'
source={'v12':Path('/mnt/data/strawberry-diagnostics/v12.blend'),'v19a':P/'strawberry-v19a-pith-ring.blend','v19b':P/'strawberry-v19b-pith-ring.blend'}
for v,shot in [('v12','central'),('v19a','central'),('v19b','central'),('v19a','bite'),('v19b','bite'),('v19b','central_macro')]:
 print('START',v,shot,flush=True)
 command=[B,'-b',str(source[v]),'--disable-autoexec','-t','4','--python',str(P/'render_v19.py'),'--',v,shot]
 cp=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,encoding='utf-8',env={**os.environ,'OMP_NUM_THREADS':'4'},timeout=90)
 print(cp.stdout[-1400:],flush=True)
 if cp.returncode:sys.exit(cp.returncode)
print('V19_ALL_RENDER_PASS',flush=True)

import subprocess,sys,json
from pathlib import Path
B=Path(sys.argv[1]);base,scene,field=map(Path,sys.argv[2:5]);here=Path(__file__).resolve().parent
for pose,v in [('whole','.20'),('plane','.20'),('bite','.32'),('tilted','.20'),('bite','.20')]:
 tag=f'{pose}-{v[1:]}';out=here/f'qa-{tag}.json'
 if out.exists():continue
 with open(here/f'qa-{tag}.log','wb') as log:
  r=subprocess.run([str(B),'-b','--factory-startup','--disable-autoexec','-t','4','--python-exit-code','1','--python',str(here/'qa_refine.py'),'--',str(base),str(scene),str(field),pose,v,str(out)],stdout=log,stderr=subprocess.STDOUT,timeout=150)
 print(tag,r.returncode,json.loads(out.read_text())['gate'] if out.exists() else None,flush=True)

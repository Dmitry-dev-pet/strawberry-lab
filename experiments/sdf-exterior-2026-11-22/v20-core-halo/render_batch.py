"""Bounded serial original Cycles batch; no external executor or GPU used."""
import argparse,json,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--blender',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out=a.out.resolve();blender=str(a.blender.resolve());script=str(Path(__file__).with_name('render_halo.py').resolve())
jobs=[('a','plane',640,24,False),('b','plane',640,24,False),('a','bite',640,24,False),('b','bite',640,24,False),('a','macro',1024,32,False),('b','macro',1024,32,False),('a','macro',1024,32,True),('b','macro',1024,32,True),('b','whole',640,24,False)]
rows=[]
for variant,shot,size,samples,clay in jobs:
    kind='core' if variant=='a' else 'halo';scene=a.out/f'strawberry-v20{variant}-{kind}-suppression.blend'
    label=f'v20{variant}-{shot}'+('-clay' if clay else '')
    output=a.out/f'cycles-{label}.png';log=a.out/f'render-{label}.log'
    assert not output.exists(),output
    cmd=[blender,'-b','-t','4','--disable-autoexec','--python-exit-code','1','--python',script,'--','--scene',str(scene),'--shot',shot,'--out',str(output),'--size',str(size),'--samples',str(samples)]
    if clay:cmd.append('--clay')
    t=time.perf_counter()
    with log.open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
    row={'job':label,'exit_code':r.returncode,'process_wall_seconds':time.perf_counter()-t};rows.append(row)
    print(json.dumps(row),flush=True)
    (a.out/'render_batch.json').write_text(json.dumps(rows,indent=2)+'\n')
    if r.returncode:raise SystemExit(r.returncode)

#!/usr/bin/env python3
"""Independent source check for V4; uses saved owner V3 NPZ only."""
from pathlib import Path
import numpy as np,json,tempfile,subprocess,sys
ROOT=Path(__file__).resolve().parent
base=np.load(ROOT/'input-v3-network.npz');N=28;L=base['lengths'];start=np.r_[0,np.cumsum(L[:-1])]
rows=[]
for label in ['0.35','0.85','1.5']:
    f=np.load(ROOT/f'v4-hook{label}.npz');orig=base['points'];q=f['points'];rad=f['radius'];assert len(L)==len(f['lengths'])==567
    assert np.array_equal(orig[:start[N]],q[:start[N]])
    assert np.array_equal(rad,base['radius'])
    assert np.array_equal(f['achene_positions'],base['achene_positions'])
    assert np.array_equal(f['branch_endpoints'],base['branch_endpoints'])
    assert np.array_equal(f['main_strand_idx'],base['main_strand_idx'])
    e=np.cumsum(L)[N:]-1
    assert np.array_equal(q[e],base['branch_endpoints'])
    for i in range(539):
        a=int(start[N+i]);assert np.array_equal(q[a:a+43],orig[a:a+43])
    changed=np.linalg.norm(q-orig,axis=1)
    m={'variant':label,'changed_vertices':int((changed>1.e-6).sum()),'max_point_change':float(changed.max()),'median_tip_change':float(np.median([np.max(changed[int(start[N+i]):int(start[N+i]+L[N+i])]) for i in range(539)])),'all_539_ends_exact':True,'carrier_and_first43_and_radius_exact':True}
    with tempfile.TemporaryDirectory() as td:
        target=Path(td)/'regenerated.npz'
        x=subprocess.run([sys.executable,str(ROOT/'generate_v4_network.py'),'--hook',label,'--out',str(target)],capture_output=True,text=True,timeout=60)
        assert x.returncode==0,(label,x.stderr)
        generated=np.load(target)
        assert set(generated.files)==set(f.files)
        assert all(np.array_equal(generated[k],f[k]) for k in f.files)
    m['deterministic_regeneration']=True;rows.append(m)
rep={'status':'PASS','source':'owned V3 28-sag0.25','variants':rows,'limit':['Does not prove visual match','No tissue geometry or shader atlas','Promotional reference shows possibly different animation state']}
(ROOT/'source-qa.json').write_text(json.dumps(rep,indent=2)+'\n')
print('V4_DATA_QA_PASS',json.dumps(rows))

#!/usr/bin/env python3
"""Verify anchor invariance + measured branch path curvature across V2 and V3."""
from pathlib import Path
import numpy as np,json,hashlib
ROOT=Path(__file__).resolve().parent
v2=np.load(ROOT/'input-v2-network.npz')
base_targets=v2['branch_endpoints'];base_seeds=v2['achene_positions']
variants=[('v2',28,'input-v2-network.npz'),('28-sag0.25',28,'v3-profile28-sag0.25.npz'),('28-sag1.0',28,'v3-profile28-sag1.0.npz'),('28-sag1.8',28,'v3-profile28-sag1.8.npz'),('14-sag1.0',14,'v3-profile14-sag1.0.npz'),('40-sag1.0',40,'v3-profile40-sag1.0.npz')]
rows=[]
for name,nmain,filename in variants:
 d=np.load(ROOT/filename)
 assert np.array_equal(d['achene_positions'],base_seeds)
 assert np.array_equal(d['branch_endpoints'],base_targets)
 assert int((d['kind']==0).sum())==nmain
 assert int((d['kind']==1).sum())==539
 lens=d['lengths'];ends=np.cumsum(lens)[nmain:]-1
 assert np.array_equal(d['points'][ends],base_targets)
 ratios=[];b=0
 for i,L in enumerate(lens):
  q=d['points'][b:b+L];b+=L
  if i<nmain:continue
  path=np.linalg.norm(np.diff(q,axis=0),axis=1).sum()
  chord=np.linalg.norm(q[-1]-q[0]);ratios.append(float(path/max(chord,1e-8)))
 rows.append({'variant':name,'main_carriers':nmain,'attached_branches':539,
 'endpoints_identical':True,'control_seed_positions_identical':True,
 'median_path_over_chord':round(float(np.median(ratios)),4),
 'p90_path_over_chord':round(float(np.percentile(ratios,90)),4),
 'points':int(len(d['points']))})
report={'status':'PASS','baseline':'actual owner V2 scene data','variants':rows,
'contract':'539 assigned 3D achene endpoints and 539 achene marker centers identical across all variants',
'limitations':['No proof of anatomic correctness or Frucht shader wiring','No arbitrary cutter or tissue cut recalculation','Frucht video zoom/pose differs from fixed-camera tests']}
(ROOT/'qa-v3-data.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('V3_QA_DATA_PASS',json.dumps(rows,ensure_ascii=False),flush=True)

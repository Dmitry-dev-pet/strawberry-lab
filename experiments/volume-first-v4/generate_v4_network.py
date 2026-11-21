#!/usr/bin/env python3
"""Local terminal-direction experiment using owned V3 splines, no Frucht code.

Changes only the final 21 points of the same 539 seed-connected paths.
The first 43 points, 28 carrier paths, 539 starts/ends, markers and radii
remain identical to the owned V3 sag0.25 source. A cubic Hermite segment
controls terminal tangent, with a localized tangential offset that vanishes
with zero first derivative at both ends.
"""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,default=ROOT/'input-v3-network.npz');ap.add_argument('--out',type=Path,required=True);ap.add_argument('--hook',type=float,required=True);ap.add_argument('--seed',type=int,default=2026112104)
a=ap.parse_args();assert 0.<=a.hook<=2.2
base=np.load(a.input)
lens=base['lengths'];kind=base['kind'];nmain=int((kind==0).sum());assert nmain==28 and len(lens)==567
seeds=base['achene_positions'];ends=base['branch_endpoints'];assert seeds.shape==ends.shape==(539,3)
orig=np.asarray(base['points'],dtype=np.float32);ret=orig.copy()
starts=np.r_[0,np.cumsum(lens[:-1])]
assert len(lens[nmain:])==539 and np.all(lens[nmain:]==64)
rng=np.random.default_rng(a.seed)
# Fixed stochastic parameters independent of hook setting; some tips largely straight.
raw=rng.uniform(0,1,539);intensity=np.where(raw<.25,raw*.32, np.where(raw<.68,.20+.72*raw,.45+.50*raw))
sign=np.where(rng.random(539)>.5,1.,-1.)
profile=np.empty(539,dtype=np.float32)
turns=[];deviations=[];offhull=[]

def unit(x):return x/(np.linalg.norm(x)+1.e-14)

def hull_r(z):
 t=np.clip((np.asarray(z)+1.18)/2.16,0,1)
 return np.maximum(.002,np.sin(np.pi*t)**.58*(.36+.92*t))

for j in range(539):
 st=int(starts[nmain+j]);Q=np.asarray(orig[st:st+64],dtype=np.float64);P3=Q[-1].copy();k=42
 theta=float(np.arctan2(P3[1],P3[0]));radial=np.array([np.cos(theta),np.sin(theta),0.]);az=np.array([-np.sin(theta),np.cos(theta),0.]);
 # Geographic geometry: empirical berry outline at endpoint height for a local normal.
 dh=float((hull_r(P3[2]+.002)-hull_r(P3[2]-.002))/.004)
 normal=unit(radial-np.array([0.,0.,np.clip(dh,-1.4,1.4)]))
 merid=unit(np.cross(az,normal))
 p0=Q[k];t0=k/63;dt=1-t0
 # C1 continuity with unchanged prefix at knot k (finite difference).
 d0=(Q[k+1]-Q[k-1]) *63/2
 endd=(Q[-1]-Q[-2]);baseline=unit(endd)
 desired=unit(.77*normal +sign[j]*(.9+.5*intensity[j])*az+.28*merid)
 w=np.clip(a.hook*intensity[j],0,1.5)
 final_dir=unit((1-min(w,1.))*baseline+min(w,1.)*desired)
 speed=np.linalg.norm(endd)*63
 # Same terminal speed magnitude; only orientation changes.
 p1=p0+d0*dt/3
 p2=P3-final_dir*speed*dt/3
 u=np.linspace(0.,1.,64-k)
 uu=u[:,None]
 B=(1-uu)**3*p0+3*(1-uu)**2*uu*p1+3*(1-uu)*uu*uu*p2+uu**3*P3
 # Localized double-bend arc; C1 at splice and exact seed destination.
 lateral=(.075*a.hook*intensity[j]*np.linalg.norm(P3-p0)) *np.sin(np.pi*u)**2
 bump=az * (sign[j]*lateral)[:,None]
 # Midline inward recession, avoid more pronounced outer silhouette than baseline.
 inbound=(-radial) * (.015*a.hook*intensity[j]*np.linalg.norm(P3-p0)*np.sin(np.pi*u)**2)[:,None]
 B=B+bump+inbound
 B[0]=Q[k];B[-1]=P3
 new=Q.copy();new[k:]=B
 ret[st:st+64]=new.astype(np.float32)
 profile[j]=w
 deviations.append(float(np.linalg.norm(new-Q,axis=1).max()))
 oldterminal=unit(Q[-1]-Q[-2]);newterminal=unit(new[-1]-new[-2]);turns.append(float(np.degrees(np.arccos(np.clip(np.dot(oldterminal,newterminal),-1,1)))))
 t=new[k:-1];hull=np.asarray(hull_r(t[:,2]))
 offhull.append(float(np.max(np.linalg.norm(t[:,:2],axis=1)-hull)))

# invariant exact end coordinates and exact prefix at the raw float32 level
nvariants=[nmain+i for i in range(539)];endindices=np.cumsum(lens)[nmain:]-1
assert np.array_equal(ret[endindices],ends)
assert np.array_equal(ret[:int(starts[nmain])],orig[:int(starts[nmain])])
for i in range(539):
 s=int(starts[nmain+i]);assert np.array_equal(ret[s:s+43],orig[s:s+43]),i
assert np.array_equal(base['radius'],base['radius'])
np.savez_compressed(a.out,**{key:base[key] for key in base.files if key!='points'},points=ret,tip_strength=profile)
metrics={'status':'PASS','schema':'strawberry-lab.volume-first-v4-local-terminal-test','source':'owner-authored V3 sag0.25; no vendor code',
'inputs':{'hook':a.hook,'seed':a.seed,'source_sha256':hashlib.sha256(a.input.read_bytes()).hexdigest()},
'anchors':{'central_carriers':nmain,'branches':539,'unchanged_seed_positions':True,'unchanged_terminal_positions':True,'unchanged_first_43_branch_points':True,'unchanged_radii':True},
'geometry':{'median_terminal_tangent_change_deg':round(float(np.median(turns)),3),'p90_terminal_tangent_change_deg':round(float(np.percentile(turns,90)),3),'median_max_local_displacement':round(float(np.median(deviations)),5),'p90_max_local_displacement':round(float(np.percentile(deviations,90)),5),'max_hull_radial_overshoot_before_endpoint':round(float(max(offhull)),5),
'fraction_tangent_change_gt_15_deg':round(float(np.mean(np.array(turns)>15)),4),'fraction_tangent_change_gt_35_deg':round(float(np.mean(np.array(turns)>35)),4)},
'known_limits':['geometry source shape and sampled seed positions are synthetic','internal curves do not establish vascular histology','Frucht promotional crop may display exploded and animated fiber effect','3D preview only; tissue field and cut unmodified']}
a.out.with_suffix('.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('V4_NETWORK_CREATED',a.out,metrics['geometry'],flush=True)

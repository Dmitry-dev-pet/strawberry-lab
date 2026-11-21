#!/usr/bin/env python3
"""Original artist-designed thin 3D fibre bundle system, independent of any cut.

Uses one deterministic set of curves for all cutting directions. Existing v0
paths are included for continuity; extra thin curved source paths give enough
spatial density to test whether visible filaments survive oriented cuts.

This is a look-development experiment, not a botanical reconstruction.
"""
import json
from pathlib import Path
import numpy as np
from scipy.interpolate import CubicSpline
ROOT=Path(__file__).resolve().parent
SOURCE=(ROOT/'input-v0') if (ROOT/'input-v0'/'fibers_3d.npz').exists() else (ROOT.parent/'fruit-static-v0'/'outputs')
OUT=ROOT/'outputs';OUT.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(2026112101)
v0=np.load(SOURCE/'fibers_3d.npz')
old_points=np.asarray(v0['points'],dtype=np.float32)
old_lens=np.asarray(v0['lengths'],dtype=np.int32)
assert sum(old_lens)==len(old_points)
lines=[];widths=[];k=0
# Preserve and lightly resample the original 146 spatial curves.
for j,L in enumerate(old_lens):
    seq=old_points[k:k+L];k+=L
    t=np.linspace(0.,1.,L)
    q=np.asarray(CubicSpline(t,seq,axis=0)(np.linspace(0,1,max(80,L))),np.float32)
    lines.append(q);widths.append(.013 if j>=122 else .010)
# Additional long spatial filaments, smoothly curved, distributing source paths
# throughout the fruit rather than painting anything onto the selected cut.
# Each is a real 3D polyline inside the analytic berry with a tiny tube radius.
N_EXTRA=348
for i in range(N_EXTRA):
    golden=2.399963229728653
    phi=(i*golden+rng.normal(0,.018))%(2*np.pi)
    # Start near the central pith, end at variable cortex heights.
    z0=float(rng.uniform(.06,.88))
    z1=float(np.clip(z0-rng.uniform(.48,1.42),-1.02,.70))
    outer_z=z1
    u=np.linspace(0,1,96,dtype=np.float32)
    ease=u*u*(3-2*u)
    # End radius inside curved body; gently arch to create branches.
    tt=np.clip((outer_z+1.18)/2.16,0,1)
    outer_R=(max(np.sin(np.pi*tt),0)**.58)*(.36+.92*tt)
    r0=float(rng.uniform(.012,.12))
    r1=float(outer_R*rng.uniform(.58,.91))
    rr=r0*(1-ease)+r1*ease
    z=z0*(1-ease)+z1*ease+(.03+.025*rng.random())*np.sin(np.pi*u)
    # Less angular drift near the cut so a source curve can generate continuous
    # longitudinal strokes if and only if it genuinely lies close to that plane.
    wiggle=float(rng.uniform(-.028,.028))
    theta=phi+wiggle*np.sin(np.pi*u)+.014*np.sin(2*np.pi*u+(i%13))
    q=np.stack((rr*np.cos(theta),rr*np.sin(theta),z),axis=-1).astype(np.float32)
    lines.append(q)
    widths.append(float(rng.uniform(.008,.015)))
# Flatten source only; never per-angle arrays or authored 2D strokes.
np.savez_compressed(OUT/'fine_fibers_3d.npz',
    points=np.concatenate(lines),lengths=np.array([len(line) for line in lines],dtype=np.int32),
    widths=np.array(widths,dtype=np.float32),source_schema=np.array('strawberry-lab.volume-first.v1.thin-3d-lines'))
meta={'schema':'strawberry-lab.volume-first.v1.1','new_curves':N_EXTRA,'previous_curves':len(old_lens),'total_curves':len(lines),
      'source_sample_points':int(sum(len(p) for p in lines)),
      'source':'continuous 3D splines in fruit coordinates; no per-view fibers',
      'radius_min_max':[round(float(min(widths)),4),round(float(max(widths)),4)],
      'status':'artist-defined independent experiment, not botanical anatomy'}
(OUT/'source-metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
print('FINE_FIBERS_GENERATED',meta)

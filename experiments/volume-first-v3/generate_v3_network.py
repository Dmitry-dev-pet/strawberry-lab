#!/usr/bin/env python3
"""Independent V3 Strawberry Lab morphology-first experiment.

Use the owner's V2 achene anchor/terminal positions verbatim, but replace
constant-radius carriers and radial interpolants with a height-dependent
11-control-point profile and continuously curved cubic Bézier paths.
Inspired by documented architectural concepts, NOT copied Frucht source.
Static morphology probe, not a commercial strawberry asset or live cutter.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator

ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser()
ap.add_argument('--input',type=Path,default=ROOT/'input-v2-network.npz')
ap.add_argument('--out',type=Path,default=ROOT/'v3-profile28-sag1.npz')
ap.add_argument('--strands',type=int,default=28)
ap.add_argument('--sag',type=float,default=1.)
ap.add_argument('--seed',type=int,default=20261121)
a=ap.parse_args()
assert 6<=a.strands<=56 and 0<=a.sag<=2.5

v2=np.load(a.input)
targets=np.asarray(v2['branch_endpoints'],dtype=np.float64)
seeds=np.asarray(v2['achene_positions'],dtype=np.float64)
assert targets.shape==seeds.shape==(539,3)
assert np.allclose(targets,v2['branch_endpoints'],atol=0,rtol=0)
rng=np.random.default_rng(a.seed)

# Explicit, ORIGINAL V3 control points: not transcribed from vendor curves.
# V2 had nearly constant core radius ~0.12-0.165 across height.
z_knots=np.array([-1.12,-.94,-.76,-.57,-.38,-.17,.05,.28,.49,.70,.91],dtype=np.float64)
r_knots=np.array([.018,.042,.094,.170,.250,.316,.334,.290,.222,.124,.023],dtype=np.float64)
profile=PchipInterpolator(z_knots,r_knots,extrapolate=False)

def hull(z):
    u=np.clip((np.asarray(z)+1.18)/2.16,0,1)
    return np.maximum(.002,np.sin(np.pi*u)**.58*(.36+.92*u))

def axis(z):
    zz=np.asarray(z,dtype=np.float64)
    return np.stack((.032*np.sin(2.7*zz+.4)+.011*np.sin(6.2*zz),
                     .026*np.cos(3.1*zz-.3)-.009*np.sin(5.3*zz),
                     zz),axis=-1)

def core_radius(z):
    zz=np.clip(np.asarray(z),z_knots[0],z_knots[-1])
    return np.minimum(profile(zz),.67*hull(zz))

def track(phi_idx,z,total):
    zz=np.asarray(z,dtype=np.float64)
    angle=2*np.pi*phi_idx/total + .095*np.sin(1.9*zz+.65*phi_idx) + .024*np.sin(5*zz+.11*phi_idx)
    rad=core_radius(zz)*(1+.07*np.cos(1.7*phi_idx)+.04*np.sin(5.4*zz+phi_idx))
    ax=axis(zz)
    return ax+np.stack((rad*np.cos(angle),rad*np.sin(angle),np.zeros_like(zz)),axis=-1)

# 28+ spatial longitudinal vascular carriers, with variable geometric profile.
carriers=[];core_tubes=[]
zlin=np.linspace(-1.10,.88,220)
for j in range(a.strands):
    crv=track(j,zlin,a.strands)
    carriers.append(crv)
    taper=.75+.25*np.sin(np.pi*np.arange(len(zlin))/(len(zlin)-1))
    core_tubes.append(.0115*taper*(.90+.14*np.sin(j*2.4)))

# One *cubic* spatial curve per actual V2 achene destination.  The 2 control
# handles encourage a rising initial tangent and an outward/downward arrival;
# their spread is parametrized by sag, without changing the target position.
branch_paths=[];branch_tubes=[];branch_index=[];curve_length=[];mean_turn=[]
for i,P3 in enumerate(targets):
    z=float(P3[2]);thet=float(np.arctan2(P3[1],P3[0]))
    # Roots sit on carrier positions at distinct heights, not a fixed ring.
    zroot=float(np.clip(z+.14+rng.uniform(-.035,.21)+.06*a.sag,-1.09,.86))
    cm=axis(np.asarray([zroot]))[0]
    j=int(np.argmin([np.linalg.norm(track(k,np.asarray([zroot]),a.strands)[0][:2]-P3[:2]) for k in range(a.strands)]))
    P0=track(j,np.asarray([zroot]),a.strands)[0]
    radial=np.array([np.cos(thet),np.sin(thet),0.]);tan=np.array([-np.sin(thet),np.cos(thet),0.]);up=np.array([0.,0.,1.])
    # Each branch has two independently controlled 3D Bezier handles.
    L=max(.06,float(np.linalg.norm(P3-P0)))
    jitter=rng.normal(0,1)
    P1=P0+L*((.08+.14*a.sag)*up+(.09+.035*a.sag)*radial+.015*jitter*tan)
    P2=P3+L*((.12+.24*a.sag)*up-(.22+.04*a.sag)*radial+.05*a.sag*np.sin(.7*j)*tan)
    t=np.linspace(0.,1.,64)[:,None]
    Q=(1-t)**3*P0+3*(1-t)**2*t*P1+3*(1-t)*t*t*P2+t**3*P3
    Q[-1]=P3 # exact, invariant V2 target in float32
    Q=np.asarray(Q,dtype=np.float32)
    branch_paths.append(Q)
    rad=.0098*(.80+.36*rng.random())*(1-.53*np.linspace(0,1,64))
    branch_tubes.append(rad.astype(np.float32))
    branch_index.append(j)
    directions=np.diff(Q,axis=0)
    segnorm=np.linalg.norm(directions,axis=1)
    curve_length.append(float(segnorm.sum()))
    un=directions/(segnorm[:,None]+1e-12)
    angle_change=np.arccos(np.clip(np.sum(un[1:]*un[:-1],axis=1),-1,1))
    mean_turn.append(float(np.sum(angle_change)))

curves=carriers+branch_paths
rads=core_tubes+branch_tubes
kind=np.r_[np.zeros(a.strands,dtype=np.uint8),np.ones(539,dtype=np.uint8)]
lens=np.asarray([len(q) for q in curves],dtype=np.int32)
pts=np.concatenate(curves).astype(np.float32)
rad=np.concatenate(rads).astype(np.float32)
ids=np.r_[np.full(a.strands,-1,dtype=np.int32),np.arange(539,dtype=np.int32)]
source=np.r_[np.arange(a.strands,dtype=np.int32),np.asarray(branch_index,dtype=np.int32)]
assert len(lens)==a.strands+539 and len(pts)==len(rad)
assert np.array_equal(pts[np.cumsum(lens)[a.strands:]-1],targets.astype(np.float32))
assert np.array_equal(seeds,v2['achene_positions'])
assert np.all(np.isfinite(pts))

# Branch shape measurements independent of color/shader/camera.
lengths=np.asarray(curve_length)
turns=np.asarray(mean_turn)
report={
 'schema':'strawberry-lab.volume-first-v3.independent-bent-carriers-and-bezier',
 'parameters':{'strands':a.strands,'sag':a.sag,'seed':a.seed},
 'source':'same immutable 539 V2 seed/terminal coordinates; original independently-authored PCHIP and cubic Bezier code',
 'main_carriers':int(a.strands),'connected_branches':539,'curves':len(curves),'points':len(pts),
 'max_endpoint_error':float(np.linalg.norm(pts[np.cumsum(lens)[a.strands:]-1]-targets,axis=1).max()),
 'core_control_knots':{'z':z_knots.tolist(),'radius':r_knots.tolist()},
 'center_profile':{'min_radius':float(np.min(core_radius(zlin))),'max_radius':float(np.max(core_radius(zlin))),'mean_radius':float(np.mean(core_radius(zlin)))},
 'branches':{'median_length':float(np.median(lengths)),'median_total_turn_radians':float(np.median(turns)),'p90_total_turn_radians':float(np.percentile(turns,90))},
 'scope_limitations':['independently chosen curve profile, not Frucht implementation', 'seed markers from V2 projected into a different berry; not original M1a geometry', 'diagnostic network only; tissue cut, shader atlas and live cutter unchanged']
}
a.out.parent.mkdir(parents=True,exist_ok=True)
np.savez_compressed(a.out,points=pts,lengths=lens,radius=rad,kind=kind,achene_idx=ids,main_strand_idx=source,
    achene_positions=seeds.astype(np.float32),branch_endpoints=targets.astype(np.float32),
    original_m1a_seed_centers=v2['original_m1a_seed_centers'],z_knots=z_knots.astype(np.float32),r_knots=r_knots.astype(np.float32))
a.out.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('V3_GENERATED',a.out, json.dumps({k:v for k,v in report.items() if k in ('parameters','center_profile','branches','curves','points','max_endpoint_error')}),flush=True)

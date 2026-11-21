#!/usr/bin/env python3
"""Generate Strawberry Lab Visual Ground Truth v0: one deterministic 3D substrate.

Artist-defined (NOT measured botany). Produce a continuous 3D RGB/pith/fiber/
height volume; any future cut orientation reads these SAME coordinates.
The veins are explicit spatial curves rasterized to one 3D distance field.
Does not use Frucht's source, assets or graphs.
"""
from pathlib import Path
import json
import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs'/'tissue_3d.npz'
N=150
RNG=np.random.default_rng(20261121)
lo=np.array([-1.30,-1.30,-1.23],dtype=np.float32)
hi=np.array([ 1.30, 1.30, 1.05],dtype=np.float32)
spacing=(hi-lo)/(N-1)

# Derived from an independent analytic fruit silhouette (not author geometry).
def radius_at(z):
    t=np.clip((z+1.18)/(2.16),0,1)
    return 1.00*np.maximum(np.sin(np.pi*t),0)**0.58*(.36+.92*t)

# Spatial vascular/filament paths, not drawn on any particular section.
paths=[]
for i in range(122):
    angle=(i*2.399963229728653 + RNG.normal(0,.22))%(2*np.pi)
    basez=RNG.uniform(-.69,.72)
    endz=np.clip(basez+RNG.normal(-.20,.31),-1.02,.76)
    start_r=RNG.uniform(.055,.19)
    end_r=float(radius_at(endz)*RNG.uniform(.68,.96))
    phase=RNG.uniform(0,2*np.pi)
    line=[]
    for t in np.linspace(0,1,44):
        g=t*t*(3-2*t)
        rr=start_r*(1-g)+end_r*g
        ang=angle+.18*np.sin(t*np.pi+phase)*t
        z=basez*(1-g)+endz*g+.055*np.sin(t*np.pi)*np.cos(3*angle)
        x=rr*np.cos(ang)+.015*np.sin(9*t+phase)
        y=rr*np.sin(ang)+.015*np.cos(8*t+phase)
        line.append((x,y,z))
    paths.append(line)
# A thin family of elongated bundles through the central pith.
for i in range(24):
    phi=i*2*np.pi/24
    rr=.06+.015*np.sin(i*7)
    paths.append([(rr*np.cos(phi+.35*z)+.018*np.sin(z*5+i),rr*np.sin(phi+.35*z)+.015*np.cos(z*4+i),z) for z in np.linspace(-1.02,.81,115)])

np.savez_compressed(ROOT/'outputs'/'fibers_3d.npz',
    points=np.concatenate([np.asarray(p,dtype=np.float32) for p in paths]),
    lengths=np.asarray([len(p) for p in paths],dtype=np.uint16))
# Rasterize all curves into a signed distance-neighborhood field.
occ=np.zeros((N,N,N),dtype=bool)
for path in paths:
    pts=np.asarray(path)
    for j in range(len(pts)-1):
        q0=pts[j];q1=pts[j+1]
        steps=max(2,int(np.linalg.norm(q1-q0)/min(spacing)*2)+1)
        t=np.linspace(0,1,steps,dtype=np.float32)[:,None]
        q=q0*(1-t)+q1*t
        ijk=np.rint((q-lo)/spacing).astype(int)
        good=np.all((ijk>=0)&(ijk<N),axis=1)
        a=ijk[good];occ[a[:,0],a[:,1],a[:,2]]=True
fiber_distance=distance_transform_edt(~occ,sampling=tuple(spacing)).astype(np.float32)

# 3D smooth and micro-contrast fields.  Seed and filtered in full volume.
def field(sigma):
    src=RNG.standard_normal((N,N,N)).astype(np.float32)
    src=gaussian_filter(src,sigma=sigma)
    return np.clip((src-src.mean())/(src.std()+1e-6),-3,3)
macro=field(9)
meso=field(2.8)
micro=field(.9)

# 3D axes; never generate 2D image textures for the three output cuts.
x=lo[0]+np.arange(N,dtype=np.float32)[:,None,None]*spacing[0]
y=lo[1]+np.arange(N,dtype=np.float32)[None,:,None]*spacing[1]
z=lo[2]+np.arange(N,dtype=np.float32)[None,None,:]*spacing[2]
r=np.hypot(x-.017*np.sin(6*z),y-.014*np.cos(4*z))
rad=radius_at(z)+.0001
rel=np.clip(r/rad,0,2)

# A connected, irregular, elongated pale core embedded INSIDE red-orange flesh.
pith_r=.090+.142*np.clip((z+1.14)/2.16,0,1)
pith_border=pith_r*(1+.15*macro+.055*np.sin(14*z+3*np.arctan2(y,x)))
pith=1/(1+np.exp(np.clip((r-pith_border)/.048,-30,30)))
core=(.55+.45*np.clip((z+1.0)/1.9,0,1))*pith

# A radiating network with warm off-white halos and narrow cores.
fib=np.exp(-np.minimum(fiber_distance/.016,10.)**2)
fib_soft=np.exp(-np.minimum(fiber_distance/.035,10.)**2)
fluct=.6+.4*np.clip(.5+.35*meso+.12*micro,0,1)
fib=np.clip(fib*fluct,0,1)

# Fully 3D cellular texture, nonuniform sizes, no plastic honeycomb domes.
celldim=(np.sin(42*x+3.4*meso)*np.sin(40*y+4.0*macro)*np.sin(43*z+2.9*meso))
cell=(.53*meso+.26*micro+.21*celldim)
cell=np.clip(cell,-2.5,2.5)

# Cortex from warm red in the middle to glossy dark red epidermis.
base=np.empty((N,N,N,3),dtype=np.float32)
red=np.array([.62,.027,.015],dtype=np.float32)
outer=np.array([.47,.010,.013],dtype=np.float32)
cortex=np.clip(.72*rel,0,1)[...,None]
base[:]=red*(1-cortex)+outer*cortex
# Controlled color modulation rather than uniform Voronoi cells.
base*=np.clip(1+.038*cell[...,None]+.012*macro[...,None],.82,1.16)
# Creamy almost white central vascular zone, with wispy boundaries.
cream=np.array([.80,.55,.39],dtype=np.float32)
base=base*(1-core[...,None]) + cream*core[...,None]
# Pale strands remain visible in both red and cream regions.
# Three-dimensional radiating tissue *sheets*. At any azimuth, their
# intersection with a cut plane appears as thin branching vein-like streaks.
# They are implicit 3D surfaces, not individually painted cut-line textures.
theta=np.arctan2(y,x)
phase=22*z + 30*r + 5.0*np.sin(3*theta+2*z)+1.9*np.sin(7*r-4*z)+2.2*meso
radial_sheets=np.exp(-np.sin(phase)**2/.085)
radial_sheets*=np.clip((r-.10)/.32,0,1)*np.clip((1.08-rel)/.30,0,1)
axial_bundles=pith*np.exp(-np.sin(10*theta+1.2*np.sin(5*z))**2/.23)*.15
strand=np.clip(.36*fib+.105*fib_soft+.15*radial_sheets+axial_bundles,.0,.59)
vein_color=np.array([.94,.67,.48],dtype=np.float32)
base=base*(1-strand[...,None])+vein_color*strand[...,None]
# A localized warm amber tissue strip nested *inside* the pale central core:
# a 3D region, not a painted mark on the longitudinal section.
axial_amber=np.exp(-(r/.105)**2)*np.exp(-((z-.20)/.43)**4)
axial_amber*=np.clip((.85+pith)*.54,0,1)
amber_rgb=np.array([.66,.115,.048],dtype=np.float32)
base=base*(1-.78*axial_amber[...,None])+amber_rgb*(.78*axial_amber[...,None])
# Subtle bright micro-wet tissue flecks and restrained color clamp.
base+=np.clip(micro,0,3)[...,None]*.008
base=np.clip(base,.006,1.0)

# Microscopic physical height is also a SINGLE 3D field, sliced consistently.
height=np.clip(.60*meso+.25*micro+.15*celldim,-2.4,2.4)*.0075
height+=(fib*.0038)
# All fields use the identical spatial axes and deterministic random seed.
np.savez_compressed(OUT,
    color=np.rint(base*255).astype(np.uint8),
    height=height.astype(np.float16),
    pith=np.rint(np.clip(pith,0,1)*255).astype(np.uint8),
    fiber=np.rint(np.clip(fib,0,1)*255).astype(np.uint8),
    axial_amber=np.rint(np.clip(axial_amber,0,1)*255).astype(np.uint8),
    radial_sheets=np.rint(np.clip(radial_sheets,0,1)*255).astype(np.uint8),
    lo=lo,hi=hi,
    seed=np.asarray(20261121,dtype=np.int32))
metadata={"schema":"strawberry-lab.visual-poc.1", "seed":20261121,"grid_shape":[N,N,N],"coordinate_bounds":{"lo":lo.tolist(),"hi":hi.tolist()},"fibers":len(paths),"fields":["color","height","pith","fiber","radial_sheets","axial_amber"],"design":"artist-design, not strawberry histology", "source":"independent Python+NumPy; single 3D tissue volume for all cut orientations"}
(ROOT/'outputs'/'tissue-metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
print('3D_VOLUME_READY',OUT, 'MB', round(OUT.stat().st_size/1e6,2), 'paths',len(paths),flush=True)

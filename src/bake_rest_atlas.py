#!/usr/bin/env python3
"""Deterministic 64^3 rest-space tissue field packed as 8x8 2D atlas.

Independent M1c research implementation (not code or measured parameters from Frucht).
RGB = simplified vascular intensity, cortex mottling, and pith mask.
The underlying functions are continuous 3-D and never depend on cutting plane.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image

N=64; COLS=8; BOUNDS=(-2.0,2.0)

def field(x,y,z):
    r=np.sqrt(x*x+y*y); zpos=np.clip((z+1.825)/3.65,0,1)
    a=np.arctan2(y,x)
    core=.255+.027*np.sin(4.6*z+.7)
    pith=np.clip((core+.055-r)/.1,0,1)
    ring=np.exp(-((r-core-.11)/.085)**2)
    rays=np.maximum(0,np.sin(a*13. + z*5. + .23*np.sin(z*8)))**14
    vessel=np.clip(.70*ring + .23*rays*np.clip((r-core)/.28,0,1),0,1)
    mottling=(.5+.25*np.sin(11*x+2*z)*np.sin(15*y-z*7)+.15*np.sin(29*z+9*x)*np.sin(19*y-7*x))
    return vessel,mottling,np.clip(pith,0,1)

def generate(n=N):
    # Index [z, y, x, channel]; y indexes bottom-up, just like Blender UV.
    xs=np.linspace(BOUNDS[0],BOUNDS[1],n,dtype=np.float32)
    xx,yy,zz=np.meshgrid(xs,xs,xs,indexing='xy')
    # array shape is [y, x, z], reshape explicitly as field evaluated per slice
    atlas=np.zeros((n*8,n*8,3),dtype=np.uint8)
    for iz,z in enumerate(xs):
        a,b,c=field(xx[:,:,iz],yy[:,:,iz],z)
        channels=np.stack([a,b,c],axis=-1)
        pixels=np.uint8(np.clip(channels,0,1)*255+.5)
        tx=iz%8; ty=iz//8
        # Bottom tile row (ty=0) maps to last rows of PNG data; intra tile y too.
        atlas[(7-ty)*n:(8-ty)*n, tx*n:(tx+1)*n]=pixels[::-1,:,:]
    return atlas

def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ns=ap.parse_args(argv)
    ns.out.parent.mkdir(exist_ok=True,parents=True)
    a=generate()
    Image.fromarray(a,'RGB').save(ns.out,optimize=True)
    info={'name':ns.out.name,'sha256':hashlib.sha256(ns.out.read_bytes()).hexdigest(),
          'size_bytes':ns.out.stat().st_size,'grid_shape':[N,N,N],'atlas_shape':[N*8,N*8],
          'layout':'8x8 tiles; tile 0 bottom-left; RGB = vessel, mottling, pith',
          'rest_bounds':list(BOUNDS),'units':'synthetic, not measured botany'}
    ns.out.with_suffix('.json').write_text(json.dumps(info,indent=2)+'\n')
    print('BAKED_REST_ATLAS',json.dumps(info),flush=True)
if __name__=='__main__':main()
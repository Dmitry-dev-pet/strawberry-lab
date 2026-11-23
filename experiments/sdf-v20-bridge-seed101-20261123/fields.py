"""Independent ARTIST core/halo field experiment using Strawberry Lab's v19 graph.

No Frucht code, node templates, coefficients or assets are used here.
The existing material atlas is deliberately not repurposed: its G is mottling,
B is pith. A separate geometry atlas carries core R and broader influence G.
"""
from __future__ import annotations
import hashlib
import numpy as np

WIDTH_FACTOR = 1.8  # ARTIST standard-deviation multiplier, not botanical data.


def wider_graph(segments, factor=WIDTH_FACTOR):
    if not np.isfinite(factor) or factor < 1.0:
        raise ValueError('Halo width factor must be finite and at least one')
    return [{**s, 'sigma_mm':float(s['sigma_mm'])*factor} for s in segments]


def unpack_atlas_channel(pixels, channel=0, n=192, columns=16):
    rows=(n+columns-1)//columns
    if pixels.shape != (rows*n,columns*n,4):
        raise ValueError('Unexpected atlas dimensions')
    return np.stack([pixels[(z//columns)*n:(z//columns+1)*n,(z%columns)*n:(z%columns+1)*n,channel] for z in range(n)])


def pack_core_halo(core, halo, columns=16):
    if core.shape != halo.shape or len(core.shape)!=3 or len(set(core.shape))!=1:
        raise ValueError('Core and halo must be equal cubic ZYX grids')
    if not np.isfinite(core).all() or not np.isfinite(halo).all():
        raise ValueError('Nonfinite field')
    if np.any(halo < core):
        raise ValueError('Halo must dominate the existing core at every voxel')
    n=core.shape[0];rows=(n+columns-1)//columns
    pixels=np.zeros((rows*n,columns*n,4),np.float32);pixels[:,:,3]=1.
    for z in range(n):
        y,x=divmod(z,columns)
        pixels[y*n:(y+1)*n,x*n:(x+1)*n,0]=core[z]
        pixels[y*n:(y+1)*n,x*n:(x+1)*n,1]=halo[z]
    return pixels


def sha_array(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def suppression(v):
    """Existing owned GN clamped SMOOTHSTEP mapping, retained for both variants."""
    t=np.clip((np.asarray(v)-0.04)/(0.48-0.04),0.,1.)
    return 1.0-0.88*t*t*(3.-2.*t)

"""Strawberry Lab M1b — deterministic THREE-DIMENSIONAL parenchyma microstructure.

An illustrative jittered 3-D Voronoi field, not microscopic reconstruction:
cell diameters and wall widths are ARTIST parameters, uncalibrated to a cultivar.
The same scalar field is sampled at any 3D point, regardless of slice orientation.

The public API is intentionally Blender-independent; all coordinates are 3D.
"""
from functools import lru_cache
from math import floor, sqrt


MASK = 0xffffffff


def _hash(x, y, z, seed):
    # Reproducible 32-bit integer mix across machines; Python hash() is avoided.
    v=(int(seed) ^ (int(x)*0x9e3779b1) ^ (int(y)*0x85ebca6b) ^ (int(z)*0xc2b2ae35)) & MASK
    v=((v ^ (v >> 16))*0x7feb352d) & MASK
    v=((v ^ (v >> 15))*0x846ca68b) & MASK
    return (v ^ (v >> 16)) & MASK


@lru_cache(maxsize=65000)
def _jittered_center(ix,iy,iz,seed):
    h=_hash(ix,iy,iz,seed)
    a=_hash(iy,iz,ix,seed+47)
    b=_hash(iz,ix,iy,seed+199)
    # Keeps every point safely within its own grid cube.
    return ((ix + .5 + .31*(h/float(MASK)-.5)),
            (iy + .5 + .31*(a/float(MASK)-.5)),
            (iz + .5 + .31*(b/float(MASK)-.5)))


def cell_measure(x,y,z,*,spacing=.115,seed=1729):
    """Nearest two cell centres in a jittered 3D lattice, nearest cell id.

    Distances in the original length units, independent of 2-D section plane.
    Kernel is a 3x3x3 neighbourhood; no external textures or Blender API.
    """
    if spacing<=0:raise ValueError('spacing must be positive')
    xx=x/spacing; yy=y/spacing; zz=z/spacing
    ax=floor(xx); ay=floor(yy); az=floor(zz)
    ds=[float('inf'),float('inf')]
    cid=None
    for ix in (ax-1,ax,ax+1):
        for iy in (ay-1,ay,ay+1):
            for iz in (az-1,az,az+1):
                cx,cy,cz=_jittered_center(ix,iy,iz,seed)
                d=(xx-cx)**2+(yy-cy)**2+(zz-cz)**2
                if d<ds[0]:
                    ds[1]=ds[0];ds[0]=d;cid=(ix,iy,iz)
                elif d<ds[1]:ds[1]=d
    return sqrt(ds[0])*spacing,sqrt(ds[1])*spacing,cid


def _smooth(a,b,x):
    t=min(1.,max(0.,(x-a)/(b-a)))
    return t*t*(3.-2.*t)


def cell_properties(x,y,z,*,spacing=.115,seed=1729):
    """3D cell-wall mask and a cell-specific brightness field.

    wall=1 in narrow intercellular zones, centre=1 in rounded cell interiors.
    Values are continuous near Voronoi boundaries except for discrete per-cell
    brightness. This is conceptual tissue only; not measured anatomy.
    """
    d1,d2,(i,j,k)=cell_measure(x,y,z,spacing=spacing,seed=seed)
    separation=max(0,d2-d1)
    wall=1.-_smooth(.0045,.018,separation)
    centre=1.-_smooth(.32*spacing,.74*spacing,d1)
    h=_hash(i,j,k,seed+9001)
    shade=.84+.16*(h/float(MASK))
    return {'cell_id':(i,j,k),'d1':d1,'d2':d2,'wall':wall,'centre':centre,'shade':shade,
            'wall_gap':separation,'spacing':spacing}


def micro_tissue_color(x,y,z,base_color,*,spacing=.115,seed=1729,inside_weight=1.,pith_weight=0.,visual_strength=1.):
    """RGB(A) for a 3D parenchyma slice and genuine geometric recess depth.

    Non-cell regions can use inside_weight=0 to suppress the diagnostic cells.
    Geometry recess is in positive distance units; orientation is decided by
    the cut-plane mesh builder, not by this coordinate-invariant field.
    """
    c=cell_properties(x,y,z,spacing=spacing,seed=seed)
    visual_strength=max(0.,min(1.,visual_strength))
    alpha=max(0.,min(1.,inside_weight))
    # Inter-cell clefts are darker; individual cells are subtly nonuniform.
    wall=c['wall']*alpha
    pale=max(0.,min(1.,pith_weight))
    diagnostic_shade=.91+.15*c['shade']-.33*wall
    shade=1.+visual_strength*(diagnostic_shade-1.)
    col=tuple(min(1,max(0,base_color[i]*shade+(0.018,0.012,0.006)[i]*c['centre']*alpha*visual_strength)) for i in range(3))
    # More transparent, uneven gel/void spacing inside pith (still conceptual).
    hollow=.006*wall*(.6+.4*pale)
    recess=visual_strength*(alpha*(.006+.009*pale)*wall - .0026*alpha*c['centre'])
    return col+(1.,),recess,{'wall':wall,'centre':c['centre'],'hollow':hollow,'cell_id':c['cell_id']}


def sample_slice_longitudinal(x,z,**kw):
    return cell_properties(x,0.,z,**kw)


def sample_slice_transverse(x,y,**kw):
    return cell_properties(x,y,0.,**kw)


if __name__=='__main__':
    print('3D cell sample at shared line:',sample_slice_longitudinal(.7,0),sample_slice_transverse(.7,0))
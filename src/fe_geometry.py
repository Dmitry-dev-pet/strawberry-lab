"""Reusable dimensioned surface/region geometry (millimetres).

Topology remains fruit-specific; computational primitives are reusable.
Unknown fruit silhouette, receptacle pith size, seed dimensions/placement,
and vascular widths are deliberately NOT treated as measured parameters.
"""
from __future__ import annotations
from math import sin,cos,pi,sqrt
from bisect import bisect_left


def strawberry_shape_radius(t:float, *,rmax_mm:float) -> float:
    """Illustrative smooth silhouette, only max radius is source-calibrated."""
    if not 0<=t<=1: raise ValueError('t must be from 0 to 1')
    def raw(x):
        return max(0.,sin(pi*x))**0.66 * (0.67+0.55*x)
    maxraw=max(raw(i/4096) for i in range(4097))
    return rmax_mm*raw(t)/maxraw


def strawberry_surface_mesh(*,height_mm:float,width_mm:float,rings:int=100,sectors:int=128):
    """Return vertices/faces of exterior receptacle in world millimetres."""
    if height_mm<=0 or width_mm<=0 or rings<10 or sectors<16: raise ValueError('invalid shape/mesh size')
    rmax=width_mm/2
    vertices=[]
    vertices.append((0.,0.,-height_mm/2))
    for i in range(1,rings):
        t=i/rings; r=strawberry_shape_radius(t,rmax_mm=rmax)
        for j in range(sectors):
            a=2*pi*j/sectors
            vertices.append((r*cos(a),r*sin(a),height_mm*(t-.5)))
    upper_idx=len(vertices);vertices.append((0.,0.,height_mm/2))
    faces=[]
    for j in range(sectors):faces.append((0,1+j,1+(j+1)%sectors))
    for i in range(rings-2):
        row0=1+i*sectors;row1=row0+sectors
        for j in range(sectors):
            a,b=row0+j,row0+(j+1)%sectors
            c,d=row1+(j+1)%sectors,row1+j
            faces.append((a,d,c,b))
    last_start=1+(rings-2)*sectors
    for j in range(sectors):faces.append((last_start+j,upper_idx,last_start+(j+1)%sectors))
    return vertices,faces


def achene_anchor_positions(*,height_mm:float,width_mm:float,count:int) -> list[tuple[float,float,float]]:
    """Area-weighted quasi-uniform schematic anchor placement, NOT measured phyllotaxis.

    Achene COUNT is rounded from a cultivar mean. Positions are an artist method;
    not claims about natural cell-to-achene distances or precise spirals.
    """
    if count<=0:raise ValueError('achene count positive')
    rmax=width_mm/2
    ts=[0.004+i*.992/1600 for i in range(1601)]
    rs=[strawberry_shape_radius(t,rmax_mm=rmax) for t in ts]
    accum=[0.]
    for i in range(1,len(ts)):
        dz=height_mm*(ts[i]-ts[i-1]); dr=rs[i]-rs[i-1]
        a=2*pi*(rs[i]+rs[i-1])/2 * sqrt(dz*dz+dr*dr)
        accum.append(accum[-1]+a)
    area=accum[-1];positions=[]
    for i in range(count):
        q=(i+.5)*area/count;k=bisect_left(accum,q)
        k=max(1,min(k,len(ts)-1))
        frac=(q-accum[k-1])/max(1e-20,accum[k]-accum[k-1])
        t=ts[k-1]*(1-frac)+ts[k]*frac
        r=strawberry_shape_radius(t,rmax_mm=rmax)
        angle=i*pi*(3-sqrt(5))
        positions.append((r*cos(angle),r*sin(angle),height_mm*(t-.5)))
    return positions


def kiwi_region_rings(boundaries_mm:tuple[float,float,float],sectors:int=180):
    """Single planar ring mesh with per-face material region, physical radii in mm.

    Assumes concentric regions on one central cross-section as a *schematic*
    of a published radial transect. Not evidence of perfect rotational symmetry
    or a whole-kiwi longitudinal anatomy.
    """
    if len(boundaries_mm)!=3 or not(0<boundaries_mm[0]<boundaries_mm[1]<boundaries_mm[2]):
        raise ValueError('boundaries must be strictly increasing positive radii')
    if sectors<24:raise ValueError('need enough sectors')
    pts=[(0.,0.,0.)]
    for r in boundaries_mm:
        for j in range(sectors):
            a=2*pi*j/sectors
            pts.append((r*cos(a),0.,r*sin(a)))
    faces=[];regions=[]
    for j in range(sectors):
        faces.append((0,1+j,1+(j+1)%sectors));regions.append(0)
    for ring in range(1,3):
        prev=1+(ring-1)*sectors;curr=1+ring*sectors
        for j in range(sectors):
            a=prev+j;b=prev+(j+1)%sectors;c=curr+(j+1)%sectors;d=curr+j
            faces.append((a,d,c,b));regions.append(ring)
    return pts,faces,regions
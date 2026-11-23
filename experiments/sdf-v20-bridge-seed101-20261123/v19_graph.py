"""Original procedural ARTIST strawberry fiber scaffold, v19 research only.

Graph topology: one continuous root trunk, 28 carrier polylines sharing points
with the trunk, 264 terminals joined exactly to sampled carrier points, and
short attached offshoots. No botanical claim about radii or positions.
"""
from __future__ import annotations
import json
import math
import hashlib
import numpy as np

SEED = 19011
BBOX = ((-18.,18.), (-18.,18.), (-1.,50.))
N = 192


def cubic(a,b,c,d,t):
    u=1.-t
    return u**3*a + 3*u*u*t*b + 3*u*t*t*c + t**3*d


def make_graph(anchors: np.ndarray, seed: int=SEED):
    """Return list with id, parent_id, seed_id, (n,3) points and artistic radii."""
    a=np.asarray(anchors,dtype=np.float32)
    assert a.shape==(264,3) and np.isfinite(a).all()
    rng=np.random.default_rng(seed)
    segs=[]
    root=np.stack([np.zeros(89),np.zeros(89),np.linspace(2.,46.,89)],axis=-1).astype(np.float32)
    segs.append({'id':0,'kind':'root','parent':None,'seed_id':None,'attach_at':None,'points':root,'sigma_mm':.72,'amplitude':.78})
    carriers=[]
    for j in range(28):
        theta=2*math.pi*(j+0.33)/28
        # Origin exactly coincides with the trunk at z=4; side carriers spiral gently in 3-D.
        zz=np.linspace(4,46,121,dtype=np.float32)
        t=(zz-4.)/42.
        r=4.2*(t**.86)
        angle=theta+ .29*np.sin(2*math.pi*t+ j*.43)*t
        p=np.stack([r*np.cos(angle),r*np.sin(angle),zz],axis=-1).astype(np.float32)
        p[0]=[0.,0.,4.] # exact shared root point exists on 0.375mm step
        seg={'id':len(segs),'kind':'carrier','parent':0,'seed_id':None,'attach_at':int(np.argmin(np.abs(root[:,2]-4.))),
             'points':p,'sigma_mm':.47,'amplitude':.76}
        segs.append(seg);carriers.append(seg)
    for seed_id, target in enumerate(a):
        ang=(math.atan2(float(target[1]),float(target[0]))-2*math.pi*.33/28)%(2*math.pi)
        j=int(np.round(ang/(2*math.pi/28)))%28
        parent=carriers[j]
        pt=parent['points']
        # Parent attachment is an actual sampled carrier vertex, never a nearby floating point.
        z0=np.clip(float(target[2])-7.5,6,43)
        idx=int(np.argmin(np.abs(pt[:,2]-z0)))
        p0=pt[idx].copy()
        p3=target.copy()
        v=p3-p0
        p1=p0+np.array([v[0]*.14,v[1]*.12,1.9],np.float32)
        p2=p0+np.array([v[0]*.79,v[1]*.81,v[2]-.9],np.float32)
        # Bounded ARTIST lateral curve: avoid perfectly straight spoke patterns.
        lateral=np.array([-v[1],v[0],0],np.float32)
        lateral/=max(1e-6,float(np.linalg.norm(lateral)))
        jitter=float(rng.uniform(-.9,.9))
        p1+=lateral*jitter; p2+=lateral*jitter*.4
        ts=np.linspace(0,1,49,dtype=np.float32)
        points=np.stack([cubic(p0,p1,p2,p3,t) for t in ts]).astype(np.float32)
        points[0]=p0;points[-1]=p3
        fid=len(segs)
        seg={'id':fid,'kind':'terminal','parent':parent['id'],'seed_id':seed_id,'attach_at':idx,
             'points':points,'sigma_mm':.34,'amplitude':.75}
        segs.append(seg)
        # One attached twig, starting exactly from this terminal's 3-D locus.
        tix=int(rng.integers(17,35));q0=points[tix].copy()
        direction=np.array([rng.normal(),rng.normal(),rng.uniform(-.1,.65)],np.float32)
        direction/=max(1e-6,float(np.linalg.norm(direction)))
        end=q0+float(rng.uniform(.85,1.9))*direction
        twig=np.linspace(q0,end,9,dtype=np.float32)
        segs.append({'id':len(segs),'kind':'twig','parent':fid,'seed_id':None,'attach_at':tix,
                     'points':twig,'sigma_mm':.28,'amplitude':.51})
    return segs


def validate_graph(segments,anchors):
    ids={s['id']:s for s in segments}
    assert ids.keys()==set(range(len(segments)))
    assert len(segments)==1+28+264+264
    assert sum(s['kind']=='terminal' for s in segments)==264
    seen=set();stack=[0]
    while stack:
        x=stack.pop()
        if x in seen: continue
        seen.add(x)
        stack.extend(s['id'] for s in segments if s['parent']==x)
    assert len(seen)==len(segments), f'disconnected graph: {len(seen)}/{len(segments)}'
    target_ids=[]; max_err=0.; max_radius=0.
    for s in segments:
        p=s['points'];assert p.ndim==2 and p.shape[1]==3 and np.isfinite(p).all()
        if s['parent'] is not None:
            pa=ids[s['parent']]['points'][s['attach_at']]
            err=float(np.linalg.norm(p[0]-pa));max_err=max(err,max_err)
            assert err<1e-6,(s['id'],err)
        if s['seed_id'] is not None:
            target_ids.append(s['seed_id'])
            assert np.array_equal(p[-1],anchors[s['seed_id']])
        max_radius=max(max_radius,float(np.linalg.norm(p[:,:2],axis=1).max()))
    assert sorted(target_ids)==list(range(264))
    return {'segments_total':len(segments),'root':1,'carriers':28,'terminals':264,'twigs':264,
            'all_connected_to_one_root':True,'parent_joint_max_error_mm':max_err,
            'endpoints_on_achene_anchors':len(target_ids),'max_graph_radius_mm':max_radius,
            'seed':SEED}


def rasterize_graph(segs, resolution=N):
    """Rasterize actual graph polylines as continuous 3D Gaussian tube solids.

    Spatial field remains fixed in rest space; no cutter- or camera-specific map.
    XYZ fixed physical bounds, output [Z,Y,X] in float32.
    """
    xmin,xmax=BBOX[0];ymin,ymax=BBOX[1];zmin,zmax=BBOX[2]
    xs=np.linspace(xmin,xmax,resolution,dtype=np.float32)
    ys=np.linspace(ymin,ymax,resolution,dtype=np.float32)
    zs=np.linspace(zmin,zmax,resolution,dtype=np.float32)
    field=np.zeros((resolution,resolution,resolution),np.float32)
    pitch=np.array([(xmax-xmin)/(resolution-1),(ymax-ymin)/(resolution-1),(zmax-zmin)/(resolution-1)],np.float32)
    applied=0;outside=0
    for s in segs:
        pts=s['points'];sigma=float(s['sigma_mm']);amp=float(s['amplitude'])
        radius=3*sigma; delta=pitch
        for a,b in zip(pts[:-1],pts[1:]):
            count=max(1,int(np.ceil(np.linalg.norm(b-a)/.18)))
            # Include segment endpoint exactly once across adjacent segments.
            for k in range(count):
                q=a+(b-a)*(k/count)
                ix=int(np.rint((q[0]-xmin)/pitch[0]));iy=int(np.rint((q[1]-ymin)/pitch[1]));iz=int(np.rint((q[2]-zmin)/pitch[2]))
                dx=int(math.ceil(radius/pitch[0]))+1;dy=int(math.ceil(radius/pitch[1]))+1;dz=int(math.ceil(radius/pitch[2]))+1
                lo=max(0,ix-dx);hi=min(resolution,ix+dx+1)
                ly=max(0,iy-dy);hy=min(resolution,iy+dy+1)
                lz=max(0,iz-dz);hz=min(resolution,iz+dz+1)
                if lo>=hi or ly>=hy or lz>=hz: outside+=1;continue
                d2=(xs[None,None,lo:hi]-q[0])**2+(ys[None,ly:hy,None]-q[1])**2+(zs[lz:hz,None,None]-q[2])**2
                patch=np.exp(-.5*d2/(sigma*sigma)).astype(np.float32)*amp
                np.maximum(field[lz:hz,ly:hy,lo:hi],patch,out=field[lz:hz,ly:hy,lo:hi])
                applied+=1
        # Attach the last endpoint as well.
        q=pts[-1]; i=int(round((q[0]-xmin)/pitch[0]));j=int(round((q[1]-ymin)/pitch[1]));k=int(round((q[2]-zmin)/pitch[2]))
        if 0<=i<resolution and 0<=j<resolution and 0<=k<resolution:
            field[k,j,i]=max(field[k,j,i],amp*.8)
    assert np.isfinite(field).all()
    return field,{'grid_shape_ZYX':[resolution]*3,'field_min':float(field.min()),'field_max':float(field.max()),
                  'field_mean':float(field.mean()),'over_025_fraction':float((field>.25).mean()),
                  'raster_dabs_applied':applied,'raster_dabs_clipped':outside,
                  'field_sha256':hashlib.sha256(field.tobytes()).hexdigest(),
                  'voxel_pitch_mm_xyz':pitch.astype(float).tolist()}


def compact_graph(segs):
    return [{'id':s['id'],'kind':s['kind'],'parent':s['parent'],'seed_id':s['seed_id'],'attach_at':s['attach_at'],
             'points':np.round(s['points'],6).tolist(),'sigma_mm':s['sigma_mm'],'amplitude':s['amplitude']} for s in segs]

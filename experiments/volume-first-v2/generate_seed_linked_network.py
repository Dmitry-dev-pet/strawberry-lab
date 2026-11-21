#!/usr/bin/env python3
"""Independent Strawberry Lab proof: 539 *existing* achene centers -> 539 spatial branches.
No Frucht algorithm or code is copied. The control concept is informed by the
visible author interface, our actual M1a achene geometry, and general botany.
"""
from pathlib import Path
import argparse, json, numpy as np
P=argparse.ArgumentParser()
P.add_argument('--input',type=Path,default=Path(__file__).with_name('m1a-539-actual-achene-centers.npz'))
P.add_argument('--out',type=Path,default=Path(__file__).with_name('v2-seed-anchored-vascular-network.npz'))
P.add_argument('--strands',type=int,default=28)
P.add_argument('--strand-width',type=float,default=1.0)
P.add_argument('--fiber-width',type=float,default=1.0)
P.add_argument('--fiber-sag',type=float,default=1.0)
P.add_argument('--pattern',type=int,default=20261121)
a=P.parse_args()
rng=np.random.default_rng(a.pattern)
src=np.load(a.input)
seeds=src['matched_center'].astype(np.float64)
assert len(seeds)==539 and len(np.unique(src['matched_index']))==539
# Project M1a seed center angular/height coordinates onto the independent
# Volume First fruit. Explicit remapping is necessary: M1a/v1 shapes differ.
z01=(seeds[:,2]-seeds[:,2].min())/np.ptp(seeds[:,2])
znew=-1.05+1.90*z01
angle=np.arctan2(seeds[:,1],seeds[:,0])
def hull_r(z):
 t=np.clip((np.asarray(z)+1.18)/2.16,0,1)
 return np.maximum(0.004,np.sin(np.pi*t)**.58*(.36+.92*t))
outer_r=hull_r(znew)*(1+.012*np.sin(7*angle+2.6*znew))
anchor=np.stack((outer_r*np.cos(angle),outer_r*np.sin(angle),znew),axis=1)
normal=np.stack((np.cos(angle),np.sin(angle),np.zeros(len(angle))),axis=1)
end=anchor-normal*0.019  # base of each achene, slightly beneath the skin
paths=[];rad=[];types=[];dest=[];sources=[]
# Central transport cylinder: 28 parameterized longitudinal carriers.
# Radius gently varies with height and is deliberately NOT the author's pchip ring.
for j in range(a.strands):
 z=np.linspace(-1.10,.88,128)
 phi=2*np.pi*j/a.strands +.024*np.sin(3.1*z+.67*j)
 rr=(.12+.045*np.exp(-((z-.15)/.62)**2))*np.maximum(.35,np.minimum(1.,hull_r(z)/.28))
 pts=np.stack((rr*np.cos(phi),rr*np.sin(phi),z),axis=1)
 paths.append(pts);rad.append(np.full(len(z),.0135*a.strand_width,dtype=np.float32))
 types.append('central');dest.append(-1);sources.append(j)
# Each branch has a corresponding original achene. Curvature is constructed in
# radial/azimuthal coordinates via a smooth interpolation + organic drift;
# this is NOT a port of the Frucht Bezier generator.
for i,(pt,th,zz) in enumerate(zip(end,angle,znew)):
 idx=int(np.round((th%(2*np.pi))*a.strands/(2*np.pi)))%a.strands
 ro_z=np.clip(zz+.13+.08*rng.random(),-1.04,.86)
 theta_root=2*np.pi*idx/a.strands +.024*np.sin(3.1*ro_z+.67*idx)
 r0=(.12+.045*np.exp(-((ro_z-.15)/.62)**2))*np.maximum(.35,min(1.,float(hull_r(ro_z))/.28))
 # minimal angular interpolation to the target seed position
 delta=((th-theta_root+np.pi)%(2*np.pi))-np.pi
 t=np.linspace(0,1,48,dtype=np.float64)
 ease=t*t*(3-2*t)
 r1=np.hypot(pt[0],pt[1])
 rr=(1-ease)*r0+ease*r1
 theta=theta_root+delta*ease + rng.uniform(-.035,.035)*np.sin(np.pi*t)
 ze=(1-ease)*ro_z+ease*zz-.065*a.fiber_sag*np.sin(np.pi*t)*(1-t)
 arr=np.column_stack((rr*np.cos(theta),rr*np.sin(theta),ze))
 arr[-1]=pt  # exact endpoint on the own M1a-derived achene-base position
 paths.append(arr)
 rad.append((.011*a.fiber_width*(1-.36*ease))*(.85+.30*rng.random()))
 types.append('branch');dest.append(i);sources.append(idx)
counts=np.array([len(p) for p in paths],dtype=np.int32)
points=np.concatenate(paths).astype('float32')
widths=np.concatenate(rad).astype('float32')
a.out.parent.mkdir(parents=True,exist_ok=True)
np.savez_compressed(a.out,points=points,lengths=counts,radius=widths,kind=np.array([0 if t=='central' else 1 for t in types],dtype='uint8'),
     achene_idx=np.array(dest,dtype='int32'),main_strand_idx=np.array(sources,dtype='int16'),
     achene_positions=anchor.astype('float32'),branch_endpoints=end.astype('float32'),original_m1a_seed_centers=seeds.astype('float32'))
# Verify connectivity and reproducibility independent of Blender.
begin=np.r_[0,np.cumsum(counts[:-1])]
ends=np.array([points[b+n-1] for b,n in zip(begin[a.strands:],counts[a.strands:])])
error=np.linalg.norm(ends-end,axis=1)
assert error.max()<1e-6 and len(ends)==539
report={'schema':'strawberry-lab.volume-first-v2.seed-link-1','source':'M1a actual 539 seed centers extracted from owned Geometry Nodes plus own projective mapping into v1 hull',
 'strands':a.strands,'connected_achenes':len(anchor),'achene_branch_ratio':'1:1','generated_curves':len(paths),'spatial_points':len(points),
 'endpoint_max_error':float(error.max()),'parameters':{k:getattr(a,k) for k in ['strands','strand_width','fiber_width','fiber_sag','pattern']},
 'notes':['Mappings from M1a center coordinates to Volume First hull are synthetic','Seed-linked architecture is independently implemented; no Frucht source nodes or binaries copied','Prototype is for 3D morphology audit, not calibrated anatomy']}
a.out.with_suffix('.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print('SEED_LINKED_SOURCE_PASS',json.dumps(report),flush=True)

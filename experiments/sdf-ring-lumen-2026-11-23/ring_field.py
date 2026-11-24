"""Independent ARTIST vascular ring fitted to our own fruit; no Frucht code or preset."""
import numpy as np
import hashlib
N=192; BOUNDS=np.array([[-25.,25.],[-25.,25.],[-2.,52.]]); SEED=7139

def profile(a,z):
 z=np.asarray(z,dtype=np.float64);r=np.linalg.norm(a[:,:2],axis=1);w=np.exp(-.5*((z[...,None]-a[:,2])/2.6)**2);envelope=(w@r)/np.maximum(w.sum(axis=-1),1e-12);t=np.clip((z-1.2)/48.,0,1)
 return np.maximum(.34*envelope*np.maximum(np.sin(np.pi*t),0.)**.62,.16),.40*np.sin(2*np.pi*t+.6)*np.sin(np.pi*t),.31*np.sin(1.5*np.pi*t-.5)*np.sin(np.pi*t)

def make_graph(a,seed=SEED):
 a=np.asarray(a,dtype=float);assert a.shape==(264,3) and np.isfinite(a).all();rng=np.random.default_rng(seed);z=np.linspace(2.8,46.5,176);rr,cx,cy=profile(a,z);t=(z-z[0])/(z[-1]-z[0]);segs=[]
 for j in range(28):
  theta=2*np.pi*j/28+.08;phase=theta+.18*np.sin(2*np.pi*t+theta)*np.sin(np.pi*t);radial=rr*(1+.065*np.sin(3*phase+3*t));p=np.column_stack([cx+radial*np.cos(phase),cy+.92*radial*np.sin(phase),z]);width=(.34+.16*np.sin(np.pi*t))*(.91+.09*np.cos(phase));segs.append(dict(id=j,kind='carrier',parent=None,seed_id=None,attach_at=None,points=p,sigma=width,amplitude=.76))
 center=np.array([0.,0.,27.])
 for j,target in enumerate(a):
  d=center-target;end=target+.95*d/np.linalg.norm(d);z0=min(46.5,max(2.8,end[2]+4.8+1.2*np.sin(end[2]/8)));idx=int(np.argmin(abs(z-z0)));cross=np.array([s['points'][idx] for s in segs[:28]]);parent=int(np.argmin(np.linalg.norm(cross[:,:2]-end[:2],axis=1)));start=cross[parent];delta=end-start;lateral=np.array([-delta[1],delta[0],0.]);lateral/=max(np.linalg.norm(lateral),1e-9);bend=rng.uniform(-.9,.9);c1=start+.25*delta+np.array([0,0,1.])+lateral*bend;c2=end-.25*delta+np.array([0,0,-.65])+lateral*bend*.4;u=np.linspace(0,1,57)[:,None];pts=(1-u)**3*start+3*(1-u)**2*u*c1+3*(1-u)*u*u*c2+u**3*end;pts[0]=start;pts[-1]=end;sig=.34-.16*u[:,0]**.8;segs.append(dict(id=len(segs),kind='terminal',parent=parent,seed_id=j,attach_at=idx,points=pts,sigma=sig,amplitude=.75))
 return segs

def validate_graph(segs,a):
 assert len(segs)==292 and [s['id'] for s in segs]==list(range(292));assert sum(s['kind']=='carrier' for s in segs)==28;terms=[s for s in segs if s['kind']=='terminal'];assert sorted(s['seed_id'] for s in terms)==list(range(264))
 for s in segs:assert np.isfinite(s['points']).all() and np.all(s['sigma']>0)
 joint=max(np.linalg.norm(s['points'][0]-segs[s['parent']]['points'][s['attach_at']]) for s in terms);offset=np.array([np.linalg.norm(s['points'][-1]-a[s['seed_id']]) for s in terms]);assert joint<1e-9 and np.max(abs(offset-.95))<1e-9
 return dict(carriers=28,terminals=264,segments=len(segs),joint_max_mm=float(joint),seed_offset_mm=[float(offset.min()),float(offset.max())],tapered_terminals=True,root_trunk=False)

def raster(segs,factor,n=N):
 axes=[np.linspace(lo,hi,n,dtype=np.float32) for lo,hi in BOUNDS];pitch=(BOUNDS[:,1]-BOUNDS[:,0])/(n-1);arr=np.zeros((n,n,n),np.float32);count=0;clipped=0
 for s in segs:
  p=s['points'];sigma=s['sigma']*factor;amp=s['amplitude']
  for k in range(len(p)-1):
   steps=max(1,int(np.ceil(np.linalg.norm(p[k+1]-p[k])/.16)))
   for u in np.arange(steps)/steps:
    q=p[k]+u*(p[k+1]-p[k]);w=sigma[k]+u*(sigma[k+1]-sigma[k]);radius=3*w;center=np.rint((q-BOUNDS[:,0])/pitch).astype(int);ext=np.ceil(radius/pitch).astype(int)+1;lo=np.maximum(0,center-ext);hi=np.minimum(n,center+ext+1)
    if np.any(hi<=lo):clipped+=1;continue
    x,y,z=[v[l:h] for v,l,h in zip(axes,lo,hi)];d2=(x[None,None,:]-q[0])**2+(y[None,:,None]-q[1])**2+(z[:,None,None]-q[2])**2;patch=arr[lo[2]:hi[2],lo[1]:hi[1],lo[0]:hi[0]];np.maximum(patch,(amp*np.exp(-.5*d2/w**2)).astype(np.float32),out=patch);count+=1
 return arr,dict(dabs=count,clipped=clipped)

def ring_relative(a,n=N):
 x,y,z=[np.linspace(lo,hi,n,dtype=np.float32) for lo,hi in BOUNDS];r,cx,cy=profile(a,z);rad=np.sqrt((x[None,None,:]-cx[:,None,None])**2+((y[None,:,None]-cy[:,None,None])/.92)**2);return np.clip(.5+(rad-r[:,None,None])/16.,0,1).astype(np.float32)

def sha(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()

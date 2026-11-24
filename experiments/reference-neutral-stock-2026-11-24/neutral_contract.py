"""Independent neutral-stock contract. Reuses owned ExteriorShape and FruitContext.
No author node trees/assets or presets. Distances in mm; shape choices ARTIST.
"""
from dataclasses import dataclass, asdict
from functools import lru_cache
import hashlib, json, math
import numpy as np
from exterior_shape import ExteriorParams, ExteriorShape, MERIDIAN_STEPS, AZIMUTH_STEPS
from fruit_platform import FruitContext, standard_registry

VERSION='neutral-stock-v1'
MAP_VERSION='common-gaussian-map-v1'

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

@dataclass(frozen=True)
class ShapeState:
    a: float=0.
    b: float=0.
    h: float=1.
    def __post_init__(self):
        for val,low,high in ((self.a,-.25,.30),(self.b,-.25,.30),(self.h,.85,1.20)):
            if isinstance(val,bool) or not math.isfinite(val) or not low<=val<=high:
                raise ValueError('Shape state outside bounded independent map')
    def radial(self,z,height):
        t=2*np.asarray(z,dtype=float)/height-1
        return 1+self.a*np.exp(-((t-.5)/.36)**2)+self.b*np.exp(-((t+.3)/.4)**2)
    def forward(self,p,height):
        p=np.array(p,dtype=float,copy=True);s=self.radial(p[...,2],height)
        p[...,:2]*=s[...,None];p[...,2]*=self.h
        return p
    def inverse(self,p,height):
        p=np.array(p,dtype=float,copy=True);p[...,2]/=self.h
        p[...,:2]/=self.radial(p[...,2],height)[...,None]
        return p
    def normal(self,p,n,height):
        p=np.asarray(p,float);n=np.asarray(n,float);z=p[...,2];t=2*z/height-1
        s=self.radial(z,height)
        ds=(2/height)*(-2*self.a*(t-.5)/.36**2*np.exp(-((t-.5)/.36)**2)-2*self.b*(t+.3)/.4**2*np.exp(-((t+.3)/.4)**2))
        out=np.empty_like(n);out[...,:2]=n[...,:2]/s[...,None]
        out[...,2]=(n[...,2]-ds*np.sum(p[...,:2]*out[...,:2],axis=-1))/self.h
        return out/np.linalg.norm(out,axis=-1,keepdims=True)

@dataclass(frozen=True)
class NeutralStock:
    instance_id: str
    context_plan_digest: str
    params: ExteriorParams
    anchors: tuple
    anchor_digest: str
    stock_key: str
    def anchor_id(self,index):
        if not 0<=index<len(self.anchors):raise IndexError(index)
        return f'{self.instance_id}:{self.anchor_digest[:16]}:achene:{index:04d}'
    def shape_key(self,state):
        return digest([MAP_VERSION,self.stock_key,asdict(state)])
    def vessel_dependency_key(self,settings):
        # Contract only; no vascular atlas constructed here.
        return digest(['future-vascular-input-v1',self.anchor_digest,settings])

def make_stock(context: FruitContext,count:int)->NeutralStock:
    if not isinstance(context,FruitContext) or context.specimen.taxon!='Fragaria × ananassa':
        raise ValueError('Needs existing Fragaria FruitContext')
    if type(count) is not int or not 100<=count<=500:
        raise ValueError('Bounded experimental count range 100..500')
    plan=standard_registry().plan(context)
    p=ExteriorParams(height_mm=context.specimen.fruit_height.mm,width_mm=context.specimen.fruit_width.mm,seed=context.seed,achene_count=count)
    anchors=tuple(ExteriorShape(p).anchors())
    ad=digest([VERSION,asdict(p),[asdict(a) for a in anchors]])
    key=digest([VERSION,ad,MERIDIAN_STEPS,AZIMUTH_STEPS,'owned-ovoid-prototype-v1'])
    return NeutralStock(context.instance_id,plan.digest(),p,anchors,ad,key)

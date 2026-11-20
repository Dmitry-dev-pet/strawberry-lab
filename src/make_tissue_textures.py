"""Bake two original procedural color fields for fast Blender / GLB display.
No photos or source textures used: all pixels derived from coordinates, noise and tissue equations.
"""
import numpy as np
from PIL import Image,ImageFilter
from pathlib import Path
from math import pi
P=Path(__file__).resolve().parent
W=1536; H=1536
rng=np.random.default_rng(1157)
y,x=np.mgrid[0:H,0:W].astype(np.float32)
t=1-y/(H-1)
u=x/(W-1)

def smooth_noise(low=10):
    a=rng.random((low,low,3))
    im=Image.fromarray(np.uint8(a*255),'RGB').resize((W,H),Image.Resampling.BICUBIC)
    return np.asarray(im,dtype=np.float32)/255-.5

noise1=smooth_noise(20)
noise2=smooth_noise(92)
noise3=rng.normal(0,1,(H,W,3)).astype(np.float32)
# Strawberry epidermis: mottled red and faint oblong streaks between golden achenes
marble=(.70*noise1+.27*noise2)
stripes=(np.sin(2*pi*(u*63+t*13+ .035*np.sin(2*pi*u*4)))+1)*.5
skin=np.stack((.74+.08*t,.033+.01*t,.066+.016*t),axis=2)
skin=skin+marble*np.array([.18,.058,.068],np.float32)
skin+=stripes[:,:,None]*np.array([.027,.008,.01])
skin+=noise3*np.array([.011,.004,.004])
skin=np.clip(skin,0,1)
Image.fromarray(np.uint8(skin*255),'RGB').save(P/'skin.png', optimize=True)

# tissue() map replicated vectorially, UV x across the longitudinal cut, vertical = z
R=1.62
xc=(u*2-1)*R
tr=np.clip(t,.001,.999)
rad=R*np.maximum(0.,np.sin(pi*tr))**.56*(.37+.93*tr)
pos=rad*(1+.027*np.sin(0+1.7*tr)+.013*np.sin(0-8*tr)+.007*np.sin(0+3.1*tr))
neg=rad*(1+.027*np.sin(7*pi+1.7*tr)+.013*np.sin(13*pi-8*tr)+.007*np.sin(19*pi+3.1*tr))
rr=np.where(xc>0,pos,neg)
q=np.abs(xc)/np.maximum(rr,.0001)
corew=(.22+.09*tr**1.3)*(1+.18*np.sin(5*tr+.6)+.05*np.sin(22*tr))
core=np.clip((corew-np.abs(xc))/.10,0,1)
edge=np.clip((q-.87)/.13,0,1)
outer=np.clip((q-.95)/.05,0,1)
angle=np.arctan2(xc,(tr-.5)*2.5+.01)
veins=np.exp(-((np.sin(angle*22+tr*12+ .5*np.sin(xc*13))/.12)**2))
branched=(.5+.5*np.sin(24*tr+8*xc+3*np.sin(angle*2)))
noise=(noise1[:,:,0]*.5+noise2[:,:,0]*.5)
cellularity=np.sin(92*xc+13*np.sin(30*tr))*np.sin(160*tr+8*np.sin(11*xc))
# deep scarlet cortex and light rosy internal flesh
red=np.array([.89,.19,.22],np.float32)
rose=np.array([.97,.38,.41],np.float32)
color=red[None,None,:]*(.65+.35*edge[:,:,None])+rose[None,None,:]*(.35-.20*edge[:,:,None])
color+=(.08*noise+.014*cellularity)[:,:,None]*np.array([1,.75,.75])
# fibrous beige-pink veins; only a light component in the surrounding flesh
vstrength=(1-core)*veins*np.clip((q-.11)/.15,0,1)*.13
color=color*(1-vstrength[:,:,None])+np.array([1,.68,.57])[None,None,:]*vstrength[:,:,None]
# pale central vascular core with irregular tissue margins
pith=np.array([.98,.75,.65],np.float32)[None,None,:]
core_tone=np.array([.98,.84,.73],np.float32)[None,None,:]
pith=pith*(.65+.35*branched[:,:,None])+core_tone*(.35-.35*branched[:,:,None])
color=color*(1-core[:,:,None])+pith*core[:,:,None]
# red dark epidermis at outer 5-10%, a genuine tissue layer
color=color*(1-.75*outer[:,:,None])+np.array([.55,.045,.07])[None,None,:]*(.75*outer[:,:,None])
# shine around surface, but avoid fake big droplets
color=np.clip(color,0,1)
Image.fromarray(np.uint8(color*255),'RGB').save(P/'flesh.png',optimize=True)
print('textures',[(p.name,p.stat().st_size) for p in [P/'skin.png',P/'flesh.png']])

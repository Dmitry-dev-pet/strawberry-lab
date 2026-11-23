"""Diagnostic plotting of two actual packed v19 3-D source fields. No AI image."""
from pathlib import Path
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
P=Path('/mnt/data/strawberry-v19');N=192
volumes={}
for var in ('a','b'):
    # Blender stores image pixels bottom-up. PNG is top-down. Restore pixel layout.
    a=np.asarray(Image.open(P/f'v19{var}-packed-tissue-192.png').convert('RGBA'),dtype=np.uint8)[::-1]
    vol=np.empty((N,N,N,4),np.float32)
    for z in range(N):
        row=z//16;col=z%16
        vol[z]=a[row*N:(row+1)*N,col*N:(col+1)*N,:]/255.0
    volumes[var]=vol

def make_rgb(pith,vascular):
    # Normalize to fixed bounds across A/B. pith (cyan), vascular (amber).
    p=np.clip(pith,0,1);r=np.clip(vascular,0,1)
    rgb=np.empty(p.shape+(3,),np.float32)
    rgb[:,:,0]=np.clip(.08+.88*r+.13*p,0,1)
    rgb[:,:,1]=np.clip(.07+.39*r+.72*p,0,1)
    rgb[:,:,2]=np.clip(.09+.08*r+.81*p,0,1)
    return rgb

fig,axes=plt.subplots(2,2,figsize=(10.3,11.2),dpi=145,constrained_layout=True)
for col,variant in enumerate(('a','b')):
    data=volumes[variant]
    row=96  # y approximately 0
    # z-first volume; x horizontal, z vertical
    xzB=data[:,row,:,2]
    xzR=data[:,row,:,0]
    ax=axes[0,col]
    ax.imshow(make_rgb(xzB,xzR),origin='lower',extent=(-18,18,-1,50),interpolation='nearest',aspect='auto')
    ax.contour(np.linspace(-18,18,N),np.linspace(-1,50,N),xzB,levels=[.5],colors='white',linewidths=.55,alpha=.9)
    ax.set_xlim(-8,8);ax.set_ylim(1,49)
    ax.set_xlabel('X, mm');ax.set_ylabel('Z, mm')
    ax.set_title('v19A: pith only' if col==0 else 'v19B: pith + bundle collar')
    zz=round((25+1)/51*191)
    xyB=data[zz,:,:,2];xyR=data[zz,:,:,0]
    ax=axes[1,col]
    ax.imshow(make_rgb(xyB,xyR),origin='lower',extent=(-18,18,-18,18),interpolation='nearest')
    ax.contour(np.linspace(-18,18,N),np.linspace(-18,18,N),xyB,levels=[.5],colors='white',linewidths=.55,alpha=.9)
    ax.set_xlim(-8,8);ax.set_ylim(-8,8)
    ax.set_xlabel('X, mm');ax.set_ylabel('Y, mm')
    ax.set_title('Cross section at Z≈25 mm')
fig.suptitle('Strawberry Lab — independent rest-space 3D tissue fields (ARTIST)\nCyan: pith / B · Amber: vascular / R · White contour: B=0.5',fontsize=13)
fig.savefig(P/'v19-tissue-zones-diagnostic.png',dpi=145)
print('v19 PLOTS CREATED',P/'v19-tissue-zones-diagnostic.png')

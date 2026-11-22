"""Unintegrated nonlinear field probe; NOT used to build delivered scenes."""
import numpy as np
from math import exp
PROFILES={'shouldered':(.23,-.12,1.08),'waisted':(-.12,.18,.96)}
def radial(z,a,b):return 1+a*exp(-((z-.5)/.36)**2)+b*exp(-((z+.3)/.4)**2)
def forward(p,params):
 a,b,h=params;s=radial(p[2],a,b);return np.array((p[0]*s,p[1]*s,p[2]*h))
def inverse(p,params):
 a,b,h=params;z=p[2]/h;s=radial(z,a,b);return np.array((p[0]/s,p[1]/s,z))
def probe():
 points=np.array([(r*np.cos(t),r*np.sin(t),z) for z in np.linspace(-1,1,25) for r in [.2,.6] for t in np.linspace(0,6,12)])
 design=np.c_[points,np.ones(len(points))];report={}
 for name,params in PROFILES.items():
  mapped=np.array([forward(p,params) for p in points]);fit=np.linalg.lstsq(design,mapped,rcond=None)[0]
  residual=np.sqrt(np.mean(np.sum((mapped-design@fit)**2,axis=1)))
  error=max(np.linalg.norm(inverse(forward(p,params),params)-p) for p in points)
  assert residual>.01 and error<1e-12
  report[name]={'params':params,'best_affine_rms_model_units':residual,'inverse_max_error':error,'integrated_into_blender':False}
 return report
if __name__=='__main__':
 import json;print(json.dumps(probe(),indent=2))

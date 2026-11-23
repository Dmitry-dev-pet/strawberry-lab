"""Generate two independent ARTIST vascular intensity candidates from unchanged v12 field.

A: piecewise remapping of existing R intensities (no topology / new routes).
B: Gaussian source-space antialias before *identical* remapping (Z/Y/X sigma).
Both produce 192^3 quantized R fields for 8-bit packed atlas read by GN and shader.
The generator intentionally does not edit the original G/B channels or Blender scene.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from scipy import ndimage
ROOT=Path(__file__).resolve().parent
SRC=Path('/mnt/data/strawberry-diagnostics/source_r_field_192.npy')
assert SRC.is_file()
raw=np.load(SRC).astype(np.float32)
assert raw.shape==(192,192,192) and np.all(np.isfinite(raw))
X=np.array([0,.02,.05,.10,.15,.20,.30,.40,.60,.75,1.],np.float32)
Y=np.array([0,.013,.055,.18,.34,.46,.62,.72,.83,.90,.95],np.float32)
assert np.all(np.diff(X)>0) and np.all(np.diff(Y)>=0)
variants={
 'v17a':np.interp(raw,X,Y).astype(np.float32),
 'v17b':np.interp(ndimage.gaussian_filter(raw,sigma=(1.2,1.5,1.5),mode='nearest'),X,Y).astype(np.float32)
}
receipt={'input_source_r_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'source':'unmodified v12 source R channel extracted by v16 audit',
 'axis_order':'Z,Y,X','voxel_pitch_mm':[51/191,36/191,36/191],
 'original_field_not_replaced':True,'piecewise_knots':{'input':X.tolist(),'output':Y.tolist()},
 'B_gaussian_sigma_voxels_ZYX':[1.2,1.5,1.5],'A_gaussian_sigma_voxels_ZYX':[0,0,0],
 'quantization':'8 bit 0..255, same as v12 packed PNG, Non-Color','scientific_status':'ARTIST, no measured vessel widths or new biological topology','outputs':{}}
for name,val in variants.items():
    out=(np.clip(np.rint(val*255),0,255).astype(np.uint8).astype(np.float32)/255.0)
    filename=name+'-source-R-192.npy'
    np.save(ROOT/filename,out)
    receipt['outputs'][name]={'npy_sha256':hashlib.sha256((ROOT/filename).read_bytes()).hexdigest(),
     'min':float(out.min()),'max':float(out.max()),'r_gt_03_pct':float((out>=.3).mean()*100)}
(ROOT/'v17-preparation.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:v['r_gt_03_pct'] for k,v in receipt['outputs'].items()},ensure_ascii=False))

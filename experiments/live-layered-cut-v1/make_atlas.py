"""Pack the verified *owned* Volume First v0 RGB 3D field to a 2D image.
Each tile is an exact z slice.  The Blender material samples this with bilinear XY
and linear interpolation across adjacent z slices, without regenerating tissue.
"""
from pathlib import Path
import numpy as np, hashlib, json
from PIL import Image
ROOT=Path(__file__).resolve().parent
src=ROOT/'tissue_3d.npz'
f=np.load(src);colors=f['color'];N=colors.shape[0];assert colors.shape==(150,150,150,3)
COLS=15;ROWS=10;assert COLS*ROWS==N
H,W=N*ROWS,N*COLS
atlas=np.zeros((H,W,3),dtype=np.uint8)
for k in range(N):
    col=k%COLS;row=k//COLS
    # PIL image origin is top-left; material UV origin bottom-left.
    atlas[(ROWS-row-1)*N:(ROWS-row)*N, col*N:(col+1)*N]=colors[:,:,k].transpose(1,0,2)[::-1]
path=ROOT/'tissue_color_atlas_150.png';Image.fromarray(atlas).save(path,optimize=True)
# 25 checks: atlas (pixel XY, slice Z) reconstructs exact original voxel values.
raw=np.array(Image.open(path))
rng=np.random.default_rng(921)
for i,j,k in rng.integers(0,N,size=(25,3)):
    y=(ROWS-k//COLS-1)*N+(N-1-j); x=(k%COLS)*N+i
    assert np.array_equal(raw[y,x],colors[i,j,k]), (i,j,k)
meta={'status':'PASS','N':N,'cols':COLS,'rows':ROWS,'size':[W,H],'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'image_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_bounds_lo':f['lo'].tolist(),'source_bounds_hi':f['hi'].tolist(),'voxel_checks':25,'interpolation':'XY bilinear + Z linear in Blender shader; no voxel value modified'}
(ROOT/'atlas-qa.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print('ATLAS_PASS',json.dumps(meta))

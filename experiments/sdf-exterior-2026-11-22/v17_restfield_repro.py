#!/usr/bin/env python3
"""Independent Strawberry Lab v17 R-only vascular field A/B; ARTIST parameters.

Extract and apply stages run under Blender 5.2.4 with the verified owner v12
scene open and --disable-autoexec. Compute stage runs under external Python
with numpy + scipy (not required inside Blender).

    blender -b v12_original.blend --disable-autoexec --python v17_restfield_repro.py -- extract OUT
    python v17_restfield_repro.py compute OUT
    blender -b v12_original.blend --disable-autoexec --python v17_restfield_repro.py -- apply OUT v17a
    blender -b v12_original.blend --disable-autoexec --python v17_restfield_repro.py -- apply OUT v17b

No original scene, G/B/A field, source tissue graph, cutter, or seed is changed.
"""
import hashlib
from pathlib import Path
import sys
import numpy as np

ATLAS_NAME = 'SDF proof v4 | 192^3 sparse volume and continuous branches'
SOURCE_SHA256 = '300a2bfeaa86831220657b74fe8b00d4d7ec0b42f4ffefca863d6410cbb405b7'
SHAPE = (192, 192, 192)
PACKED_SHAPE = (2304, 3072, 4)


def source_image():
    import bpy
    path = Path(bpy.data.filepath)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == SOURCE_SHA256, 'Must use verified unchanged original v12'
    im = bpy.data.images[ATLAS_NAME]
    assert im.packed_file is not None and tuple(im.size) == (3072, 2304)
    return im


def pixels_to_volume(im):
    pix = np.empty(len(im.pixels), np.float32)
    im.pixels.foreach_get(pix)
    return pix.reshape((12, 192, 16, 192, 4)).transpose(0, 2, 1, 3, 4).reshape(SHAPE+(4,))


def red_to_packed_plane(red):
    assert red.shape == SHAPE
    return red.reshape((12,16,192,192)).transpose(0,2,1,3).reshape((2304,3072))


def run_extract(out):
    im=source_image()
    arr=pixels_to_volume(im)
    np.save(out/'v17_original_atlas.npy',arr)
    print('EXTRACT_OK',arr.shape,'original R max',float(np.max(arr[...,0])))


def run_compute(out):
    from scipy.ndimage import gaussian_filter
    original=np.load(out/'v17_original_atlas.npy',mmap_mode='r')
    red=original[...,0]
    pitch_mm=np.array((51/191,36/191,36/191),dtype=np.float64) # z,y,x
    a=-np.expm1(-3.0*red)
    b=-np.expm1(-3.0*gaussian_filter(red,sigma=tuple((0.22/pitch_mm).tolist()),mode='nearest',output=np.float32))
    for name,data in [('v17a',a),('v17b',b)]:
        result=np.clip(data,0,1).astype(np.float32)
        np.save(out/f'{name}_red.npy',result)
        print('FIELD_OK',name,'mean',float(result.mean()),'R>=0.3',float((result>=.3).mean()))
    # Test that the original atlas is not mutated by compute.
    assert not np.shares_memory(red,np.load(out/'v17a_red.npy'))


def run_apply(out,variant):
    import bpy
    assert variant in ('v17a','v17b')
    im=source_image()
    red=np.load(out/f'{variant}_red.npy')
    assert red.shape==SHAPE and np.isfinite(red).all()
    buffer=np.empty(len(im.pixels),np.float32)
    im.pixels.foreach_get(buffer)
    target=buffer.reshape(PACKED_SHAPE)
    nonred_sha=hashlib.sha256(target[:,:,1:].tobytes()).hexdigest()
    target[:,:,0]=red_to_packed_plane(red)
    assert hashlib.sha256(target[:,:,1:].tobytes()).hexdigest()==nonred_sha
    im.pixels.foreach_set(buffer)
    im.update();im.pack()
    s=bpy.context.scene
    s['v17_experiment']='R-only ARTIST rest-space vascular field intensity/anti-aliasing; no source anatomy change'
    s['v17_variant']=variant
    s['v17_source_scene_sha256']=SOURCE_SHA256
    s['v17_nonred_sha256']=nonred_sha
    s.frame_set(20)
    dest=out/f'strawberry-sdf-{variant}.blend'
    assert not dest.exists(),f'Refusing overwrite: {dest}'
    bpy.ops.wm.save_as_mainfile(filepath=str(dest),compress=True)
    print('SAVE_OK',variant,dest.stat().st_size,hashlib.sha256(dest.read_bytes()).hexdigest())


def main():
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    assert len(argv) in (2,3),'usage: extract|compute|apply OUT [v17a|v17b]'
    command,out=argv[:2]
    out=Path(out).expanduser().resolve()
    out.mkdir(parents=True,exist_ok=True)
    if command=='extract':run_extract(out)
    elif command=='compute':run_compute(out)
    elif command=='apply' and len(argv)==3:run_apply(out,argv[2])
    else:raise ValueError(argv)

if __name__=='__main__':main()

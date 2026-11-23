# Original strawberry SDF v9 (local research): one hypothesis, central tapered pale vascular sheath.
# Source v8 is preserved, no author Frucht source copied. All tissue values ARTIST.
import bpy, numpy as np, math, hashlib, json, time, os
from pathlib import Path
ROOT=Path(os.environ.get('STRAWBERRY_SDF_OUT', str(Path(__file__).resolve().parents[2] / 'build/sdf-vertical-slice')))
SRC=ROOT/'strawberry-sdf-vertical-slice-v8.blend'
OUT=ROOT/'strawberry-sdf-vertical-slice-v9-core-sheath.blend'
assert SRC.is_file() and not OUT.exists(), 'Missing v8 or refusing to overwrite v9'
t0=time.monotonic()
bpy.ops.wm.open_mainfile(filepath=str(SRC),use_scripts=False)
N=192; COLS=16; ROWS=12
img=bpy.data.images['SDF proof v4 | 192^3 sparse volume and continuous branches']
assert list(img.size)==[3072,2304] and img.packed_file
p=np.empty(3072*2304*4,dtype=np.float32)
img.pixels.foreach_get(p)
a=p.reshape((2304,3072,4))
xs=np.linspace(-18,18,N,dtype=np.float32)
X,Y=np.meshgrid(xs,xs)
R=np.sqrt(X*X+Y*Y)
before_r=a[:,:,0].copy(); before_g=a[:,:,1].copy()
zs=np.linspace(-1,50,N,dtype=np.float32)
sheath_info=[]
for iz,z in enumerate(zs):
    h=float(np.clip((z-5.)/41.,0,1))
    profile=max(0,math.sin(math.pi*h))**0.85
    radius=4.8*profile*(1.+0.035*math.sin(0.19*z))
    width=0.72+0.42*profile
    ring=np.exp(-0.5*((R-radius)/width)**2).astype(np.float32)*(min(1.,2.8*profile))
    y=(iz//COLS)*N; x=(iz%COLS)*N
    prev=a[y:y+N,x:x+N,2]
    prev[:]=np.clip(0.08*prev+0.92*ring,0,1)
    if iz in (20,80,120,160):sheath_info.append((iz,round(float(z),2),round(radius,2),round(width,2)))
assert np.array_equal(before_r,a[:,:,0]) and np.array_equal(before_g,a[:,:,1]),'Vascular/mottling channels must not change'
img.pixels.foreach_set(p)
img.update()
img.pack()
mat=bpy.data.materials['SDF proof v8 | cut cells flattened on SAME vessel atlas']
pith=mat.node_tree.nodes['Mix (Legacy).001']
pith.inputs[2].default_value=(0.98,0.85,0.75,1)
scene=bpy.context.scene
scene['v9_experiment']='One change only: tapered annular pale sheath in shared rest-space atlas blue channel; exact v8 R/G, SDF, achenes, wetness retained.'
scene['v9_evidence']='Artist lookdev parameter, NOT botanical measurement. No source Frucht nodes or textures.'
scene.frame_set(20)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
manifest={'version':'v9-core-sheath-local','source':'v8','source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'blend_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'red_and_green_atlas_channels_unchanged':True,'schematic_sheath':sheath_info,'seconds':round(time.monotonic()-t0,2),'biology':'ARTIST','visual_accepted':False}
(ROOT/'v9-core-sheath-local.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('V9_LOCAL_BUILT='+json.dumps(manifest),flush=True)

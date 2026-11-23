"""V9 visual hypothesis from owner Frucht video t=10.0s.
Only expand original-rest central pith domain + restrained shader pith color.
SDF cuts, cell displacement, seed culling and existing strand R field unchanged.
All new anatomy-like values are ARTIST, not measured biology.
"""
import bpy,numpy as np,hashlib,json,os,time
from pathlib import Path
P=Path(os.environ.get('STRAWBERRY_SDF_OUT',str(Path(__file__).resolve().parents[2]/'build/sdf-vertical-slice')))
SRC=P/'strawberry-sdf-vertical-slice-v8.blend';DEST=P/'strawberry-sdf-vertical-slice-v9.blend'
assert SRC.is_file() and not DEST.exists()
t0=time.monotonic()
bpy.ops.wm.open_mainfile(filepath=str(SRC),use_scripts=False)
source=bpy.data.images['SDF proof v4 | 192^3 sparse volume and continuous branches']
assert list(source.size)==[3072,2304] and source.packed_file
px=np.empty(2304*3072*4,np.float32);source.pixels.foreach_get(px);px=px.reshape(2304,3072,4)
N=192;C=16;ROWS=12
xx,yy=np.meshgrid(np.linspace(-18,18,N,dtype=np.float32),np.linspace(-18,18,N,dtype=np.float32))
orig_blues=[];new_blues=[]
for k,z in enumerate(np.linspace(-1,50,N,dtype=np.float32)):
    tx=k%C;ty=k//C
    sl=px[ty*N:(ty+1)*N,tx*N:(tx+1)*N,:]
    old=sl[:,:,2].copy()
    # A longitudinal central pith/spindle, independent of camera and cut angle.
    # Reference t10 shows roughly a quarter-width bright central interior,
    # tapering to the tip, and radiating thinner pale strands.
    center_x=.40*np.sin(z*.14)
    center_y=.28*np.sin(z*.11+.6)
    radial=np.sqrt(((xx-center_x)*1.02)**2+((yy-center_y)*.88)**2)
    radius=1.45+3.45*np.exp(-((z-28.5)/13.8)**2)
    # Increase radius slightly near shoulder where fibers fan out.
    radius+=.55*np.exp(-((z-38)/4.5)**2)
    ribbon=np.clip((radius-radial)/.80,-25,25)
    mask=1/(1+np.exp(-ribbon))
    # Shallow translucent irregularity along Z, not a flat white stripe.
    fiber_noise=.83+.13*np.sin(1.3*xx+z*.24)*np.cos(1.5*yy-z*.2)
    # Keep source pith as baseline and add an elongated original-coordinate field.
    updated=np.clip(np.maximum(old*.65,mask*fiber_noise),0,1)
    sl[:,:,2]=updated
    if k in (30,95,144,170):orig_blues.append([int(k),float(old.mean()),float(old.max())]);new_blues.append([int(k),float(updated.mean()),float(updated.max())])
name='V9 | owner-video guided central spindle pith + source strands'
im=bpy.data.images.new(name,width=3072,height=2304,alpha=True,float_buffer=False)
im.colorspace_settings.name='Non-Color'
im.pixels.foreach_set(px.ravel());im.update()
outatlas=P/'tissue-v9-central-spindle.png'
im.filepath_raw=str(outatlas);im.file_format='PNG';im.save();im.pack()
# Absolutely preserve R and G channels; spatial pith B only is changed.
material=bpy.data.materials['SDF proof v8 | cut cells flattened on SAME vessel atlas']
material.name='V9 | warm wet pith, same source vascular R field'
for node in material.node_tree.nodes:
    if node.bl_idname=='ShaderNodeTexImage' and node.image==source:
        node.image=im
pithmix=[n for n in material.node_tree.nodes if n.bl_idname=='ShaderNodeMixRGB' and tuple(round(v,2) for v in n.inputs[2].default_value[:3])==(0.89,0.36,0.30)]
assert len(pithmix)==1,len(pithmix)
pithmix[0].inputs[2].default_value=(.95,.73,.65,1)
gn=bpy.data.node_groups['V8 | original rest-space vascular field (192^3)']
found=0
for node in gn.nodes:
    if node.bl_idname=='GeometryNodeImageTexture' and node.inputs['Image'].default_value==source:
        node.inputs['Image'].default_value=im;found+=1
assert found==2,found
bpy.context.scene['v9_hypothesis']='Owner Frucht reference 10.0sec has broad pale central spindle. Expand central pith B field only; preserve vascular R, cell relief, skin and cutters.'
bpy.context.scene['v9_biology']='ALL new pith morphology is ARTIST; not measured strawberry histology.'
bpy.context.scene['v9_video_sha256']='cbe17cfd0ffa0e7697462892a28bd339e0b9666418276287499c49ca6bae684e'
bpy.context.scene.frame_set(20)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(DEST))
record={'version':'v9','source_v8_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),
 'v9_sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),
 'v9_atlas_sha256':hashlib.sha256(outatlas.read_bytes()).hexdigest(),
 'author_reference_seconds':10.0,'new_tissue_channel':'Blue/pith only; R vascular and G mottling preserved',
 'pith_color':[.95,.73,.65],'ARTIST':True,'elapsed_build_s':round(time.monotonic()-t0,2),
 'old_blue_slices':orig_blues,'new_blue_slices':new_blues}
(P/'v9-build.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print('V9_BUILT',json.dumps(record),flush=True)

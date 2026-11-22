"""Strawberry Lab v4 lookdev: sparse volumetric vascular fibers, subtle cellular wet cut.
This is an independent ARTIST field; no commercial Frucht code or textures.
"""
import bpy, numpy as np, os, time, hashlib, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
P=Path(os.environ.get("STRAWBERRY_SDF_OUT",str(ROOT/"build/sdf-vertical-slice")))
BLEND=P/"strawberry-sdf-vertical-slice-v3.blend"
t0=time.monotonic()
bpy.ops.wm.open_mainfile(filepath=str(BLEND),use_scripts=False)
scene=bpy.context.scene
mesh=bpy.data.objects["SDF visible seeds | planar"].data
attr=mesh.attributes["achene_center"]
centers=np.array([attr.data[i*178].vector[:] for i in range(264)],dtype=np.float32)
N=192;C=16;ROWS=12
XS=np.linspace(-18,18,N,dtype=np.float32)
YS=np.linspace(-18,18,N,dtype=np.float32)
ZS=np.linspace(-1,50,N,dtype=np.float32)
dx=(XS[-1]-XS[0])/(N-1);dy=dx;dz=(ZS[-1]-ZS[0])/(N-1)
vessel=np.zeros((N,N,N),dtype=np.float32)
# Curved, distinct seed-linked branch paths in ORIGINAL 3D fruit coordinates.
# Exponential tube kernels are anti-aliased at the voxel level, not actual plant diameters.
for index,(sx,sy,sz) in enumerate(centers):
    rng=np.random.default_rng(index+219)
    trunk=(index%3==0)
    amplitude=(.69 if trunk else .24)*(0.80+0.2*rng.random())
    radius=(.27 if trunk else .19)
    startz=float(max(0,sz-rng.uniform(8.,15.)))
    p0=np.array([rng.uniform(-1.2,1.2),rng.uniform(-1.2,1.2),startz],dtype=np.float32)
    p1=np.array([sx*.15+rng.uniform(-1,1),sy*.15+rng.uniform(-1,1),min(48,sz-5.5)],dtype=np.float32)
    p2=np.array([sx*.58+rng.uniform(-.8,.8),sy*.58+rng.uniform(-.8,.8),min(49,sz-1.0)],dtype=np.float32)
    p3=np.array([sx*.97,sy*.97,sz-.25],dtype=np.float32)
    steps=70 if trunk else 45
    for f in np.linspace(0,1,steps,dtype=np.float32):
        q=((1-f)**3*p0+3*(1-f)**2*f*p1+3*(1-f)*f*f*p2+f**3*p3)
        ix=int(round((q[0]+18)/dx));iy=int(round((q[1]+18)/dy));iz=int(round((q[2]+1)/dz))
        # width changes along branch; wide only at bottom, no merged white mass
        rw=radius*(1.28-.35*f)
        radius_vox=3 if trunk else 2
        a=max(0,ix-radius_vox);b=min(N,ix+radius_vox+1)
        c=max(0,iy-radius_vox);d=min(N,iy+radius_vox+1)
        e=max(0,iz-radius_vox);h=min(N,iz+radius_vox+1)
        if a>=b or c>=d or e>=h:continue
        d2=(XS[None,None,a:b]-q[0])**2+(YS[None,c:d,None]-q[1])**2+(ZS[e:h,None,None]-q[2])**2
        # anti-aliased thin line; no arbitrary large 3D dots
        kern=np.exp(-d2/(2*(rw*rw+(.10*dz)**2)))*amplitude
        target=vessel[e:h,c:d,a:b]
        np.maximum(target,kern,out=target)
print("BUNDLE_RASTER",N,len(centers),"seconds",round(time.monotonic()-t0,2),flush=True)

# Shared broad wisps are low-contrast vascular-looking tissue, not literal vascular bundle solids.
X,Y=np.meshgrid(XS,YS)
R=np.sqrt(X*X+Y*Y)+1e-4
TH=np.arctan2(Y,X)
# Wisp sheets help thin fibers remain visible in different planar orientations.
# Contrast stays below main tube fibers to avoid the old 'white blobs'.
for zi,z in enumerate(ZS):
    phase=(9.*TH +.44*np.sin(z*.22 +R*.17)+ .18*R+.39)
    d_sheet=(R/9.)*np.sin(phase)
    # Slight longitudinal waviness; this is a thin *3D* field, not a 2D cut texture
    wisp=.16*np.exp(-(d_sheet/.25)**2)*np.clip((R-1.5)/3,0,1)
    np.maximum(vessel[zi],wisp.astype(np.float32),out=vessel[zi])
# Generate 3-channel atlas: R=sparse vessels, G=3D cortex mottling, B=pith
# Packing (Z slices in bottom-up 16x12 grid), same contract as v3.
pixels=np.zeros((ROWS*N,C*N,4),dtype=np.float32)
pixels[:,:,3]=1.0
core=2.7+.20*np.sin(ZS*.2)
for zi,z in enumerate(ZS):
    pith=1/(1+np.exp(np.clip((R-(core[zi]))*1.45,-20,20)))
    mottling=(.57+.10*np.sin(X*.64+z*.22)*np.cos(Y*.95-z*.31)
             +.04*np.cos(X*3.7+Y*2.1+z*1.7))
    tx=zi%C;ty=zi//C
    pixels[ty*N:(ty+1)*N,tx*N:(tx+1)*N,0]=np.clip(vessel[zi],0,1)
    pixels[ty*N:(ty+1)*N,tx*N:(tx+1)*N,1]=np.clip(mottling,0,1)
    pixels[ty*N:(ty+1)*N,tx*N:(tx+1)*N,2]=pith
print('DISTRIBUTION',{k:np.percentile(vessel,k).round(3).item() for k in (50,80,90,95,99)},flush=True)

name='SDF proof v4 | 192^3 sparse volume and continuous branches'
img=bpy.data.images.new(name,width=C*N,height=ROWS*N,alpha=True,float_buffer=False)
img.colorspace_settings.name='Non-Color'
img.pixels.foreach_set(pixels.ravel())
img.update()
img.filepath_raw=str(P/'tissue-v4-192.png')
img.file_format='PNG';img.save();img.pack()
print('V4_ATLAS_PACKED',img.size[:],round(time.monotonic()-t0,2),flush=True)
# Preserve previous v3 image for historical readbacks; replace only image sampling nodes.
mat=bpy.data.materials['SDF proof v2 | spatial vascular/pith fields + cut microtexture']
mat.name='SDF proof v4 | sparse branches + cell sheen'
nodes=mat.node_tree.nodes; links=mat.node_tree.links
for node in nodes:
    if node.bl_idname=='ShaderNodeTexImage':node.image=img
    if node.bl_idname=='ShaderNodeMath':
        for socket in node.inputs:
            if socket.is_linked:continue
            val=socket.default_value
            if node.operation=='MINIMUM' and abs(val-127)<.001:socket.default_value=191
            if node.operation=='MULTIPLY' and abs(val-127)<.001:socket.default_value=191
            if node.operation=='MULTIPLY' and abs(val-(127/128))<.001:socket.default_value=191/192
            if node.operation=='ADD' and abs(val-(.5/128))<.001:socket.default_value=.5/192
            if node.operation=='DIVIDE' and abs(val-8)<.001:socket.default_value=12
            if node.operation=='MULTIPLY' and abs(val-.78)<.001:socket.default_value=.56

# Material: transparent moisture sheen with fine cell normal, soft fiber color
bs=next(n for n in nodes if n.bl_idname=='ShaderNodeBsdfPrincipled')
bs.inputs['Subsurface Weight'].default_value=.13
bs.inputs['Roughness'].default_value=.32
bs.inputs['Coat Weight'].default_value=.16
bs.inputs['Coat Roughness'].default_value=.11
mixes=[n for n in nodes if n.bl_idname=='ShaderNodeMixRGB']
for m in mixes:
    if m.inputs[1].is_linked:continue
    col=tuple(m.inputs[1].default_value)
    if abs(col[0]-.48)<.02 and col[1]<.1:
        m.inputs[1].default_value=(.62,.045,.058,1)
        print("PULP_BASE_COLOR")
    if abs(col[0]-.89)<.02 and abs(col[1]-.36)<.02:
        m.inputs[2].default_value=(.94,.49,.39,1)
        print("PITH_COLOR")
    if m.blend_type=='MULTIPLY':
        m.inputs[0].default_value=.14
for m in mixes:
    if m.inputs[2].is_linked:continue
    col=tuple(m.inputs[2].default_value)
    if abs(col[0]-.97)<.02 and abs(col[1]-.75)<.02:
        m.inputs[2].default_value=(.95,.70,.60,1)
        print("FIBER_COLOR")
vornodes=sorted([n for n in nodes if n.bl_idname=='ShaderNodeTexVoronoi'],key=lambda o:o.location.y,reverse=True)
for nodel,scale in zip(vornodes,(2.7,8.5,24.)):
    nodel.inputs['Scale'].default_value=scale
bump=next(n for n in nodes if n.bl_idname=='ShaderNodeBump')
bump.inputs['Strength'].default_value=.43
bump.inputs['Distance'].default_value=.06
# Add micro-edge pigment + varying roughness. Small colored rims only in cut material.
edge=vornodes[0]
edge_map=nodes.new('ShaderNodeMapRange');edge_map.clamp=True;edge_map.location=(1320,100)
edge_map.inputs['From Min'].default_value=.006;edge_map.inputs['From Max'].default_value=.07
edge_map.inputs['To Min'].default_value=.55;edge_map.inputs['To Max'].default_value=.02
links.new(edge.outputs['Distance'],edge_map.inputs['Value'])
shader_mix=nodes.new('ShaderNodeMixRGB');shader_mix.blend_type='MIX'
shader_mix.location=(1500,860)
shader_mix.inputs[2].default_value=(.98,.64,.54,1)
# Final color currently linked from last MixRGB
old=bs.inputs['Base Color'].links[0].from_socket
links.remove(bs.inputs['Base Color'].links[0])
strength=nodes.new('ShaderNodeMath');strength.operation='MULTIPLY'
strength.inputs[1].default_value=.10;strength.location=(1260,-90)
links.new(edge_map.outputs['Result'],strength.inputs[0])
links.new(strength.outputs[0],shader_mix.inputs[0]);links.new(old,shader_mix.inputs[1])
links.new(shader_mix.outputs['Color'],bs.inputs['Base Color'])
rough=nodes.new('ShaderNodeMapRange');rough.clamp=True;rough.location=(1230,-630)
rough.inputs['From Min'].default_value=0.;rough.inputs['From Max'].default_value=.50
rough.inputs['To Min'].default_value=.24;rough.inputs['To Max'].default_value=.45
links.new(edge.outputs['Distance'],rough.inputs['Value'])
links.new(rough.outputs['Result'],bs.inputs['Roughness'])
# Reduce silhouette cap displacement: roughness now largely lives in the shader.
for label in ('planar','bite'):
    g=bpy.data.node_groups['SDF cutter + rest-space | '+label]
    for node in g.nodes:
        if node.bl_idname=='ShaderNodeMath' and node.operation=='MULTIPLY':
            if any(not sock.is_linked and abs(sock.default_value-.27)<.001 for sock in node.inputs):
                for sock in node.inputs:
                    if not sock.is_linked and abs(sock.default_value-.27)<.001:sock.default_value=.16
scene['tissue_v4']='ARTIST 192^3: sparse thin curves from achene anchors, faint 3D wisps, cell/juice microshading; all cuts sample identical rest-space field'
scene['v4_visual_status']='EXPERIMENT ONLY; artistic vascular trajectories, not microscopy or verified anatomy'
scene.frame_set(20)
dest=P/'strawberry-sdf-vertical-slice-v4.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(dest))
manifest={'source_sha256':hashlib.sha256(BLEND.read_bytes()).hexdigest(),
'blend_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
'atlas_sha256':hashlib.sha256((P/'tissue-v4-192.png').read_bytes()).hexdigest(),
'dimensions':[N,N,N],'atlas_dimensions':[C*N,ROWS*N],
'seed_anchors':len(centers),'source':'own sculpted exterior; all tissue data ARTIST',
'build_sec':round(time.monotonic()-t0,2)}
(P/'v4-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('V4_DONE',json.dumps(manifest),flush=True)

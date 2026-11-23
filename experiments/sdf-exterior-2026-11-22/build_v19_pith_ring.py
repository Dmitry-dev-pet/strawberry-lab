"""Independent Strawberry Lab v19: explicitly separate central pith and vascular bundle zone.

Controlled A/B from owner-private v12 scene (unchanged):
 A: tapered pith (Blue) + original R strand field
 B: same tapered pith (Blue) + central annular/longitudinal bundle-zone signal in R.

This is an ARTIST tissue zoning hypothesis motivated by Darrow 1966 and
Hurtado & Knoche 2026; NOT measured pith/bundle widths; NOT copied Frucht nodes.
Both variants reuse the same packed rest-space 192^3 atlas API, SDF cutter,
seed placement, GN Voronoi and material controls. Only RGB image pixels differ.
"""
from pathlib import Path
import bpy,numpy as np,math,time,json,hashlib
SRC=Path('/mnt/data/strawberry-diagnostics/v12.blend')
OUT=Path('/mnt/data/strawberry-v19')
SHA='300a2bfeaa86831220657b74fe8b00d4d7ec0b42f4ffefca863d6410cbb405b7'
assert SRC.is_file() and hashlib.sha256(SRC.read_bytes()).hexdigest()==SHA
out_variants={k:OUT/f'strawberry-v19{k}-pith-ring.blend' for k in ('a','b')}
assert all(not f.exists() for f in out_variants.values())
start=time.monotonic();N=192;COL=16;ROW=12
xs=np.linspace(-18,18,N,dtype=np.float32)
ys=np.linspace(-18,18,N,dtype=np.float32)
zs=np.linspace(-1,50,N,dtype=np.float32)
X,Y=np.meshgrid(xs,ys)
receipts={}
# 3-D sources are not tied to a camera or a cutter. Source physiology is not measured.
for variant,dest in out_variants.items():
    bpy.ops.wm.open_mainfile(filepath=str(SRC),use_scripts=False)
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    old=bpy.data.images['SDF proof v4 | 192^3 sparse volume and continuous branches']
    assert tuple(old.size)==(3072,2304) and old.packed_file and old.colorspace_settings.name=='Non-Color'
    data=np.empty((ROW*N,COL*N,4),np.float32)
    old.pixels.foreach_get(data.ravel())
    keep_G=data[:,:,1].copy();keep_A=data[:,:,3].copy()
    original_R=data[:,:,0].copy()
    ring_amplitudes=[]; core_extents=[]
    for iz,z_ in enumerate(zs):
        z=float(z_)
        # Mild axis curvature, *not* a measured 3-D centerline
        cx=.25*math.sin(z*.13+.35);cy=.21*math.sin(z*.11+.5)
        radial=np.sqrt(((X-cx)*1.04)**2+((Y-cy)*.97)**2)
        # Smooth tapered pith: radius max ≈2.8 mm, unlike the 4–5 mm
        # previous rejected all-white v9 spindle experiment.
        v=max(0.,min(1.,(z-1.5)/48.))
        radius=1.12+1.68*max(0.,math.sin(math.pi*v))**.82
        def smoothstep(x):
            u=max(0.,min(1.,x));return u*u*(3-2*u)
        axial=smoothstep((z-4.0)/6.0)*smoothstep((48.0-z)/5.5)
        # Centrally more homogeneous (pith), soft boundary into bundle zone.
        core=np.clip((radius-radial)/.49,-18,18)
        pith=(1/(1+np.exp(-core)))*(.92*axial)
        pith=pith*(.955+.045*np.cos(z*.29+X*.36+Y*.21))
        tx=iz%COL;ty=iz//COL
        sl=data[ty*N:(ty+1)*N,tx*N:(tx+1)*N,:]
        sl[:,:,2]=np.clip(pith,0,1)
        if variant=='b':
            # Collar of longitudinal vascular bundles around central pith;
            # a *set of bundles*, not a uniform bright white annulus.
            theta=np.arctan2(Y-cy,X-cx)
            vessel_r=radius+.84+.09*math.sin(z*.16)
            radial_profile=np.exp(-.5*((radial-vessel_r)/.47)**2)
            phase=12*theta+.105*z+.25*np.sin(.21*z+1.3*theta)
            # high at curved bundles, low between; no straight regular bars
            discrete=np.exp(-.5*(np.sin(phase)/.37)**2)
            amplitude=(.13+.46*discrete)*axial*(.85+.15*math.sin(z*.18+1.2)**2)
            collar=radial_profile*amplitude
            # Preserve all source radial seed-connected strands and centres.
            sl[:,:,0]=np.maximum(sl[:,:,0],collar).astype(np.float32)
            ring_amplitudes.append([iz,round(float(collar.max()),4),round(float(np.mean(collar)),5)])
        core_extents.append([iz,round(radius,3),round(axial,3)])
    assert np.array_equal(data[:,:,1],keep_G)
    assert np.array_equal(data[:,:,3],keep_A)
    if variant=='a':assert np.array_equal(data[:,:,0],original_R)
    new=bpy.data.images.new(f'Strawberry v19{variant} | centered pith and vascular collar ARTIST',width=COL*N,height=ROW*N,alpha=True,float_buffer=False)
    new.colorspace_settings.name='Non-Color'
    new.pixels.foreach_set(data.ravel());new.update()
    png=OUT/f'v19{variant}-packed-tissue-192.png'
    assert not png.exists()
    new.filepath_raw=str(png);new.file_format='PNG';new.save();new.pack()
    bindings={'shader':0,'gn':0}
    for material in bpy.data.materials:
        if not material.use_nodes:continue
        for n in material.node_tree.nodes:
            if n.bl_idname=='ShaderNodeTexImage' and n.image==old:
                n.image=new;bindings['shader']+=1
    for group in bpy.data.node_groups:
        if group.bl_idname!='GeometryNodeTree':continue
        for n in group.nodes:
            if n.bl_idname=='GeometryNodeImageTexture' and n.inputs['Image'].default_value==old:
                n.inputs['Image'].default_value=new;bindings['gn']+=1
    assert bindings=={'shader':2,'gn':2},bindings
    sc=bpy.context.scene
    sc['v19_hypothesis']='A/B organ identity: tapered central pith B distinct from a central annular/longitudinal bundle zone R; same 192cubed rest atlas'
    sc['v19_variant']='A pith-only with source R, B pith plus partial vascular collar in same original space'
    sc['v19_anatomy']='ARTIST sizes, derived only qualitatively from Darrow 1966 Figs 19-38/39 and Hurtado & Knoche 2026 Fig1'
    sc['v19_no_vendor_source']='Original independent code, no Frucht Kiwi GPL source or commercial strawberry assets'
    sc.frame_set(20)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    receipts[variant]={
        'scene':dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
        'atlas':png.name,'atlas_sha256':hashlib.sha256(png.read_bytes()).hexdigest(),
        'pith_radius_mid_mm':round(float(core_extents[round((25+1)/51*(N-1))][1]),3),
        'channel_bindings':bindings,'R_source_unchanged':variant=='a',
        'green_and_alpha_unchanged':True,'pith_blue_new':True,
        'collar_peak':float(max(x[1] for x in ring_amplitudes)) if ring_amplitudes else 0.,
        'source_atlas':old.name,'scene_file_size':dest.stat().st_size,
        'provenance':'ARTIST scientific qualitative topology, not calibrated or commercial source'
    }
    print('V19_VARIANT_CREATED',variant,json.dumps(receipts[variant]),flush=True)
receipt={'source_v12_sha256':SHA,'Blender':bpy.app.version_string,'variants':receipts,'n':N,'time_s':round(time.monotonic()-start,2),'original_source_untouched':True,'new_fields':'B tapered pith; B variant only adds R discreet annular bundle zone','status':'Engineering UNTESTED / Visual UNREVIEWED'}
(OUT/'v19-build.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print('V19_BUILD_PASS',receipt['time_s'],flush=True)

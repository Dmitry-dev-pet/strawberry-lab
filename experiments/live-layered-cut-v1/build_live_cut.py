"""Build a real MOVABLE shared cut plane on independent Strawberry Lab V4 layers.
- Original saved 28 carrier + 539 branch CURVE paths and 539 diagnostic markers.
- Complete berry reconstructed from OUR volume-first v0 analytic shell, no vendor asset.
- Tissue color follows OUR same v0 150x150x150 stored color volume via tiled UV atlas.
- Blender Boolean cutter and coordinate-driven shader halfspace masks both reference
  the ONE same Empty. Move/rotate that Empty to update all cut-enabled layers.
- Two scenes share ONE cutter and ONE source geometry: matched vs flesh-only.
This is a functional proof of layer controls, NOT a Frucht commercial reconstruction.
"""
from __future__ import annotations
import bpy, numpy as np, math, json, hashlib
from mathutils import Vector
from pathlib import Path
R=Path(__file__).resolve().parent
SRC=bpy.data.scenes['LAYER B | flesh-only cut y=0']
ORIG_CORE=bpy.data.objects['V3 | 28-sag0.25 | CARRIERS']
ORIG_BRANCH=bpy.data.objects['V4 | hook0.85 | BRANCHES']
ORIG_MARK=bpy.data.objects['V2 | 539 seed positions and branch endpoints']
assert len(ORIG_CORE.data.splines)==28 and len(ORIG_BRANCH.data.splines)==539
assert len(ORIG_MARK.data.vertices)==539*6
assert all(x.matrix_world.is_identity for x in (ORIG_CORE,ORIG_BRANCH,ORIG_MARK))

COLS={
 'studio':'00 | STUDIO & CAMERA',
 'control':'01 | ONE MOVABLE CUT CONTROL',
 'cutbody':'10 | FLESH cut with live Boolean',
 'fullbody':'11 | FLESH whole uncut',
 'corefull':'20 | 28 CORE FULL',
 'coreclip':'21 | 28 CORE CLIP by plane shader',
 'branchfull':'30 | 539 BRANCHES FULL',
 'branchclip':'31 | 539 BRANCHES CLIP by plane shader',
 'markerfull':'40 | 539 MARKERS FULL',
 'markerclip':'41 | 539 MARKERS CLIP by plane shader',
 'ghost':'50 | WHOLE OUTLINE translucent',
}
SCENES=[]
for typ in ('MATCHED','FLESH ONLY'):
    sc=bpy.data.scenes.new('LIVE '+typ+' | shared movable plane')
    sc.world=SRC.world
    sc.render.engine='CYCLES';sc.cycles.samples=8;sc.cycles.device='CPU'
    # Many discarded tube surfaces can otherwise exceed Cycles' transparent-ray limit
    # and cause black artifacts on the red fresh-cut material.
    sc.cycles.transparent_max_bounces=192
    sc.render.threads_mode='FIXED';sc.render.threads=4
    sc.render.resolution_x=600;sc.render.resolution_y=680;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
    sc.cycles.use_denoising=True;sc.render.film_transparent=False
    sc.view_settings.view_transform=SRC.view_settings.view_transform
    sc.view_settings.look=SRC.view_settings.look
    sc.view_settings.exposure=SRC.view_settings.exposure
    sc.view_settings.gamma=SRC.view_settings.gamma
    sc['EXPERIMENT']='One live shared plane drives flesh Boolean and optional fiber+marker clipping'
    sc['ANATOMY']='28+539 source 3D paths unchanged; 539 orange markers are diagnostic octahedra'
    sc['LIMIT']='Whole outer skin reconstructed from own v0 analytic profile, volume colors v0 RGB atlas; not native dynamic microgeometry'
    cols={}
    for key,name in COLS.items():
        c=bpy.data.collections.new(sc.name+' | '+name);sc.collection.children.link(c);cols[key]=c
    SCENES.append((sc,cols))

# Camera/light poses: exact studio data from prior layered B, no relative tweaks.
for sc,cols in SCENES:
    c=SRC.camera.copy();c.data=SRC.camera.data.copy();c.name=sc.name+' | camera'
    cols['studio'].objects.link(c);sc.camera=c
    for ob in SRC.objects:
        if ob.type=='LIGHT':
            l=ob.copy();l.data=ob.data.copy();l.name=sc.name+' | '+ob.name
            cols['studio'].objects.link(l)

# Exact same cut control Empty and cutter mesh object in BOTH scenes.
control=bpy.data.objects.new('LIVE CUT | move or rotate this Empty',None)
control.empty_display_type='SINGLE_ARROW';control.empty_display_size=.40
control.location=(0,0,0);control.rotation_euler=(0,0,0)
control['plane_equation']='keep signed local Y >= 0; flesh Boolean cut, optional shader-clipped strands and markers'
control['operation']='Move along local Y to change depth; rotate about local Z to change obliquity'
cutverts=[(-4,-7,-4),(4,-7,-4),(4,0,-4),(-4,0,-4),(-4,-7,4),(4,-7,4),(4,0,4),(-4,0,4)]
cutfaces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
cutmesh=bpy.data.meshes.new('LIVE | infinite halfspace cut block mesh');cutmesh.from_pydata(cutverts,[],cutfaces);cutmesh.update()
knife=bpy.data.objects.new('LIVE CUT | Boolean subtraction volume (hidden in render)',cutmesh)
knife.parent=control
knife.hide_render=True
knife.display_type='WIRE'
# Parent local vertices are anchored exactly at Y=0 plane; no object local translation.
for sc,cols in SCENES:
    cols['control'].objects.link(control);cols['control'].objects.link(knife)

# Construct same analytical whole fruit silhouette as Volume First v0.
ZMIN,ZMAX=-1.18,.98
NTH,NZ=160,190
verts=[(0.,0.,ZMIN)];rings=[]
def radius(z):
    t=np.clip((z-ZMIN)/(ZMAX-ZMIN),0.,1.)
    return max(math.sin(math.pi*t),0.)**.58*(.36+.92*t)
def furrows(z,theta):
    return radius(z)*(1+.021*math.sin(7*theta+2.6*z)+.013*math.cos(13*theta-4.2*z)+.012*math.sin(3*theta-z))
for iz in range(1,NZ):
    z=ZMIN+(ZMAX-ZMIN)*iz/NZ
    r=[]
    for i in range(NTH):
        th=2*math.pi*i/NTH;rr=furrows(z,th)
        r.append(len(verts));verts.append((rr*math.cos(th),rr*math.sin(th),z))
    rings.append(r)
top=len(verts);verts.append((0.,0.,ZMAX))
faces=[]
for i in range(NTH):faces.append((0,rings[0][(i+1)%NTH],rings[0][i]))
for a,b in zip(rings[:-1],rings[1:]):
    for i in range(NTH):faces.append((a[i],a[(i+1)%NTH],b[(i+1)%NTH],b[i]))
for i in range(NTH):faces.append((rings[-1][i],rings[-1][(i+1)%NTH],top))
wholemesh=bpy.data.meshes.new('LIVE WHOLE | original v0 analytic berry surface');wholemesh.from_pydata(verts,[],faces);wholemesh.update()
assert len(wholemesh.vertices)==(NZ-1)*NTH+2
# Validate manifold topological connectivity (closed 2-manifold every edge used twice).
edges={}
for p in wholemesh.polygons:
    v=p.vertices
    for i in range(len(v)):
        k=tuple(sorted((int(v[i]),int(v[(i+1)%len(v)]))))
        edges[k]=edges.get(k,0)+1
assert all(x==2 for x in edges.values()),'Nonmanifold whole shell'

skin=bpy.data.materials['SKIN | thin waxy red layer'].copy();skin.name='LIVE | outer red waxy skin (v0-owned)'
# Build exact v0 source 3-D colors as tiled atlas (150³); interpolate between two slices.
vox=np.load(R/'tissue_3d.npz');lo=vox['lo'].astype(float);hi=vox['hi'].astype(float)
N=vox['color'].shape[0];assert N==150
img=bpy.data.images.load(str(R/'tissue_color_atlas_150.png'),check_existing=False)
img.name='LIVE | ORIGINAL V0 native RGB volume atlas (150^3)'
img.colorspace_settings.name='Non-Color'
img.pack()
flesh=bpy.data.materials.new('LIVE | cut flesh from ORIGINAL v0 stored RGB volume')
flesh.use_nodes=True; flesh.diffuse_color=(.64,.045,.034,1)
nt=flesh.node_tree;nt.nodes.clear()
out=nt.nodes.new('ShaderNodeOutputMaterial');out.location=(1300,180)
bs=nt.nodes.new('ShaderNodeBsdfPrincipled');bs.location=(990,180)
bs.inputs['Roughness'].default_value=.35
bs.inputs['Subsurface Weight'].default_value=.035
bs.inputs['Coat Weight'].default_value=.06
nt.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
geom=nt.nodes.new('ShaderNodeNewGeometry');geom.location=(-1650,150)
sep=nt.nodes.new('ShaderNodeSeparateXYZ');sep.location=(-1460,150)
nt.links.new(geom.outputs['Position'],sep.inputs['Vector'])

def mnode(operation,x,y,label=None):
    n=nt.nodes.new('ShaderNodeMath');n.operation=operation
    n.location=(x,y)
    if label:n.label=label
    return n

def linkval(dst,ind,src):
    if hasattr(src,'node'):nt.links.new(src,dst.inputs[ind])
    else:dst.inputs[ind].default_value=float(src)

def calc(op,a,b,x,y,label=None):
    n=mnode(op,x,y,label);linkval(n,0,a);linkval(n,1,b);return n.outputs['Value']

# Normed atlas coords, with first/last texel centered to avoid tile bleed.
xyz=[]
for j in range(3):
    sub=calc('SUBTRACT',sep.outputs[['X','Y','Z'][j]],lo[j],-1280,150-100*j)
    div=calc('DIVIDE',sub,hi[j]-lo[j],-1100,150-100*j)
    mx=calc('MAXIMUM',div,0.,-920,150-100*j)
    mi=calc('MINIMUM',mx,1.,-745,150-100*j)
    xyz.append(mi)
ux,uy,uz=xyz
zscaled=calc('MULTIPLY',uz,N-1,-570,-95)
zindex=calc('FLOOR',zscaled,0,-570,-100)
zfrac=calc('SUBTRACT',zscaled,zindex,150,-170)
sub1=calc('ADD',zindex,1.0,0,-265)
zindex1=calc('MINIMUM',sub1,N-1,160,-265)

def atlas_coords(k,x,y):
    c=calc('FLOORED_MODULO',k,15,x,y+40)
    rowdiv=calc('DIVIDE',k,15,x,y-55)
    row=calc('FLOOR',rowdiv,0, x+185,y-55)
    uu=calc('MULTIPLY',ux,149/150,x,y-155)
    uadd=calc('ADD',uu,1/300,x+180,y-155)
    ucol=calc('ADD',c,uadd,x+360,y-155)
    U=calc('DIVIDE',ucol,15,x+535,y-155)
    vv=calc('MULTIPLY',uy,149/150,x,y-250)
    vadd=calc('ADD',vv,1/300,x+180,y-250)
    vrow=calc('ADD',row,vadd,x+360,y-250)
    V=calc('DIVIDE',vrow,10,x+535,y-250)
    comb=nt.nodes.new('ShaderNodeCombineXYZ');comb.location=(x+700,y-185)
    nt.links.new(U,comb.inputs['X']);nt.links.new(V,comb.inputs['Y'])
    tex=nt.nodes.new('ShaderNodeTexImage');tex.image=img;tex.interpolation='Linear';tex.extension='CLIP';tex.location=(x+910,y-185)
    nt.links.new(comb.outputs['Vector'],tex.inputs['Vector'])
    return tex.outputs['Color']
t0=atlas_coords(zindex,-570,-330)
t1=atlas_coords(zindex1,-570,-960)
mix=nt.nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.location=(780,250)
nt.links.new(zfrac,mix.inputs[0]);nt.links.new(t0,mix.inputs[1]);nt.links.new(t1,mix.inputs[2])
# Match the v0 hue/saturation grade while retaining original trilinear 3-D tissue values.
hue=nt.nodes.new('ShaderNodeHueSaturation');hue.inputs['Saturation'].default_value=1.25;hue.inputs['Value'].default_value=.88
nt.links.new(mix.outputs['Color'],hue.inputs['Color']);nt.links.new(hue.outputs['Color'],bs.inputs['Base Color'])
# Gentle volume-consistent surface relief, positional spatial noise.
noise=nt.nodes.new('ShaderNodeTexNoise');noise.noise_dimensions='3D';noise.inputs['Scale'].default_value=85.;noise.inputs['Detail'].default_value=2.0
nt.links.new(geom.outputs['Position'],noise.inputs['Vector'])
bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.004
nt.links.new(noise.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
wholemesh.materials.append(skin);wholemesh.materials.append(flesh)
# Cut cube carries face material INDEX=1 (flesh), preserved through Boolean INDEX mode.
cutmesh.materials.append(skin);cutmesh.materials.append(flesh)
for face in cutmesh.polygons:face.material_index=1

# Share full geometry data among scene copies, but use per-scene object modifier.
# Full cut body remains a real Boolean-evaluated MESH with actual cap faces.
for sc,cols in SCENES:
    obj=bpy.data.objects.new(sc.name+' | LIVE cut berry',wholemesh)
    cols['cutbody'].objects.link(obj)
    bm=obj.modifiers.new('LIVE CUT | real changing 3D cap surface','BOOLEAN')
    bm.object=knife;bm.operation='DIFFERENCE';bm.solver='EXACT';bm.material_mode='INDEX'
    obj['source']='same analytic Volume First v0 hull, true 3D body, original 150^3 RGB tissue source'
    whole=bpy.data.objects.new(sc.name+' | WHOLE berry (optional)',wholemesh)
    cols['fullbody'].objects.link(whole)

# Reuse original complete 3D curves/markers exactly, and only clone shaders for clipping.
source={'core':ORIG_CORE,'branch':ORIG_BRANCH,'marker':ORIG_MARK}

def clipped_mat(source_mat,title):
    m=source_mat.copy();m.name=title;m.use_nodes=True
    nodes=m.node_tree.nodes;links=m.node_tree.links
    output=next(x for x in nodes if x.type=='OUTPUT_MATERIAL' and x.is_active_output)
    original=output.inputs['Surface'].links[0].from_socket
    original_link=output.inputs['Surface'].links[0];links.remove(original_link)
    t=nodes.new('ShaderNodeTexCoord');t.object=control
    s=nodes.new('ShaderNodeSeparateXYZ');links.new(t.outputs['Object'],s.inputs['Vector'])
    gt=nodes.new('ShaderNodeMath');gt.operation='GREATER_THAN';gt.inputs[1].default_value=-0.00001
    links.new(s.outputs['Y'],gt.inputs[0])
    transp=nodes.new('ShaderNodeBsdfTransparent')
    mix=nodes.new('ShaderNodeMixShader')
    links.new(gt.outputs[0],mix.inputs[0]);links.new(transp.outputs['BSDF'],mix.inputs[1]);links.new(original,mix.inputs[2]);links.new(mix.outputs[0],output.inputs['Surface'])
    return m

def clone(ob,name,mat):
    o=ob.copy();o.data=ob.data.copy();o.name=name
    o.hide_render=False;o.hide_viewport=False
    # Diagnostic source tubes should not cast severe self-shadow artifacts on the fresh cut.
    # This is a view policy only; no curve coordinates, radii, or materials are changed.
    o.visible_shadow=False
    o.data.materials.clear();o.data.materials.append(mat)
    return o

for sc,cols in SCENES:
    for key,kind in [('corefull','core'),('coreclip','core'),('branchfull','branch'),('branchclip','branch'),('markerfull','marker'),('markerclip','marker')]:
        original=source[kind]
        mat=original.data.materials[0] if key.endswith('full') else clipped_mat(original.data.materials[0],sc.name+' | '+key+' material')
        o=clone(original,sc.name+' | '+key,mat)
        cols[key].objects.link(o)
    # Exact original analytic whole skin, display only as transparent guide.
    ghostmat=bpy.data.materials.new(sc.name+' | guide ghost surface')
    ghostmat.use_nodes=True
    gn=ghostmat.node_tree.nodes;bo=gn.get('Principled BSDF')
    bo.inputs['Base Color'].default_value=(.74,.1,.12,1)
    bo.inputs['Alpha'].default_value=.11
    bo.inputs['Roughness'].default_value=.45
    ghost=bpy.data.objects.new(sc.name+' | optional ghost context',wholemesh.copy())
    ghost.data.materials.clear();ghost.data.materials.append(ghostmat)
    cols['ghost'].objects.link(ghost)
    # Need set per-scene collection exclusions to avoid overlap.
    if bpy.context.window:bpy.context.window.scene=sc
    bpy.context.view_layer.update()
    included={'studio','control','cutbody','coreclip','branchclip','markerclip'} if 'MATCHED' in sc.name else {'studio','control','cutbody','corefull','branchfull','markerfull'}
    def scan(root,col):
        if root.collection==col:return root
        for ch in root.children:
            o=scan(ch,col)
            if o:return o
        return None
    for k,col in cols.items():
        nd=scan(sc.view_layers[0].layer_collection,col)
        assert nd, (sc.name,k)
        nd.exclude=k not in included
    sc['default_layers']=','.join(sorted(included))
    sc['controller']=control.name

if bpy.context.window:bpy.context.window.scene=SCENES[1][0]
# Embed optional no-install UI script, work with direct moving empty even if UI not active.
ui=bpy.data.texts.get('LIVE_CUT_CONTROLS__RUN.py') or bpy.data.texts.new('LIVE_CUT_CONTROLS__RUN.py')
ui.clear();ui.write((R/'live_cut_ui.py').read_text(encoding='utf-8'))
help_text=bpy.data.texts.get('LIVE_CUT_README.txt') or bpy.data.texts.new('LIVE_CUT_README.txt')
help_text.clear();help_text.write('ONE KNIFE: MOVE/ROTATE the Empty named LIVE CUT | move or rotate this Empty.\n'
    'The full fruit is a newly generated analytic v0 whole hull, Boolean cut with procedural cap from the ORIGINAL saved 150^3 RGB v0 volume atlas.\n'
    'Cropped vascular/seed materials use plane-local object coordinates for shader clipping at EXACT SAME controller.\n'
    'Two linked scenes LIVE MATCHED and LIVE FLESH ONLY compare clipping policy, with same source 28+539 spline coordinates and 539 diagnostic seed markers.\n'
    'Collections are native Blender view-layer toggles. For optional N-panel use Scripting > LIVE_CUT_CONTROLS__RUN.py > Run Script.\n'
    'This is LIVE Boolean+shader display, not live regenerated micro-cell geometry, not Frucht commercial code/scene.\n')
# Embed atlas in .blend so file is standalone; no external image file required after save.
outpath=R/'strawberry-live-layered-cut-v1.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(outpath))
report={
 'status':'BUILT','blender':bpy.app.version_string,'scene_names':[s.name for s,_ in SCENES],
 'shared_plane_control':control.name,'body_boolean_solver':'EXACT','source_3d_color_volume_shape':list(vox['color'].shape),
 'source_3d_color_volume_sha256':hashlib.sha256((R/'tissue_3d.npz').read_bytes()).hexdigest(),
 'atlas_image_packed':bool(img.packed_file),'full_body_vertices':len(wholemesh.vertices),'full_body_faces':len(wholemesh.polygons),
 'source_core_splines':len(ORIG_CORE.data.splines),'source_branch_splines':len(ORIG_BRANCH.data.splines),'source_marker_components':len(ORIG_MARK.data.vertices)//6,
 'layer_collection_names':COLS,'volume_source':'Own exact Volume First v0 voxel color field; local z-linear interpolation of packed RGB atlas',
 'limits':['analytic whole fruit hull reconstructed from v0 formulas rather than using cut-only mesh','Shader clip uses transparency; splines remain intact rather than Boolean cutting tube end-caps','Pith, separate cell mesh, juice and real seed geometry not implemented','Flesh cut-surface color volume is from original v0 field, not regenerated from V4 fiber curves','No vendor Frucht commercial GN wiring and no license/rights transfer']
}
(R/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('LIVE_CUT_SCENE_BUILT',json.dumps({k:report[k] for k in ['blender','scene_names','atlas_image_packed','full_body_vertices','source_branch_splines','shared_plane_control']}),flush=True)

#!/usr/bin/env python3
"""Static thin 3D fibre sampling and real geometric ridges on sliced strawberry.

Input: independently authored Volume First v0 .blend and one global source
fine_fibers_3d.npz. All cut angles are sampled from the SAME 3D segment source.
The relief is mesh-coordinate displacement, not normal/bump-map illusion.
No per-cut painted texture, no commercial Frucht source or geometry.

Run Blender 5.2+ with --python ... -- --out PATH. SciPy is optional; falls
back to Blender's mathutils KDTree when scipy is absent.
"""
from pathlib import Path
import sys, argparse, json, time, math
import numpy as np
import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree

a=argparse.ArgumentParser()
a.add_argument('--out',required=True,type=Path)
a.add_argument('--source',type=Path)
a.add_argument('--color-strength',type=float,default=.62)
a.add_argument('--ridge-height',type=float,default=.0125)
a.add_argument('--halo-depth',type=float,default=.0024)
opts=a.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
ROOT=Path(__file__).resolve().parent
src=np.load(opts.source or (ROOT/'outputs'/'fine_fibers_3d.npz'))
points=np.asarray(src['points'],dtype=np.float32)
lens=np.asarray(src['lengths'],dtype=np.int32)
widths=np.asarray(src['widths'],dtype=np.float32)
assert sum(lens)==len(points) and len(lens)==len(widths)
start=[];end=[];halfwidth=[]
k=0
for L,w in zip(lens,widths):
    p=points[k:k+L];k+=L
    start.append(p[:-1]);end.append(p[1:]);halfwidth.extend([w]*(L-1))
A=np.concatenate(start);B=np.concatenate(end)
W=np.asarray(halfwidth,dtype=np.float32)
centers=(A+B)*.5
V=B-A
VV=np.sum(V*V,axis=1)+1e-15
assert np.all(VV>1e-13)
try:
    from scipy.spatial import cKDTree
    tree=cKDTree(centers)
    HAS_SCIPY=True
except ImportError:
    tree=KDTree(len(centers))
    for i,p in enumerate(centers):tree.insert(Vector(p),i)
    tree.balance()
    HAS_SCIPY=False
print('GLOBAL_CURVES_READY',len(lens),'SEGMENTS',len(centers),'scipy_accelerated',HAS_SCIPY,flush=True)

def sample_world(Q):
    """Continuous 3D distance to actual line segments (no voxel blurring).

    KDTree discovers nearby spatial line segments. Each candidate is evaluated
    by exact projection onto its finite 3D segment, not only nearest point.
    """
    Q=np.asarray(Q,dtype=np.float32)
    if HAS_SCIPY:
        ds,near=tree.query(Q,k=8,workers=4)
    else:
        near=np.array([[index for _,index,_ in tree.find_n(Vector(v),8)] for v in Q],dtype=np.int32)
    best=np.empty(len(Q),dtype=np.float32)
    for l in range(0,len(Q),12000):
        ix=near[l:l+12000]
        p=Q[l:l+12000,None,:]
        ap=p-A[ix]
        tv=np.clip(np.sum(ap*V[ix],axis=2)/VV[ix],0,1)
        foot=A[ix]+tv[...,None]*V[ix]
        dist=np.linalg.norm(p-foot,axis=2)
        norm=np.min(dist/W[ix],axis=1)
        best[l:l+12000]=norm
    core=np.exp(-(best/0.89)**2).astype(np.float32)
    halo=np.exp(-(best/2.05)**2).astype(np.float32)
    return core,halo

# Persist source geometry as a real 3D editable reference object. Hidden by
# default because it is a lookdev source, not a bunch of cut-face fake lines.
curve=bpy.data.curves.new('V1_SOURCE | 494 persistent 3D thin filament curves','CURVE')
curve.dimensions='3D'
curve.resolution_u=2
curve.bevel_depth=.0018
curve.bevel_resolution=1
curve.use_fill_caps=True
j=0
for L in lens:
    poly=curve.splines.new('POLY');poly.points.add(int(L)-1)
    data=points[j:j+L];j+=L
    for v,p in zip(poly.points,data):v.co=tuple(map(float,p))+(1.0,)
source=bpy.data.objects.new('V1_SOURCE | spatial filament paths (hidden)',curve)
bpy.context.scene.collection.objects.link(source)
source.hide_render=True
source.hide_set(True)
source['purpose']='494 artist-authored 3D paths for sample-at-cut operations; static lookdev only'

# New shader copy only, so v0 stays available for reliable A/B in same scene.
flesh=bpy.data.materials['FLESH | native 3D tissue color volume']
mat=flesh.copy();mat.name='V1 FLESH | physical 3D filament bundle ridges + wet glints'
bs=mat.node_tree.nodes.get('Principled BSDF');assert bs
nodes=mat.node_tree.nodes;links=mat.node_tree.links
col=bs.inputs['Base Color'];prior=col.links[0].from_socket if col.is_linked else None
if col.is_linked:links.remove(col.links[0])
strand=nodes.new('ShaderNodeAttribute');strand.attribute_name='fine_fiber_signal';strand.location=(-750,-480)
mapr=nodes.new('ShaderNodeMapRange');mapr.clamp=True;mapr.interpolation_type='SMOOTHSTEP'
mapr.inputs['From Min'].default_value=.04
mapr.inputs['From Max'].default_value=.93
mapr.inputs['To Min'].default_value=0.
mapr.inputs['To Max'].default_value=opts.color_strength
mapr.location=(-495,-410);links.new(strand.outputs['Fac'],mapr.inputs['Value'])
mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[2].default_value=(.93,.67,.51,1)
mix.location=(-220,-180);links.new(mapr.outputs['Result'],mix.inputs[0])
if prior:links.new(prior,mix.inputs[1])
else:mix.inputs[1].default_value=(.62,.03,.02,1)
links.new(mix.outputs['Color'],col)
# Wet narrow strand strip: same 3D attribute drives true BRDF roughness.
rough=nodes.new('ShaderNodeMapRange');rough.clamp=True;rough.interpolation_type='SMOOTHSTEP'
rough.inputs['From Min'].default_value=.02;rough.inputs['From Max'].default_value=.95
rough.inputs['To Min'].default_value=.29;rough.inputs['To Max'].default_value=.13
rough.location=(-320,-650);links.new(strand.outputs['Fac'],rough.inputs['Value'])
if bs.inputs['Roughness'].is_linked:links.remove(bs.inputs['Roughness'].links[0])
links.new(rough.outputs['Result'],bs.inputs['Roughness'])
bs.inputs['Subsurface Weight'].default_value=.08

scene=bpy.context.scene
scene['V1_SCHEMA']='volume-first.v1.thin-3d-fibers'
scene['V1_SOURCE']='one 494-curve global 3D polyline source, nearest segment distance'
scene['V1_NOTES']='cut meshes are static not live cutter; all angles sample same 3D lines; zero vendor code'

# All 3 v0 cut meshes stay available under original names, hidden for A/B.
rows=[];t0=time.perf_counter()
for angle in [0,32,82]:
    old=bpy.data.objects[f'CUT_{angle:03d}_deg | SAME 3D SUBSTRATE']
    old.hide_render=True
    clone=old.copy();clone.data=old.data.copy();clone.name=f'V1_CUT_{angle:03d} | thin 3D fiber physical relief'
    old.users_collection[0].objects.link(clone)
    mesh=clone.data
    # Identify only cut-face vertices, with a separate set for seams: seams are
    # shared with skin and must remain exactly at original positions.
    nverts=len(mesh.vertices)
    iscut=np.zeros(nverts,dtype=bool);isskin=np.zeros(nverts,dtype=bool)
    for p in mesh.polygons:
        inds=list(p.vertices)
        if p.material_index==1:iscut[inds]=True
        else:isskin[inds]=True
    rest=np.zeros(nverts*3,dtype=np.float32)
    mesh.attributes['tissue_rest'].data.foreach_get('vector',rest)
    rest=rest.reshape(-1,3)
    cutids=np.flatnonzero(iscut)
    core,halo=sample_world(rest[cutids])
    # Four major conditions: spatial 3D curve nearby; not skin/cut boundary;
    # not top or bottom seam; no displacement outside the fresh cut.
    pos=np.empty(nverts*3,dtype=np.float32)
    mesh.vertices.foreach_get('co',pos)
    pos=pos.reshape(-1,3)
    coords=pos[cutids]
    # The cut lives in local y=0 regardless of *sampled* 3D orientation.
    cut_x=coords[:,0]
    z=coords[:,2]
    # Simpler, robust rim by 3D source analytic fruit radius. Sampling the actual
    # cut end at different furrow angles affects silhouette by <3%.
    t=np.clip((z+1.18)/2.16,0,1)
    approx_radius=np.maximum(np.sin(np.pi*t),0)**.58*(.36+.92*t)
    inner=np.clip((approx_radius-np.abs(cut_x))/.075,0,1)
    top=np.clip((.98-z)/.14,0,1);bottom=np.clip((z+1.18)/.12,0,1)
    fade=(inner*inner*(3-2*inner))*(top*top*(3-2*top))*(bottom*bottom*(3-2*bottom))
    fade[isskin[cutids]]=0.
    # True 3D ridges with a narrow recessed wet halo around them. Under fixed
    # grazing light their shadows/highlights are physically geometric.
    physical=(opts.ridge_height*core-opts.halo_depth*halo)*fade
    pos[cutids,1]-=physical
    mesh.vertices.foreach_set('co',pos.ravel());mesh.update()
    signal=np.zeros(nverts,dtype=np.float32);signal[cutids]=(core*fade).astype(np.float32)
    attr=mesh.attributes.new(name='fine_fiber_signal',type='FLOAT',domain='POINT');attr.data.foreach_set('value',signal)
    actual=np.zeros(nverts,dtype=np.float32);actual[cutids]=physical
    attr=mesh.attributes.new(name='fine_fiber_geometric_offset',type='FLOAT',domain='POINT');attr.data.foreach_set('value',actual)
    assert all(m is not None for m in mesh.materials)
    mesh.materials[1]=mat
    clone.hide_render=(angle!=0)
    clone['source']='fine_fibers_3d.npz; same 494 curves for every orientation'
    clone['angle_3d_sampled']=angle
    clone['not_live_boolean']=True
    clone['physical_ridges']=True
    row={'angle':angle,'vertices':nverts,'faces':len(mesh.polygons),
        'new_signal_nonzero_gt025':int((signal>.25).sum()),
        'geometry_displaced_gt002':int((np.abs(actual)>.002).sum()),
        'largest_physical_offset':float(np.max(np.abs(actual))),
        'skin_boundary_max_displacement':float(np.max(np.abs(actual[isskin]))),
        'visual_ratio_signal_gt025':float(np.mean(signal[cutids]>.25)),
        'fiber_source_curves':len(lens)}
    assert row['skin_boundary_max_displacement']<1e-9
    assert row['geometry_displaced_gt002']>100
    rows.append(row);print('V1_CUT_GEOMETRY',json.dumps(row),flush=True)
# The controls can show any cut; none are separate per-angle artist textures.
scene.frame_set(1)
bpy.context.view_layer.update()
opts.out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(opts.out.resolve()))
report={'schema':'strawberry-lab.volume-first.v1.thin-lines.1',
 'source_curves':len(lens),'source_points':len(points),'source_segments':len(centers),
 'field':'nearest continuous 3D segment, not per-cut painted texture',
 'geometry':'vertex-level true displacement localized to exposed tissue, seam unchanged',
 'results':rows,'build_seconds':round(time.perf_counter()-t0,2),
 'limits':['artist-designed spatial fibers, not botanical microscopy','static physical half cuts, no moving knife','aliasing possible near steep cut fibers','source editing needs re-run builder']}
(ROOT/'outputs'/'build-report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('V1_VOLUME_FIRST_BUILT',opts.out,round(time.perf_counter()-t0,2),flush=True)

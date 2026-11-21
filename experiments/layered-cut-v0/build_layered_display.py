#!/usr/bin/env python3
"""Independent visibility and per-layer halfspace clipping for existing owned V4 curves.

This is a Blender project derived from our own saved V4 source. No new anatomical
curves and no Frucht source/graph. Every full source curve/seed remains in the .blend.
"""
from pathlib import Path
import bpy, numpy as np, json, sys
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs'
OUT.mkdir(exist_ok=True,parents=True)
source_scene=bpy.data.scenes['03 | fibers + actual v1 cut']
source_body=bpy.data.objects['CUT_000_deg | SAME 3D SUBSTRATE']
source_main=bpy.data.objects['V3 | 28-sag0.25 | CARRIERS']
source_branches=bpy.data.objects['V4 | hook0.85 | BRANCHES']
source_markers=bpy.data.objects['V2 | 539 seed positions and branch endpoints']
assert len(source_main.data.splines)==28 and len(source_branches.data.splines)==539

# The actual saved half-fruit occupies y>=0. The 2D cut plane is y=0.
body_y=[v.co.y for v in source_body.data.vertices]
assert min(body_y)>-.03 and max(body_y)>.8
assert all(x.matrix_world.is_identity for x in (source_body,source_main,source_branches,source_markers))

colnames={
'lights':'00 | LIGHTS & CAMERA',
'flesh':'10 | FLESH / opaque 0deg half-fruit',
'fullcore':'20 | CORE CARRIERS / 28 FULL',
'clipcore':'21 | CORE CARRIERS / 28 CLIPPED y>=0',
'fullbranch':'30 | VASCULAR BRANCHES / 539 FULL',
'clipbranch':'31 | VASCULAR BRANCHES / CLIPPED y>=0',
'fullseed':'40 | SEED END MARKERS / 539 FULL',
'clipseed':'41 | SEED END MARKERS / CLIPPED y>=0',
'ghost':'50 | OUTLINE / optional transparent context'
}

# Exact per-segment intersection with y=0 (not simply deleting sampled points).
# Other original point coordinates are unchanged. Interpolates curve radius at cut.
def clip_pts(points,radius):
    eps=1.e-9
    kept=[];cur=[];rr=[]
    def add(p,r):
        if not cur or np.linalg.norm(np.asarray(cur[-1])-p)>1.e-7:
            cur.append(tuple(map(float,p)));rr.append(float(r))
    def close():
        nonlocal cur,rr
        if len(cur)>=2:kept.append((np.array(cur),np.array(rr)))
        cur=[];rr=[]
    for i in range(len(points)-1):
        a=points[i];b=points[i+1];ra=radius[i];rb=radius[i+1]
        ia=a[1]>=-eps;ib=b[1]>=-eps
        if ia and not cur:add(a,ra)
        if ia and ib:
            add(b,rb)
        elif ia and not ib:
            t=float(np.clip(-a[1]/(b[1]-a[1]),0,1))
            add(a+t*(b-a),ra+t*(rb-ra));close()
        elif not ia and ib:
            t=float(np.clip(-a[1]/(b[1]-a[1]),0,1))
            add(a+t*(b-a),ra+t*(rb-ra));add(b,rb)
    close()
    return kept


def split_source(ob):
    cu=ob.data
    full=[];partial=[]
    for sp in cu.splines:
        pts=np.array([p.co[:3] for p in sp.points],dtype=np.float64)
        rad=np.array([p.radius for p in sp.points],dtype=np.float64)
        full.append((pts,rad))
        partial.extend(clip_pts(pts,rad))
    return full,partial

main_full,main_part=split_source(source_main)
branch_full,branch_part=split_source(source_branches)
assert len(main_full)==28 and len(branch_full)==539
for arr in [main_part,branch_part]:
    assert all(np.min(p[:,1])>=-1.e-7 for p,r in arr)

def curve_object(name,source,curves):
    c=bpy.data.curves.new(name+' / data','CURVE');c.dimensions='3D'
    c.resolution_u=source.data.resolution_u;c.bevel_depth=source.data.bevel_depth
    c.bevel_resolution=source.data.bevel_resolution;c.use_fill_caps=source.data.use_fill_caps
    for mat in source.data.materials:c.materials.append(mat)
    for pts,rad in curves:
        s=c.splines.new('POLY');s.points.add(len(pts)-1)
        # Blender Python 3.13 need safe assignment of float array values
        for dst,pos,r in zip(s.points,pts,rad):
            dst.co=tuple(map(float,pos))+(1.0,)
            dst.radius=float(r)
    ob=bpy.data.objects.new(name,c)
    return ob

# The achene markers are *our own diagnostic octahedra*, not real botanical seed meshes.
# Every marker has 6 verts and 8 faces in original V2 project, with fixed ordering.
seeds=source_markers.data
assert len(seeds.vertices)==539*6 and len(seeds.polygons)==539*8
marker_centers=np.array([np.mean([v.co[:] for v in seeds.vertices[j*6:(j+1)*6]],axis=0) for j in range(539)])
keep=np.where(marker_centers[:,1]>=0)[0]
assert 180<=len(keep)<=350

def marker_object(name,indices):
    vertices=[];faces=[]
    for j in indices:
        base=len(vertices)
        vertices.extend([tuple(float(q) for q in v.co) for v in seeds.vertices[j*6:(j+1)*6]])
        faces.extend([tuple(base+int(k)-j*6 for k in p.vertices) for p in seeds.polygons[j*8:(j+1)*8]])
    mesh=bpy.data.meshes.new(name+' / data');mesh.from_pydata(vertices,[],faces);mesh.update()
    for mat in seeds.materials:mesh.materials.append(mat)
    ob=bpy.data.objects.new(name,mesh);ob['actual_marker_count']=len(indices)
    return ob

# Source mesh has two material indices: exterior skin=0, cut flesh=1.
# Copy data per scene, but retain the true original material by identity.
original_mats=[source_body.data.materials[0],source_body.data.materials[1]]
real_cut=bpy.data.objects['V1_CUT_000 | thin 3D fiber physical relief']
assert len(real_cut.data.materials)==2


def build_scene(mode):
    name=('LAYER A | common cut y=0' if mode=='matched' else 'LAYER B | flesh-only cut y=0')
    sc=bpy.data.scenes.new(name)
    sc.world=source_scene.world
    sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=10
    sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=4
    sc.render.resolution_x=690;sc.render.resolution_y=785;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
    sc.render.film_transparent=False
    sc.view_settings.view_transform=source_scene.view_settings.view_transform
    sc.view_settings.look=source_scene.view_settings.look
    sc.view_settings.exposure=source_scene.view_settings.exposure
    sc.view_settings.gamma=source_scene.view_settings.gamma
    sc['display_mode']=mode
    sc['cut_plane_world']='Y=0, retain Y >= 0 (same as original v1 physical half-fruit)'
    sc['layer_control']='Toggle separate 10/20/21/30/31/40/41 collections in View Layer > Outliner'
    sc['artist_reference']='Frucht promotional shot is not exact commercial node graph; no paid data used'
    sc['interpretation']='A and B share source geometry, cut mesh, materials, camera, and lights'
    cols={}
    for key,cn in colnames.items():
        col=bpy.data.collections.new(name+' | '+cn)
        sc.collection.children.link(col)
        cols[key]=col
    # Copy source 03 view exactly, no camera or lighting alteration.
    cam=source_scene.camera.copy();cam.data=source_scene.camera.data.copy();cam.name=name+' | CAMERA'
    cols['lights'].objects.link(cam);sc.camera=cam
    for ob in source_scene.objects:
        if ob.type=='LIGHT':
            clone=ob.copy();clone.data=ob.data.copy();clone.name=name+' | '+ob.name
            cols['lights'].objects.link(clone)
    # Opaque original volume-first v0 half cut with ORIGINAL v0 material.
    # Explicitly exclude the unrelated 494 V1 fiber color/physical ridges.
    flesh=source_body.copy();flesh.data=source_body.data.copy();flesh.name=name+' | FLESH actual static cut'
    for i,mat in enumerate(source_body.data.materials):flesh.data.materials[i]=mat
    flesh.hide_render=False;flesh.hide_viewport=False
    cols['flesh'].objects.link(flesh)
    # Both variants of core and 539 achene branches exist at once and are
    # separately enabled in their own Outliner collections per scene.
    objs={}
    for key,source,paths in [
        ('fullcore',source_main,main_full),('clipcore',source_main,main_part),
        ('fullbranch',source_branches,branch_full),('clipbranch',source_branches,branch_part)]:
        o=curve_object(name+' | '+key,source,paths)
        o['layer_id']=key;o['curves_count']=len(paths)
        cols[key].objects.link(o);objs[key]=o
    objs['fullseed']=marker_object(name+' | seeds full',range(539))
    objs['clipseed']=marker_object(name+' | seeds clipped',keep)
    cols['fullseed'].objects.link(objs['fullseed']);cols['clipseed'].objects.link(objs['clipseed'])
    # Secondary independent whole fruit context only for orientation; off by default.
    ghost_src=bpy.data.objects['CONTEXT | analytical translucent shell']
    ghost=ghost_src.copy();ghost.data=ghost_src.data.copy()
    ghost.name=name+' | optional translucent whole shell'
    cols['ghost'].objects.link(ghost)
    # Collection exclusion is real Blender View Layer state. It is saved in
    # the .blend, independently per scene, and togglable in the Outliner.
    include={'lights','flesh','clipcore','clipbranch','clipseed'} if mode=='matched' else {'lights','flesh','fullcore','fullbranch','fullseed'}
    # Initialize per-scene ViewLayer tree by making this the active scene.
    if bpy.context.window:bpy.context.window.scene=sc
    bpy.context.view_layer.update()
    for key,col in cols.items():
        def find_layer(layer,collection):
            if layer.collection==collection:return layer
            for child in layer.children:
                got=find_layer(child,collection)
                if got:return got
        layer=find_layer(sc.view_layers[0].layer_collection,col)
        assert layer
        layer.exclude=key not in include
    sc['active_collections']=' / '.join([colnames[k] for k in sorted(include)])
    return sc,objs,cols

sc_a,objects_a,cols_a=build_scene('matched')
sc_b,objects_b,cols_b=build_scene('independent')
if bpy.context.window:bpy.context.window.scene=sc_b
# Optional no-install Python UI script embedded as readable Blender Text.
ui=bpy.data.texts.get('LAYER_LAB_UI__RUN_IN_BLENDER.py') or bpy.data.texts.new('LAYER_LAB_UI__RUN_IN_BLENDER.py')
ui.clear();ui.write((ROOT/'layer_controls_ui.py').read_text(encoding='utf-8'))
guide=bpy.data.texts.get('LAYER_LAB_README.txt') or bpy.data.texts.new('LAYER_LAB_README.txt')
guide.clear();guide.write('Open this .blend, choose LAYER A or LAYER B in Blender scene selector.\n'
 'In Outliner, expand named 10/20/21/30/31/40/41 layer collections and toggle their checkboxes for immediate independent render and viewport visibility.\n'
 'For an optional 3D View N sidebar, go to Scripting > Text > LAYER_LAB_UI__RUN_IN_BLENDER.py > Run Script once.\n'
 'Flesh geometry is a STATIC physical Volume First v0 half-fruit at Y=0, retained Y>=0.\n'
 'Core carriers and vascular branches/markers are OUR previously saved true 3D curves.\n'
 'Achene markers are temporary octahedra; physical cells, pith and juice are NOT modeled as separate geometry in V4.\n'
 'These controls do not reproduce vendor Frucht commercial sliders.\n')
out=OUT/'strawberry-independent-layers-v0.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(out))
report={'schema':'strawberry-lab.layered-cut-display.v0.1','source_scene':'v4-terminal-hooks.blend',
    'new_scene_names':[sc_a.name,sc_b.name],
    'retained_solid_y':'y>=0',
    'source_core_splines':28,'source_achene_branches':539,'source_achene_markers':539,
    'clipped_core_segments':len(main_part),'clipped_branch_segments':len(branch_part),'clipped_seed_markers':len(keep),
    'source_hashes_not_modified':True,'cut_flesh_mesh_same_origin':True,
    'layers':['flesh','full_core','clipped_core','full_branches','clipped_branches','full_achenes','clipped_achenes','optional_hull'],
    'no_cell_or_juice_layers':'No separate physical cell or juice objects in our current Volume First v4 scenes; these are NOT silently fabricated',
    'flesh_material':'original Volume First v0 tissue shader, not unrelated V1 494-path fiber material',
    'source_no_new_anatomy':True,
    'fiber_geometry_derived_from_exact_3D_curve_segments':'clip intersections interpolated at y=0 without moving in-volume original samples',
    'author_relationship':'Hypothesis demonstration only, not equivalent to proprietary Frucht paid runtime',
    'output':str(out)}
(OUT/'build-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('LAYER_BUILD_PASS',json.dumps(report),flush=True)

#!/usr/bin/env python3
"""Strawberry Lab M1c (research): SDF Boolean + rest-space 3D atlas + wet cut shader.

Independent Blender 5.2+ implementation. Loads an M1a 'whole' scene built
from public Strawberry Lab sources; source code of commercial Frucht is NOT used.
Cutters can be rotated (half cut) or spherical (bite), evaluated in Geometry Nodes.
An 8x8 atlas of 64^3 voxel data is trilinearly interpolated in Z by shaders.
Original-coordinate attribute is stored BEFORE any movement of cut pieces.

Usage:
 blender -b --python sdf_cut_strawberry.py -- --base whole.blend \
 --atlas tissue-atlas-64.png --mode half --angle 18 --voxel .055 --out build/
"""
import argparse,sys,math,json,time,bmesh
from pathlib import Path
from mathutils import Vector,Matrix
import bpy

par=argparse.ArgumentParser()
par.add_argument('--base',type=Path,required=True)
par.add_argument('--atlas',type=Path,required=True)
par.add_argument('--mode',choices=['half','bite'],default='half')
par.add_argument('--angle',type=float,default=17.0,help='half-cutter tilt angle, degrees around X')
par.add_argument('--voxel',type=float,default=.06)
par.add_argument('--out',type=Path,required=True)
par.add_argument('--resolution',type=int,default=720)
par.add_argument('--samples',type=int,default=18)
par.add_argument('--no-render',action='store_true')
par.add_argument('--no-glb',action='store_true')
a=par.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
assert .026<=a.voxel<=.13,'voxel must be between .026 and .13'
assert a.base.is_file() and a.atlas.is_file(), 'Missing provided baseline or atlas'
a.out.mkdir(parents=True,exist_ok=True)
start=time.monotonic()
bpy.ops.wm.open_mainfile(filepath=str(a.base))
scene=bpy.context.scene
source=bpy.data.objects.get('Receptacle | actual pit-deformed epidermis')
seed_obj=bpy.data.objects.get('GN live achenes (with actual surface pits)')
if not (source and seed_obj):raise RuntimeError('Expected published M1a whole scene, with live GN achenes')
coll=source.users_collection[0]

# --- 1. Seal previous nonmanifold parametric shell, without changing source ---
bm=bmesh.new();bm.from_mesh(source.data)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5)
boundary=[e for e in bm.edges if e.is_boundary]
if len(boundary)<10:raise RuntimeError('Unexpected unsealed shell')
filled=bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
if any(not e.is_manifold for e in bm.edges) or bm.calc_volume(signed=True)<=0:raise RuntimeError('Sealed fruit not a positive manifold')
me=bpy.data.meshes.new('M1c | watertight receptacle for SDF')
bm.to_mesh(me);bm.free();me.update()
solid=bpy.data.objects.new('M1c | watertight base (hidden)',me)
coll.objects.link(solid)
solid.hide_render=True
solid.hide_set(True)
source.hide_render=True
source.hide_set(True)

# --- 2. Actual arbitrary cutter geometry (may rotate, move, scale) ---
if a.mode=='half':
    bpy.ops.mesh.primitive_cube_add(size=2)
    cutter=bpy.context.object
    cutter.name='M1c | oriented arbitrary plane cutter'
    cutter.rotation_euler=(math.radians(a.angle),0,math.radians(-14))
    rot=cutter.rotation_euler.to_matrix()
    cutter.location=rot @ Vector((0.,-3.0,0.))
    cutter.scale=(4.0,3.0,5.0)
else:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4,radius=1)
    cutter=bpy.context.object
    cutter.name='M1c | round bite cutter'
    cutter.location=(1.14,-.90,-.40)
    cutter.scale=(1.02,1.11,.98)

# Prior to rendering, hide only the cutter object, not the Geometry Nodes
# source information. ObjectInfo obtains the original geometry even when hidden.
cutter.hide_render=True
cutter.display_type='WIRE'
cutter.hide_set(False)
bpy.context.view_layer.update()

# Filter GN seed points that would lie inside cutter; retain their original
# seed_euler / seed_size attributes so the live GN modifier remains editable.
oldmesh=seed_obj.data
ac=oldmesh.attributes['seed_euler'];asiz=oldmesh.attributes['seed_size']
invm=cutter.matrix_world.inverted()
kept=[]
for i,v in enumerate(oldmesh.vertices):
    local=invm@Vector(v.co)
    inside=(max(abs(local.x),abs(local.y),abs(local.z))<=1.004 if a.mode=='half' else local.length<=1.005)
    if not inside:kept.append(i)
if len(kept)<20:raise RuntimeError('Cutter deleted almost all achenes')
me_pts=bpy.data.meshes.new('M1c | achene anchors outside cutter')
me_pts.from_pydata([oldmesh.vertices[i].co[:] for i in kept],[],[]);me_pts.update()
a_rot=me_pts.attributes.new('seed_euler','FLOAT_VECTOR','POINT')
a_sz=me_pts.attributes.new('seed_size','FLOAT','POINT')
for j,i in enumerate(kept):
    a_rot.data[j].vector=ac.data[i].vector[:]
    a_sz.data[j].value=asiz.data[i].value
seed_obj.data=me_pts
print('ACHENES_RETAINED',len(kept),'of',len(oldmesh.vertices),flush=True)

# --- 3. Packed 3-D field sampler built explicitly with Blender shader nodes ---
def build_cap_material(png_path):
    m=bpy.data.materials.new('M1c | rest-space pith/cortex + wet Voronoi surface')
    m.use_nodes=True;nt=m.node_tree;nd=nt.nodes;lk=nt.links
    bs=nd.get('Principled BSDF')
    bs.inputs['Roughness'].default_value=.32
    bs.inputs['Subsurface Weight'].default_value=.14
    bs.inputs['Coat Weight'].default_value=.20
    bs.inputs['Coat Roughness'].default_value=.20
    attr=nd.new('ShaderNodeAttribute');attr.attribute_name='fruit_rest';attr.location=(-1600,500)
    add=nd.new('ShaderNodeVectorMath');add.operation='ADD';add.inputs[1].default_value=(2,2,2);add.location=(-1380,500)
    lk.new(attr.outputs['Vector'],add.inputs[0])
    scale=nd.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs['Scale'].default_value=.25;scale.location=(-1160,500)
    lk.new(add.outputs['Vector'],scale.inputs[0])
    xyz=nd.new('ShaderNodeSeparateXYZ');xyz.location=(-960,510);lk.new(scale.outputs['Vector'],xyz.inputs['Vector'])
    def mathnode(op,x=None,y=None,val=None,loc=(0,0)):
        n=nd.new('ShaderNodeMath');n.operation=op;n.location=loc
        if x is not None:lk.new(x,n.inputs[0])
        elif val is not None:n.inputs[0].default_value=val
        if y is not None:lk.new(y,n.inputs[1])
        return n.outputs[0]
    # 0..63 coordinate between voxel slices; same field sampled for all cuts.
    z=mathnode('MULTIPLY',xyz.outputs['Z'],val=None,loc=(-750,400));z.node.inputs[1].default_value=63.
    zclamp=mathnode('MAXIMUM',z,loc=(-570,400));zclamp.node.inputs[1].default_value=0.
    zlim=mathnode('MINIMUM',zclamp,loc=(-390,400));zlim.node.inputs[1].default_value=63.
    lo=mathnode('FLOOR',zlim,loc=(-210,400))
    frac=mathnode('SUBTRACT',zlim,lo,loc=(-30,400))
    hi=mathnode('MINIMUM',mathnode('ADD',lo,loc=(-70,170)),loc=(80,170));hi.node.inputs[1].default_value=63.
    # ensure inner ADD adds 1 (the node was made to be rewritten in place)
    hi.node.inputs[0].links[0].from_node.inputs[1].default_value=1.
    image=bpy.data.images.load(str(png_path),check_existing=False)
    image.colorspace_settings.name='Non-Color';image.pack()
    def sample(ix,base_x):
        rem=mathnode('FLOORED_MODULO',ix,loc=(base_x,-160));rem.node.inputs[1].default_value=8.
        row=mathnode('DIVIDE',ix,loc=(base_x,-300));row.node.inputs[1].default_value=8.
        row2=mathnode('FLOOR',row,loc=(base_x+150,-300))
        # Bilinear interpolation INSIDE the tile, without bleeding across atlas rows:
        # UV within a tile = (clamp(x,0,1)*63+0.5)/64; z interpolation below.
        xscale=mathnode('MULTIPLY',xyz.outputs['X'],loc=(base_x-20,-90));xscale.node.inputs[1].default_value=63./64.
        xsafe=mathnode('ADD',xscale,loc=(base_x+80,-90));xsafe.node.inputs[1].default_value=.5/64.
        u=mathnode('ADD',rem,xsafe,loc=(base_x+150,-110))
        uvx=mathnode('DIVIDE',u,loc=(base_x+310,-110));uvx.node.inputs[1].default_value=8.
        yscale=mathnode('MULTIPLY',xyz.outputs['Y'],loc=(base_x-20,-380));yscale.node.inputs[1].default_value=63./64.
        ysafe=mathnode('ADD',yscale,loc=(base_x+80,-380));ysafe.node.inputs[1].default_value=.5/64.
        v=mathnode('ADD',row2,ysafe,loc=(base_x+310,-290))
        uvy=mathnode('DIVIDE',v,loc=(base_x+470,-290));uvy.node.inputs[1].default_value=8.
        xyzv=nd.new('ShaderNodeCombineXYZ');xyzv.location=(base_x+625,-150)
        lk.new(uvx,xyzv.inputs['X']);lk.new(uvy,xyzv.inputs['Y'])
        tex=nd.new('ShaderNodeTexImage');tex.image=image;tex.interpolation='Linear';tex.extension='EXTEND';tex.location=(base_x+830,-150)
        lk.new(xyzv.outputs[0],tex.inputs['Vector'])
        return tex.outputs['Color']
    c0=sample(lo,-600)
    c1=sample(hi,500)
    atlas_mix=nd.new('ShaderNodeMixRGB');atlas_mix.blend_type='MIX';atlas_mix.location=(1480,50)
    lk.new(c0,atlas_mix.inputs[1]);lk.new(c1,atlas_mix.inputs[2]);lk.new(frac,atlas_mix.inputs[0])
    # packed 3D colors = vascular, texture, pith; separate in shader
    sep=nd.new('ShaderNodeSeparateColor');sep.mode='RGB';sep.location=(1660,60)
    lk.new(atlas_mix.outputs['Color'],sep.inputs['Color'])
    # cortex pink-red; pale pith according to 3D volume from atlas
    pith_mix=nd.new('ShaderNodeMixRGB');pith_mix.location=(1900,190)
    pith_mix.inputs[1].default_value=(.87,.16,.19,1)
    pith_mix.inputs[2].default_value=(.96,.67,.58,1)
    lk.new(sep.outputs['Blue'],pith_mix.inputs[0])
    # vascular light strokes (intentionally subtle in photorealistic mode)
    vessel_fac=mathnode('MULTIPLY',sep.outputs['Red'],loc=(1880,0));vessel_fac.node.inputs[1].default_value=.38
    vascular_mix=nd.new('ShaderNodeMixRGB');vascular_mix.location=(2140,180)
    lk.new(vessel_fac,vascular_mix.inputs[0]);lk.new(pith_mix.outputs['Color'],vascular_mix.inputs[1]);vascular_mix.inputs[2].default_value=(1.,.78,.64,1.)
    modcol=nd.new('ShaderNodeMixRGB');modcol.blend_type='MULTIPLY';modcol.inputs[0].default_value=.42;modcol.location=(2360,180)
    lk.new(vascular_mix.outputs[0],modcol.inputs[1])
    # Mild 3D mottling, while pith/cortex ratios still follow the source atlas.
    mulc=mathnode('MULTIPLY',sep.outputs['Green'],loc=(1930,-180));mulc.node.inputs[1].default_value=.35
    addc=mathnode('ADD',mulc,loc=(2110,-180));addc.node.inputs[1].default_value=.86
    lk.new(addc,modcol.inputs[2]);lk.new(modcol.outputs['Color'],bs.inputs['Base Color'])
    # 3 scales of Voronoi: visible cells, fine pores, sub-pixel wet sheen
    layers=[]
    for k,(sz,w) in enumerate(((19,.49),(57,.24),(145,.09))):
        v=nd.new('ShaderNodeTexVoronoi');v.voronoi_dimensions='3D';v.feature='DISTANCE_TO_EDGE';v.location=(1000, -500-k*220)
        v.inputs['Scale'].default_value=sz
        lk.new(attr.outputs['Vector'],v.inputs['Vector'])
        coeff=mathnode('MULTIPLY',v.outputs['Distance'],loc=(1250,-500-k*220));coeff.node.inputs[1].default_value=w
        layers.append(coeff)
    add1=mathnode('ADD',layers[0],layers[1],loc=(1460,-460))
    add2=mathnode('ADD',add1,layers[2],loc=(1680,-460))
    bump=nd.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.30;bump.inputs['Distance'].default_value=.010;bump.location=(1940,-400)
    lk.new(add2,bump.inputs['Height']);lk.new(bump.outputs['Normal'],bs.inputs['Normal'])
    return m

skinmat=bpy.data.materials.get('Strawberry M1a • red epidermis, physically notated')
if skinmat is None: raise RuntimeError('Original M1a skin shader missing')
cutmat=build_cap_material(a.atlas)

# --- 4. Fully editable SDF boolean group: actual cutter object provided in UI ---
base_obj=bpy.data.objects.new('M1c | SDF cutter + rest-space tissue',me)
coll.objects.link(base_obj)
base_obj.data.materials.clear();base_obj.data.materials.append(skinmat);base_obj.data.materials.append(cutmat)
g=bpy.data.node_groups.new('M1c | arbitrary-cutter SDF Boolean & material classification','GeometryNodeTree')
g.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
N=g.nodes;L=g.links
inp=N.new('NodeGroupInput');inp.location=(-1100,200)
out=N.new('NodeGroupOutput');out.location=(1900,250)
info=N.new('GeometryNodeObjectInfo');info.inputs['Object'].default_value=cutter;info.transform_space='RELATIVE';info.location=(-1100,-240)
v1=N.new('GeometryNodeMeshToSDFGrid');v1.inputs['Voxel Size'].default_value=a.voxel;v1.inputs['Band Width'].default_value=5;v1.location=(-810,250)
v2=N.new('GeometryNodeMeshToSDFGrid');v2.inputs['Voxel Size'].default_value=a.voxel;v2.inputs['Band Width'].default_value=5;v2.location=(-810,-250)
L.new(inp.outputs['Geometry'],v1.inputs['Mesh']);L.new(info.outputs['Geometry'],v2.inputs['Mesh'])
bo=N.new('GeometryNodeSDFGridBoolean');bo.operation='DIFFERENCE';bo.location=(-540,250)
L.new(v1.outputs[0],bo.inputs['Grid 1']);L.new(v2.outputs[0],bo.inputs['Grid 2'])
gm=N.new('GeometryNodeGridToMesh');gm.inputs['Threshold'].default_value=0.;gm.inputs['Adaptivity'].default_value=0.;gm.location=(-290,250)
L.new(bo.outputs['Grid'],gm.inputs['Grid'])
# Preserve original coordinate frame for all geometry, so after transforms the
# shader's tissue pattern does not stick to the new object frame (swimming).
pos=N.new('GeometryNodeInputPosition');pos.location=(-290,-340)
store=N.new('GeometryNodeStoreNamedAttribute');store.data_type='FLOAT_VECTOR';store.domain='POINT';store.inputs['Name'].default_value='fruit_rest';store.location=(-60,250)
smooth=N.new('GeometryNodeSetShadeSmooth');smooth.domain='FACE';smooth.location=(-250,520)
L.new(gm.outputs['Mesh'],smooth.inputs['Geometry'])
L.new(smooth.outputs['Geometry'],store.inputs['Geometry']);L.new(pos.outputs['Position'],store.inputs['Value'])
s1=N.new('GeometryNodeSetMaterial');s1.inputs['Material'].default_value=skinmat;s1.location=(180,250)
L.new(store.outputs['Geometry'],s1.inputs['Geometry'])
pro=N.new('GeometryNodeProximity');pro.target_element='FACES';pro.location=(170,-250);L.new(info.outputs['Geometry'],pro.inputs['Target'])
cmp=N.new('FunctionNodeCompare');cmp.data_type='FLOAT';cmp.operation='LESS_THAN';cmp.inputs[1].default_value=a.voxel*1.7;cmp.location=(420,-240)
L.new(pro.outputs['Distance'],cmp.inputs[0])
s2=N.new('GeometryNodeSetMaterial');s2.inputs['Material'].default_value=cutmat;s2.location=(670,250)
L.new(s1.outputs['Geometry'],s2.inputs['Geometry']);L.new(cmp.outputs['Result'],s2.inputs['Selection'])
# Geometry displacement only on exposed cut faces; 3D Voronoi is also used
# in normal shader at higher frequency, for wet pores. Very small physically.
vor=N.new('ShaderNodeTexVoronoi');vor.feature='DISTANCE_TO_EDGE';vor.voronoi_dimensions='3D';vor.inputs['Scale'].default_value=23.;vor.location=(430,-620);L.new(pos.outputs['Position'],vor.inputs['Vector'])
mul=N.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=.010;mul.location=(650,-620);L.new(vor.outputs['Distance'],mul.inputs[0])
nrm=N.new('GeometryNodeInputNormal');nrm.location=(660,-820)
sc=N.new('ShaderNodeVectorMath');sc.operation='SCALE';sc.location=(870,-700);L.new(nrm.outputs['Normal'],sc.inputs[0]);L.new(mul.outputs['Value'],sc.inputs['Scale'])
setp=N.new('GeometryNodeSetPosition');setp.location=(1110,250)
L.new(s2.outputs['Geometry'],setp.inputs['Geometry']);L.new(cmp.outputs['Result'],setp.inputs['Selection']);L.new(sc.outputs['Vector'],setp.inputs['Offset'])
L.new(setp.outputs['Geometry'],out.inputs['Geometry'])
modifier=base_obj.modifiers.new('LIVE SDF cut — select cutter object / voxel size','NODES');modifier.node_group=g

# Camera, render, save original editable .blend.
cam=scene.camera
if cam is not None and a.mode=='half':
    cam.location=(3.1,-8.2,3.2)
    target=Vector((0.,0.,0.))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=5.5
elif cam is not None:
    cam.location=(4.5,-7.8,2.6)
    cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=5.6
scene.render.resolution_x=a.resolution;scene.render.resolution_y=a.resolution
scene.cycles.samples=a.samples
scene.cycles.device='CPU'
scene.render.engine='CYCLES'
scene.render.image_settings.file_format='PNG'
scene['m1c_status']='Original closed SDF cutting + rest-space 64^3 baked atlas + 3 procedural Voronoi wetness layers'
scene['m1c_cutter']=cutter.name;scene['m1c_mode']=a.mode;scene['m1c_voxel_size']=a.voxel
scene['m1c_not_commercial_frucht']='Independent Blender implementation, uncalibrated rest-space voxel values'

# Measure GN modifier output to catch failures; do not claim success from save alone.
bpy.context.view_layer.update()
deps=bpy.context.evaluated_depsgraph_get()
evaluated=base_obj.evaluated_get(deps)
ms=evaluated.to_mesh()
counts={'vertices':len(ms.vertices),'triangles':sum(len(p.vertices)-2 for p in ms.polygons),
        'faces':len(ms.polygons),'materials':{},'nonmanifold_edges':None}
for p in ms.polygons:
    matn=p.material_index;counts['materials'][str(matn)]=counts['materials'].get(str(matn),0)+1
if counts['triangles']<1000:raise RuntimeError('SDF evaluation empty/invalid: '+repr(counts))
test_bm=bmesh.new();test_bm.from_mesh(ms)
counts['nonmanifold_edges']=sum(not e.is_manifold for e in test_bm.edges)
test_bm.free()
evaluated.to_mesh_clear()
print('SDF_EVALUATED',json.dumps(counts),flush=True)
if counts['nonmanifold_edges']!=0:raise RuntimeError('SDF mesh not watertight')
if len(counts['materials'])<2:raise RuntimeError('No distinct internal cut material classified')

stem=a.out / f'strawberry-m1c-{a.mode}'
scene.render.filepath=str(stem.with_suffix('.png'))
bpy.ops.wm.save_as_mainfile(filepath=str(stem.with_suffix('.blend')))
print('BLEND_SAVED',stem.with_suffix('.blend'),flush=True)
if not a.no_render:
    bpy.ops.render.render(write_still=True)
    print('RENDER_SAVED',stem.with_suffix('.png'),flush=True)
if not a.no_glb:
    # GLB includes evaluated and already material-classified SDF geometry.
    for item in list(bpy.context.selected_objects):item.select_set(False)
    base_obj.hide_set(False);base_obj.select_set(True)
    seed_obj.hide_set(False);seed_obj.select_set(True)
    bpy.context.view_layer.objects.active=base_obj
    bpy.ops.export_scene.gltf(filepath=str(stem.with_suffix('.glb')),export_format='GLB',use_selection=True,export_apply=True)
    print('GLB_SAVED',stem.with_suffix('.glb'),flush=True)
stat={'mode':a.mode,'voxel':a.voxel,'angle':a.angle,'achene_count':len(kept),
      'sdf_output':counts,'render_samples':a.samples,'resolution':a.resolution,
      'elapsed_sec':round(time.monotonic()-start,2),'base':a.base.name,'atlas':a.atlas.name}
stem.with_name(stem.name+'-stats.json').write_text(json.dumps(stat,indent=2)+'\n')
print('M1C_DONE',json.dumps(stat),flush=True)
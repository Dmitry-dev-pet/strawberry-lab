#!/usr/bin/env python3
"""Original procedural strawberry prototype, independent of Frucht assets.
Blender 5.2+: --background --python generate_strawberry.py -- --mode cut|whole
Shape/seed positions/slice follow mathematical functions; seeds use Geometry Nodes.
The cut-plane y=0 intersects the actual 3-D fruit and exposes calculated tissue fields.
GLB uses baked geometry/material textures for real-time Three.js rendering.
"""
import bpy
import math
import random
import sys
import argparse
import os
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin,cos,pi,sqrt

OUT=Path(__file__).resolve().parent
P=argparse.ArgumentParser()
P.add_argument('--mode',choices=['whole','cut'],default='cut')
P.add_argument('--preview',action='store_true')
P.add_argument('--samples',type=int,default=24)
P.add_argument('--resolution',type=int,default=920)
args=P.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
CUT = args.mode=='cut'
random.seed(1729)
H = 3.65
R = 1.62
V=Vector
bpy.ops.wm.read_factory_settings(use_empty=True)

# ---- Shape and tissue field definitions ----
def radius(t,th=0):
    t=max(0.00001,min(.99999,t))
    profile=R * pow(max(0.,sin(pi*t)),.56) * (.37+.93*t)
    ridge=.027*sin(7*th+1.7*t)+.013*sin(13*th-8*t)+.007*sin(19*th+3.1*t)
    return max(0, profile*(1+ridge))

def pt(t,th):
    r=radius(t,th)
    return (r*cos(th),r*sin(th),(t-.5)*H)

def normal(t,th):
    eps=.0005
    slope=(radius(min(.99999,t+eps),th)-radius(max(.00001,t-eps),th))/(2*eps*H)
    return V((cos(th),sin(th),-slope)).normalized()

def tissue(x,z):
    """Normalized tissue fields at cut coordinates; shared with texture generator.
    Radius comes from the same function as the 3-D skin (no painted photo).
    Fields: outer epidermis, cortex/flesh, pale vascular pith, fibers.
    """
    t=max(.0005,min(.9995,z/H+.5))
    side=radius(t,0) if x>=0 else radius(t,pi)
    q=min(2.0,abs(x)/max(side,.0001))
    # strawberry's white vascular pith, irregular and tapered toward the tip
    corew=.22+.09*(t**1.3)
    corew*=1+.18*sin(5*t+.6)+.05*sin(22*t)
    core=max(0.,min(1.,(corew-abs(x))/.075))
    cortex=max(0.,min(1.,(1-q)/.12))
    epidermis=max(0.,min(1.,(q-.93)/.065))
    return dict(t=t,q=q,core=core,cortex=cortex,epidermis=epidermis)

# ---- Blender materials ----
def mat(name,color,rough=.6,tex=None,metal=0,coat=0):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    m.diffuse_color=(*color,1)
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=rough
    bs.inputs['Metallic'].default_value=metal
    bs.inputs['Coat Weight'].default_value=coat
    if tex:
        nd=m.node_tree.nodes.new('ShaderNodeTexImage')
        nd.image=bpy.data.images.load(str(OUT/tex),check_existing=True)
        nd.image.pack()
        nd.interpolation='Linear'
        m.node_tree.links.new(nd.outputs['Color'],bs.inputs['Base Color'])
    return m

SKIN=mat('Strawberry | Skin pigment (baked procedural texture)',(.62,.036,.055),.55,'skin.png',coat=.06)
CAP=mat('Strawberry | Tissue map (core, cortex, vascular bundles)',(.68,.19,.23),.48,'flesh.png',coat=.08)
PIT=mat('Strawberry | Seed pits',(.26,.015,.018),.9)
SEED=mat('Strawberry | Golden achenes',(.69,.39,.105),.56,metal=.018,coat=.08)
LEAF=mat('Strawberry | Calyx green',(.105,.29,.045),.63)
LEAF_L=mat('Strawberry | Green leaf veins',(.25,.43,.09),.8)
STEM=mat('Strawberry | Stem',(.24,.28,.055),.84)
VEIN=mat('Strawberry | Cut fibers',(.98,.71,.56),.58)
FLOOR=mat('Studio | Charcoal',(.046,.065,.080),.78)

model_col=bpy.data.collections.new('01 • STRAWBERRY MODEL')
bpy.context.scene.collection.children.link(model_col)
studio_col=bpy.data.collections.new('02 • STUDIO (not exported)')
bpy.context.scene.collection.children.link(studio_col)

def mkmesh(name,verts,faces,material,uv=None,smooth=True):
    mesh=bpy.data.meshes.new(name+' mesh')
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    o=bpy.data.objects.new(name,mesh)
    model_col.objects.link(o)
    if material: mesh.materials.append(material)
    if uv:
        uvmap=mesh.uv_layers.new(name='UVMap')
        for pol in mesh.polygons:
            for li in pol.loop_indices:
                uvmap.data[li].uv=uv[mesh.loops[li].vertex_index]
    for pol in mesh.polygons: pol.use_smooth=smooth
    return o

# ---- Solid body: genuine 3D shape, y>0 retained in a longitudinal cut ----
def make_skin():
    N=196
    S=128 if CUT else 256
    verts=[]; faces=[]; uv=[]
    for j in range(N+1):
        t=.001+j*.998/N
        for i in range(S+1):
            th=(pi if CUT else 2*pi)*i/S
            verts.append(pt(t,th))
            uv.append((th/(2*pi),t))
    for j in range(N):
        for i in range(S):
            b=j*(S+1)+i
            faces.append((b,b+1,b+S+2,b+S+1))
    skin=mkmesh('SKIN | Parametric strawberry surface',verts,faces,SKIN,uv)
    skin['generator']='radius(t,theta) + radial ridges; profile and cut use same shape equation'
    return skin

# ---- Flat cut face, with a true side-to-side tessellated surface and tissue UV map ----
def make_cut_flesh():
    N=190;M=125
    verts=[];faces=[];uv=[]
    for j in range(N+1):
        t=.001+j*.998/N
        z=H*(t-.5)
        neg=-radius(t,pi); pos=radius(t,0)
        for i in range(M+1):
            s=i/M
            x=neg+(pos-neg)*s
            # small micro-relief; preserves a precise planar outer outline
            rel=.0022 * (1-(2*s-1)**8) * sin(11*t+31*s)*sin(83*t+9*s)
            verts.append((x,-.003-rel,z))
            uv.append(((x/R+1)/2,t))
    for j in range(N):
        for i in range(M):
            b=j*(M+1)+i
            # normals toward negative Y
            faces.append((b,b+1,b+M+2,b+M+1))
    o=mkmesh('CUT | Calculated anatomical tissue (epidermis / cortex / pith)',verts,faces,CAP,uv,False)
    o['tissue_model']='tissue(x,z): core, cortex, epidermis fields; cut plane y=0'
    return o

# ---- Surface seed positions (achene fruits), defined independent of texture ----
# Use area-weighted vertical sampling of the actual surface.
import bisect
cdf=[];samples=[];total=0.
for i in range(1001):
    t=.002+.996*i/1000
    eps=.001
    drdt=(radius(min(.999,t+eps),0)-radius(max(.001,t-eps),0))/(2*eps)
    w=radius(t,0)*sqrt(H*H+drdt*drdt)
    total+=w
    cdf.append(total)
    samples.append(t)

def t_of(s):
    k=bisect.bisect_left(cdf,s*total)
    return samples[min(k,len(samples)-1)]

def seed_data():
    pts=[];rot=[];sz=[];pits=[];pitfaces=[]
    all_n=690
    # Golden-angle stratification; each achene is physically separate.
    for i in range(all_n):
        t=t_of((i+.5)/all_n)
        if t<.095 or t>.91: continue
        th=(i*2*pi*.618033988749895+random.uniform(-.060,.060))%(2*pi)
        if CUT and not (.045<th<pi-.045): continue
        p=V(pt(t,th)); n=normal(t,th)
        tangent=V((-sin(th),cos(th),0)).normalized()
        up=n.cross(tangent).normalized()
        # Orthogonal local seed frame: X runs circumferentially, Y runs lengthwise, Z outwards
        from mathutils import Matrix
        quat=Matrix(((tangent.x,up.x,n.x),(tangent.y,up.y,n.y),(tangent.z,up.z,n.z))).to_quaternion()
        e=quat.to_euler()
        jitter=random.uniform(.82,1.20)
        pts.append(tuple(p+n*.021))
        rot.append(tuple(e))
        sz.append(jitter)
        # A shallow dark red pit under the seed, generated as actual triangles
        i0=len(pits)
        pits.append(tuple(p+n*.008))
        sides=10
        for k in range(sides):
            a=2*pi*k/sides
            pits.append(tuple(p + tangent*(.039*jitter*cos(a)) + up*(.061*jitter*sin(a)) + n*.012))
        for k in range(sides):
            pitfaces.append((i0,i0+1+k,i0+1+(k+1)%sides))
    mkmesh('DETAIL | Individual seed sockets',pits,pitfaces,PIT,smooth=False)
    return pts,rot,sz

# ---- Geometry Nodes: real instancing of a seed primitive on generated 3D points ----
def make_seeds():
    coords,rotation,sizes=seed_data()
    seedproto=bpy.data.meshes.new('Achene prototype mesh')
    # Golden, flattened egg ellipsoid with sharper tip at upper side.
    v=[];f=[];NS=12;NR=9
    for j in range(NR+1):
        a=pi*j/NR
        for k in range(NS):
            b=2*pi*k/NS
            v.append((.032*sin(a)*cos(b), .057*sin(a)*sin(b)*(1+.16*cos(a)), .022*cos(a)+.005))
    for j in range(NR):
        for k in range(NS):
            a=j*NS+k;b=j*NS+(k+1)%NS;c=(j+1)*NS+(k+1)%NS;d=(j+1)*NS+k
            f.append((a,b,c,d))
    seedproto.from_pydata(v,[],f);seedproto.update();seedproto.materials.append(SEED)
    proto=bpy.data.objects.new('GN SOURCE | Achene prototype',seedproto)
    model_col.objects.link(proto)
    proto.hide_render=True
    proto.hide_set(True)
    seedpts=bpy.data.meshes.new('Deterministic golden-angle positions')
    seedpts.from_pydata(coords,[],[]);seedpts.update()
    a=seedpts.attributes.new('seed_euler','FLOAT_VECTOR','POINT')
    b=seedpts.attributes.new('seed_size','FLOAT','POINT')
    for i,r in enumerate(rotation):a.data[i].vector=r
    for i,s in enumerate(sizes):b.data[i].value=s
    o=bpy.data.objects.new('GN | Surface achenes • instanced seeds',seedpts)
    model_col.objects.link(o)
    ng=bpy.data.node_groups.new('Strawberry | Achenes from coordinates','GeometryNodeTree')
    ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    density_socket=ng.interface.new_socket(name='Density',in_out='INPUT',socket_type='NodeSocketFloat')
    density_socket.default_value=1.0
    size_socket=ng.interface.new_socket(name='Size',in_out='INPUT',socket_type='NodeSocketFloat')
    size_socket.default_value=1.0
    ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    N=ng.nodes;L=ng.links
    gi=N.new('NodeGroupInput');gi.location=(-650,230)
    go=N.new('NodeGroupOutput');go.location=(660,210)
    idx=N.new('GeometryNodeInputIndex');idx.location=(-650,-170)
    rv=N.new('FunctionNodeRandomValue');rv.data_type='FLOAT';rv.location=(-450,-170)
    rv.inputs['Min'].default_value=0;rv.inputs['Max'].default_value=1
    L.new(idx.outputs['Index'],rv.inputs['ID'])
    cmp=N.new('FunctionNodeCompare');cmp.data_type='FLOAT';cmp.operation='LESS_THAN';cmp.location=(-220,-150)
    L.new(rv.outputs['Value'],cmp.inputs['A']);L.new(gi.outputs['Density'],cmp.inputs['B'])
    oi=N.new('GeometryNodeObjectInfo');oi.location=(-430,400);oi.inputs['Object'].default_value=proto
    atrot=N.new('GeometryNodeInputNamedAttribute');atrot.data_type='FLOAT_VECTOR';atrot.location=(-430,-390)
    atrot.inputs['Name'].default_value='seed_euler'
    erot=N.new('FunctionNodeEulerToRotation');erot.location=(-200,-350)
    L.new(atrot.outputs['Attribute'],erot.inputs['Euler'])
    ats=N.new('GeometryNodeInputNamedAttribute');ats.data_type='FLOAT';ats.location=(-420,-560)
    ats.inputs['Name'].default_value='seed_size'
    sm=N.new('ShaderNodeMath');sm.operation='MULTIPLY';sm.location=(-180,-550)
    L.new(ats.outputs['Attribute'],sm.inputs[0]);L.new(gi.outputs['Size'],sm.inputs[1])
    ins=N.new('GeometryNodeInstanceOnPoints');ins.location=(100,260)
    L.new(gi.outputs['Geometry'],ins.inputs['Points'])
    L.new(oi.outputs['Geometry'],ins.inputs['Instance'])
    L.new(cmp.outputs['Result'],ins.inputs['Selection'])
    L.new(erot.outputs['Rotation'],ins.inputs['Rotation'])
    L.new(sm.outputs['Value'],ins.inputs['Scale'])
    realize=N.new('GeometryNodeRealizeInstances');realize.location=(380,210)
    L.new(ins.outputs['Instances'],realize.inputs['Geometry'])
    L.new(realize.outputs['Geometry'],go.inputs['Geometry'])
    mod=o.modifiers.new('Geometry Nodes • Live seed density and size','NODES')
    mod.node_group=ng
    # Blender 5.2 geometry-nodes modifier uses interface defaults here;
    # modifier custom ID properties are unavailable in this runtime.
    for it in ng.interface.items_tree:
        if it.item_type=='SOCKET' and it.in_out=='INPUT':
            if it.name=='Density':it.default_value=1.0
            if it.name=='Size':it.default_value=1.0
    o['method']='Golden-angle seed coordinates -> GN instancing with changeable Density and Size'
    return o,proto

# ---- Cut surface structural fibers: as separate small real meshes ----
def make_cap_fibers():
    verts=[];faces=[];count=145
    rng=random.Random(121)
    for i in range(count):
        start_t=.18 + .67*((i+.5)/count)
        direction=1 if i%2==0 else -1
        r=radius(start_t,0 if direction>0 else pi)
        startx=direction*(.08+.10*rng.random())
        endx=direction*r*rng.uniform(.72,.98)
        endt=max(.055,min(.955,start_t+rng.uniform(-.08,.08)))
        ix=len(verts)
        width=rng.uniform(.0016,.0043)
        steps=11
        for j in range(steps):
            s=j/(steps-1)
            x=startx+(endx-startx)*s
            t=start_t+(endt-start_t)*s+.009*sin(s*pi*2+i*.7)*s*(1-s)
            z=(t-.5)*H
            # y just in front of cut face
            yy=-.011
            ww=width*(1-.74*s)
            verts.extend([(x-ww,yy,z),(x+ww,yy,z)])
        for j in range(steps-1):
            q=ix+2*j
            faces.append((q,q+1,q+3,q+2))
    return mkmesh('CUT | Small 3D vascular fibers',verts,faces,VEIN,smooth=False)

# ---- Leafy green calyx; each leaf has curvature and a distinct central ridge ----
def make_calyx():
    leafverts=[];leaffaces=[];veinverts=[];veinfaces=[]
    rng=random.Random(114)
    count=9
    stemtop=H*.5+.13
    for k in range(count):
        th=2*pi*(k+.12*rng.random())/count
        L=rng.uniform(1.05,1.42)
        W=rng.uniform(.24,.36)
        origin=V((0,0,stemtop-.05))
        tip=V((L*cos(th),L*sin(th),stemtop-.26))
        side=V((-sin(th),cos(th),0))
        idx=len(leafverts)
        for j in range(9):
            t=j/8
            center=origin*(1-t)+tip*t
            center.z+=.10*sin(pi*t)
            width=W*pow(max(0,sin(pi*t)),.7) * (1+.10*sin(8*t+k))
            for s in (-1,0,1):
                q=center+side*s*width
                if s==0: q.z+=.042*sin(pi*t)
                leafverts.append(tuple(q))
        for j in range(8):
            base=idx+j*3
            for a in (0,1):
                leaffaces.append((base+a,base+a+3,base+a+4,base+a+1))
        # central midrib mesh
        iv=len(veinverts)
        for j in range(8):
            t=j/7
            mid=origin*(1-t)+tip*t;mid.z+=.10*sin(pi*t)+.047
            d=side*.008
            veinverts.extend([tuple(mid-d),tuple(mid+d)])
        for j in range(7):
            b=iv+2*j;veinfaces.append((b,b+1,b+3,b+2))
    mkmesh('CALYX | Nine curved lobed sepals',leafverts,leaffaces,LEAF)
    mkmesh('CALYX | Individual leaf veins',veinverts,veinfaces,LEAF_L,smooth=False)
    # stalk, physically extruded 3D mesh
    bz=stemtop-.02
    ztop=stemtop+.44
    verts=[];faces=[];N=20
    for j in range(9):
        t=j/8
        z=bz+(ztop-bz)*t
        x=.04*sin(t*pi*.8)
        y=.014*sin(1.6*pi*t)
        r=.10*(1-.4*t)
        for k in range(N):
            a=2*pi*k/N
            verts.append((x+r*cos(a),y+r*sin(a),z))
    for j in range(8):
        for k in range(N):
            b=j*N+k
            faces.append((b,j*N+(k+1)%N,(j+1)*N+(k+1)%N,b+N))
    mkmesh('CALYX | Stem',verts,faces,STEM)

# ---- Assemble ----
skin=make_skin()
if CUT:
    make_cut_flesh()
    make_cap_fibers()
seed_obj,proto=make_seeds()
make_calyx()

# Validate node-instanced seed output to ensure live seed Geometry Nodes is effective.
bpy.context.view_layer.update()
deps=bpy.context.evaluated_depsgraph_get()
me=seed_obj.evaluated_get(deps).to_mesh()
nverts=len(me.vertices) if me else 0
print('CHECK_SEEDS',len(seed_obj.data.vertices),'instance_points',nverts,'evaluated_verts',flush=True)
if nverts<1000: raise RuntimeError('GN seeds failed to evaluate')
seed_obj.evaluated_get(deps).to_mesh_clear()

# ---- Studio for real Cycles render ----
w=bpy.data.worlds.new('Soft indigo studio ambience')
w.use_nodes=True
w.node_tree.nodes.get('Background').inputs['Color'].default_value=(.075,.088,.108,1)
w.node_tree.nodes.get('Background').inputs['Strength'].default_value=.7
sc=bpy.context.scene;sc.world=w
for name,loc,power,size,color in [
    ('Key softbox',(-6,-8,9),1050,7,(1,.94,.89)),
    ('Rim light',(4,6,7),1350,5,(.88,.96,1)),
    ('Front fill',(3,-7,3),620,6,(1,1,1)),
]:
    ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.shape='DISK';ld.size=size;ld.color=color
    ob=bpy.data.objects.new(name,ld);studio_col.objects.link(ob)
    ob.location=loc;ob.rotation_euler=(-ob.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Portrait camera');camera=bpy.data.objects.new('Portrait camera',cd)
studio_col.objects.link(camera)
camera.location=(4.3,-8.0,2.2) if CUT else (5.1,-8.8,3.0)
camera.rotation_euler=(V((0,0,-.06))-camera.location).to_track_quat('-Z','Y').to_euler()
cd.type='ORTHO';cd.ortho_scale=5.7
sc.camera=camera
# Floor plane below fruit
fm=bpy.data.meshes.new('Backdrop plane');fm.from_pydata([(-200,-200,-2.5),(200,-200,-2.5),(200,200,-2.5),(-200,200,-2.5)],[],[(0,1,2,3)]);fm.materials.append(FLOOR)
flo=bpy.data.objects.new('Backdrop plane',fm);studio_col.objects.link(flo)
sc.render.engine='CYCLES';sc.cycles.device='CPU'
sc.cycles.samples=args.samples
sc.cycles.use_denoising=True
sc.cycles.max_bounces=4
sc.render.resolution_x=args.resolution
sc.render.resolution_y=args.resolution
sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'
sc.view_settings.view_transform='AgX'
sc.render.filepath=str(OUT/f'strawberry-{args.mode}.png')

# Save editable live GN scene before baking model for GLB
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'strawberry-{args.mode}.blend'))
print('SCENE_SAVED',flush=True)

# Bake GN seed mesh in export-only duplicate, so GLB contains true mesh triangles
bpy.ops.object.select_all(action='DESELECT')
for o in list(model_col.objects):
    if o==proto: continue
    if o.type=='MESH':
        if o==seed_obj:
            evaluated=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
            baked=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get())
            b=bpy.data.objects.new('SEEDS | Baked real achene geometry',baked)
            model_col.objects.link(b)
            b.select_set(True)
        else:
            o.select_set(True)
# Exclude the procedurally instanced seed object from export, preserve original in .blend
seed_obj.select_set(False)
proto.select_set(False)
bpy.ops.export_scene.gltf(filepath=str(OUT/f'strawberry-{args.mode}.glb'),export_format='GLB',use_selection=True,export_apply=True,export_materials='EXPORT',export_texcoords=True,export_yup=True,export_cameras=False,export_lights=False)
print('GLB_SAVED',os.path.getsize(str(OUT/f'strawberry-{args.mode}.glb')),flush=True)
if args.preview:
    # No two overlapping seed geometries in the render
    seed_obj.hide_render=True
    bpy.ops.render.render(write_still=True)
    print('RENDER_SAVED',sc.render.filepath,os.path.getsize(sc.render.filepath),flush=True)
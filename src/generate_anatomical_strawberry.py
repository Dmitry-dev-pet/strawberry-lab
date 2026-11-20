#!/usr/bin/env python3
"""Strawberry Lab M1a: anatomy-first procedural Strawberry in Blender 5.2+.

Procedural 3D tissues, linked achene vascular routes, true achene depressions,
longitudinal + transverse caps evaluated from the SAME 3D fields. GLB export.

Biology reference: Hurtado & Knoche 2026 10.3389/fhort.2026.1779354;
Darrow, The Strawberry, USDA figs 19-38/19-39.
Numerical parameters are art choices rather than scientifically calibrated.
All source code is independently implemented; not extracted from Frucht.
"""
import argparse
from pathlib import Path
import random, sys, math, json, os, time
from math import sin, cos, pi, sqrt, exp

parser=argparse.ArgumentParser()
parser.add_argument('--mode',choices=['whole','longitudinal','transverse','anatomy'],default='longitudinal')
parser.add_argument('--out',type=Path,default=Path(__file__).resolve().parent.parent/'outputs')
parser.add_argument('--resolution',type=int,default=760)
parser.add_argument('--samples',type=int,default=16)
parser.add_argument('--seed',type=int,default=1729)
parser.add_argument('--no-render',action='store_true')
parser.add_argument('--no-glb',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
args.out.mkdir(parents=True,exist_ok=True)

import bpy
from mathutils import Vector,Matrix,kdtree
sys.path.insert(0, str(Path(__file__).resolve().parent))
from strawberry_biology import (FruitParams,point,normal,radius,pith_radius,fields,tissue_color,
    sample_achenes,vascular_graph,validate_graph,clamp)


start=time.monotonic()
P=FruitParams(seed=args.seed)
H=2*P.half_height
bpy.ops.wm.read_factory_settings(use_empty=True)

model=bpy.data.collections.new('Strawberry | M1a geometry')
bpy.context.scene.collection.children.link(model)
studio=bpy.data.collections.new('Studio (render only)')
bpy.context.scene.collection.children.link(studio)
diagnostic=bpy.data.collections.new('Biology | root-connected vascular graph (toggle)')
bpy.context.scene.collection.children.link(diagnostic)


def material(name,col,rough=.6,coat=0,metal=0,sss=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*col,1)
    bs.inputs['Roughness'].default_value=rough
    bs.inputs['Coat Weight'].default_value=coat
    bs.inputs['Metallic'].default_value=metal
    bs.inputs['Subsurface Weight'].default_value=sss
    return m

skinmat=material('Strawberry M1a • red epidermis, physically notated',(.57,.018,.035),.39,coat=.14,sss=.08)
bs=skinmat.node_tree.nodes.get('Principled BSDF');N=skinmat.node_tree.nodes;L=skinmat.node_tree.links
coord=N.new('ShaderNodeTexCoord');coord.location=(-950,280)
noise=N.new('ShaderNodeTexNoise');noise.noise_dimensions='3D';noise.inputs['Scale'].default_value=17;noise.inputs['Detail'].default_value=3;noise.inputs['Roughness'].default_value=.7;noise.location=(-730,330);L.new(coord.outputs['Generated'],noise.inputs['Vector'])
cr=N.new('ShaderNodeValToRGB');cr.location=(-450,360)
cr.color_ramp.elements[0].position=.24;cr.color_ramp.elements[0].color=(.30,.012,.025,1)
cr.color_ramp.elements[1].position=.74;cr.color_ramp.elements[1].color=(.79,.054,.071,1)
cr.color_ramp.elements.new(.47).color=(.63,.025,.039,1)
L.new(noise.outputs['Fac'],cr.inputs['Fac'])
sub=N.new('ShaderNodeTexNoise');sub.noise_dimensions='3D';sub.inputs['Scale'].default_value=180;sub.inputs['Detail'].default_value=2;sub.location=(-715,-60);L.new(coord.outputs['Generated'],sub.inputs['Vector'])
bump=N.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.23;bump.inputs['Distance'].default_value=.012;bump.location=(-190,-80)
L.new(sub.outputs['Fac'],bump.inputs['Height']);L.new(bump.outputs['Normal'],bs.inputs['Normal'])
# Green shoulder is a maturity gradient, not fixed biological coloring.
geom=N.new('ShaderNodeNewGeometry');geom.location=(-940,-360)
sep=N.new('ShaderNodeSeparateXYZ');sep.location=(-730,-350);L.new(geom.outputs['Position'],sep.inputs['Vector'])
mr=N.new('ShaderNodeMapRange');mr.clamp=True;mr.interpolation_type='SMOOTHSTEP';mr.inputs['From Min'].default_value=1.12;mr.inputs['From Max'].default_value=1.79;mr.location=(-480,-305)
L.new(sep.outputs['Z'],mr.inputs['Value'])
merge=N.new('ShaderNodeMixRGB');merge.blend_type='MIX';merge.location=(-185,280);merge.inputs[2].default_value=(.14,.27,.044,1)
L.new(cr.outputs['Color'],merge.inputs[1]);L.new(mr.outputs['Result'],merge.inputs[0]);L.new(merge.outputs['Color'],bs.inputs['Base Color'])

achene_mat=material('Achenes | individual gold-brown dry fruits',(.70,.38,.13),.43,coat=.05,sss=.02)
calyxmat=material('Calyx | curved living sepals',(.105,.285,.05),.53,sss=.05)
midribmat=material('Calyx | central leaf ribs',(.23,.43,.095),.73)
stemmat=material('Stem | brown-green',(.26,.28,.066),.79)
capmat=material('Exposed receptacle | 3D color field of pith/cortex/bundle zone',(.8,.23,.25),.67,sss=.055)
bs=capmat.node_tree.nodes.get('Principled BSDF');A=capmat.node_tree.nodes.new('ShaderNodeAttribute');A.attribute_name='tissue_color';A.location=(-350,130)
capmat.node_tree.links.new(A.outputs['Color'],bs.inputs['Base Color'])
texture=capmat.node_tree.nodes.new('ShaderNodeTexNoise');texture.inputs['Scale'].default_value=170;texture.inputs['Detail'].default_value=3;texture.location=(-450,-160)
bump=capmat.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.11;bump.inputs['Distance'].default_value=.004;bump.location=(-180,-80)
capmat.node_tree.links.new(texture.outputs['Fac'],bump.inputs['Height']);capmat.node_tree.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
networkmat=material('Anatomy | radial fibrovascular bundles (not literal white noodles)',(.91,.70,.42),.64)
ringmat=material('Anatomy | continuous vascular cylinder',(.95,.78,.57),.57)
floormat=material('Studio | deep slate',(.038,.051,.067),.8)


def meshobj(name,vertices,faces,mat,collection=model,uv=None,coldata=None,smooth=True):
    me=bpy.data.meshes.new(name+' mesh');me.from_pydata(vertices,[],faces);me.update()
    ob=bpy.data.objects.new(name,me);collection.objects.link(ob)
    if mat is not None: me.materials.append(mat)
    if uv is not None:
        uvmap=me.uv_layers.new(name='UVMap')
        for poly in me.polygons:
            for li in poly.loop_indices:
                uvmap.data[li].uv=uv[me.loops[li].vertex_index]
    if coldata is not None:
        attr=me.color_attributes.new(name='tissue_color',type='FLOAT_COLOR',domain='CORNER')
        for poly in me.polygons:
            for li in poly.loop_indices:
                attr.data[li].color=coldata[me.loops[li].vertex_index]
    for poly in me.polygons:poly.use_smooth=smooth
    return ob


def curveobj(name,tracks,material_,width,collection=diagnostic):
    cv=bpy.data.curves.new(name,'CURVE');cv.dimensions='3D';cv.resolution_u=2
    cv.bevel_depth=width;cv.resolution_u=2;cv.bevel_resolution=2
    for pts in tracks:
        sp=cv.splines.new('POLY');sp.points.add(len(pts)-1)
        for i,p in enumerate(pts):sp.points[i].co=(*p,1)
    ob=bpy.data.objects.new(name,cv);collection.objects.link(ob)
    cv.materials.append(material_)
    return ob

anchors=sample_achenes(P)
branches=vascular_graph(anchors,P)
ok,msg=validate_graph(anchors,branches)
if not ok: raise RuntimeError(msg)
print('CONNECTED_GRAPH',msg,flush=True)
# Spatial index is used to deform actual receptacle mesh around each achene.
kd=kdtree.KDTree(len(anchors))
for i,a in enumerate(anchors):kd.insert(Vector(a['point']),i)
kd.balance()


def deformed_pt(t,theta):
    raw=Vector(point(t,theta,P));n=Vector(normal(t,theta,P))
    near,ix,dist=kd.find(raw)
    a=anchors[ix]
    depth=P.pit_depth*math.exp(-1.1*(dist/(P.pit_width*a['size']))**2)
    return raw-n*depth


def keep(a):
    if args.mode in ('whole','anatomy'):return True
    if args.mode=='longitudinal':return sin(a['theta'])>=.003
    if args.mode=='transverse':return a['t']<=.5
    return True

active=[a for a in anchors if keep(a)]
active_by_id={a['id'] for a in active}
active_branches=[b for b in branches if b['achene_id'] in active_by_id]

# Skin surface, now with real achene-induced pits. For cut models, only
# the physically retained half of the shell is built.
def create_skin():
    if args.mode=='anatomy':return None
    n_z=146 if args.mode!='transverse' else 83
    n_th=160 if args.mode=='longitudinal' else 256
    tmax=.5 if args.mode=='transverse' else .999
    verts=[];faces=[];uv=[]
    for j in range(n_z+1):
        t=.001+(tmax-.001)*j/n_z
        for i in range(n_th+1):
            th=(pi if args.mode=='longitudinal' else 2*pi)*i/n_th
            verts.append(tuple(deformed_pt(t,th)))
            uv.append((th/(2*pi),t))
    for j in range(n_z):
        for i in range(n_th):
            b=j*(n_th+1)+i
            faces.append((b,b+1,b+n_th+2,b+n_th+1))
    o=meshobj('Receptacle | actual pit-deformed epidermis',verts,faces,skinmat,uv=uv)
    o['pit_depth']=P.pit_depth;o['achene_anchor_count']=len(anchors)
    return o


def cap_longitudinal():
    nz=155; nx=140
    verts=[];faces=[];uv=[];cols=[]
    for j in range(nz+1):
        t=.001+.998*j/nz
        left=deformed_pt(t,pi);right=deformed_pt(t,0)
        for i in range(nx+1):
            u=i/nx
            x=left.x*(1-u)+right.x*u
            y=left.y*(1-u)+right.y*u
            # Nonzero 3D micro-topography in tissue, zero on the outer seam.
            relief=.0055*sin(24*x+13*t)*sin(68*t+7*x)*((1-(2*u-1)**2)**2)
            y-=relief
            z=(t-.5)*H
            verts.append((x,y,z))
            uv.append((u,t))
            cols.append(tissue_color(x,0,z,P))
    for j in range(nz):
        for i in range(nx):
            b=j*(nx+1)+i;faces.append((b,b+1,b+nx+2,b+nx+1))
    ob=meshobj('Exposed tissue | longitudinal 3D field',verts,faces,capmat,uv=uv,coldata=cols,smooth=False)
    ob['cut']='y = 0 (keeps y > 0)';ob['tissue']='source strawberry_biology.fields(x,y,z)'
    return ob


def cap_transverse():
    nr=95; ns=256
    verts=[(0,0,0)];faces=[];uv=[(.5,.5)];cols=[tissue_color(0,0,0,P)]
    for j in range(1,nr+1):
        s=j/nr
        for i in range(ns):
            th=2*pi*i/ns
            end=deformed_pt(.5,th)
            x=end.x*s;y=end.y*s
            z=(1-s)*.0045*sin(x*44+8*y)*sin(y*53-7*x)
            verts.append((x,y,z))
            uv.append(((x/P.radius+1)/2,(y/P.radius+1)/2))
            cols.append(tissue_color(x,y,0,P))
    for i in range(ns):faces.append((0,1+i,1+(i+1)%ns))
    for j in range(1,nr):
        for i in range(ns):
            a=1+(j-1)*ns+i;b=1+(j-1)*ns+(i+1)%ns
            c=1+j*ns+(i+1)%ns;d=1+j*ns+i
            faces.append((a,d,c,b))
    ob=meshobj('Exposed tissue | transverse 3D field',verts,faces,capmat,uv=uv,coldata=cols,smooth=False)
    ob['cut']='z = 0 (keeps z < 0)';ob['tissue']='source strawberry_biology.fields(x,y,z)'
    return ob

skin=create_skin()
if args.mode=='longitudinal':cap_longitudinal()
if args.mode=='transverse':cap_transverse()

# Achenes: real dry fruits instanced through live Blender Geometry Nodes.
def make_achene_instances():
    proto_verts=[];proto_faces=[];circle=14;rows=11
    for j in range(rows+1):
        aa=pi*j/rows
        for i in range(circle):
            th=2*pi*i/circle
            radius_a=sin(aa)*(1+.14*cos(aa))
            proto_verts.append((.034*radius_a*cos(th),.052*radius_a*sin(th),.024*cos(aa)+.005))
    for j in range(rows):
        for i in range(circle):
            a=j*circle+i;b=j*circle+(i+1)%circle;c=(j+1)*circle+(i+1)%circle;d=(j+1)*circle+i
            proto_faces.append((a,b,c,d))
    me=bpy.data.meshes.new('Anatomical achene primitive')
    me.from_pydata(proto_verts,[],proto_faces);me.update();me.materials.append(achene_mat)
    proto=bpy.data.objects.new('GN prototype | dry fruit / achene',me);model.objects.link(proto)
    proto.hide_render=True
    proto.hide_set(True)
    verts=[];rot=[];sizes=[]
    for a in active:
        pt=deformed_pt(a['t'],a['theta']);n=Vector(a['normal'])
        # The ellipsoid root sits within the depression, not on untouched skin.
        center=pt+n*.013
        tangent=Vector((-sin(a['theta']),cos(a['theta']),0)).normalized()
        up=n.cross(tangent).normalized()
        quat=Matrix(((tangent.x,up.x,n.x),(tangent.y,up.y,n.y),(tangent.z,up.z,n.z))).to_quaternion()
        verts.append(tuple(center));rot.append(tuple(quat.to_euler()));sizes.append(a['size'])
    points=bpy.data.meshes.new('Anchored seeds: independent from cap texture')
    points.from_pydata(verts,[],[]);points.update()
    attr=points.attributes.new('seed_euler','FLOAT_VECTOR','POINT')
    scal=points.attributes.new('seed_size','FLOAT','POINT')
    for i,(r,s) in enumerate(zip(rot,sizes)):
        attr.data[i].vector=r;scal.data[i].value=s
    obj=bpy.data.objects.new('GN live achenes (with actual surface pits)',points);model.objects.link(obj)
    ng=bpy.data.node_groups.new('M1a | Live achene instancing','GeometryNodeTree')
    ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    nd=ng.nodes;li=ng.links
    inp=nd.new('NodeGroupInput');inp.location=(-650,160)
    out=nd.new('NodeGroupOutput');out.location=(500,160)
    oi=nd.new('GeometryNodeObjectInfo');oi.inputs['Object'].default_value=proto;oi.location=(-620,350)
    atr=nd.new('GeometryNodeInputNamedAttribute');atr.data_type='FLOAT_VECTOR';atr.inputs['Name'].default_value='seed_euler';atr.location=(-600,-150)
    ats=nd.new('GeometryNodeInputNamedAttribute');ats.data_type='FLOAT';ats.inputs['Name'].default_value='seed_size';ats.location=(-610,-350)
    erot=nd.new('FunctionNodeEulerToRotation');erot.location=(-340,-140);li.new(atr.outputs['Attribute'],erot.inputs['Euler'])
    inst=nd.new('GeometryNodeInstanceOnPoints');inst.location=(-80,180)
    li.new(inp.outputs['Geometry'],inst.inputs['Points']);li.new(oi.outputs['Geometry'],inst.inputs['Instance'])
    li.new(erot.outputs['Rotation'],inst.inputs['Rotation']);li.new(ats.outputs['Attribute'],inst.inputs['Scale'])
    real=nd.new('GeometryNodeRealizeInstances');real.location=(220,160)
    li.new(inst.outputs['Instances'],real.inputs['Geometry']);li.new(real.outputs['Geometry'],out.inputs['Geometry'])
    mod=obj.modifiers.new('Geometry Nodes — anchored achene instances','NODES');mod.node_group=ng
    return obj,proto

seed_obj,seed_proto=make_achene_instances()

# Independent uneven calyx with real folded lobes and stem; not displayed on
# the lower transverse half because the stem is physically cut off.
def create_calyx():
    if args.mode=='transverse':return
    rng=random.Random(P.seed+198)
    verts=[];faces=[];ribv=[];ribf=[]
    count=10; top=P.half_height+.12
    for k in range(count):
        ang=2*pi*(k+.20*rng.random())/count
        size=rng.uniform(.92,1.53);width=rng.uniform(.18,.36)
        rv=Vector((0,0,top-.06));tip=Vector((size*cos(ang),size*sin(ang),top-.18-rng.uniform(0,.16)))
        tangent=Vector((-sin(ang),cos(ang),0));begin=len(verts)
        for j in range(13):
            u=j/12;c=rv*(1-u)+tip*u
            c.z+=.16*sin(pi*u)+.06*u*sin(2*pi*u+k*.6)
            w=width*sin(pi*u)**.75*(1+.06*sin(11*u+k))
            for ss in (-1,0,1):
                q=c+tangent*w*ss
                if ss==0:q.z+=.07*sin(pi*u)
                verts.append(tuple(q))
        for j in range(12):
            for ii in (0,1):
                b=begin+j*3+ii;faces.append((b,b+3,b+4,b+1))
        st=len(ribv)
        for j in range(12):
            u=j/11;c=rv*(1-u)+tip*u
            c.z+=.16*sin(pi*u)+.07*sin(pi*u)+.06*u*sin(2*pi*u+k*.6)
            ribv.extend([tuple(c+tangent*.006),tuple(c-tangent*.006)])
        for j in range(11):
            b=st+j*2;ribf.append((b,b+1,b+3,b+2))
    meshobj('Calyx | ten asymmetrical curled sepals',verts,faces,calyxmat)
    meshobj('Calyx | folded veins on each sepal',ribv,ribf,midribmat)
    v=[];f=[];steps=9;seg=24
    for j in range(steps+1):
        u=j/steps
        z=top-.06+.55*u
        center=Vector((.025*sin(pi*u),.015*sin(2*pi*u),z))
        r=.105*(1-.40*u)
        for i in range(seg):
            a=2*pi*i/seg
            v.append(tuple(center+Vector((r*cos(a),r*sin(a),0))))
    for j in range(steps):
        for i in range(seg):
            a=j*seg+i;b=j*seg+(i+1)%seg;c=(j+1)*seg+(i+1)%seg;d=(j+1)*seg+i
            f.append((a,b,c,d))
    meshobj('Peduncle | tapered green stem',v,f,stemmat)

create_calyx()

# Real branching graph from individual achenes to continuous vascular zone.
# The network remains editable in .blend, but only becomes visible in the
# transparent/anatomy schematic mode; the photorealistic cap colors are driven
# independently by 3D tissue fields, not by arbitrary 2D lines.
tracks=[b['points'] for b in branches]  # all, including branches hidden within tissue
network=curveobj('Vascular network | branches to every achene',tracks,networkmat,.007)
# The vascular cylinder is a tessellated full cylinder (anatomical visualization).
verts=[];faces=[];nz=91;na=40
for j in range(nz):
    t=.008+.984*j/(nz-1);rr=pith_radius(t,P)+.075;z=(t-.5)*H
    for i in range(na):
        th=2*pi*i/na
        verts.append((rr*cos(th),rr*sin(th),z))
for j in range(nz-1):
    for i in range(na):
        a=j*na+i;b=j*na+(i+1)%na;c=(j+1)*na+(i+1)%na;d=(j+1)*na+i
        faces.append((a,b,c,d))
cylinder=meshobj('Vascular core | central continuous bundle cylinder',verts,faces,ringmat,collection=diagnostic)
if args.mode!='anatomy':
    network.hide_render=True;cylinder.hide_render=True
else:
    # Viewer can toggle these components and inspect 3D connectivity.
    seed_proto.hide_render=True

bpy.context.view_layer.update()
deps=bpy.context.evaluated_depsgraph_get()
evalobj=seed_obj.evaluated_get(deps)
evalmesh=evalobj.to_mesh()
vertex_count=len(evalmesh.vertices)
evalobj.to_mesh_clear()
if vertex_count<1000:raise RuntimeError('Live Geometry Nodes achene instancing failed')
print('CHECK_GN',json.dumps({'achene_count_full':len(anchors),'achene_count_visible':len(active),'evaluated_vertices':vertex_count}),flush=True)

# Actual studio (Cycles, not AI-generated image).
w=bpy.data.worlds.new('Blue-black ambient fill');w.use_nodes=True
w.node_tree.nodes['Background'].inputs['Color'].default_value=(.062,.073,.095,1)
w.node_tree.nodes['Background'].inputs['Strength'].default_value=.72
sc=bpy.context.scene;sc.world=w
for name,loc,power,size,color in [
    ('Key softbox',(-4.2,-6.5,8.1),1050,6,(1,.93,.88)),
    ('Rim softbox',(3.8,5.0,7.0),1360,5,(.84,.93,1.)),
    ('Front fill',(1.7,-7.1,2.9),540,5,(1,1,1))]:
    ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.shape='DISK';ld.size=size;ld.color=color
    ob=bpy.data.objects.new(name,ld);studio.objects.link(ob);ob.location=loc
    ob.rotation_euler=(-ob.location).to_track_quat('-Z','Y').to_euler()

camera_data=bpy.data.cameras.new('Orthographic reference camera');camera=bpy.data.objects.new('Orthographic reference camera',camera_data)
studio.objects.link(camera)
if args.mode=='transverse':
    camera.location=(4.1,-7.2,6.7);target=Vector((0,0,-.65))
elif args.mode=='anatomy':
    camera.location=(5,-8,3);target=Vector((0,0,-.05))
elif args.mode=='longitudinal':
    camera.location=(3.55,-8.5,2.3);target=Vector((0,0,-.06))
else:
    camera.location=(4.8,-8.6,2.8);target=Vector((0,0,0))
camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
camera_data.type='ORTHO';camera_data.ortho_scale=5.9
sc.camera=camera
floor=meshobj('Studio | non-exportable floor',[(-100,-100,-2.25),(100,-100,-2.25),(100,100,-2.25),(-100,100,-2.25)],[(0,1,2,3)],floormat,collection=studio)

sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=args.samples
sc.cycles.use_denoising=True;sc.cycles.max_bounces=4
sc.render.resolution_x=args.resolution;sc.render.resolution_y=args.resolution;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.view_settings.view_transform='AgX'
basename='strawberry-m1a-'+args.mode
sc.render.filepath=str(args.out/(basename+'.png'))

scene_path=args.out/(basename+'.blend')
# Real Blender scene retains live GN instancing, cap fields, mesh + full vascular graph.
sc['source']='https://github.com/Dmitry-dev-pet/strawberry-lab'
sc['scientific_references']='Darrow 1966 Fig 19-38, 19-39; Hurtado & Knoche 2026 Fig 1'
sc['not_scientifically_calibrated']='Parametric prototype. Vessel thickness, routes and colors are artistic.'
sc['visible_mode']=args.mode
sc['biological_generator']='strawberry_biology.py'
bpy.ops.wm.save_as_mainfile(filepath=str(scene_path))
print('SCENE_SAVED',str(scene_path),flush=True)

if not args.no_render:
    bpy.ops.render.render(write_still=True)
    print('RENDER_SAVED',str(args.out/(basename+'.png')),flush=True)

# Bake a temporary copy of GN seeds only for glTF export. The saved .blend
# remains fully procedural; no duplicate achenes appear in the render.
if not args.no_glb:
    bpy.ops.object.select_all(action='DESELECT')
    for ob in model.objects:
        if ob.type=='MESH' and ob!=seed_proto and ob!=seed_obj:
            ob.select_set(True)
    evaluated=seed_obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    baked=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get())
    baked_ob=bpy.data.objects.new('EXPORT | baked achene triangles',baked);model.objects.link(baked_ob)
    baked_ob.select_set(True)
    export_path=args.out/(basename+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(export_path),export_format='GLB',use_selection=True,export_apply=True,export_materials='EXPORT',export_texcoords=True,export_yup=True,export_cameras=False,export_lights=False)
    print('GLB_SAVED',str(export_path),export_path.stat().st_size,flush=True)

stats={'mode':args.mode,'seed':args.seed,'achene_count_total':len(anchors),'achene_count_visible':len(active),'connected_vascular_routes':len(branches),'gn_evaluated_vertices':vertex_count,'mesh_objects':len([o for o in model.objects if o.type=='MESH']),'run_seconds':round(time.monotonic()-start,2),'blender_version':bpy.app.version_string,'resolution':args.resolution,'samples':args.samples,'rendered':not args.no_render,'glb_exported':not args.no_glb,'biological_claim':'Inspired by botany, NOT quantitatively validated.'}
(args.out/(basename+'-stats.json')).write_text(json.dumps(stats,indent=2)+'\n',encoding='utf-8')
print('SCENE_STATS',json.dumps(stats),flush=True)
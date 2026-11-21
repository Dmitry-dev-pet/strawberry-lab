#!/usr/bin/env python3
"""Independent Strawberry Lab M1e experiment: persistent 3D cavity + moving SDF knife.

Run in Blender >=5.2 (bpy). This is a small standalone technical fixture,
NOT the author's Frucht strawberry or a validated photoreal production fruit.
M1c/M1d-style SDF/GN; cavity and cutter are separate editable mesh objects.
All dimensions are in metres. Frame 1: closed cavity; 15/30: opened cavity.
"""
import bpy
import math
from mathutils import Vector

# Standalone diagnostic: do not load M1d, modify existing milestones or source assets.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'
sc.unit_settings.scale_length = 1.0
sc.frame_start, sc.frame_end = 1, 30
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 640
sc.render.resolution_y = 640
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'
sc.render.film_transparent = False
sc.world.color = (.13, .13, .13)
sc.view_settings.view_transform = 'AgX'
sc['origin'] = 'INDEPENDENT_STRAWBERRY_LAB_M1E_DIAGNOSTIC'
sc['evidence'] = 'artist geometry; not measured tissue or copied Frucht mesh'
sc['blender_units'] = 'metres'

# A watertight, asymmetric artist-profile receptacle.
n_ring, n_seg = 100, 120
H, R = .035, .034
verts, faces = [], []
for j in range(n_ring + 1):
    t = .002 + .996 * j / n_ring
    z = (2*t-1)*H
    for k in range(n_seg):
        theta = 2*math.pi*k/n_seg
        rr = R * math.sin(math.pi*t)**.61 * (.46+.73*t)
        rr *= 1+.025*math.sin(7*theta+2*t)+.015*math.sin(13*theta-4*t)
        verts.append((rr*math.cos(theta),rr*math.sin(theta),z))
for j in range(n_ring):
    for k in range(n_seg):
        a=j*n_seg+k
        b=j*n_seg+(k+1)%n_seg
        faces.append((a,b,b+n_seg,a+n_seg))
low=len(verts)
verts.append((0,0,-H))
high=len(verts)
verts.append((0,0,H))
for k in range(n_seg):
    faces.append((low,(k+1)%n_seg,k))
    a=n_ring*n_seg+k
    b=n_ring*n_seg+(k+1)%n_seg
    faces.append((high,a,b))
me=bpy.data.meshes.new('M1e | sealed fruit seed geometry')
me.from_pydata(verts,[],faces)
me.update()
src=bpy.data.objects.new('SRC_outer_fruit_shape',me)
sc.collection.objects.link(src)
src.hide_render=True
src.hide_set(True)

# One continuous, closed internal void: a deformed ellipsoid.
bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32)
void=bpy.context.object
void.name='SRC_internal_cavity_editable'
void.scale=(.0115,.010,.017)
void.location=(0,.002,.0015)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
for v in void.data.vertices:
    q=v.co.copy()
    v.co.x *= (1+.06*math.sin(185*q.z+7*q.y))
    v.co.y *= (1+.07*math.cos(163*q.x+4*q.z))
void.hide_render=True
void.hide_set(True)

# Large closed cube behaves as an arbitrary half-space knife; its top Y face is the cut.
bpy.ops.mesh.primitive_cube_add(size=2.0)
knife=bpy.context.object
knife.name='CTRL_movable_cut_plane'
knife.scale=(.06,.055,.065)
for frame,plane_y in [(1,-.048),(15,0.0),(30,.008)]:
    knife.location=(0,plane_y-.055,0)
    knife.keyframe_insert(data_path='location',frame=frame)
knife.hide_render=True
knife.display_type='WIRE'
knife.hide_set(True)

# Look-dev only; no assertions of scientific tissue accuracy.
def mat(name,rgba,rough=.38,coat=.0):
    m=bpy.data.materials.new(name)
    m.diffuse_color=rgba
    m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=rgba
    bs.inputs['Roughness'].default_value=rough
    bs.inputs['Coat Weight'].default_value=coat
    return m
skin=mat('MAT_satin_epidermis',(.47,.035,.055,1),.36,.26)
cut=mat('MAT_local_cut_pulp',(.82,.28,.34,1),.44,.19)
inner=mat('MAT_wet_void_walls',(.31,.035,.09,1),.18,.48)
# A micro-normal shader is distinct from 3D cavity topology.
tex=cut.node_tree.nodes.new('ShaderNodeTexVoronoi')
tex.feature='DISTANCE_TO_EDGE'
tex.inputs['Scale'].default_value=150.0
bump=cut.node_tree.nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value=.16
bump.inputs['Distance'].default_value=.00035
cut.node_tree.links.new(tex.outputs['Distance'],bump.inputs['Height'])
cut.node_tree.links.new(bump.outputs['Normal'],cut.node_tree.nodes['Principled BSDF'].inputs['Normal'])

obj=bpy.data.objects.new('HERO_strawberry_cavity_cut_evaluated',me.copy())
sc.collection.objects.link(obj)
g=bpy.data.node_groups.new('M1e | BODY minus CAVITY minus KNIFE | SDF','GeometryNodeTree')
g.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
N,L=g.nodes,g.links
inp=N.new('NodeGroupInput')
out=N.new('NodeGroupOutput')
def object_sdf(target):
    info=N.new('GeometryNodeObjectInfo')
    info.inputs['Object'].default_value=target
    info.transform_space='RELATIVE'
    sdf=N.new('GeometryNodeMeshToSDFGrid')
    sdf.inputs['Voxel Size'].default_value=.0016
    sdf.inputs['Band Width'].default_value=5
    L.new(info.outputs['Geometry'],sdf.inputs['Mesh'])
    return info,sdf
body=N.new('GeometryNodeMeshToSDFGrid')
body.inputs['Voxel Size'].default_value=.0016
body.inputs['Band Width'].default_value=5
L.new(inp.outputs['Geometry'],body.inputs['Mesh'])
void_info,void_sdf=object_sdf(void)
knife_info,knife_sdf=object_sdf(knife)
subtract_void=N.new('GeometryNodeSDFGridBoolean')
subtract_void.operation='DIFFERENCE'
L.new(body.outputs['SDF Grid'],subtract_void.inputs['Grid 1'])
L.new(void_sdf.outputs['SDF Grid'],subtract_void.inputs['Grid 2'])
subtract_knife=N.new('GeometryNodeSDFGridBoolean')
subtract_knife.operation='DIFFERENCE'
L.new(subtract_void.outputs['Grid'],subtract_knife.inputs['Grid 1'])
L.new(knife_sdf.outputs['SDF Grid'],subtract_knife.inputs['Grid 2'])
surf=N.new('GeometryNodeGridToMesh')
surf.inputs['Threshold'].default_value=0.0
surf.inputs['Adaptivity'].default_value=0.0
L.new(subtract_knife.outputs['Grid'],surf.inputs['Grid'])
rest=N.new('GeometryNodeStoreNamedAttribute')
rest.domain='POINT'
rest.data_type='FLOAT_VECTOR'
rest.inputs['Name'].default_value='fruit_rest'
pos=N.new('GeometryNodeInputPosition')
L.new(surf.outputs['Mesh'],rest.inputs['Geometry'])
L.new(pos.outputs['Position'],rest.inputs['Value'])
s0=N.new('GeometryNodeSetMaterial')
s0.inputs['Material'].default_value=skin
L.new(rest.outputs['Geometry'],s0.inputs['Geometry'])

def near_surface(info,threshold):
    prox=N.new('GeometryNodeProximity')
    prox.target_element='FACES'
    L.new(info.outputs['Geometry'],prox.inputs['Target'])
    comp=N.new('FunctionNodeCompare')
    comp.data_type='FLOAT'
    comp.operation='LESS_THAN'
    comp.inputs['B'].default_value=threshold
    L.new(prox.outputs['Distance'],comp.inputs['A'])
    return comp.outputs['Result']
cavity_sel=near_surface(void_info,.003)
knife_sel=near_surface(knife_info,.003)
s1=N.new('GeometryNodeSetMaterial')
s1.inputs['Material'].default_value=inner
L.new(s0.outputs['Geometry'],s1.inputs['Geometry'])
L.new(cavity_sel,s1.inputs['Selection'])
s2=N.new('GeometryNodeSetMaterial')
s2.inputs['Material'].default_value=cut
L.new(s1.outputs['Geometry'],s2.inputs['Geometry'])
L.new(knife_sel,s2.inputs['Selection'])

# Low-amplitude 3D cell pattern only on exposed material interfaces.
either=N.new('FunctionNodeBooleanMath')
either.operation='OR'
L.new(cavity_sel,either.inputs[0])
L.new(knife_sel,either.inputs[1])
vor=N.new('ShaderNodeTexVoronoi')
vor.voronoi_dimensions='3D'
vor.feature='DISTANCE_TO_EDGE'
vor.inputs['Scale'].default_value=270.0
L.new(pos.outputs['Position'],vor.inputs['Vector'])
mul=N.new('ShaderNodeMath')
mul.operation='MULTIPLY'
mul.inputs[1].default_value=.00032
L.new(vor.outputs['Distance'],mul.inputs[0])
normal=N.new('GeometryNodeInputNormal')
scale=N.new('ShaderNodeVectorMath')
scale.operation='SCALE'
L.new(normal.outputs['Normal'],scale.inputs[0])
L.new(mul.outputs['Value'],scale.inputs['Scale'])
displace=N.new('GeometryNodeSetPosition')
L.new(s2.outputs['Geometry'],displace.inputs['Geometry'])
L.new(either.outputs[0],displace.inputs['Selection'])
L.new(scale.outputs['Vector'],displace.inputs['Offset'])
L.new(displace.outputs['Geometry'],out.inputs['Geometry'])
modifier=obj.modifiers.new('M1e | LIVE cavity + arbitrary knife','NODES')
modifier.node_group=g
obj['cut_contract']='body minus persistent cavity minus independent moving cutter'
obj['voxel_m']=.0016
obj['not_histology']='Procedural visual approximation'

# Delivery camera, working sun + point fill (not Area lights).
def aim(o,p=(0,0,0)):
    o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
camdata=bpy.data.cameras.new('CAM_main_data')
cam=bpy.data.objects.new('CAM_main',camdata)
sc.collection.objects.link(cam)
cam.location=(.025,-.23,.075)
aim(cam,(0,0,0))
camdata.type='ORTHO'
camdata.ortho_scale=.115
sc.camera=cam
def light(name,typ,loc,energy):
    ld=bpy.data.lights.new(name,typ)
    lo=bpy.data.objects.new(name,ld)
    sc.collection.objects.link(lo)
    lo.location=loc
    ld.energy=energy
    if typ=='SUN':aim(lo)
    return lo
light('LGT_key','SUN',(-.12,-.08,.25),2.4)
f=light('LGT_fill','POINT',(.15,-.13,.04),20)
f.data.shadow_soft_size=.11
sc.world.use_nodes=True
sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.075,.07,.09,1)
sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
sc.frame_set(15)
bpy.context.view_layer.update()
result={'scene':'independent M1e cavity SDF proof','body':obj.name,
        'cavity':void.name,'cutter':knife.name,'frames':[1,15,30],
        'blender':bpy.app.version_string,'source':'Strawberry Lab original procedural diagnostic'}
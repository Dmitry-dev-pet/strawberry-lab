#!/usr/bin/env python3
"""Independent Strawberry Lab M1e6 proof of GN-only local edge refinement.

Starting point: owned verified M1e5 .blend; no Frucht assets/nodes or Python
handlers are needed for the resulting live GN surface. This is not a magical
selected Subdivide Mesh node; Blender 5.2 Mesh Bevel has an edge selection,
which we exploit only away from the outer-skin and void seams.
"""
import bpy, sys, argparse
from pathlib import Path
ap=argparse.ArgumentParser()
ap.add_argument('--out',required=True,type=Path)
ap.add_argument('--segments',default=2,type=int)
ap.add_argument('--width',default=0.006,type=float)
ap.add_argument('--skin-clear',default=0.075,type=float)
ap.add_argument('--cavity-clear',default=0.060,type=float)
ap.add_argument('--mode',choices=['bevel','control'],default='bevel')
ap.add_argument('--material',choices=['original','fiber'],default='original')
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
scene=bpy.context.scene
body=bpy.data.objects['M1c | SDF cutter + rest-space tissue']
old=body.modifiers[0].node_group
assert 'M1e3' in old.name
skin=bpy.data.objects['M1c | watertight base (hidden)']
cavity=bpy.data.objects['M1e | persistent internal cavity (separate 3D mesh)']
knife=bpy.data.objects['M1e | independently moving knife (cube half space)']
network=bpy.data.objects['M1e4 | persistent 3D curved fibers (source)']
base_flesh=bpy.data.materials['M1c | rest-space pith/cortex + wet Voronoi surface']
strand_material=bpy.data.materials.get('M1e4 | strawberry cut flesh with 3D strands')
assert strand_material is not None

g=old.copy();g.name='M1e6 | pure GN localized selected bevel + 3D strand field | '+a.mode
body.modifiers[0].node_group=g
N,L=g.nodes,g.links
sub=N['M1e3 | true cut-surface mesh refinement']
cutpos=N['M1e3 | CutSurface true geometry']
in_socket=sub.inputs['Mesh'].links[0].from_socket
for ln in list(cutpos.inputs['Geometry'].links):L.remove(ln)
cutmat=N['M1e3 | actual cut material only']
cvmat=N['M1e3 | actual inner cavity material only']

def info(obj,nickname):
    i=N.new('GeometryNodeObjectInfo');i.name='M1e6 | '+nickname+' info'
    i.transform_space='RELATIVE';i.inputs['Object'].default_value=obj
    return i

def dist(obj,nickname):
    i=info(obj,nickname)
    p=N.new('GeometryNodeProximity');p.name='M1e6 | distance to '+nickname;p.target_element='FACES'
    L.new(i.outputs['Geometry'],p.inputs['Target'])
    return p.outputs['Distance']

def compare(a,b,label,op='GREATER_THAN'):
    n=N.new('FunctionNodeCompare');n.name='M1e6 | '+label;n.data_type='FLOAT';n.operation=op
    L.new(a,n.inputs['A']);n.inputs['B'].default_value=b
    return n.outputs['Result']

def band(a,b,label):
    n=N.new('FunctionNodeBooleanMath');n.name='M1e6 | '+label;n.operation='AND'
    L.new(a,n.inputs[0]);L.new(b,n.inputs[1]);return n.outputs['Boolean']

if a.mode=='bevel':
    # Select only internal edges of the genuine freshly cut face, far enough
    # from both persistent surface boundaries to avoid disturbing skin/void seams.
    sel=cutmat.outputs['Selection']
    sel=band(sel,compare(dist(skin,'outer shell'),a.skin_clear,'inner cut away from skin'), 'cut & away from skin')
    sel=band(sel,compare(dist(cavity,'cavity'),a.cavity_clear,'inner cut away from void'),'avoid hole rim')
    # Existing original cut is locally planar; beveling only nearly coplanar
    # selected edges avoids grabbing skin/cavity sharp junction edges.
    angle=N.new('GeometryNodeInputMeshEdgeAngle');angle.name='M1e6 | edge dihedral'
    sel=band(sel,compare(angle.outputs['Unsigned Angle'],.30,'coplanar interior edge',op='LESS_THAN'),'cut face interior angle')
    bev=N.new('GeometryNodeMeshBevel');bev.name='M1e6 | LOCAL Mesh Bevel with selected edges'
    bev.inputs['Segments'].default_value=a.segments
    bev.inputs['Start Left Offset'].default_value=a.width
    bev.inputs['Start Right Offset'].default_value=a.width
    bev.inputs['End Left Offset'].default_value=a.width
    bev.inputs['End Right Offset'].default_value=a.width
    bev.inputs['Shape'].default_value=.5
    L.new(in_socket,bev.inputs['Mesh'])
    L.new(sel,bev.inputs['Selection'])
    feed=bev.outputs['Mesh']
else:
    feed=in_socket

# Continuous source-rest space 3D splines => nearest-point field, regardless
# of cut orientation or knife position. No Python per-pose rebuild / KDTree.
points=info(network,'authored 3D 135 curves')
ctp=N.new('GeometryNodeMeshToPoints');ctp.name='M1e6 | 3D source spline mesh vertices to points';ctp.mode='VERTICES'
L.new(points.outputs['Geometry'],ctp.inputs['Mesh'])
prox=N.new('GeometryNodeProximity');prox.name='M1e6 | 3D distance to source filaments';prox.target_element='POINTS'
L.new(ctp.outputs['Points'],prox.inputs['Target'])
rest=N.new('GeometryNodeInputNamedAttribute');rest.name='M1e6 | rest space input';rest.data_type='FLOAT_VECTOR';rest.inputs['Name'].default_value='fruit_rest'
L.new(rest.outputs['Attribute'],prox.inputs['Source Position'])
mapr=N.new('ShaderNodeMapRange');mapr.name='M1e6 | strand falloff'
mapr.clamp=True;mapr.interpolation_type='SMOOTHSTEP'
mapr.inputs['From Min'].default_value=.010;mapr.inputs['From Max'].default_value=.066
mapr.inputs['To Min'].default_value=.53;mapr.inputs['To Max'].default_value=0.
L.new(prox.outputs['Distance'],mapr.inputs['Value'])
store=N.new('GeometryNodeStoreNamedAttribute');store.name='M1e6 | live strand field on cut';store.data_type='FLOAT';store.domain='POINT'
store.inputs['Name'].default_value='m1e4_fiber';L.new(feed,store.inputs['Geometry'])
L.new(cutmat.outputs['Selection'],store.inputs['Selection']);L.new(mapr.outputs['Result'],store.inputs['Value'])
L.new(store.outputs['Geometry'],cutpos.inputs['Geometry'])

# Keep original 3D rest-space macro/cell and cavity displacement unchanged.
# Replace cut flesh with our previously authored strand material, which reads
# m1e4_fiber attribute (without GPL Frucht shader).
out=next(n for n in N if n.bl_idname=='NodeGroupOutput' and n.is_active_output)
last=out.inputs['Geometry'].links[0].from_socket
for link in list(out.inputs['Geometry'].links):L.remove(link)
apply=N.new('GeometryNodeSetMaterial');apply.name='M1e6 | live 3D filament color on cut'
apply.inputs['Material'].default_value=(base_flesh if a.material=='original' else strand_material)
L.new(last,apply.inputs['Geometry']);L.new(cutmat.outputs['Selection'],apply.inputs['Selection'])
L.new(apply.outputs['Geometry'],out.inputs['Geometry'])
# Clean up disconnected, expensive original full-mesh global Subdivide node.
N.remove(sub)

scene['m1e6_architecture']='Native Blender 5.2 GN cut-local Mesh Bevel plus source-rest 3D filament field, no handler'
scene['m1e6_note']='Selected Mesh Bevel is NOT selected Subdivide Mesh; GN proof requires QA'
body['m1e6_mode']=a.mode
body['m1e6_material']=a.material
body['m1e6_bevel_segments']=a.segments
body['m1e6_bevel_width']=a.width
# disable prior snapshot and fallback visibility: new original body evaluated by GN
snap=bpy.data.objects.get('M1e5 | EXACT live-local CutSurface')
if snap:
    snap.hide_render=True;snap.hide_set(True)
body.hide_render=False;body.hide_set(False)
scene['m1e5_mode']='FAST_GN_ALWAYS_LIVE'
scene.frame_set(15);bpy.context.view_layer.update()
a.out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()))
print('M1E6_BUILT',str(a.out.resolve()),'nodes',len(N),'mode',a.mode)

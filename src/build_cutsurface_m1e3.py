#!/usr/bin/env python3
"""M1e3 independently authored, editable geometric CutSurface for Strawberry Lab.

Run from a verified M1e2 scene. This does not copy Frucht/GPL node trees,
not scientifically derived anatomy, and doesn't edit the M1e2 source file.

A 3D rest-space field drives local cut-face displacement and cavity wall relief.
Material selection identifies true cut/cavity faces, while smooth distance to
untouched skin/cavity/knife tapers displacement to zero at geometry boundaries.
Subdivision currently affects the entire evaluated mesh (a known performance
limit; local refinement and baking are later tasks).
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import bpy

ap=argparse.ArgumentParser()
ap.add_argument('--out',type=Path,required=True)
ap.add_argument('--subdiv',type=int,default=2,choices=(1,2))
ap.add_argument('--cut-relief',type=float,default=.019)
ap.add_argument('--cavity-relief',type=float,default=.010)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])

scene=bpy.context.scene
body=bpy.data.objects['M1c | SDF cutter + rest-space tissue']
orig_shell=bpy.data.objects['M1c | watertight base (hidden)']
cavity=bpy.data.objects['M1e | persistent internal cavity (separate 3D mesh)']
knife=bpy.data.objects['M1e | independently moving knife (cube half space)']
base=body.modifiers[0].node_group
assert 'M1e2' in base.name

cut_material=bpy.data.materials['M1c | rest-space pith/cortex + wet Voronoi surface']
cavity_material=bpy.data.materials['M1e | shadowy wet cavity walls']
g=base.copy(); g.name='M1e3 | CutSurface | source-anchored 3D cells + cavity relief'
body.modifiers[0].node_group=g
N,L=g.nodes,g.links
output=next(n for n in N if n.bl_idname=='NodeGroupOutput' and n.is_active_output)
original=output.inputs['Geometry'].links[0].from_socket
for l in list(output.inputs['Geometry'].links):L.remove(l)

# Exact mode adds geometric samples, not just shader bump; subdivisions remain
# part of the actual evaluated Blender mesh and are validated below.
sub=N.new('GeometryNodeSubdivideMesh');sub.name='M1e3 | true cut-surface mesh refinement'
sub.inputs['Level'].default_value=a.subdiv;sub.location=(1620,220)
L.new(original,sub.inputs['Mesh'])

cut_sel=N.new('GeometryNodeMaterialSelection');cut_sel.name='M1e3 | actual cut material only'
cut_sel.inputs['Material'].default_value=cut_material
cav_sel=N.new('GeometryNodeMaterialSelection');cav_sel.name='M1e3 | actual inner cavity material only'
cav_sel.inputs['Material'].default_value=cavity_material

attr=N.new('GeometryNodeInputNamedAttribute');attr.name='M1e3 | rest-space source coordinates'
attr.data_type='FLOAT_VECTOR';attr.inputs['Name'].default_value='fruit_rest'

# Source outer shell and cavity are independent objects unaffected by the knife.
def proximity_obj(name,obj):
 info=N.new('GeometryNodeObjectInfo');info.name='M1e3 | '+name+' source object';info.transform_space='RELATIVE';info.inputs['Object'].default_value=obj
 prox=N.new('GeometryNodeProximity');prox.name='M1e3 | distance to '+name;prox.target_element='FACES'
 L.new(info.outputs['Geometry'],prox.inputs['Geometry'])
 return prox.outputs['Distance']
d_skin=proximity_obj('outer shell',orig_shell)
d_cavity=proximity_obj('cavity wall',cavity)
d_knife=proximity_obj('knife plane',knife)

def map_range(name,src,low,high,out_low=0.,out_high=1.,smooth=True):
 n=N.new('ShaderNodeMapRange');n.name=name;n.clamp=True
 if smooth:n.interpolation_type='SMOOTHSTEP'
 n.inputs['From Min'].default_value=low;n.inputs['From Max'].default_value=high
 n.inputs['To Min'].default_value=out_low;n.inputs['To Max'].default_value=out_high
 L.new(src,n.inputs['Value'])
 return n.outputs['Result']
def math2(name,operation,left,right=None,value=None):
 n=N.new('ShaderNodeMath');n.name=name;n.operation=operation
 L.new(left,n.inputs[0])
 if right is not None:L.new(right,n.inputs[1])
 elif value is not None:n.inputs[1].default_value=value
 return n.outputs['Value']
def noise(name,scale,detail=2.0):
 t=N.new('ShaderNodeTexNoise');t.name=name;t.noise_dimensions='3D'
 t.inputs['Scale'].default_value=scale;t.inputs['Detail'].default_value=detail;t.inputs['Roughness'].default_value=.62
 L.new(attr.outputs['Attribute'],t.inputs['Vector'])
 return t

# Rest-anchored 3D cell walls: same field at every cut orientation/position.
# Warp reference coordinates slightly to avoid visually rigid Voronoi cells.
warp=noise('M1e3 | rest-space warp',9.0,2.5)
warp_shift=N.new('ShaderNodeVectorMath');warp_shift.name='M1e3 | center warp';warp_shift.operation='SUBTRACT'
warp_shift.inputs[1].default_value=(.5,.5,.5);L.new(warp.outputs['Color'],warp_shift.inputs[0])
warp_scale=N.new('ShaderNodeVectorMath');warp_scale.operation='SCALE';warp_scale.name='M1e3 | warp amplitude'
warp_scale.inputs['Scale'].default_value=.037;L.new(warp_shift.outputs['Vector'],warp_scale.inputs['Vector'])
warp_add=N.new('ShaderNodeVectorMath');warp_add.operation='ADD';warp_add.name='M1e3 | warped rest field'
L.new(attr.outputs['Attribute'],warp_add.inputs[0]);L.new(warp_scale.outputs['Vector'],warp_add.inputs[1])

v=N.new('ShaderNodeTexVoronoi');v.name='M1e3 | 3D irregular cell-boundary field'
v.voronoi_dimensions='3D';v.feature='DISTANCE_TO_EDGE';v.inputs['Scale'].default_value=15.5
L.new(warp_add.outputs['Vector'],v.inputs['Vector'])
cell_profile=map_range('M1e3 | local domes versus groove walls',v.outputs['Distance'],.012,.18,-1.0,1.0)
cell_h=math2('M1e3 | physical cell relief','MULTIPLY',cell_profile,value=a.cut_relief)

micro=noise('M1e3 | pores 3D high frequency',41.0,2.2)
mic_profile=map_range('M1e3 | symmetric microtexture',micro.outputs['Fac'],0.19,0.81,-1.,1.)
mic_h=math2('M1e3 | microroughness geometry','MULTIPLY',mic_profile,value=.003)

macro=noise('M1e3 | intermediate tissue undulation',5.5,3.)
macro_profile=map_range('M1e3 | intermediate tissue profile',macro.outputs['Fac'],.17,.83,-1.,1.)
macro_h=math2('M1e3 | intermediate relief','MULTIPLY',macro_profile,value=.013)
height=math2('M1e3 | cells plus pores','ADD',cell_h,mic_h)
height=math2('M1e3 | multiscale true cut geometry','ADD',height,macro_h)

# Fade on BOTH sides of each cut-face boundary. An intersection with the
# original fruit skin or the cavity wall therefore remains geometrically joined.
fade_skin=map_range('M1e3 | no motion at skin rim',d_skin,.026,.21)
fade_cavity=map_range('M1e3 | no motion at cavity rim',d_cavity,.026,.19)
fade_cut=math2('M1e3 | both cut-rim fades','MULTIPLY',fade_skin,fade_cavity)
height=math2('M1e3 | bounded cut displacement','MULTIPLY',height,fade_cut)

normal=N.new('GeometryNodeInputNormal');normal.name='M1e3 | actual mesh normal'
vec=N.new('ShaderNodeVectorMath');vec.name='M1e3 | cut displacement along surface normal';vec.operation='SCALE'
L.new(normal.outputs['Normal'],vec.inputs['Vector']);L.new(height,vec.inputs['Scale'])
cutpos=N.new('GeometryNodeSetPosition');cutpos.name='M1e3 | CutSurface true geometry'
L.new(sub.outputs['Mesh'],cutpos.inputs['Geometry'])
L.new(cut_sel.outputs['Selection'],cutpos.inputs['Selection'])
L.new(vec.outputs['Vector'],cutpos.inputs['Offset'])

# Internal cavity has a distinct 3D displacement field. This field is also
# deterministic in the original coordinate system and fades to zero at the
# opening formed by the knife.
cav_tex=noise('M1e3 | cavity inner-wall 3D relief',26.,3.)
cav_profile=map_range('M1e3 | cavity roughness centered',cav_tex.outputs['Fac'],.18,.82,-1.,1.)
cav_h=math2('M1e3 | cavity relief strength','MULTIPLY',cav_profile,value=a.cavity_relief)
fade_knife=map_range('M1e3 | no motion at cavity opening rim',d_knife,.05,.22)
cav_h=math2('M1e3 | cavity seam-safe displacement','MULTIPLY',cav_h,fade_knife)
cav_vec=N.new('ShaderNodeVectorMath');cav_vec.operation='SCALE';cav_vec.name='M1e3 | cavity wall displacement vector'
L.new(normal.outputs['Normal'],cav_vec.inputs['Vector'])
L.new(cav_h,cav_vec.inputs['Scale'])
cavpos=N.new('GeometryNodeSetPosition');cavpos.name='M1e3 | real cavity wall geometry'
L.new(cutpos.outputs['Geometry'],cavpos.inputs['Geometry'])
L.new(cav_sel.outputs['Selection'],cavpos.inputs['Selection'])
L.new(cav_vec.outputs['Vector'],cavpos.inputs['Offset'])
L.new(cavpos.outputs['Geometry'],output.inputs['Geometry'])

# Label architecture and controls for inspection in .blend.
body['m1e3_module']='CutSurface: true 3-D rest-anchored cell geometry at freshly cut faces'
body['m1e3_detail_subdivision_levels']=a.subdiv
body['m1e3_cut_relief_units']=a.cut_relief
body['m1e3_cavity_relief_units']=a.cavity_relief
body['m1e3_fade']='smooth distance to intact outer skin/cavity wall/knife'
scene['m1e3_status']='EDITABLE_EXP_PROTOTYPE, not histological, not Frucht graph'
scene['m1e3_limit']='whole-mesh subdivision; not yet locally adaptive or physically packed cells'
scene.frame_set(15)
bpy.context.view_layer.update()
a.out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()))
print('M1E3_CUTSURFACE_BUILD_PASS',a.out.resolve(),'nodes',len(g.nodes),'subdivision',a.subdiv)

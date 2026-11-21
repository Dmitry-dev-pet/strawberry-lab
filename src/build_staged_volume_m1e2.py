#!/usr/bin/env python3
"""Independent Strawberry Lab prototype: split M1e into static SourceVolume and live Cut.

Reads existing Strawberry Lab M1e scene; does not copy Frucht's node graphs.
Reuses existing fruit shell, saved cavity mesh, knife, materials, and seeds.
The source is a *named 3D SDF grid*; a separate Geometry Nodes graph subtracts
an independently moving knife. This is a functional split, not a baked cache.

For a visually identical baseline, only the *wiring* of the volume/cutter is changed.
No additional cell histology or visual-quality claims.
"""
import bpy, json, time, sys, argparse
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
ap=argparse.ArgumentParser()
ap.add_argument('--out',type=Path,required=True,help='Write the new editable .blend here')
opt=ap.parse_args(args)
p=opt.out.parent;p.mkdir(parents=True,exist_ok=True)
start=time.perf_counter()
scene=bpy.context.scene
body=bpy.data.objects['M1c | SDF cutter + rest-space tissue']
cavity=bpy.data.objects['M1e | persistent internal cavity (separate 3D mesh)']
knife=bpy.data.objects['M1e | independently moving knife (cube half space)']
old=body.modifiers[0].node_group
assert old and 'M1e' in old.name
# Untouched old staged data in the loaded .blend remains available for A/B.
# Create a separate copy of the original sealed fruit mesh as the source object.
source=bpy.data.objects.new('M1e2 | 3D SourceVolume (outer minus cavity)',body.data.copy())
body.users_collection[0].objects.link(source)
source['pipeline']='STATIC_SOURCE_SDF (not baked; Blender may reevaluate on frame changes)'
source.hide_render=True
source.hide_set(True)
source.display_type='BOUNDS'

# SourceVolume: one independently editable 3-D continuous field, named inside
# Blender's volume geometry component. All operations follow Blender's own APIs.
vol=bpy.data.node_groups.new('M1e2 | SourceVolume : body minus cavity','GeometryNodeTree')
vol.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
vol.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
VN,VL=vol.nodes,vol.links
entry=VN.new('NodeGroupInput');entry.location=(-800,200)
exit=VN.new('NodeGroupOutput');exit.location=(400,200)
outer_sdf=VN.new('GeometryNodeMeshToSDFGrid');outer_sdf.name='3D solid field of original closed surface';outer_sdf.location=(-550,270)
outer_sdf.inputs['Voxel Size'].default_value=.038
outer_sdf.inputs['Band Width'].default_value=5
VL.new(entry.outputs['Geometry'],outer_sdf.inputs['Mesh'])
void_info=VN.new('GeometryNodeObjectInfo');void_info.name='Live cavity geometry';void_info.inputs['Object'].default_value=cavity;void_info.transform_space='RELATIVE';void_info.location=(-800,-170)
void_sdf=VN.new('GeometryNodeMeshToSDFGrid');void_sdf.name='3D cavity negative field';void_sdf.inputs['Voxel Size'].default_value=.038;void_sdf.inputs['Band Width'].default_value=5;void_sdf.location=(-550,-160)
VL.new(void_info.outputs['Geometry'],void_sdf.inputs['Mesh'])
sub=VN.new('GeometryNodeSDFGridBoolean');sub.name='BODY minus CAVITY, independent of knife';sub.operation='DIFFERENCE';sub.location=(-250,220)
VL.new(outer_sdf.outputs['SDF Grid'],sub.inputs['Grid 1']);VL.new(void_sdf.outputs['SDF Grid'],sub.inputs['Grid 2'])
store=VN.new('GeometryNodeStoreNamedGrid');store.name='Store retained 3-D SDF as fruit_solid';store.data_type='FLOAT';store.inputs['Name'].default_value='fruit_solid';store.location=(40,220)
VL.new(sub.outputs['Grid'],store.inputs['Grid']);VL.new(store.outputs['Volume'],exit.inputs['Geometry'])
source.modifiers.new('M1e2 static 3D volume source','NODES').node_group=vol

# Live Cutter: fetch the field from the evaluated source, then subtract knife.
# Preserve the M1e material classification, rest position and deformation.
ng=old.copy();ng.name='M1e2 | LIVE Cut : volume field minus knife'
body.modifiers[0].node_group=ng
N,L=ng.nodes,ng.links
old_bo=next(n for n in N if n.name=='M1e | second boolean after cavity')
knife_sdf=next(n for n in N if n.name=='M1e | knife SDF')
assert old_bo.inputs['Grid 2'].is_linked
for link in list(old_bo.inputs['Grid 1'].links):L.remove(link)
info=N.new('GeometryNodeObjectInfo');info.name='M1e2 | SourceVolume object';info.inputs['Object'].default_value=source;info.transform_space='RELATIVE';info.location=(-1180,-1200)
get=N.new('GeometryNodeGetNamedGrid');get.name='M1e2 | read fruit_solid grid';get.data_type='FLOAT';get.inputs['Name'].default_value='fruit_solid';get.inputs['Remove'].default_value=False;get.location=(-910,-1200)
L.new(info.outputs['Geometry'],get.inputs['Volume'])
L.new(get.outputs['Grid'],old_bo.inputs['Grid 1'])
old_bo.name='M1e2 | live DIFFERENCE (source volume minus knife)'
# Remove now-disconnected computational nodes to establish precisely one
# SDF conversion in the moving-knife graph. Leave extra object references used
# for categorizing exterior, cavity and cut surface materials in place.
keep_names={old_bo.name,knife_sdf.name}
for n in list(N):
 if n.bl_idname in ('GeometryNodeSDFGridBoolean','GeometryNodeMeshToSDFGrid') and n.name not in keep_names:
  N.remove(n)

assert sum(n.bl_idname=='GeometryNodeMeshToSDFGrid' for n in N)==1
assert sum(n.bl_idname=='GeometryNodeSDFGridBoolean' for n in N)==1
assert sum(n.bl_idname=='GeometryNodeMeshToSDFGrid' for n in VN)==2
assert sum(n.bl_idname=='GeometryNodeSDFGridBoolean' for n in VN)==1

scene['m1e2_pipeline']='SourceVolume(body - cavity) -> Cut(source - knife) -> exposed surface shaders'
scene['m1e2_source_volume'] = source.name
scene['m1e2_source_grid']='fruit_solid'
scene['m1e2_implementation']='independent Strawberry Lab GN; not Frucht licensed node group'
scene['m1e2_limit']='source volume not baked, performance must be benchmarked, macro cell geometry unchanged'
scene.frame_set(30)
bpy.context.view_layer.update()
path=opt.out.resolve()
bpy.ops.wm.save_as_mainfile(filepath=str(path))
print('M1E2_BUILD_OK',str(path),'elapsed',round(time.perf_counter()-start,3),'s','nodes',len(VN),len(N),flush=True)

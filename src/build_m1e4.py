#!/usr/bin/env python3
"""Strawberry Lab M1e4: source-3D filament skeleton + local watertight cut mesh.

Independent work based ONLY on Strawberry Lab's own M1e3 scene.
Command: blender -b strawberry-m1e3-cutsurface-fast.blend --python build_m1e4.py -- \
 --frame 15 --cuts 2 --out m1e4-frame15.blend

Keeps the M1e3 geometry-nodes live engine in the scene (hidden for exact snapshot).
The locally refined detail is a per-pose BMesh bake: move knife => re-run this
script to update the exact cut snapshot. This is NOT a live editable local mesh GN.
The original spline data is derived from our own M1a achene vascular paths;
its biological lengths/densities and colors remain artistic, not measurements.
"""
import argparse, sys, time, json, math, random
from pathlib import Path
import bpy, bmesh
from mathutils import Vector
from mathutils.kdtree import KDTree

p=argparse.ArgumentParser()
p.add_argument('--frame',type=int,default=15)
p.add_argument('--mode',choices=('beauty','diagnostic'),default='beauty')
p.add_argument('--cuts',type=int,default=2,choices=(0,1,2))
p.add_argument('--out',type=Path,required=True)
p.add_argument('--report',type=Path)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
t=time.perf_counter();s=bpy.context.scene;s.frame_set(a.frame)
body=bpy.data.objects['M1c | SDF cutter + rest-space tissue']
cutmod=next(m for m in body.modifiers if m.type=='NODES')
cut_graph=cutmod.node_group
assert 'M1e3' in cut_graph.name
knife=bpy.data.objects['M1e | independently moving knife (cube half space)']
orig_curve=bpy.data.objects['Vascular network | branches to every achene']
orig_shell=bpy.data.objects['M1c | watertight base (hidden)']
assert orig_curve.type=='CURVE'

# Return the unchanged M1e2 surface from the same stored procedural upstream
# graph. The cut and cavity are still calculated by the live SDF pipeline.
upstream=cut_graph.nodes['M1e3 | true cut-surface mesh refinement'].inputs['Mesh'].links[0].from_socket
base_group=cut_graph.copy();base_group.name='M1e4 | baseline GN for exact pose evaluation'
out=next(n for n in base_group.nodes if n.bl_idname=='NodeGroupOutput' and n.is_active_output)
for link in list(out.inputs['Geometry'].links):base_group.links.remove(link)
base_group.links.new(base_group.nodes[upstream.node.name].outputs[upstream.identifier],out.inputs['Geometry'])
cutmod.node_group=base_group
s.frame_set(a.frame);dg=bpy.context.evaluated_depsgraph_get();dg.update()
e=body.evaluated_get(dg)
base_mesh=bpy.data.meshes.new_from_object(e,preserve_all_data_layers=True,depsgraph=dg)
base_mesh.name=f'M1e4 | source cut mesh F{a.frame:02d}'
cutmod.node_group=cut_graph
bpy.context.view_layer.update()

mi={m.name:i for i,m in enumerate(base_mesh.materials) if m is not None}
mat_cut=bpy.data.materials['M1c | rest-space pith/cortex + wet Voronoi surface']
mat_cav=bpy.data.materials['M1e | shadowy wet cavity walls']
mat_skin=next(m for m in base_mesh.materials if m and m.name.startswith('Strawberry M1a'))
ic=mi[mat_cut.name]; iv=mi[mat_cav.name]; isk=mi[mat_skin.name]
start_verts=len(base_mesh.vertices);start_faces=len(base_mesh.polygons)

# Deterministic 3D branching subset of our existing curves. Never flattened
# into a 2D pattern or assumed biologically calibrated.
chosen=tuple((i,sp) for i,sp in enumerate(orig_curve.data.splines) if i%4==0)
full_points=[Vector(q.co[:3]) for _,sp in chosen for q in sp.points]
assert len(full_points)>1000
kd=KDTree(len(full_points))
for i,q in enumerate(full_points):kd.insert(q,i)
kd.balance()

# Cutter's editable top surface. This works for any rotated plane cutter.
plane_point=knife.matrix_world @ Vector((0,1,0))
plane_normal=(knife.matrix_world.to_3x3() @ Vector((0,1,0))).normalized()

bm=bmesh.new();bm.from_mesh(base_mesh)
for face in bm.faces:face.normal_update()
chosen_faces=[f for f in bm.faces if f.material_index==ic or
              (f.material_index==iv and abs((f.calc_center_median()-plane_point).dot(plane_normal))<.54)]
chosen_edges=set(edge for face in chosen_faces for edge in face.edges)
local_edge_count=len(chosen_edges)
start_refine=time.perf_counter()
if a.cuts:
 bmesh.ops.subdivide_edges(bm,edges=list(chosen_edges),cuts=a.cuts,use_grid_fill=True,smooth=0.)
refine_s=time.perf_counter()-start_refine
bad=sum(not edge.is_manifold for edge in bm.edges)
if bad:raise RuntimeError('Local subdivision broke the shell: '+str(bad))

# 3D rest attribute and artist-designed filament distance. The source curves
# are unchanged by the cutter, so all cut directions sample the same 3D field.
rest=bm.verts.layers.float_vector.get('fruit_rest')
if rest is None:raise RuntimeError('Missing original source rest coordinate')
fiber=bm.verts.layers.float.get('m1e4_fiber') or bm.verts.layers.float.new('m1e4_fiber')
# Treat boundary vertices as anchored; those incident to skin cannot move.
count_visible=0;zero_skin=0
for vert in bm.verts:
 if not vert.is_valid:continue
 types={f.material_index for f in vert.link_faces}
 if isk in types:
  vert[fiber]=0;zero_skin+=1;continue
 if ic not in types and iv not in types:
  vert[fiber]=0;continue
 d=kd.find(Vector(vert[rest]))[2]
 if ic in types:
  # A tapered stroke, smooth and real 3D: source fibers are curved splines.
  x=max(0.,min(1.,(.082-d)/.062))
  strength=x*x*(3-2*x)
  vert[fiber]=strength*.53
 else:
  x=max(0.,min(1.,(.040-d)/.029))
  strength=x*x*(3-2*x)
  vert[fiber]=strength*.09
 if vert[fiber]>.11:count_visible+=1

new_mesh=bpy.data.meshes.new(f'M1e4 | LOCAL refined cut frame {a.frame}')
for existing_material in base_mesh.materials:new_mesh.materials.append(existing_material)
bm.to_mesh(new_mesh);bm.free();new_mesh.update()
# Ensure all material slots from evaluated source survive.
if len(new_mesh.materials)<3:raise RuntimeError('Lost material slots after local refinement')
assert new_mesh.attributes.get('fruit_rest') is not None
assert new_mesh.attributes.get('m1e4_fiber') is not None
frozen=bpy.data.objects.new(f'M1e4 | local CutSurface SNAPSHOT frame {a.frame}',new_mesh)
body.users_collection[0].objects.link(frozen)
frozen['snapshot_frame']=a.frame
frozen['subdiv_cuts_on_selected_edges']=a.cuts
frozen['dynamic']='NO, recompute snapshot for each cutter pose using build_m1e4.py'
frozen['rest_space_field']='distance to authored M1a 3D curves, not 2D cut texture'
frozen['exact_local_selection']='fresh cut faces + cavity near open knife'

# Shared wet flesh material with an additional 3D filament attribute layer.
# This leaves the whole-fruit skin and original saved shaders untouched.
mat=mat_cut.copy();mat.name='M1e4 | strawberry cut flesh with 3D strands'
nt=mat.node_tree;nodes=nt.nodes;links=nt.links
shader=nodes.get('Principled BSDF');assert shader
inp=shader.inputs['Base Color']
wire=inp.links[0] if inp.is_linked else None
attr=nodes.new('ShaderNodeAttribute');attr.attribute_name='m1e4_fiber';attr.location=(shader.location.x-480,shader.location.y-520)
color=nodes.new('ShaderNodeMixRGB');color.blend_type='MIX';color.location=(shader.location.x-250,shader.location.y+130)
color.inputs[2].default_value=(.98,.69,.60,1)
links.new(attr.outputs['Fac'],color.inputs[0])
if wire:
 src=wire.from_socket;links.remove(wire);links.new(src,color.inputs[1])
else:color.inputs[1].default_value=tuple(inp.default_value)
links.new(color.outputs['Color'],inp)
# Lighting response and wetness still follow the existing procedural shader.
shader.inputs['Subsurface Weight'].default_value=.16
shader.inputs['Roughness'].default_value=.32

# Copy only the M1e3 downstream geometric displacement stage; supply our
# local BMesh rather than calling its whole-mesh Subdivide Mesh node.
g=cut_graph.copy();g.name='M1e4 | localized CutSurface GN after BMesh snapshot'
cutpos=g.nodes['M1e3 | CutSurface true geometry']
for l in list(cutpos.inputs['Geometry'].links):g.links.remove(l)
gin=next(n for n in g.nodes if n.bl_idname=='NodeGroupInput')
g.links.new(gin.outputs['Geometry'],cutpos.inputs['Geometry'])
# Material assignment occurs after the inherited cut and cavity relief stages.
out=next(n for n in g.nodes if n.bl_idname=='NodeGroupOutput' and n.is_active_output)
oldout=out.inputs['Geometry'].links[0].from_socket
for l in list(out.inputs['Geometry'].links):g.links.remove(l)
sel=g.nodes['M1e3 | actual cut material only']
newmat=g.nodes.new('GeometryNodeSetMaterial');newmat.name='M1e4 | expose 3D strand material only on cut'
newmat.inputs['Material'].default_value=mat
g.links.new(oldout,newmat.inputs['Geometry']);g.links.new(sel.outputs['Selection'],newmat.inputs['Selection'])
# Small actual geometric ridges follow the 3D filament field on the cut.
filattr=g.nodes.new('GeometryNodeInputNamedAttribute');filattr.data_type='FLOAT';filattr.inputs['Name'].default_value='m1e4_fiber'
filscale=g.nodes.new('ShaderNodeMath');filscale.operation='MULTIPLY';filscale.inputs[1].default_value=.004
mnorm=g.nodes.new('GeometryNodeInputNormal');mvec=g.nodes.new('ShaderNodeVectorMath');mvec.operation='SCALE'
g.links.new(filattr.outputs['Attribute'],filscale.inputs[0]);g.links.new(mnorm.outputs['Normal'],mvec.inputs[0]);g.links.new(filscale.outputs['Value'],mvec.inputs['Scale'])
filpos=g.nodes.new('GeometryNodeSetPosition');filpos.name='M1e4 | actual local filament ridges'
g.links.new(newmat.outputs['Geometry'],filpos.inputs['Geometry']);g.links.new(sel.outputs['Selection'],filpos.inputs['Selection']);g.links.new(mvec.outputs['Vector'],filpos.inputs['Offset'])
g.links.new(filpos.outputs['Geometry'],out.inputs['Geometry'])
frozen.modifiers.new('M1e4 | rest-space CutSurface after selective BMesh refinement','NODES').node_group=g

# A physical 3D spline-network retained separately for source inspection.
# The source is authored from OUR M1a paths, not the third-party Frucht graph.
curve=bpy.data.curves.new('M1e4 | real 3D interior strand source','CURVE')
curve.dimensions='3D';curve.resolution_u=4;curve.bevel_depth=.008;curve.bevel_resolution=2
curve.use_fill_caps=True
for i,sp in chosen:
 spline=curve.splines.new('POLY');spline.points.add(len(sp.points)-1)
 for j,pt in enumerate(sp.points):
  q=spline.points[j];q.co=pt.co;alpha=j/(len(sp.points)-1)
  q.radius=.95*(1-alpha)+.38*alpha
source=bpy.data.objects.new('M1e4 | persistent 3D curved fibers (source)',curve)
body.users_collection[0].objects.link(source)
source.hide_render=True;source.hide_set(True)
source['scope']='3D ARTIST strands derived from our M1a paths'

# True 3D tube geometry: clip the curve POINTS against the same live SDF knife.
# This is an interactive diagnostic layer. Endpoints are approximate to the
# resample step; the per-pose baked field supplies fine cut continuity.
tubes=bpy.data.objects.new('M1e4 | LIVE 3D filament tubes, clipped by knife',curve.copy())
body.users_collection[0].objects.link(tubes)
ng=bpy.data.node_groups.new('M1e4 | LIVE trim filaments by same SDF knife','GeometryNodeTree')
ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
N=ng.nodes;L=ng.links
ipt=N.new('NodeGroupInput');otp=N.new('NodeGroupOutput')
res=N.new('GeometryNodeResampleCurve');res.inputs['Count'].default_value=60
L.new(ipt.outputs['Geometry'],res.inputs['Curve'])
kninfo=N.new('GeometryNodeObjectInfo');kninfo.inputs['Object'].default_value=knife;kninfo.transform_space='RELATIVE'
ksdf=N.new('GeometryNodeMeshToSDFGrid');ksdf.inputs['Voxel Size'].default_value=.035;ksdf.inputs['Band Width'].default_value=5
L.new(kninfo.outputs['Geometry'],ksdf.inputs['Mesh'])
samp=N.new('GeometryNodeSampleGrid');pos=N.new('GeometryNodeInputPosition')
L.new(ksdf.outputs['SDF Grid'],samp.inputs['Grid']);L.new(pos.outputs['Position'],samp.inputs['Position'])
comp=N.new('FunctionNodeCompare');comp.data_type='FLOAT';comp.operation='LESS_THAN';comp.inputs['B'].default_value=-.012
L.new(samp.outputs['Value'],comp.inputs['A'])
delete=N.new('GeometryNodeDeleteGeometry');delete.domain='POINT';delete.mode='ALL'
L.new(res.outputs['Curve'],delete.inputs['Geometry']);L.new(comp.outputs['Result'],delete.inputs['Selection'])
profile=N.new('GeometryNodeCurvePrimitiveCircle');profile.inputs['Resolution'].default_value=7;profile.inputs['Radius'].default_value=.008
ctm=N.new('GeometryNodeCurveToMesh');ctm.inputs['Fill Caps'].default_value=True
L.new(delete.outputs['Geometry'],ctm.inputs['Curve']);L.new(profile.outputs['Curve'],ctm.inputs['Profile Curve'])
warm=bpy.data.materials.new('M1e4 | ivory sub-surface filament')
warm.diffuse_color=(.93,.63,.48,1);warm.use_nodes=True
pbr=warm.node_tree.nodes.get('Principled BSDF');pbr.inputs['Base Color'].default_value=(.93,.63,.48,1);pbr.inputs['Roughness'].default_value=.39;pbr.inputs['Subsurface Weight'].default_value=.13
sm=N.new('GeometryNodeSetMaterial');sm.inputs['Material'].default_value=warm
L.new(ctm.outputs['Mesh'],sm.inputs['Geometry']);L.new(sm.outputs['Geometry'],otp.inputs['Geometry'])
tubes.modifiers.new('Live SDF clip 3D fibers','NODES').node_group=ng
tubes.hide_render=(a.mode=='beauty')
# Tubes are diagnostic geometry: they can be hidden independently in lookdev.
tubes['real_3d']=True;tubes['animated_cut']='same knife object as main fruit'
tubes['warning']='artist fiber network; geometry cuts at sampled curve points, not exact solid Boolean'

# Camera and surrounding original scene remain unchanged for controlled A/B.
body.hide_render=True;body.hide_set(True)
frozen.hide_render=False;frozen.hide_set(False)
s['m1e4_snapshot_frame']=a.frame;s['m1e4_local_cuts']=a.cuts
s['m1e4_limit']='Exact local topology is per-pose BMesh bake; original live SDF hidden, still editable'
s['m1e4_source']='Original Strawberry Lab M1a 3D vascular polylines, artist calibration'
s['m1e4_not_frucht']='Independent implementation; Frucht GPL/private sources not copied'
bpy.context.view_layer.update()
a.out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()))
summary={'status':'BUILT_NOT_YET_VALIDATED','blender':bpy.app.version_string,
 'frame':a.frame,'cuts':a.cuts,'visual_mode':a.mode,'baseline_vertices':start_verts,'baseline_faces':start_faces,
 'selected_faces_before':len(chosen_faces),'selected_edges_before':local_edge_count,
 'locally_refined_vertices':len(new_mesh.vertices),'locally_refined_faces':len(new_mesh.polygons),
 'nonmanifold_edges_pre_GN':bad,'skinned_vertices_anchored':zero_skin,
 'fiber_points_source':len(full_points),'fiber_splines_source':len(chosen),
 'fiber_positive_vertices':count_visible,'local_subdiv_seconds':round(refine_s,4),
 'total_build_seconds':round(time.perf_counter()-t,4),
 'warnings':['artist network only','frozen local mesh requires per-pose rebuild','curve clipping approx to resample points']}
if a.report:
 a.report.parent.mkdir(parents=True,exist_ok=True)
 a.report.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
print('M1E4_BUILT',json.dumps(summary),flush=True)

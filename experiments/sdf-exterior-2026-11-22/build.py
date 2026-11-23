# Strawberry Lab — experimental SDF vertical slice based on sculpted exterior.
# Self-contained working prototype, independent of Frucht commercial assets.
import bpy, os, math, bmesh, json, sys, time
from mathutils import Vector
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=Path(os.environ.get('STRAWBERRY_SDF_BASE',str(ROOT/'build/exterior-v1/strawberry-exterior.blend')))
OUT=Path(os.environ.get('STRAWBERRY_SDF_OUT',str(ROOT/'build/sdf-vertical-slice')))
OUT.mkdir(parents=True,exist_ok=True)
T0=time.monotonic()
VOXEL=0.27
bpy.ops.wm.open_mainfile(filepath=str(BASE))
sc=bpy.context.scene
body=bpy.data.objects['Receptacle | sculpted skin and achene pits']
acoll=bpy.data.collections['Achenes | linked ovoid meshes']
seeds=sorted([ob for ob in acoll.objects if ob.type=='MESH'],key=lambda ob: ob.name)
assert len(seeds)==264
skin=body.data.materials[0]
M=body.matrix_world.copy(); Mi=M.inverted_safe()
cutcoll=bpy.data.collections.new('SDF proof | movable cutters')
sc.collection.children.link(cutcoll)
evalcoll=bpy.data.collections.new('SDF proof | live cut objects')
sc.collection.children.link(evalcoll)

def link_node(N, typ, label=None):
 n=N.new(typ)
 if label:n.label=label
 return n

# One shared procedural rest-space tissue shader for all cuts.
mat=bpy.data.materials.new('SDF proof | rest-space wet tissue / ARTIST')
mat.use_nodes=True
n=mat.node_tree.nodes; n.clear(); lk=mat.node_tree.links
out=n.new('ShaderNodeOutputMaterial');out.location=(1400,240)
bs=n.new('ShaderNodeBsdfPrincipled');bs.location=(1150,240)
bs.inputs['Roughness'].default_value=.38
bs.inputs['Subsurface Weight'].default_value=.09
bs.inputs['Coat Weight'].default_value=.12
bs.inputs['Coat Roughness'].default_value=.18
lk.new(bs.outputs['BSDF'],out.inputs['Surface'])
attr=n.new('ShaderNodeAttribute');attr.attribute_name='fruit_rest';attr.location=(-1250,200)
vec=n.new('ShaderNodeVectorMath');vec.operation='MULTIPLY';vec.inputs[1].default_value=(1.,1.,0.);vec.location=(-1050,400)
lk.new(attr.outputs['Vector'],vec.inputs[0])
radius=n.new('ShaderNodeVectorMath');radius.operation='LENGTH';radius.location=(-850,350)
lk.new(vec.outputs['Vector'],radius.inputs[0])
scale=n.new('ShaderNodeMath');scale.operation='DIVIDE';scale.inputs[1].default_value=13.0;scale.location=(-640,450)
lk.new(radius.outputs['Value'],scale.inputs[0])
ramp=n.new('ShaderNodeValToRGB');ramp.location=(-380,430)
ramp.color_ramp.elements[0].position=.13;ramp.color_ramp.elements[0].color=(.90,.44,.37,1)
ramp.color_ramp.elements[1].position=.90;ramp.color_ramp.elements[1].color=(.66,.038,.050,1)
lk.new(scale.outputs['Value'],ramp.inputs['Fac'])
noise=n.new('ShaderNodeTexNoise');noise.noise_dimensions='3D';noise.inputs['Scale'].default_value=.46;noise.inputs['Detail'].default_value=4.0;noise.location=(-800,-70)
lk.new(attr.outputs['Vector'],noise.inputs['Vector'])
mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.22;mix.location=(0,370)
lk.new(ramp.outputs['Color'],mix.inputs[1]);lk.new(noise.outputs['Fac'],mix.inputs[2])
lk.new(mix.outputs['Color'],bs.inputs['Base Color'])
vor=n.new('ShaderNodeTexVoronoi');vor.voronoi_dimensions='3D';vor.feature='DISTANCE_TO_EDGE'
vor.inputs['Scale'].default_value=1.5;vor.location=(-720,-400)
lk.new(attr.outputs['Vector'],vor.inputs['Vector'])
bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.20;bump.inputs['Distance'].default_value=.012;bump.location=(250,-260)
lk.new(vor.outputs['Distance'],bump.inputs['Height'])
lk.new(bump.outputs['Normal'],bs.inputs['Normal'])

# Combine all 264 achenes, assigning each vertex its owner's ORIGINAL local center.
verts=[];faces=[];centers=[]
for ob in seeds:
 transform=Mi @ ob.matrix_world
 center=Mi @ ob.matrix_world.translation
 off=len(verts)
 verts.extend([tuple(transform @ v.co) for v in ob.data.vertices])
 centers.extend([tuple(center)]*len(ob.data.vertices))
 faces.extend([tuple(off+k for k in poly.vertices) for poly in ob.data.polygons])
sme=bpy.data.meshes.new('SDF proof | 264 source achene solids with anchor attribute')
sme.from_pydata(verts,[],faces);sme.update()
sme.materials.append(seeds[0].data.materials[0])
at=sme.attributes.new('achene_center','FLOAT_VECTOR','POINT')
flat=[v for center in centers for v in center]
at.data.foreach_set('vector',flat)
assert len(verts)==sum(len(o.data.vertices) for o in seeds)
assert len(faces)>30000
print('SEEDS',len(seeds),'VERTS',len(verts),'FACES',len(faces),flush=True)

# Editable cutter geometries are one shared control for fruit and seed culling.
def make_cut(name,mode):
 if mode=='plane':
  bpy.ops.mesh.primitive_cube_add(size=2)
  cutter=bpy.context.object
  cutter.name='SDF cutter | planar (move or rotate)'
  cutter.location=M @ Vector((0.,-33.5,23.))
  cutter.rotation_euler=(math.radians(9),0,math.radians(-10))
  cutter.scale=(42,37,54)
 else:
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3,radius=1)
  cutter=bpy.context.object
  cutter.name='SDF cutter | spherical bite (move or scale)'
  cutter.location=M @ Vector((9.,-12.,26.))
  cutter.scale=(12.,12.,12.)
 for cl in list(cutter.users_collection):cl.objects.unlink(cutter)
 cutcoll.objects.link(cutter)
 cutter.display_type='WIRE'
 cutter.hide_render=True
 cutter['purpose']='Move, rotate or scale; both body and achene mask respond live'
 cutname=name
 co=bpy.data.objects.new('SDF visible body | '+name,body.data.copy())
 evalcoll.objects.link(co)
 co.matrix_world=M
 co.data.materials.clear()
 co.data.materials.append(skin)
 co.data.materials.append(mat)
 g=bpy.data.node_groups.new('SDF cutter + rest-space | '+name,'GeometryNodeTree')
 g.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
 g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
 N=g.nodes; L=g.links
 inp=N.new('NodeGroupInput');out=N.new('NodeGroupOutput')
 info=N.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE';info.inputs['Object'].default_value=cutter
 v1=N.new('GeometryNodeMeshToSDFGrid');v1.inputs['Voxel Size'].default_value=VOXEL;v1.inputs['Band Width'].default_value=5
 v2=N.new('GeometryNodeMeshToSDFGrid');v2.inputs['Voxel Size'].default_value=VOXEL;v2.inputs['Band Width'].default_value=5
 bo=N.new('GeometryNodeSDFGridBoolean');bo.operation='DIFFERENCE'
 grid=N.new('GeometryNodeGridToMesh');grid.inputs['Threshold'].default_value=0
 sm=N.new('GeometryNodeSetShadeSmooth')
 st=N.new('GeometryNodeStoreNamedAttribute');st.data_type='FLOAT_VECTOR';st.domain='POINT';st.inputs['Name'].default_value='fruit_rest'
 pos=N.new('GeometryNodeInputPosition')
 mat1=N.new('GeometryNodeSetMaterial');mat1.inputs['Material'].default_value=skin
 prox=N.new('GeometryNodeProximity');prox.target_element='FACES'
 comp=N.new('FunctionNodeCompare');comp.data_type='FLOAT';comp.operation='LESS_THAN';comp.inputs['B'].default_value=VOXEL*2.15
 mat2=N.new('GeometryNodeSetMaterial');mat2.inputs['Material'].default_value=mat
 for a,b in ((inp.outputs['Geometry'],v1.inputs['Mesh']),(info.outputs['Geometry'],v2.inputs['Mesh']),
 (v1.outputs['SDF Grid'],bo.inputs['Grid 1']),(v2.outputs['SDF Grid'],bo.inputs['Grid 2']),
 (bo.outputs['Grid'],grid.inputs['Grid']),(grid.outputs['Mesh'],sm.inputs['Geometry']),
 (sm.outputs['Geometry'],st.inputs['Geometry']),(pos.outputs['Position'],st.inputs['Value']),
 (st.outputs['Geometry'],mat1.inputs['Geometry']),(info.outputs['Geometry'],prox.inputs['Target']),
 (prox.outputs['Distance'],comp.inputs['A']),(comp.outputs['Result'],mat2.inputs['Selection']),
 (mat1.outputs['Geometry'],mat2.inputs['Geometry']),(mat2.outputs['Geometry'],out.inputs['Geometry'])): L.new(a,b)
 mod=co.modifiers.new('LIVE SDF body cut', 'NODES');mod.node_group=g
 so=bpy.data.objects.new('SDF visible seeds | '+name,sme)
 evalcoll.objects.link(so)
 so.matrix_world=M
 sg=bpy.data.node_groups.new('SDF live achene center mask | '+name,'GeometryNodeTree')
 sg.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
 sg.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
 SN=sg.nodes;SL=sg.links
 si=SN.new('NodeGroupInput');sout=SN.new('NodeGroupOutput')
 sinfo=SN.new('GeometryNodeObjectInfo');sinfo.transform_space='RELATIVE';sinfo.inputs['Object'].default_value=cutter
 sdf=SN.new('GeometryNodeMeshToSDFGrid');sdf.inputs['Voxel Size'].default_value=VOXEL;sdf.inputs['Band Width'].default_value=5
 attr=SN.new('GeometryNodeInputNamedAttribute');attr.data_type='FLOAT_VECTOR';attr.inputs['Name'].default_value='achene_center'
 sample=SN.new('GeometryNodeSampleGrid')
 scmp=SN.new('FunctionNodeCompare');scmp.data_type='FLOAT';scmp.operation='LESS_THAN';scmp.inputs['B'].default_value=-VOXEL*.5
 delt=SN.new('GeometryNodeDeleteGeometry');delt.domain='POINT';delt.mode='ALL'
 for a,b in ((si.outputs['Geometry'],delt.inputs['Geometry']),(sinfo.outputs['Geometry'],sdf.inputs['Mesh']),
 (sdf.outputs['SDF Grid'],sample.inputs['Grid']),(attr.outputs['Attribute'],sample.inputs['Position']),
 (sample.outputs['Value'],scmp.inputs['A']),(scmp.outputs['Result'],delt.inputs['Selection']),
 (delt.outputs['Geometry'],sout.inputs['Geometry'])):SL.new(a,b)
 so.modifiers.new('LIVE SDF achene anchor visibility','NODES').node_group=sg
 return co,so,cutter

plane,ps,pc=make_cut('planar','plane')
bite,bsobj,bc=make_cut('bite','sphere')
# Render 3 poses on one timeline. All geometry/cutters remain live and editable.
state_objects=[body]+seeds+[plane,ps,bite,bsobj]
for fr,kind in [(1,'whole'),(20,'plane'),(40,'bite')]:
 for ob in state_objects:
  visible=(ob==body or ob in seeds) if kind=='whole' else ((ob in (plane,ps)) if kind=='plane' else (ob in (bite,bsobj)))
  ob.hide_render=not visible
  ob.hide_viewport=not visible
  ob.keyframe_insert(data_path='hide_render',frame=fr)
  ob.keyframe_insert(data_path='hide_viewport',frame=fr)
# Calyx remains as-is: this early version does NOT yet cut leaves.
sc.frame_start=1;sc.frame_end=40
sc.render.engine='CYCLES'
sc.cycles.device='CPU'
sc.cycles.samples=12
sc.render.resolution_x=600;sc.render.resolution_y=600
sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'
sc['prototype']='SDF vertical slice / independent rest-space shader'
sc['limitation']='Calyx not cutter-controlled; achene center masks can retain intersecting seed edges; artistic tissues; no cached 3D atlas yet'
sc['positions']='frames 1 whole, 20 movable plane, 40 movable spherical bite'
sc['voxel_mm']=VOXEL
sc.frame_set(20)
# Do not overwrite current original: Blender is in a separate background process.
dest=OUT/'strawberry-sdf-vertical-slice.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(dest))
print('BLEND_SAVED',dest,flush=True)
stats={'source':str(BASE),'blend':str(dest),'voxel_mm':VOXEL,'achene_objects':len(seeds),'original_seed_vertices':len(verts),'source_mesh_faces':len(body.data.polygons),'render_engine':sc.render.engine,'seconds':round(time.monotonic()-T0,3)}
for fr,obj,seed in [(20,plane,ps),(40,bite,bsobj)]:
 sc.frame_set(fr)
 dg=bpy.context.evaluated_depsgraph_get()
 so=obj.evaluated_get(dg); me=so.to_mesh()
 bm=bmesh.new();bm.from_mesh(me)
 count={'verts':len(me.vertices),'faces':len(me.polygons),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'material_faces':{}}
 for pol in me.polygons:count['material_faces'][str(pol.material_index)]=count['material_faces'].get(str(pol.material_index),0)+1
 bm.free();so.to_mesh_clear()
 em=seed.evaluated_get(dg);me2=em.to_mesh()
 count['remaining_achene_vertices']=len(me2.vertices)
 count['remaining_achenes']=len(me2.vertices)//len(seeds[0].data.vertices)
 count['achene_vertices_per_source']=len(seeds[0].data.vertices)
 em.to_mesh_clear()
 assert count['faces']>1000 and count['nonmanifold_edges']==0 and len(count['material_faces'])>1, count
 stats['plane' if fr==20 else 'bite']=count
 print('EVALUATED',fr,json.dumps(count),flush=True)
(OUT/'validation.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2))
print('VALIDATED',json.dumps(stats,ensure_ascii=False),flush=True)

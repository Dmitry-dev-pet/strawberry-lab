"""Strawberry Lab v7 -- Frucht-inspired local cut cells using ONE shared source voxel field.

Independent original implementation. Start FROM v4 (not v5/v6) to preserve the
visually stronger vascular hierarchy. Tissue atlas red channel is sampled by
Geometry Nodes in native rest-space, flattening cells over exact same fibers that
the cut shader renders. Cells are subtle geometry confined to the cut face;
moisture is separately shader-defined. All biology/art parameters are ARTIST.
"""
import bpy,os,math,json,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(os.environ.get('STRAWBERRY_SDF_OUT',str(ROOT/'build/sdf-vertical-slice')))
SOURCE=OUT/'strawberry-sdf-vertical-slice-v4.blend'
DEST=OUT/'strawberry-sdf-vertical-slice-v7.blend'
assert SOURCE.is_file() and not DEST.exists(),"Required source missing or refusing to overwrite v7."
ts=time.monotonic()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE),use_scripts=False)
sc=bpy.context.scene
image=bpy.data.images.get('SDF proof v4 | 192^3 sparse volume and continuous branches')
assert image and image.packed_file and list(image.size)==[3072,2304], "Source volumetric atlas not packed"
material=bpy.data.materials['SDF proof v4 | sparse branches + cell sheen']
material.name='SDF proof v7 | cut cells flattened on SAME vessel atlas'

def mn(g,op,x=None,y=None,val=None,label=None):
 n=g.nodes.new('ShaderNodeMath');n.operation=op
 if label:n.label=label
 if x is not None:g.links.new(x,n.inputs[0])
 if y is not None:g.links.new(y,n.inputs[1])
 elif val is not None:n.inputs[1].default_value=val
 return n.outputs[0]
def vm(g,op,a=None,b=None,const=None,label=None):
 n=g.nodes.new('ShaderNodeVectorMath');n.operation=op
 if label:n.label=label
 if a is not None:g.links.new(a,n.inputs[0])
 if b is not None:g.links.new(b,n.inputs[1])
 elif const is not None:n.inputs[1].default_value=const
 return n.outputs['Vector']
def mr(g,x,mi,ma,lo,hi,label):
 n=g.nodes.new('ShaderNodeMapRange')
 n.data_type='FLOAT';n.interpolation_type='SMOOTHSTEP'
 n.clamp=True;n.label=label
 for k,v in (('From Min',mi),('From Max',ma),('To Min',lo),('To Max',hi)):
  n.inputs[k].default_value=v
 g.links.new(x,n.inputs['Value'])
 return n.outputs['Result']
def rgba_r(g,colorsocket):
 n=g.nodes.new('FunctionNodeSeparateColor');n.mode='RGB';g.links.new(colorsocket,n.inputs['Color'])
 return n.outputs['Red']

# Reusable sampled-image field function; exact packed-v4 contract 192 slices in
# 16x12 tiles, UV guarded against bleeding, XY linear + Z interpolation.
field=bpy.data.node_groups.new('V7 | original rest-space vascular field (192^3)','GeometryNodeTree')
field.interface.new_socket(name='rest_xyz',in_out='INPUT',socket_type='NodeSocketVector')
field.interface.new_socket(name='vascular_intensity',in_out='OUTPUT',socket_type='NodeSocketFloat')
inp=field.nodes.new('NodeGroupInput');output=field.nodes.new('NodeGroupOutput')
norm=field.nodes.new('ShaderNodeVectorMath')
norm.operation='MULTIPLY_ADD'
norm.inputs[1].default_value=(1./36,1./36,1./51)
norm.inputs[2].default_value=(.5,.5,1./51)
field.links.new(inp.outputs['rest_xyz'],norm.inputs[0])
sep=field.nodes.new('ShaderNodeSeparateXYZ');field.links.new(norm.outputs['Vector'],sep.inputs['Vector'])
x,y,z=sep.outputs['X'],sep.outputs['Y'],sep.outputs['Z']
x=mr(field,x,0,1,0,1,'Clamp X to atlas source range')
y=mr(field,y,0,1,0,1,'Clamp Y to atlas source range')
z=mr(field,z,0,1,0,1,'Clamp Z to atlas source range')
ix=mn(field,'MULTIPLY',z,val=191)
lo=mn(field,'FLOOR',ix)
hi=mn(field,'MINIMUM',mn(field,'ADD',lo,val=1),val=191)
frac=mn(field,'SUBTRACT',ix,lo)
px=mn(field,'ADD',mn(field,'MULTIPLY',x,val=191./192.),val=.5/192)
py=mn(field,'ADD',mn(field,'MULTIPLY',y,val=191./192.),val=.5/192)
def image_slice(idx,tag):
 cx=mn(field,'FLOORED_MODULO',idx,val=16,label=tag+' tile X')
 cy=mn(field,'FLOOR',mn(field,'DIVIDE',idx,val=16),label=tag+' tile Y')
 u=mn(field,'DIVIDE',mn(field,'ADD',cx,px),val=16)
 v=mn(field,'DIVIDE',mn(field,'ADD',cy,py),val=12)
 co=field.nodes.new('ShaderNodeCombineXYZ');field.links.new(u,co.inputs['X']);field.links.new(v,co.inputs['Y'])
 sampler=field.nodes.new('GeometryNodeImageTexture');sampler.label=tag+' shared original atlas'
 sampler.inputs['Image'].default_value=image
 assert sampler.inputs['Image'].default_value==image
 field.links.new(co.outputs['Vector'],sampler.inputs['Vector'])
 return rgba_r(field,sampler.outputs['Color'])
v0=image_slice(lo,'lower Z');v1=image_slice(hi,'upper Z')
vessel=mn(field,'ADD',
 mn(field,'MULTIPLY',v0,mn(field,'SUBTRACT',None,frac,val=None)),
 mn(field,'MULTIPLY',v1,frac))
# Correct (1-fraction) term with a constant-initialized math node.
# The SUBTRACT created above had a default 0 for input0; explicitly set 1.
for n in field.nodes:
 if n.bl_idname=='ShaderNodeMath' and n.operation=='SUBTRACT':
  if n.inputs[1].is_linked and n.inputs[1].links[0].from_socket==frac:
   n.inputs[0].default_value=1.
field.links.new(vessel,output.inputs['vascular_intensity'])
field['provenance']='Independent sample of packed v4 192cubed 16x12 RGB atlas; R channel'
field['coord_units']='Strawberry mm rest-space; bbox x/y[-18,+18] z[-1,50]'

for tag in ('planar','bite'):
 g=bpy.data.node_groups['SDF cutter + rest-space | '+tag]
 ns=g.nodes;lk=g.links
 dst=next(n for n in ns if n.bl_idname=='NodeGroupOutput')
 old=next(n for n in ns if n.bl_idname=='GeometryNodeSetPosition')
 finalmat=[n for n in ns if n.bl_idname=='GeometryNodeSetMaterial'][-1]
 origin=next(n for n in ns if n.bl_idname=='NodeGroupInput')
 capcompare=next(n for n in ns if n.bl_idname=='FunctionNodeCompare')
 # Remove previous v4 cut-face displacement, leaving the SDF cutter and materials intact.
 for oldname in ('Voronoi Texture','Position.001','Math','Math.001','Normal','Vector Math','Set Position'):
  n=ns.get(oldname)
  if n:ns.remove(n)
 for li in list(dst.inputs['Geometry'].links):lk.remove(li)
 sub=ns.new('GeometryNodeSubdivideMesh');sub.name='V7 | subdivide original watertight SDF once'
 sub.inputs['Level'].default_value=1
 lk.new(finalmat.outputs['Geometry'],sub.inputs['Mesh'])
 p=ns.new('GeometryNodeInputPosition')
 rest=ns.new('GeometryNodeInputNamedAttribute');rest.data_type='FLOAT_VECTOR';rest.inputs['Name'].default_value='fruit_rest'
 vascular=ns.new('GeometryNodeGroup');vascular.node_tree=field
 vascular.name='V7 | vessel sample from SAME 192cubed atlas'
 lk.new(rest.outputs['Attribute'],vascular.inputs['rest_xyz'])
 storev=ns.new('GeometryNodeStoreNamedAttribute');storev.data_type='FLOAT';storev.domain='POINT'
 storev.inputs['Name'].default_value='v7_vascular_intensity'
 lk.new(sub.outputs['Mesh'],storev.inputs['Geometry'])
 lk.new(vascular.outputs['vascular_intensity'],storev.inputs['Value'])
 # Physical local cell displacement created in 3D, not drawn as UV.
 noise=ns.new('ShaderNodeTexNoise');noise.noise_dimensions='3D';noise.inputs['Scale'].default_value=.48
 noise.inputs['Detail'].default_value=2.3
 lk.new(rest.outputs['Attribute'],noise.inputs['Vector'])
 warp0=vm(g,'SUBTRACT',noise.outputs['Color'],const=(.5,.5,.5))
 warp=ns.new('ShaderNodeVectorMath');warp.operation='SCALE'
 warp.inputs['Scale'].default_value=.48
 lk.new(warp0,warp.inputs[0])
 coord=vm(g,'ADD',rest.outputs['Attribute'],warp.outputs['Vector'])
 cells=ns.new('ShaderNodeTexVoronoi');cells.voronoi_dimensions='3D';cells.feature='DISTANCE_TO_EDGE'
 cells.inputs['Scale'].default_value=2.05
 cells.inputs['Randomness'].default_value=.96
 lk.new(coord,cells.inputs['Vector'])
 # Subtle small cells: broad plateaus with soft troughs, <0.02 mm (ARTIST).
 cellh=mr(g,cells.outputs['Distance'],.015,.22,-.017,.017,'Frucht-inspired shallow cell pillows')
 fine=ns.new('ShaderNodeTexNoise');fine.noise_dimensions='3D';fine.inputs['Scale'].default_value=5.2
 fine.inputs['Detail'].default_value=2.2;lk.new(coord,fine.inputs['Vector'])
 fineh=mn(g,'MULTIPLY',mn(g,'SUBTRACT',fine.outputs['Fac'],val=.5),val=.005)
 height=mn(g,'ADD',cellh,fineh)
 # Exact *source image* vessel field flattens geometric cell bumps.
 fiber_flat=mr(g,vascular.outputs['vascular_intensity'],.04,.48,1.,.12,
                 'No cell relief on same pale vascular fibers')
 orig=ns.new('GeometryNodeProximity');orig.target_element='FACES'
 lk.new(origin.outputs['Geometry'],orig.inputs['Target'])
 seam=mr(g,orig.outputs['Distance'],.15,.70,0.,1.,
            'Do not disturb original skin or sharp cut rim')
 capmask=mn(g,'MULTIPLY',capcompare.outputs['Result'],seam)
 capmask=mn(g,'MULTIPLY',capmask,fiber_flat)
 ctrl=ns.new('ShaderNodeValue');ctrl.name='V7_CELL_STRENGTH'
 ctrl.label='Artistic cell amplitude: 0=no extra cell geometry; 1=default'
 ctrl.outputs['Value'].default_value=1.
 height=mn(g,'MULTIPLY',height,ctrl.outputs['Value'])
 displaced=mn(g,'MULTIPLY',height,capmask,label='Cut-only relief attenuated over EXACT strands')
 storeh=ns.new('GeometryNodeStoreNamedAttribute');storeh.domain='POINT';storeh.data_type='FLOAT'
 storeh.inputs['Name'].default_value='v7_cell_height_mm'
 lk.new(storev.outputs['Geometry'],storeh.inputs['Geometry'])
 lk.new(displaced,storeh.inputs['Value'])
 nor=ns.new('GeometryNodeInputNormal')
 normalvec=ns.new('ShaderNodeVectorMath');normalvec.operation='SCALE'
 lk.new(nor.outputs['Normal'],normalvec.inputs[0])
 lk.new(displaced,normalvec.inputs['Scale'])
 sp=ns.new('GeometryNodeSetPosition');sp.name='V7 | actual cut cell pillows'
 lk.new(storeh.outputs['Geometry'],sp.inputs['Geometry'])
 lk.new(normalvec.outputs['Vector'],sp.inputs['Offset'])
 lk.new(sp.outputs['Geometry'],dst.inputs['Geometry'])
 g['v7_recipe']='Subdivide SDF once; sample SAME 192cubed vascular atlas in rest xyz; flatten cell on strands; wetness shader only'
 print('V7_NODES',tag,len(g.nodes),flush=True)

# Retain original 3 wet Voronoi layers, but no huge glossy center patch.
nodes=material.node_tree.nodes
bs=next(n for n in nodes if n.bl_idname=='ShaderNodeBsdfPrincipled')
bs.inputs['Roughness'].default_value=.43
bs.inputs['Subsurface Weight'].default_value=.15
bs.inputs['Coat Weight'].default_value=.085
bs.inputs['Coat Roughness'].default_value=.26
bump=next(n for n in nodes if n.bl_idname=='ShaderNodeBump')
bump.inputs['Strength'].default_value=.19
bump.inputs['Distance'].default_value=.017
for n in nodes:
 if n.bl_idname=='ShaderNodeMapRange':
  if abs(n.inputs['To Min'].default_value-.24)<.01 and abs(n.inputs['To Max'].default_value-.45)<.01:
   n.inputs['To Min'].default_value=.37
   n.inputs['To Max'].default_value=.52
 if n.bl_idname=='ShaderNodeMixRGB' and len(n.inputs)>=3 and not n.inputs[2].is_linked:
  col=tuple(n.inputs[2].default_value)
  if abs(col[0]-.95)<.01 and abs(col[1]-.70)<.01:
   n.inputs[2].default_value=(.87,.57,.48,1)

sc['v7_architecture']='Back to v4. Cells only cut-surface microdisplacement, suppressed exactly over same 192^3 volumetric vessels. Independent wet material.'
sc['v7_not_histology']='Cell size/wetness and vascular geometry are all ARTIST; no per-cell 3D membrane solids.'
sc.frame_set(20)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(DEST))
manifest={'version':'v7','starting_point':'v4, not v5/v6','source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          'atlas_sha256':hashlib.sha256((OUT/'tissue-v4-192.png').read_bytes()).hexdigest(),
          'v7_blend_sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),
          'shared_3d_vascular_field':'192^3 RGB channel R packed 16x12; Z linear interpolation both cuts',
          'cut_cells':'Geometry Nodes Subdivide + shallow warped 3D Voronoi, flatten above same vascular atlas',
          'biology':'ARTIST, no measured per-cell membrane geometry','seconds':round(time.monotonic()-ts,2)}
(OUT/'v7-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('V7_SAVED',json.dumps(manifest,ensure_ascii=False),flush=True)
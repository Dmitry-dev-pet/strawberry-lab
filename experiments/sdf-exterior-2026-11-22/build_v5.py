"""Strawberry Lab v5: actual cut-local cellular displacement in native Geometry Nodes.
Do not affect whole fruit, achene geometry/culling, or original cut SDF pipeline.
Cells are ARTIST mesostructure, not validated individual cell membranes.
"""
import bpy, math, time, json, hashlib, os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
P=Path(os.environ.get('STRAWBERRY_SDF_OUT',str(ROOT/'build/sdf-vertical-slice')))
BASE=P/'strawberry-sdf-vertical-slice-v4.blend'
DEST=P/'strawberry-sdf-vertical-slice-v5.blend'
t0=time.monotonic()
assert BASE.is_file() and not DEST.exists(),'Missing v4 source or refusing to overwrite existing v5'
bpy.ops.wm.open_mainfile(filepath=str(BASE),use_scripts=False)
sc=bpy.context.scene
NGC=0
def get(g,id_name):
    out=[n for n in g.nodes if n.bl_idname==id_name]
    if not out:raise RuntimeError('Cannot find '+id_name+' in '+g.name)
    return out
def mathnode(g,op,x=None,y=None,v=None,name=None):
    n=g.nodes.new('ShaderNodeMath');n.operation=op
    if name:n.label=name
    if x is not None:g.links.new(x,n.inputs[0])
    if y is not None:g.links.new(y,n.inputs[1])
    elif v is not None:n.inputs[1].default_value=v
    return n.outputs[0]
def vector_math(g,op,a=None,b=None,constant=None,label=''):
    n=g.nodes.new('ShaderNodeVectorMath');n.operation=op
    if label:n.label=label
    if a is not None:g.links.new(a,n.inputs[0])
    if b is not None:g.links.new(b,n.inputs[1])
    elif constant is not None:n.inputs[1].default_value=constant
    return n.outputs['Vector']
def maprange(g,source,from_min,from_max,to_min,to_max,label):
    n=g.nodes.new('ShaderNodeMapRange');n.label=label
    n.data_type='FLOAT'
    n.interpolation_type='SMOOTHSTEP'
    n.clamp=True
    n.inputs['From Min'].default_value=from_min
    n.inputs['From Max'].default_value=from_max
    n.inputs['To Min'].default_value=to_min
    n.inputs['To Max'].default_value=to_max
    g.links.new(source,n.inputs['Value'])
    return n.outputs['Result']

for mode in ('planar','bite'):
    g=bpy.data.node_groups['SDF cutter + rest-space | '+mode]
    ns=g.nodes;lk=g.links
    out=get(g,'NodeGroupOutput')[0]
    matnodes=get(g,'GeometryNodeSetMaterial')
    assert len(matnodes)==2
    final_material=matnodes[1]
    inp=get(g,'NodeGroupInput')[0]
    cutter_dist=get(g,'GeometryNodeProximity')[0]
    # The v4 displacement pipeline is replaced, not compounded.
    for oldname in ('Set Position','Voronoi Texture','Position.001','Math','Math.001','Normal','Vector Math'):
        old=ns.get(oldname)
        if old:ns.remove(old)
    for edge in list(out.inputs['Geometry'].links):lk.remove(edge)
    sub=ns.new('GeometryNodeSubdivideMesh')
    sub.name='V5 / full closed mesh subdivide once'
    sub.inputs['Level'].default_value=1
    lk.new(final_material.outputs['Geometry'],sub.inputs['Mesh'])
    pos=ns.new('GeometryNodeInputPosition')
    pos.label='Same source rest coordinates, no cut-specific UV'
    orig=ns.new('GeometryNodeProximity')
    orig.target_element='FACES'
    orig.label='Distance to original fruit skin for zero-relief seam'
    lk.new(inp.outputs['Geometry'],orig.inputs['Target'])
    fade_outer=maprange(g,orig.outputs['Distance'],.22,.82,0.,1.,'Seam protection: no skin displacement')
    fade_cutter=maprange(g,cutter_dist.outputs['Distance'],.06,.43,1.,0.,'Cut face only; zero outside cutter surface')
    mask=mathnode(g,'MULTIPLY',fade_outer,fade_cutter,name='Smooth 3D cap-only mask')
    warpnoise=ns.new('ShaderNodeTexNoise')
    warpnoise.noise_dimensions='3D';warpnoise.inputs['Scale'].default_value=.64
    warpnoise.inputs['Detail'].default_value=2.1
    warpnoise.label='Irregular 3D cell placement'
    lk.new(pos.outputs['Position'],warpnoise.inputs['Vector'])
    warpcenter=vector_math(g,'SUBTRACT',warpnoise.outputs['Color'],constant=(.5,.5,.5),label='Center warp')
    warp=ns.new('ShaderNodeVectorMath');warp.operation='SCALE';warp.inputs['Scale'].default_value=.78
    lk.new(warpcenter,warp.inputs[0])
    warped=vector_math(g,'ADD',pos.outputs['Position'],warp.outputs['Vector'])
    cell=ns.new('ShaderNodeTexVoronoi')
    cell.label='True mesh cell pillows (not just normal bump)'
    cell.voronoi_dimensions='3D';cell.feature='DISTANCE_TO_EDGE'
    cell.inputs['Scale'].default_value=1.23
    cell.inputs['Randomness'].default_value=.94
    lk.new(warped,cell.inputs['Vector'])
    meso=maprange(g,cell.outputs['Distance'],.018,.21,-.115,.115,'Cell centres rise; cell walls recessed (mm)')
    noise=ns.new('ShaderNodeTexNoise');noise.noise_dimensions='3D'
    noise.label='Nonuniform mesocellular relief'
    noise.inputs['Scale'].default_value=5.0
    noise.inputs['Detail'].default_value=2.0
    lk.new(warped,noise.inputs['Vector'])
    fine=mathnode(g,'SUBTRACT',noise.outputs['Fac'],v=.5)
    fine=mathnode(g,'MULTIPLY',fine,v=.055,name='Tiny real ridges, shader does the subvoxel pores')
    relief=mathnode(g,'ADD',meso,fine,name='Raw mm cell topography')
    strength=ns.new('ShaderNodeValue')
    strength.name='V5_CELL_RELIEF_STRENGTH'
    strength.label='V5 cell strength (0 disables all new geometry offsets)'
    strength.outputs['Value'].default_value=1.0
    relief=mathnode(g,'MULTIPLY',relief,strength.outputs['Value'])
    actual=mathnode(g,'MULTIPLY',relief,mask,name='Cut-only measurable geometric displacement (mm)')
    store=ns.new('GeometryNodeStoreNamedAttribute')
    store.data_type='FLOAT';store.domain='POINT'
    store.inputs['Name'].default_value='v5_cut_cell_relief_mm'
    lk.new(sub.outputs['Mesh'],store.inputs['Geometry'])
    lk.new(actual,store.inputs['Value'])
    normal=ns.new('GeometryNodeInputNormal')
    normal_offset=ns.new('ShaderNodeVectorMath')
    normal_offset.operation='SCALE'
    lk.new(normal.outputs['Normal'],normal_offset.inputs[0])
    lk.new(actual,normal_offset.inputs['Scale'])
    displace=ns.new('GeometryNodeSetPosition')
    displace.label='Physical, local wet-cell relief on cut face'
    lk.new(store.outputs['Geometry'],displace.inputs['Geometry'])
    lk.new(normal_offset.outputs['Vector'],displace.inputs['Offset'])
    lk.new(displace.outputs['Geometry'],out.inputs['Geometry'])
    # Organizer - labels are also a form of audit metadata
    g['v5_cell_relief']='Per-vertex geometry, continuous 3D Voronoi, original-skin seam fade + cutter proximity'
    g['v5_cell_size']='ARTIST not microscope-derived'
    print('CELL_GN_PREPARED',mode,len(ns),flush=True)

# Cut-only shader: lower broad/central specular, local moisture microvariation.
mat=bpy.data.materials['SDF proof v4 | sparse branches + cell sheen']
mat.name='SDF proof v5 | cell sculpt + restrained wet highlights'
N=mat.node_tree.nodes;L=mat.node_tree.links
princip=next(n for n in N if n.bl_idname=='ShaderNodeBsdfPrincipled')
princip.inputs['Subsurface Weight'].default_value=.16
princip.inputs['Coat Weight'].default_value=.07
princip.inputs['Coat Roughness'].default_value=.22
princip.inputs['Metallic'].default_value=0.0
bump=next(n for n in N if n.bl_idname=='ShaderNodeBump')
bump.inputs['Strength'].default_value=.24
bump.inputs['Distance'].default_value=.028
# Cut colors: central pith + vessels are soft rather than saturated whitish.
for n in N:
    if n.bl_idname=='ShaderNodeMath' and n.operation=='MULTIPLY':
        for inp in n.inputs:
            if not inp.is_linked and abs(inp.default_value-.56)<.005:
                inp.default_value=.34
    if n.bl_idname=='ShaderNodeMixRGB':
        for inp in (n.inputs[1],n.inputs[2]):
            if inp.is_linked:continue
            col=tuple(inp.default_value)
            if abs(col[0]-.95)<.01 and abs(col[1]-.70)<.01:
                inp.default_value=(.79,.45,.39,1)
    if n.bl_idname=='ShaderNodeMapRange':
        # v4 roughness mapping: 0.24..0.45 -> 0.37..0.52
        if abs(n.inputs['To Min'].default_value-.24)<.01 and abs(n.inputs['To Max'].default_value-.45)<.01:
            n.inputs['To Min'].default_value=.36
            n.inputs['To Max'].default_value=.53

# 3D micro moisture: separate gently varying roughness around the cells.
rest=next(n for n in N if n.bl_idname=='ShaderNodeAttribute' and n.attribute_name=='fruit_rest')
moist=N.new('ShaderNodeTexNoise')
moist.noise_dimensions='3D';moist.inputs['Scale'].default_value=13.
moist.inputs['Detail'].default_value=2.;moist.label='Micro moist film in rest coordinates'
L.new(rest.outputs['Vector'],moist.inputs['Vector'])
rough_input=princip.inputs['Roughness']
old=rough_input.links[0].from_socket if rough_input.links else None
roughblend=N.new('ShaderNodeMixRGB');roughblend.blend_type='MIX'
roughblend.inputs[0].default_value=.22
roughblend.label='Wet cell microrelief without broad white patch'
if old:
    L.remove(rough_input.links[0]);L.new(old,roughblend.inputs[1])
else:roughblend.inputs[1].default_value=(.43,.43,.43,1)
moistmap=N.new('ShaderNodeMapRange')
moistmap.clamp=True
moistmap.inputs['From Min'].default_value=.22
moistmap.inputs['From Max'].default_value=.80
moistmap.inputs['To Min'].default_value=.32
moistmap.inputs['To Max'].default_value=.51
L.new(moist.outputs['Fac'],moistmap.inputs['Value'])
L.new(moistmap.outputs['Result'],roughblend.inputs[2])
L.new(roughblend.outputs['Color'],rough_input)

sc['v5_status']='EDITABLE CELLULAR MESH EXPERIMENT. No per-cell manifold solids; local Voronoi mesh deformation. Skin/rim fade. ARTIST.'
sc['v5_source']='v4 scene, packed 192^3 field unchanged, native Geometry Nodes cut displacement + cut-only wet material'
sc['v5_voronoi_mesorelief']='Physical geometry. Strength=1; adjust node V5_CELL_RELIEF_STRENGTH in each cutter GN group'
sc.frame_set(20)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(DEST))
info={'version':'v5','source_sha256':hashlib.sha256(BASE.read_bytes()).hexdigest(),'blend_sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),'source_v4_atlas_sha256':hashlib.sha256((P/'tissue-v4-192.png').read_bytes()).hexdigest(),'cut_resolution_level':1,'wall_center_displacement_mm':[-.115,.115],'scientific_status':'ARTIST','seconds':round(time.monotonic()-t0,2)}
(P/'v5-manifest.json').write_text(json.dumps(info,indent=2)+'\n')
print('SAVED_V5',json.dumps(info),flush=True)

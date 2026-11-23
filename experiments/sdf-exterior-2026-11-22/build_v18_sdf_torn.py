"""Strawberry Lab v18: experimental source-rest 3D field driven SDF tear.

Input: exact SHA-verified owner v12 original .blend. NO Frucht or third-party assets.
Separate source v12 untouched; independent scripts-disabled GN cutter edit.
Variant A is the VolumeCube/GN control with zero fracture; B is volume field perturbation.
Both share the exact same sampling/cutter/geometry/material graph and 192^3 packed volume.
"""
import bpy, sys, pathlib, hashlib, json

ROOT=pathlib.Path('/mnt/data/strawberry_v18')
SOURCE=pathlib.Path('/mnt/data/strawberry_v17/v12_original.blend')
SOURCE_SHA='300a2bfeaa86831220657b74fe8b00d4d7ec0b42f4ffefca863d6410cbb405b7'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_SHA
argv=sys.argv[sys.argv.index('--')+1:]
assert len(argv)==1 and argv[0] in ('a','b','c'),argv
variant=argv[0]

# Blender already loads source before running this script.
assert pathlib.Path(bpy.data.filepath)==SOURCE
sc=bpy.context.scene
original_image=bpy.data.images['SDF proof v4 | 192^3 sparse volume and continuous branches']
assert original_image.packed_file is not None
vascular=bpy.data.node_groups['V8 | original rest-space vascular field (192^3)']

summary={"variant":variant,"source_sha":SOURCE_SHA,"voxel_size_mm":0.271,
         "volume_min":(-19,-19,-5),"volume_max":(19,19,53),"resolution":(140,140,214),
         "tear_strength":{'a':0.0,'b':1.0,'c':0.28}[variant],
         "field_recipe":"ARTIST; original volume R+anisotropic 3D noise before SDF remesh; independent of cutter pose"}

def math_node(g,operation,label,a=None,b=None):
    n=g.nodes.new('ShaderNodeMath');n.operation=operation;n.label=label
    if isinstance(a,(int,float)):n.inputs[0].default_value=a
    elif a is not None:g.links.new(a,n.inputs[0])
    if isinstance(b,(int,float)):n.inputs[1].default_value=b
    elif b is not None:g.links.new(b,n.inputs[1])
    return n.outputs['Value']

def map_range(g,label,value,x0,x1,y0,y1):
    n=g.nodes.new('ShaderNodeMapRange');n.label=label
    n.interpolation_type='SMOOTHSTEP';n.clamp=True
    g.links.new(value,n.inputs['Value'])
    n.inputs['From Min'].default_value=x0;n.inputs['From Max'].default_value=x1
    n.inputs['To Min'].default_value=y0;n.inputs['To Max'].default_value=y1
    return n.outputs['Result']

for tag in ('planar','bite'):
    g=bpy.data.node_groups['SDF cutter + rest-space | '+tag]
    N=g.nodes;L=g.links
    original_grid=N['Grid to Mesh']
    smoother=N['Set Shade Smooth']
    body_sdf=N['Mesh to SDF Grid'].outputs['SDF Grid']
    knife_sdf=N['Mesh to SDF Grid.001'].outputs['SDF Grid']
    # Build a signed continuous 3D density field using original live body/cutter SDF grids.
    grid=N.new('GeometryNodeVolumeCube');grid.name='V18 | rest-space fracture volume 3D';grid.label='V18 | true 3D signed field, independent of cutter pose'
    grid.inputs['Min'].default_value=(-19,-19,-5);grid.inputs['Max'].default_value=(19,19,53)
    grid.inputs['Resolution X'].default_value=140;grid.inputs['Resolution Y'].default_value=140;grid.inputs['Resolution Z'].default_value=214
    grid.inputs['Background'].default_value=-5.0
    pos=N.new('GeometryNodeInputPosition');pos.name='V18 | evaluated voxel rest position'
    bs=N.new('GeometryNodeSampleGrid');bs.name='V18 | sample source body SDF';L.new(body_sdf,bs.inputs['Grid']);L.new(pos.outputs['Position'],bs.inputs['Position'])
    cs=N.new('GeometryNodeSampleGrid');cs.name='V18 | sample live cutter SDF';L.new(knife_sdf,cs.inputs['Grid']);L.new(pos.outputs['Position'],cs.inputs['Position'])
    # The exact same 3D R atlas used by shader + v8 cell flattening: no new fibers as objects.
    vf=N.new('GeometryNodeGroup');vf.name='V18 | shared original vascular rest-space R';vf.node_tree=vascular
    L.new(pos.outputs['Position'],vf.inputs['rest_xyz'])
    R=vf.outputs['vascular_intensity']
    mask=map_range(g,'V18 | medium-strength vascular 3D envelope (ARTIST)',R,.035,.18,0,1)
    # Anisotropic 3D noise: narrow in XY, elongated in Z. Continuous in full volume;
    # changing cutter orientation does not rebuild any 2D map.
    vec=N.new('ShaderNodeVectorMath');vec.name='V18 | fibre orientation scale 3D';vec.operation='MULTIPLY'
    vec.inputs[1].default_value=(.62,.72,.16)
    L.new(pos.outputs['Position'],vec.inputs[0])
    noi=N.new('ShaderNodeTexNoise');noi.name='V18 | anisotropic 3D strand irregularity';noi.noise_dimensions='3D'
    noi.inputs['Scale'].default_value=1.65;noi.inputs['Detail'].default_value=2.4;noi.inputs['Roughness'].default_value=.58
    L.new(vec.outputs['Vector'],noi.inputs['Vector'])
    nshape=map_range(g,'V18 | elongated strand peaks',noi.outputs['Fac'],.42,.61,0,1)
    # Coarser envelope changes tear clustering without changing vascular graph.
    vec2=N.new('ShaderNodeVectorMath');vec2.name='V18 | broad 3D tissue envelope coords';vec2.operation='MULTIPLY'
    vec2.inputs[1].default_value=(.22,.24,.13);L.new(pos.outputs['Position'],vec2.inputs[0])
    noi2=N.new('ShaderNodeTexNoise');noi2.name='V18 | broad tissue cohesion noise';noi2.noise_dimensions='3D'
    noi2.inputs['Scale'].default_value=1.08;noi2.inputs['Detail'].default_value=2.0;noi2.inputs['Roughness'].default_value=.55
    L.new(vec2.outputs['Vector'],noi2.inputs['Vector'])
    macro=map_range(g,'V18 | broad 3D tissue cohesion',noi2.outputs['Fac'],.27,.73,.25,1.)
    # Retain tissue as 3D protrusions where structural strands intersect cut.
    strandcore=math_node(g,'MULTIPLY','V18 | strands x long 3D peaks',mask,nshape)
    strandcore=math_node(g,'MULTIPLY','V18 | strands x volume envelope',strandcore,macro)
    positive=math_node(g,'MULTIPLY','V18 | max 0.90mm cohesive tissue retention',strandcore,.90)
    # Soft tissue erodes between strands, a real 3D cavity, not a shader-only stroke.
    inv=math_node(g,'SUBTRACT','V18 | soft tissue away from strands',1.,mask)
    rough=map_range(g,'V18 | sparse low-intensity tissue erosion',noi.outputs['Fac'],.41,.68,0,1)
    negative=math_node(g,'MULTIPLY','V18 | erosion mask',rough,inv)
    negative=math_node(g,'MULTIPLY','V18 | max 0.28mm soft erosion',negative,-.28)
    signed=math_node(g,'ADD','V18 | continuous 3D tearing height in mm',positive,negative)
    knob=N.new('ShaderNodeValue');knob.name='V18_TEAR_STRENGTH';knob.label='V18 | 0=zero-tear control 1=experimental fracture';knob.outputs['Value'].default_value=summary['tear_strength']
    displacement=math_node(g,'MULTIPLY','V18 | strength gain',signed,knob.outputs['Value'])
    changed_cutter=math_node(g,'ADD','V18 | cutter SDF + 3D cohesion field',cs.outputs['Value'],displacement)
    keep_cutter=math_node(g,'MULTIPLY','V18 | subtract cutter distance',changed_cutter,-1)
    inside=math_node(g,'MAXIMUM','V18 | SDF of (body minus field-warped cutter)',bs.outputs['Value'],keep_cutter)
    density=math_node(g,'MULTIPLY','V18 | negate signed distance to inside density',inside,-1)
    L.new(density,grid.inputs['Density'])
    surface=N.new('GeometryNodeVolumeToMesh');surface.name='V18 | native 3D fracture grid to closed mesh'
    surface.inputs['Resolution Mode'].default_value='Grid';surface.inputs['Threshold'].default_value=0.0;surface.inputs['Adaptivity'].default_value=0.0
    L.new(grid.outputs['Volume'],surface.inputs['Volume'])
    # Original materials + rest coords + cut-cell relief remain exactly downstream.
    L.new(surface.outputs['Mesh'],smoother.inputs['Mesh'])
    # original_grid is now unused; intentional retained unmodified source baseline.
    g['v18_geometry_contract']='Sample original body/cutter SDF at same 3D voxel positions + rest vascular field; VolumeCube iso zero; no loose tube objects.'
    g['v18_artist_notice']='All voxel sizes, tear amplitudes, and noise fields are ARTIST; no measured microscopic strawberry tissue.'
    print('V18_GROUP',tag,'nodes',len(N),'links',len(L),flush=True)

sc['v18_experiment']='3D SDF tissue cohesion vs true original live cutter, v18a control/v18b nonperiodic strain; one rest atlas; ARTIST'
sc['v18_variant']=variant
sc['v18_v12_sha256']=SOURCE_SHA
sc.frame_set(40)
ROOT.mkdir(exist_ok=True)
path=ROOT/('strawberry-v18'+variant+'-source-rest-torn-sdf.blend')
assert not path.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
summary['scene_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();summary['scene_bytes']=path.stat().st_size
(ROOT/('v18'+variant+'-build.json')).write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print('V18_BUILD_OK',json.dumps(summary),flush=True)

"""v19: physically attached rooted 3D vascular scaffold through one SDF and rest atlas.

Research only; source is SHA-pinned owner v18A (derived from original v12).
A and B contain identical image, materials, routes and GN, differing only in solid
scaffold-retention gain (0/1). No original file is overwritten.
"""
import sys, os, json, time, pathlib, hashlib, math
import bpy
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from v19_graph import make_graph,validate_graph,rasterize_graph,compact_graph

SCRIPT_DIR=pathlib.Path(__file__).resolve().parent
ROOT=pathlib.Path(os.environ.get('STRAWBERRY_V19_OUT',str(SCRIPT_DIR))).expanduser().resolve()
ROOT.mkdir(parents=True,exist_ok=True)
assert os.environ.get('STRAWBERRY_V19_BASE'), 'Provide SHA-pinned owner v18A scene via STRAWBERRY_V19_BASE'
SOURCE=pathlib.Path(os.environ['STRAWBERRY_V19_BASE']).expanduser().resolve()
SRC_SHA='a2e387a13fb12a3d023f6c9d65b23755b6889ade9ad3dc4d4cbfa45c5d96cea0'
V12_SHA='300a2bfeaa86831220657b74fe8b00d4d7ec0b42f4ffefca863d6410cbb405b7'
assert pathlib.Path(bpy.data.filepath).resolve()==SOURCE
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SRC_SHA
assert bpy.context.scene['v18_v12_sha256']==V12_SHA
assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
for name in ['strawberry-v19a-graph-only.blend','strawberry-v19b-solid-scaffold.blend']:
    assert not (ROOT/name).exists(), f'refusing overwrite: {name}'
start=time.perf_counter()
seeds=bpy.data.objects['SDF visible seeds | planar']
attr=seeds.data.attributes['achene_center']
count=len(seeds.data.vertices)
assert count%264==0
stride=count//264
anchors=np.array([attr.data[i*stride].vector[:] for i in range(264)],np.float32)
assert anchors.shape==(264,3)
segs=make_graph(anchors)
graph_validation=validate_graph(segs,anchors)
field,raster_validation=rasterize_graph(segs)
(ROOT/'v19_graph_private.json').write_text(json.dumps({'validation':graph_validation,'graph':compact_graph(segs)},indent=1,ensure_ascii=False)+'\n')
np.save(ROOT/'v19_raster_R.npy',field)
print('V19_GRAPH_PASS',json.dumps({**graph_validation,**raster_validation}),flush=True)

# REPACK R only, preserving the exact original 192^3 RGB/alpha volume and the
# existing image users in the material and Geometry Nodes.
img=bpy.data.images['SDF proof v4 | 192^3 sparse volume and continuous branches']
assert img.packed_file is not None and list(img.size)==[3072,2304]
pixels=np.empty((2304,3072,4),np.float32)
img.pixels.foreach_get(pixels.ravel())
gba_hash_before=hashlib.sha256(pixels[:,:,1:].tobytes()).hexdigest()
old_r_hash=hashlib.sha256(pixels[:,:,0].tobytes()).hexdigest()
# 12 rows x 16 cols, each tile is z-single 192^2 XY.
for z in range(192):
    row,col=divmod(z,16)
    tile=pixels[row*192:(row+1)*192,col*192:(col+1)*192,0]
    tile[:]=np.maximum(field[z],tile*.08)
assert hashlib.sha256(pixels[:,:,1:].tobytes()).hexdigest()==gba_hash_before
packed_r_hash=hashlib.sha256(pixels[:,:,0].tobytes()).hexdigest()
img.pixels.foreach_set(pixels.ravel());img.update()
img.name='V19 | rooted 264-seed graph 192^3 rest R (ARTIST)'
img['provenance']='Original Blender v12 atlas unchanged GBA; R from deterministic connected 3-D artist graph'
img['source_v12_sha256']=V12_SHA
img['graph_seed']=19011
img.pack()
assert img.packed_file is not None
# Verify two consumers in shader + two in source GN field.
mat_users=[(m.name,n.name) for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeTexImage' and n.image==img]
gn_users=[(g.name,n.name) for g in bpy.data.node_groups if g.bl_idname=='GeometryNodeTree' for n in g.nodes if n.bl_idname=='GeometryNodeImageTexture' and n.inputs['Image'].default_value==img]
assert len(mat_users)==2 and len(gn_users)==2,(mat_users,gn_users)

# Save analytic graph as a Blender curve, initially hidden in viewport/render;
# this is the editable *same underlying rooted 3-D structure* (not detached fibers
# to be rendered on top of the cut). Its numerical implicit tube field drives
# physically retained portions of the body in both SDF cut groups.
curve=bpy.data.curves.new('V19_ARTIST_RootedVascularScaffold','CURVE')
curve.dimensions='3D';curve.resolution_u=1;curve.bevel_depth=0.;curve.resolution_u=1
for seg in segs:
    poly=curve.splines.new('POLY')
    poly.points.add(len(seg['points'])-1)
    for i,p in enumerate(seg['points']): poly.points[i].co=(float(p[0]),float(p[1]),float(p[2]),1.)
obj=bpy.data.objects.new('DIAGNOSTIC | 1 root, 28 carriers, 264 achene-linked branches, 264 twigs',curve)
bpy.context.scene.collection.objects.link(obj)
obj.hide_render=True;obj.hide_set(True)
obj['role']='EDITABLE_ARTIST_SOURCE_GRAPH_DO_NOT_CLAIM_BIOLOGICAL'
obj['body_operation']='Implicit tube presence in common 192^3 rest field; not separately composited render geometry'

def math_node(g,operation,label,a=None,b=None):
    n=g.nodes.new('ShaderNodeMath');n.operation=operation;n.label=label
    for i,v in enumerate((a,b)):
        if isinstance(v,(int,float)):n.inputs[i].default_value=v
        elif v is not None:g.links.new(v,n.inputs[i])
    return n.outputs[0]

for tag in ('planar','bite'):
    g=bpy.data.node_groups['SDF cutter + rest-space | '+tag]
    N=g.nodes;L=g.links
    grid=N['V18 | rest-space fracture volume 3D']
    source=grid.inputs['Density'].links[0].from_socket
    body=N['V18 | sample source body SDF'].outputs['Value']
    cut=N['V18 | sample live cutter SDF'].outputs['Value']
    R=N['V18 | shared original vascular rest-space R'].outputs['vascular_intensity']
    # Approximate distance-to-tube from measured scalar graph field, clipped to
    # source receptacle AND to 0.9 mm on the cutter interior side. This is a
    # physically retained attached SDF tubular *volume*, not displacement noise.
    tube_strength=math_node(g,'SUBTRACT','V19 | tube implicit intensity - iso 0.25',R,.25)
    tube_signed=math_node(g,'MULTIPLY','V19 | tube signed density approx mm',tube_strength,.72)
    depth=math_node(g,'ADD','V19 | only <= 0.90 mm beyond cut',cut,.90)
    inside_original=math_node(g,'MULTIPLY','V19 | never emerge outside source skin',body,-1)
    clipped=math_node(g,'MINIMUM','V19 | graph tube inside original body',tube_signed,inside_original)
    retained=math_node(g,'MINIMUM','V19 | graph tube max protrusion',clipped,depth)
    union=math_node(g,'MAXIMUM','V19 | SDF union base + attached tubes',source,retained)
    difference=math_node(g,'SUBTRACT','V19 | solid graft difference',union,source)
    gain=N.new('ShaderNodeValue');gain.name='V19_SCAFFOLD_SOLID_GAIN';gain.label='V19 structural tube union: 0 field-only / 1 attached solids'
    gain.outputs[0].default_value=0
    delta=math_node(g,'MULTIPLY','V19 | physical fiber gain',difference,gain.outputs[0])
    result=math_node(g,'ADD','V19 | continuous SDF body + fibers',source,delta)
    L.new(result,grid.inputs['Density'])
    g['v19_hypothesis']='Single explicit rooted seed-linked graph -> common 3D atlas in rest-space -> SDF union attached fiber stubs at any original cutter pose'
    g['v19_reference']='Independent author code. Unmeasured geometry ARTIST. No Frucht node tree.'
    print('V19_GROUP',tag,len(N),'nodes',len(L),'links',flush=True)

s=bpy.context.scene
s['v19_graph_source']='One root/28 carriers/264 terminals/264 twigs from actual seed anchors, all ARTIST geometry'
s['v19_sha_v12']=V12_SHA
s['v19_original_GBA_sha256']=gba_hash_before
s['v19_original_R_sha256']=old_r_hash
s['v19_updated_R_sha256']=packed_r_hash
s['v19_graph_sha256']=raster_validation['field_sha256']
s['v19_repro_seed']=19011
s.frame_set(20)
results={'source_sha256':SRC_SHA,'source_original_v12_sha256':V12_SHA,
         'mat_users':mat_users,'GN_users':gn_users,'GBA_sha256':gba_hash_before,
         'old_R_sha256':old_r_hash,'new_R_sha256':packed_r_hash,
         'topology':graph_validation,'field':raster_validation,'build_sec':None,
         'variants':{}}
for variant,gain in [('a',0.0),('b',1.0)]:
    for tag in ('planar','bite'):
        bpy.data.node_groups['SDF cutter + rest-space | '+tag].nodes['V19_SCAFFOLD_SOLID_GAIN'].outputs[0].default_value=gain
    s['v19_variant']=variant
    dest=ROOT/('strawberry-v19'+variant+('-graph-only' if variant=='a' else '-solid-scaffold')+'.blend')
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(dest),compress=True)
    results['variants'][variant]={'gain':gain,'file':dest.name,'size_bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
    print('V19_SAVED',variant,results['variants'][variant],flush=True)
results['build_sec']=round(time.perf_counter()-start,2)
(ROOT/'v19_build.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n')
print('V19_BUILD_PASS',results['build_sec'],flush=True)

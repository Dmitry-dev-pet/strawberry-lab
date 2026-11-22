"""Strawberry Lab v11 — independent directional wet-fiber cut lookdev (ARTIST).
Source v10's editable SDF cutter and 192^3 atlas, no Frucht nodes/assets.
ONE hypothesis: anisotropic physical cut-cell relief + sparse fiber color + localized microfilm.
"""
import bpy,os,hashlib,time,json
from pathlib import Path
P=Path(os.environ.get("STRAWBERRY_SDF_OUT",str(Path(__file__).resolve().parents[2]/'build/sdf-vertical-slice')))
SRC=P/"strawberry-sdf-vertical-slice-v10-ragged-bite.blend"
DST=P/"strawberry-sdf-vertical-slice-v11-wet-fibers.blend"
assert SRC.is_file() and not DST.exists(),"Missing v10 or refusing overwrite v11"
t0=time.monotonic()
bpy.ops.wm.open_mainfile(filepath=str(SRC),use_scripts=False)
sc=bpy.context.scene
assert bpy.data.objects.get('SDF cutter | spherical bite (move or scale)')
atlas=bpy.data.images.get('SDF proof v4 | 192^3 sparse volume and continuous branches')
assert atlas and atlas.packed_file and list(atlas.size)==[3072,2304]
for tag in ('planar','bite'):
 g=bpy.data.node_groups['SDF cutter + rest-space | '+tag]
 v=next(n for n in g.nodes if n.bl_idname=='ShaderNodeTexVoronoi')
 assert v.feature=='DISTANCE_TO_EDGE' and v.voronoi_dimensions=='3D'
 inp=v.inputs['Vector']
 assert inp.is_linked
 upstream=inp.links[0].from_socket
 # Stretch micro cells longitudinally: small transverse spacing / longer z dimension.
 anis=g.nodes.new('ShaderNodeVectorMath')
 anis.operation='MULTIPLY'
 anis.label='V11 ARTIST | longitudinal elongated cut cells, same rest space'
 anis.name='V11 | elongate cut cell field'
 anis.inputs[1].default_value=(1.55,1.55,0.48)
 g.links.new(upstream,anis.inputs[0])
 g.links.new(anis.outputs['Vector'],inp)
 # Preserve same SDF and existing local geometric displacement.
 assert g.nodes.get('V8 | actual cut cell pillows')
 g['v11_hypothesis']='Anisotropic cut-face 3D Voronoi; spatial 192^3 vascular field unchanged'
 print('V11_CUT_ANISOTROPY',tag,tuple(anis.inputs[1].default_value),flush=True)

mat=bpy.data.materials['SDF proof v8 | cut cells flattened on SAME vessel atlas']
mat.name='SDF v11 | directional fibers and localized wetness (ARTIST)'
nodes=mat.node_tree.nodes
ln=mat.node_tree.links
bs=next(n for n in nodes if n.bl_idname=='ShaderNodeBsdfPrincipled')
sep=next(n for n in nodes if n.bl_idname=='ShaderNodeSeparateColor')
prev=nodes['Math.033']
assert prev.operation=='MULTIPLY' and prev.inputs[0].is_linked
assert prev.inputs[0].links[0].from_node==sep
# Sharpen only the visible color response to the old vascular intensity field.
r=nodes.new('ShaderNodeMapRange')
r.label='V11 ARTIST | suppress blurred vascular halos, keep strand cores'
r.clamp=True;r.interpolation_type='SMOOTHSTEP'
r.inputs['From Min'].default_value=.10
r.inputs['From Max'].default_value=.50
r.inputs['To Min'].default_value=0.
r.inputs['To Max'].default_value=.95
ln.new(sep.outputs['Red'],r.inputs['Value'])
ln.new(r.outputs['Result'],prev.inputs[0])
# New fine directional film normal: 3D rest-space, not camera-projected.
pos=next(n for n in nodes if n.bl_idname=='ShaderNodeAttribute' and n.attribute_name=='fruit_rest')
squeeze=nodes.new('ShaderNodeVectorMath')
squeeze.operation='MULTIPLY'
squeeze.label='V11 | narrow wet striations in fruit rest space'
squeeze.inputs[1].default_value=(1.25,1.25,.18)
ln.new(pos.outputs['Vector'],squeeze.inputs[0])
noise=nodes.new('ShaderNodeTexNoise')
noise.noise_dimensions='3D'
noise.inputs['Scale'].default_value=4.2
noise.inputs['Detail'].default_value=2.0
noise.inputs['Roughness'].default_value=.52
ln.new(squeeze.outputs['Vector'],noise.inputs['Vector'])
bump=nodes.new('ShaderNodeBump')
bump.label='V11 wet grooves | material normals, not claimed cell solids'
bump.inputs['Strength'].default_value=.15
bump.inputs['Distance'].default_value=.009
ln.new(noise.outputs['Fac'],bump.inputs['Height'])
oldbump=nodes['Bump']
assert oldbump.outputs['Normal'].is_linked
ln.new(oldbump.outputs['Normal'],bump.inputs['Normal'])
ln.new(bump.outputs['Normal'],bs.inputs['Normal'])
# Local wet pockets using the same 3D noise: lower roughness at glistening micro-zones.
rough=nodes['Map Range.001']
assert rough.outputs['Result'].is_linked
rough.inputs['To Min'].default_value=.28
rough.inputs['To Max'].default_value=.47
ramp=nodes.new('ShaderNodeMapRange')
ramp.clamp=True;ramp.interpolation_type='SMOOTHSTEP'
ramp.inputs['From Min'].default_value=.35
ramp.inputs['From Max'].default_value=.7
ramp.inputs['To Min'].default_value=.0
ramp.inputs['To Max'].default_value=.10
ln.new(noise.outputs['Fac'],ramp.inputs['Value'])
math=nodes.new('ShaderNodeMath');math.operation='SUBTRACT'
ln.new(rough.outputs['Result'],math.inputs[0]);ln.new(ramp.outputs['Result'],math.inputs[1])
lo=nodes.new('ShaderNodeMath');lo.operation='MAXIMUM';lo.inputs[1].default_value=.16
ln.new(math.outputs[0],lo.inputs[0]);ln.new(lo.outputs[0],bs.inputs['Roughness'])
bs.inputs['Subsurface Weight'].default_value=.17
bs.inputs['Coat Weight'].default_value=.11
bs.inputs['Coat Roughness'].default_value=.22
sc['v11_hypothesis']='On v10 only: elongated shallow GN cut cells + sharpened sparse fiber shader response + rest-space microfilm normals/roughness. Base 192cubed atlas and SDF cutter unchanged.'
sc['v11_biology']='ARTIST, not measured biological fibers or histology'
sc['v11_source']='independent v10 derived from own v8; original private Frucht film only visual reference'
sc.frame_set(20)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(DST))
doc={'version':'v11-wet-fibers','parent':'v10-ragged-bite','source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'dest_sha256':hashlib.sha256(DST.read_bytes()).hexdigest(),'input_3d_atlas_name':atlas.name,'unchanged_atlas_pixels':True,'axis_scale':[1.55,1.55,.48],'microfilm_scale':[1.25,1.25,.18],'visual_status':'UNREVIEWED','biology':'ARTIST','build_seconds':round(time.monotonic()-t0,2)}
(P/'v11-build.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
print('V11_BUILD='+json.dumps(doc,ensure_ascii=False),flush=True)

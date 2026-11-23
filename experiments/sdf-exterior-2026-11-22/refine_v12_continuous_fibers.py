"""v12 restrained directional wetness. Restore continuous original 3D fibers.
Child of v11 (which remains intact), and v10/v8 unchanged. ARTIST.
"""
import bpy,hashlib,json,os,time
from pathlib import Path
P=Path(os.environ.get("STRAWBERRY_SDF_OUT",str(Path(__file__).resolve().parents[2]/'build/sdf-vertical-slice')))
SRC=P/"strawberry-sdf-vertical-slice-v11-wet-fibers.blend"
DST=P/"strawberry-sdf-vertical-slice-v12-continuous-wet.blend"
assert SRC.is_file() and not DST.exists()
start=time.monotonic()
bpy.ops.wm.open_mainfile(filepath=str(SRC),use_scripts=False)
for typ in ("planar","bite"):
 g=bpy.data.node_groups['SDF cutter + rest-space | '+typ]
 n=g.nodes['V11 | elongate cut cell field']
 assert n.operation=='MULTIPLY'
 n.inputs[1].default_value=(1.24,1.24,.67)
mat=bpy.data.materials['SDF v11 | directional fibers and localized wetness (ARTIST)']
mat.name='SDF v12 | continuous vascular fibers, restrained wetness (ARTIST)'
n=mat.node_tree.nodes;ln=mat.node_tree.links
rsp=next(x for x in n if x.bl_idname=='ShaderNodeMapRange' and x.label.startswith('V11 ARTIST | suppress'))
sep=n['Separate Color']
mult=n['Math.033']
assert mult.inputs[0].links[0].from_node==rsp
ln.new(sep.outputs['Red'],mult.inputs[0])
n.remove(rsp)
wetbump=next(x for x in n if x.bl_idname=='ShaderNodeBump' and x.label.startswith('V11 wet grooves'))
wetbump.inputs['Strength'].default_value=.075
wetbump.inputs['Distance'].default_value=.007
wet_ramp=next(x for x in n if x.bl_idname=='ShaderNodeMapRange' and x.inputs['To Max'].default_value>.099 and x.inputs['To Max'].default_value<.101 and x.inputs['From Min'].default_value>.34)
wet_ramp.inputs['To Max'].default_value=.045
rough=n['Map Range.001']
rough.inputs['To Min'].default_value=.33
rough.inputs['To Max'].default_value=.49
bs=n['Principled BSDF']
bs.inputs['Coat Weight'].default_value=.09
bs.inputs['Coat Roughness'].default_value=.26
bs.inputs['Subsurface Weight'].default_value=.16
sc=bpy.context.scene
sc['v12_hypothesis']='Preserve continuous v10 192^3 vascular R, mild anisotropic GN Voronoi and restrained 3D microfilm'
sc['v12_biology']='ARTIST, scientific anatomy not validated'
sc.frame_set(20)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(DST))
receipt={'parent':'v11','source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'dest_sha256':hashlib.sha256(DST.read_bytes()).hexdigest(),'biology':'ARTIST','seconds':round(time.monotonic()-start,2),'status':'unreviewed'}
(P/'v12-build.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print('V12_BUILD='+json.dumps(receipt),flush=True)

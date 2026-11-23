"""One original, bounded PR49 material hypothesis: existing native 3D tissue domains -> SSS.
A=0 exactly original Principled SSS 0.08; B=1 variable sub-surface mixing.
No copied Frucht nodes, new geometry, atlas changes, or new random field.
"""
import bpy, argparse, sys, hashlib, json
from pathlib import Path
SRC_SHA='0b79e33b0725f807524061b1afe79671f4fcf1c6b5c429bd8203cec8d6a21bd2'
BODY='Receptacle | canonical PR29 hull'; CAP='SDF | inherited 150^3 tissue + own multiscale wetness'
A='LIVE | ORIGINAL V0 native RGB volume atlas (150^3)'
parser=argparse.ArgumentParser();parser.add_argument('--source',required=True,type=Path);parser.add_argument('--outdir',required=True,type=Path)
a=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);source=a.source.resolve();out=a.outdir.resolve()
assert source.is_file() and hashlib.sha256(source.read_bytes()).hexdigest()==SRC_SHA and not out.exists()
assert bpy.app.version[:2]==(5,2)
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
sc=bpy.context.scene;body=sc.objects[BODY];material=bpy.data.materials[CAP];g=material.node_tree
assert len([o for o in sc.objects if o.get('role')=='achene'])==264
assert len(g.nodes)==82
bs=next(n for n in g.nodes if n.type=='BSDF_PRINCIPLED');ss=bs.inputs['Subsurface Weight']
assert not ss.is_linked and abs(ss.default_value-.08)<1e-5
assert abs(bs.inputs['Subsurface Scale'].default_value-.012)<1e-5
assert bs.inputs['Base Color'].links[0].from_node.name == 'Hue/Saturation/Value'
assert g.nodes.get('MATERIAL V20 | live optical response gain') is None
orig_image_sha=hashlib.sha256(bytes(bpy.data.images[A].packed_file.data)).hexdigest()
raw_mesh_hash=hashlib.sha256(repr([tuple(v.co) for v in body.data.vertices]).encode()).hexdigest()
original_link_signatures=sorted((l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in g.links)

def node(kind,name):
 n=g.nodes.new(kind);n.name=n.label=name;return n

def wire(out,inp):g.links.new(out,inp)

def mathn(op,name,left,right=None):
 n=node('ShaderNodeMath',name);n.operation=op
 for i,v in enumerate([left,right]):
  if v is None:continue
  if isinstance(v,(int,float)):n.inputs[i].default_value=v
  else:wire(v,n.inputs[i])
 return n.outputs[0]

body['sdf_optical_gain']=0.;body.id_properties_ui('sdf_optical_gain').update(min=0.,max=1.,description='ARTIST 0 = current SSS 0.08; 1 = spatial cell-aware SSS, same GN fields, same scene/material except SSS weight')
gain=node('ShaderNodeValue','MATERIAL V20 | live optical response gain');gain.outputs[0].default_value=0.
d=gain.outputs[0].driver_add('default_value').driver;v=d.variables.new();v.name='control';v.targets[0].id=body;v.targets[0].data_path='["sdf_optical_gain"]';d.expression='control'
cell=node('ShaderNodeAttribute','MATERIAL V20 | same real cell-suppression field');cell.attribute_name='sdf_v20_cell_suppression'
vascular=node('ShaderNodeAttribute','MATERIAL V20 | same real vascular core');vascular.attribute_name='sdf_v20_core'
# Spatially coherent *artist* optical hypothesis: low SSS close to existing R paths,
# more SSS in the surrounding red cell tissue. Exactly one user gain drives the delta.
vascular_fade=mathn('SUBTRACT','MATERIAL V20 | do not wash bright vascular core',1.,mathn('MULTIPLY','MATERIAL V20 | core attenuation ARTIST 0.8',vascular.outputs['Fac'],.8))
spatial=mathn('MULTIPLY','MATERIAL V20 | shared 3D cell-domain optical response',cell.outputs['Fac'],vascular_fade)
on=mathn('MULTIPLY','MATERIAL V20 | one-factor A B',spatial,gain.outputs[0])
extra=mathn('MULTIPLY','MATERIAL V20 | bounded SSS delta ARTIST 0.20',on,.20)
final=mathn('ADD','MATERIAL V20 | SSS weight existing 0.08 + delta',.08,extra)
wire(final,ss)
# Distinct from new mesh, vectors, material noise; preserve old shader links and original file.
assert len(g.nodes)==82+len([n for n in g.nodes if n.name.startswith('MATERIAL V20 |')])
for link in original_link_signatures:assert link in sorted((l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in g.links)
assert bs.inputs['Base Color'].links[0].from_node.name=='Hue/Saturation/Value'
assert len([n for n in g.nodes if n.type=='TEX_IMAGE'])==2
assert hashlib.sha256(bytes(bpy.data.images[A].packed_file.data)).hexdigest()==orig_image_sha
assert hashlib.sha256(repr([tuple(v.co) for v in body.data.vertices]).encode()).hexdigest()==raw_mesh_hash
out.mkdir(parents=True)
receipts=[]
for tag,value in [('A',0.),('B',1.)]:
 body['sdf_optical_gain']=value;body.update_tag();sc.frame_set(sc.frame_current);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
 p=out/f'cell-optical-{tag}.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(p),compress=True)
 receipts.append({'variant':tag,'gain':value,'scene_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
record={'status':'BUILT_A_B_UNVERIFIED','input_sha256':SRC_SHA,'blender':bpy.app.version_string,'source_material':CAP,'original_sss_weight':.08,'added_artist_sss_weight_max':.20,'ss_scale_BU':.012,'ss_scale_mm':.012*sc.unit_settings.scale_length*1000,'original_packed_atlas_sha256':orig_image_sha,'raw_mesh_hash':raw_mesh_hash,'original_mat_nodes':82,'new_mat_nodes':len(g.nodes),'control':'sdf_optical_gain','source_attributes':['sdf_v20_core','sdf_v20_cell_suppression'],'other_principled_sockets_unchanged':True,'notes':'ONLY Subsurface Weight now varies; no color/radius/geometry/light modifications. All values ARTIST.','scenes':receipts}
(out/'build.json').write_text(json.dumps(record,indent=2)+'\n');print('OPTICAL_AB_BUILT',json.dumps(receipts),flush=True)

"""Independent saved scene provenance: original body, vascular & tissue grids, shaders and seeds unchanged."""
from pathlib import Path
import bpy,sys,hashlib,json,argparse,numpy as np
p=argparse.ArgumentParser();p.add_argument('--source',required=True,type=Path);p.add_argument('--scene-dir',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert not a.out.exists()
assert hashlib.sha256(a.source.read_bytes()).hexdigest()=='4732b465b103f9a0b4ab262dfeae51e26a8865aa586c3779d472d86eed845399'
results={}
for label,path in [('source',a.source),('A',a.scene_dir/'torn-A.blend'),('B',a.scene_dir/'torn-B.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(path.resolve()),use_scripts=False);assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
 s=bpy.context.scene;b=s.objects['Receptacle | canonical PR29 hull'];coords=np.empty(len(b.data.vertices)*3,np.float32);b.data.vertices.foreach_get('co',coords)
 images={}
 for name in ['LIVE | ORIGINAL V0 native RGB volume atlas (150^3)','V20 bridge | seed101 core R halo G 192^3 ARTIST']:
  img=bpy.data.images[name];images[name]={'sha256':hashlib.sha256(bytes(img.packed_file.data)).hexdigest(),'width':img.size[0],'height':img.size[1]}
 mat=bpy.data.materials['SDF | inherited 150^3 tissue + own multiscale wetness'];gn=b.modifiers[0].node_group
 result={'scene_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'raw_mesh_sha256':hashlib.sha256(coords.tobytes()).hexdigest(),'source_vertex_count':len(b.data.vertices),'seeds':sum(o.get('role')=='achene' for o in s.objects),'images':images,'material_nodes':len(mat.node_tree.nodes),'geometry_nodes':len(gn.nodes),'blender':bpy.app.version_string}
 if label!='source':
  result['tear_gain']=float(b['sdf_torn_extrude_gain']);assert result['geometry_nodes']==112
  result['extrude_node']=gn.nodes['TEAR | actual connected tear flaps (not a normal bump)'].bl_idname
 results[label]=result
for v in ['A','B']:
 for k in ['raw_mesh_sha256','source_vertex_count','seeds','images','material_nodes']:
  assert results[v][k]==results['source'][k],(v,k)
assert results['A']['tear_gain']==0 and results['B']['tear_gain']==1
assert results['source']['seeds']==264
rec={'status':'PASS_BYTE_IDENTICAL_RAW_MESH_AND_ATLASES_A_B_SOURCE','results':results}
a.out.write_text(json.dumps(rec,indent=2)+'\n');print('TORN_PROVENANCE_PASS',json.dumps({x:{'scene_sha':v['scene_sha256'],'mesh_sha':v['raw_mesh_sha256'],'mat_nodes':v['material_nodes'],'gn_nodes':v['geometry_nodes']} for x,v in results.items()}))

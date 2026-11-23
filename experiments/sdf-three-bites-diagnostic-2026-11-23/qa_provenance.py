"""Independent saved .blend provenance audit: A vs C source body, atlases, shader, achene population."""
import bpy,json,hashlib,argparse,numpy as np
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--scene-a',required=True,type=Path);p.add_argument('--scene-c',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
a=p.parse_args(__import__('sys').argv[__import__('sys').argv.index('--')+1:]);assert not a.out.exists()
r={}
for key,file in [('A',a.scene_a),('C',a.scene_c)]:
 assert file.is_file();bpy.ops.wm.open_mainfile(filepath=str(file.resolve()),use_scripts=False);assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
 s=bpy.context.scene;fruit=s.objects['Receptacle | canonical PR29 hull'];cut=s.objects['SDF | editable sphere bite'];seeds=[o for o in s.objects if o.get('role')=='achene']
 coords=np.zeros((len(fruit.data.vertices),3),np.float32);fruit.data.vertices.foreach_get('co',coords.ravel())
 mats=bpy.data.materials['SDF | inherited 150^3 tissue + own multiscale wetness']
 packed={name:hashlib.sha256(bytes(bpy.data.images[name].packed_file.data)).hexdigest() for name in ['LIVE | ORIGINAL V0 native RGB volume atlas (150^3)','V20 bridge | seed101 core R halo G 192^3 ARTIST']}
 src_seeds=[]
 for seed in sorted(seeds,key=lambda x:x.name):
  h=hashlib.sha256();h.update(seed.name.encode());h.update(repr([tuple(v.co) for v in seed.data.vertices]).encode());src_seeds.append(h.digest())
 r[key]={'scene_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'body_source_xyz_sha256':hashlib.sha256(coords.tobytes()).hexdigest(),'tissue_atlases_sha256':packed,'original_cut_shader_nodes':len(mats.node_tree.nodes),'body_GN_nodes':len(fruit.modifiers[0].node_group.nodes),'achene_objects':len(seeds),'achene_source_meshes_sha256':hashlib.sha256(b''.join(src_seeds)).hexdigest(),'seed_GN_node_count':len(seeds[0].modifiers[0].node_group.nodes),'cut_mesh_vertices':len(cut.data.vertices),'cut_mesh_faces':len(cut.data.polygons)}
for name in ['body_source_xyz_sha256','tissue_atlases_sha256','original_cut_shader_nodes','body_GN_nodes','achene_objects','achene_source_meshes_sha256']:assert r['A'][name]==r['C'][name],name
assert r['A']['seed_GN_node_count']==21 and r['C']['seed_GN_node_count']==32
r['status']='PASS_UNCHANGED_SOURCE_GEOMETRY_ATLASES_CUT_SHADER_AND_SEEDS';a.out.write_text(json.dumps(r,indent=2));print('PROVENANCE_PASS',json.dumps({k:{'body':v['body_source_xyz_sha256'],'atlas':v['tissue_atlases_sha256'],'seeds':v['achene_objects'],'seed_nodes':v['seed_GN_node_count']} for k,v in r.items() if k in ('A','C')}))

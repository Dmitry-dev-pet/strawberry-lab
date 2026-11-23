"""Independent saved-scene QA for one shared GN cell-interior response + material A/B.
Independent from the builder, autoexec disabled. Measures actual evaluated SDF meshes.
"""
import bpy,bmesh,numpy as np,json,hashlib,resource,sys,time
from pathlib import Path
from math import radians
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--scene-dir',required=True,type=Path);parser.add_argument('--out',required=True,type=Path)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);SC=args.scene_dir.resolve();OUT=args.out.resolve()
assert not OUT.exists()
mm=22.22222276
poses=[('whole',0,.32,False,False),('plane',1,.32,False,False),('oblique',1,.32,True,False),('sphere',2,.32,False,False),('edge',2,.32,False,True),('plane_fine',1,.20,False,False),('edge_fine',2,.20,False,True)]
report={'blender':bpy.app.version_string,'test':'actual evaluated SDF A/B with identical source and mesh, different shared cell field response','states':[],'variants':{},'expected_A_source_sha256':{'whole':'459c8027ec1ff1aa181cfafb0bea250ca8bb5ddd1b708a37b74c1087b6ed6263','plane':'a165e4d603ea0e5238ca81c65a43f28d2de688e6b285df6d743c9e79d940955c','edge':'af454e777ea6f529deaaec7bf66bf03ca5b842a02b3e3d8fdc16610146a9da39','plane_fine':'15cb6cd0ad6a9ab7135ad1b3538d92bc5831a3f969c7e13e2fdf21ce136f655c','edge_fine':'5fd551e73f40eba1b43f2dcf636d15774c73626e4c0fd2d4839b71a64ebac3da'}}
records={}
for variant in ('A','B'):
 path=SC/f'cell-coherent-{variant}.blend';bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False);assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
 scene=bpy.context.scene;b=scene.objects['Receptacle | canonical PR29 hull'];ng=b.modifiers[0].node_group;mat=bpy.data.materials['SDF | inherited 150^3 tissue + own multiscale wetness'];sg=mat.node_tree
 assert len(ng.nodes)==87 and len(sg.nodes)==89 and len([x for x in scene.objects if x.get('role')=='achene'])==264
 assert ng.nodes['CELL COHERENCE | store common material+shape field'].inputs['Name'].default_value=='sdf_cell_lobe_response'
 assert sg.nodes['CELL COHERENCE | exact GN cell lobe response'].attribute_name=='sdf_cell_lobe_response'
 bs=next(n for n in sg.nodes if n.type=='BSDF_PRINCIPLED');assert bs.inputs['Base Color'].links[0].from_node.name=='CELL COHERENCE | original warm cell pulp blend'
 assert bs.inputs['Roughness'].links[0].from_node.name.startswith('CELL COHERENCE | preserve source roughness add subtle cell')
 assert abs(bs.inputs['Subsurface Weight'].default_value-.08)<1e-5
 assert abs(b['sdf_cell_surface_gain']-(0 if variant=='A' else 1))<1e-5
 original_pack=hashlib.sha256(bytes(bpy.data.images['LIVE | ORIGINAL V0 native RGB volume atlas (150^3)'].packed_file.data)).hexdigest()
 rawarr=np.array([tuple(v.co) for v in b.data.vertices],np.float32);raw=hashlib.sha256(rawarr.tobytes()).hexdigest()
 report['variants'][variant]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'original_pack':original_pack,'raw_hull':raw,'source_mesh_vertices':len(b.data.vertices),'gn_nodes':len(ng.nodes),'shader_nodes':len(sg.nodes)}
 rec=[]
 for label,mode,voxel,oblique,edge in poses:
  start=time.monotonic();b['sdf_mode']=mode;b['sdf_voxel_mm']=voxel;b['sdf_tissue_gain']=1;b['sdf_use_broad_halo']=1
  plane=scene.objects['SDF | editable plane halfspace'];sphere=scene.objects['SDF | editable sphere bite']
  plane.location=(0,.08 if oblique else 0,0);plane.rotation_euler=(radians(29) if oblique else 0,0,radians(32) if oblique else 0)
  sphere.location=(.82,-.70,-.42) if edge else (.60,-.70,.42);sphere.scale=(1.04,)*3 if edge else (.65,)*3
  b.update_tag();scene.frame_set(scene.frame_current);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
  evaluated=b.evaluated_get(dg);m=evaluated.to_mesh();N=len(m.vertices)
  xyz=np.zeros((N,3),np.float32);m.vertices.foreach_get('co',xyz.ravel());assert np.isfinite(xyz).all()
  sha=hashlib.sha256(xyz.tobytes()).hexdigest()
  attrs={}
  for name in ['sdf_rest_position','sdf_v20_core','sdf_v20_halo','sdf_v20_cell_suppression','sdf_cell_lobe_response','sdf_v20_height_mm']:
   obj=m.attributes.get(name);assert obj,name
   a=np.zeros((N,3),np.float32) if obj.data_type=='FLOAT_VECTOR' else np.zeros(N,np.float32)
   obj.data.foreach_get('vector' if obj.data_type=='FLOAT_VECTOR' else 'value',a.ravel())
   attrs[name]=a
  assert attrs['sdf_cell_lobe_response'].min()>=-1e-4 and attrs['sdf_cell_lobe_response'].max()<=1.0001
  assert np.all(attrs['sdf_v20_halo']>=attrs['sdf_v20_core']-1e-4)
  bm=bmesh.new();bm.from_mesh(m);bad=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);bm.free();assert bad==0 and vol>0
  indices=np.zeros(len(m.polygons),np.int32);m.polygons.foreach_get('material_index',indices);cap=int((indices==2).sum());assert (cap==0)==(mode==0)
  row={'label':label,'voxel_mm':voxel,'vertices':N,'polygons':len(m.polygons),'cap_faces':cap,'xyz_sha':sha,'attrs_sha':{k:hashlib.sha256(x.tobytes()).hexdigest() for k,x in attrs.items()},'cell_field_minmax':[float(attrs['sdf_cell_lobe_response'].min()),float(attrs['sdf_cell_lobe_response'].max())],'max_relief_height_mm':float(attrs['sdf_v20_height_mm'].max()),'nonmanifold_edges':bad,'positive_volume':vol>0,'seconds':round(time.monotonic()-start,3)}
  print('QA',variant,label,voxel,N,'cap',cap,'cellmax',round(row['cell_field_minmax'][1],5),'maxheight',round(row['max_relief_height_mm'],5),'time',row['seconds'],flush=True)
  rec.append((row,xyz,attrs));evaluated.to_mesh_clear()
 records[variant]=rec
assert report['variants']['A']['original_pack']==report['variants']['B']['original_pack']
assert report['variants']['A']['raw_hull']==report['variants']['B']['raw_hull']
for i in range(len(poses)):
 a,x,fa=records['A'][i];b,y,fb=records['B'][i];label=a['label']
 assert a['vertices']==b['vertices'] and a['polygons']==b['polygons'] and a['cap_faces']==b['cap_faces']
 assert all(a['attrs_sha'][j]==b['attrs_sha'][j] for j in ['sdf_v20_core','sdf_v20_halo','sdf_v20_cell_suppression','sdf_cell_lobe_response','sdf_rest_position'])
 delta=np.linalg.norm(y-x,axis=1)*mm
 maxd=float(delta.max());changed=int((delta>.001).sum())
 if a['cap_faces']==0:
  assert maxd==0 and changed==0
 else:
  assert .003<maxd<.057,(label,maxd)
  assert changed>200,(label,changed)
 if label in report['expected_A_source_sha256']:assert a['xyz_sha']==report['expected_A_source_sha256'][label],(label,a['xyz_sha'])
 report['states'].append({'pose':label,'voxel_mm':a['voxel_mm'],'n_vertices':a['vertices'],'cap_faces':a['cap_faces'],'A_sha':a['xyz_sha'],'B_sha':b['xyz_sha'],'max_real_geometric_difference_mm':maxd,'vertices_changed_gt_0_001mm':changed,'common_cell_field_minmax':a['cell_field_minmax'],'A_height_max_mm':a['max_relief_height_mm'],'B_height_max_mm':b['max_relief_height_mm'],'times_seconds':{'A':a['seconds'],'B':b['seconds']}})
report['status']='PASS_INDEPENDENT_CELL_GEOMETRY_AND_SHADER_SHARED_FIELD'
report['rss_kb']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
OUT.write_text(json.dumps(report,indent=2)+'\n')
print('ALL_STATES_PASS',len(report['states']),flush=True)

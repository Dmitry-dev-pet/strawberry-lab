"""Independent native geometry and material-boundary QA for pith color experiment."""
import sys,json,hashlib,resource,time
from pathlib import Path
import bpy,numpy as np,bmesh
A,B,O=map(Path,sys.argv[sys.argv.index('--')+1:]);assert A.is_file() and B.is_file() and not O.exists()
BODY='Receptacle | canonical PR29 hull';CAP='SDF | inherited 150^3 tissue + own multiscale wetness';ATTR='sdf_rest_position';IMAGE='LIVE | ORIGINAL V0 native RGB volume atlas (150^3)'
report={'status':'UNVERIFIED','blender':bpy.app.version_string,'inputs':{},'states':[]}
def load(p):
 bpy.ops.wm.open_mainfile(filepath=str(p.resolve()),use_scripts=False);assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
 s=bpy.context.scene;b=s.objects[BODY];m=bpy.data.materials[CAP];g=m.node_tree
 attr=next(n for n in g.nodes if n.type=='ATTRIBUTE' and n.attribute_name==ATTR)
 sep=g.nodes['Separate XYZ'];warp=g.nodes['ARTIST | pith-color lookup only']
 assert len(sep.inputs['Vector'].links)==1 and sep.inputs['Vector'].links[0].from_node==warp
 assert warp.inputs[0].links[0].from_node==attr
 for name in ['Own 3D wetness scale 20','Own 3D wetness scale 60','Own 3D wetness scale 150']:
  assert g.nodes[name].inputs['Vector'].links[0].from_node==attr
 img=bpy.data.images[IMAGE]
 img_sha=hashlib.sha256(bytes(img.packed_file.data)).hexdigest()
 meshes=hashlib.sha256()
 for obj in sorted((x for x in s.objects if x.type=='MESH'),key=lambda x:x.name):
  meshes.update(obj.name.encode());co=np.empty(len(obj.data.vertices)*3,np.float32);obj.data.vertices.foreach_get('co',co);meshes.update(co.tobytes())
 shape=(len([x for x in s.objects if x.get('role')=='achene']),len(b.modifiers[0].node_group.nodes),len(bpy.data.materials[CAP].node_tree.nodes))
 assert shape[0]==264 and 'sdf_v20_core' in b.modifiers[0].node_group.nodes['V20 bridge: sdf_v20_core'].inputs['Name'].default_value
 return s,b,g,{'atlas_sha256':img_sha,'raw_geometry_sha256':meshes.hexdigest(),'graph_shape':shape,'live_gain':float(b['sdf_pith_color_compact_gain'])}

def evaluate(b,s,mode,vox,edge):
 b['sdf_mode']=mode;b['sdf_voxel_mm']=vox;b['sdf_tissue_gain']=1.0;b['sdf_use_broad_halo']=1.0
 sph=s.objects['SDF | editable sphere bite'];sph.location=(.82,-.70,-.42) if edge else (.60,-.70,.42);sph.scale=(1.04,)*3 if edge else (.65,)*3
 b.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update()
 dep=bpy.context.evaluated_depsgraph_get();dep.update();ev=b.evaluated_get(dep);me=ev.to_mesh();arr=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',arr)
 bm=bmesh.new();bm.from_mesh(me);nonman=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True);bm.free()
 rec={'vertices':len(me.vertices),'coords_sha256':hashlib.sha256(arr.tobytes()).hexdigest(),'nonmanifold_edges':nonman,'positive_volume':volume>0}
 ev.to_mesh_clear();assert nonman==0 and volume>0
 return rec
allrec={}
for name,path in [('A',A),('B',B)]:
 s,b,g,entry=load(path);report['inputs'][name]={**entry,'scene_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 assert entry['live_gain']==(0 if name=='A' else 1)
 for shot,mode,vox,edge in [('whole',0,.32,False),('plane',1,.32,False),('edge_bite',2,.32,True),('plane_fine',1,.20,False),('edge_bite_fine',2,.20,True)]:
  t=time.monotonic();rec=evaluate(b,s,mode,vox,edge);allrec.setdefault(shot,{})[name]=rec;print('QA',name,shot,rec['vertices'],round(time.monotonic()-t,2),flush=True)
assert report['inputs']['A']['atlas_sha256']==report['inputs']['B']['atlas_sha256']
assert report['inputs']['A']['raw_geometry_sha256']==report['inputs']['B']['raw_geometry_sha256']
for shot,rs in allrec.items():
 assert rs['A']==rs['B'],(shot,rs)
 report['states'].append({'pose':shot,'same_geometry':True,'metrics':rs['A']})
report['status']='PASS_SHADER_COLOR_ONLY_MATCHED_GEOMETRY';report['max_rss_kb']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
O.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('QA_PASS',report['status'],'states',len(report['states']),flush=True)

"""Independent scripts-disabled QA: one pre-existing vascular field drives geometry and shader."""
import bpy,sys,hashlib,json,resource,time
from pathlib import Path
import numpy as np,bmesh
argv=sys.argv[sys.argv.index('--')+1:];A,B,O=map(Path,argv[:3]);EXPECTED_GAIN=float(argv[3]) if len(argv)>3 else 1.0
assert 0<=EXPECTED_GAIN<=1 and A.is_file() and B.is_file() and not O.exists()
BODY='Receptacle | canonical PR29 hull';MAT='SDF | inherited 150^3 tissue + own multiscale wetness';ATLAS='LIVE | ORIGINAL V0 native RGB volume atlas (150^3)';CORE='sdf_v20_core'
res={'status':'UNVERIFIED','blender':bpy.app.version_string,'scenes':{},'poses':[]}

def load(p,variant):
 bpy.ops.wm.open_mainfile(filepath=str(p.resolve()),use_scripts=False);assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
 s=bpy.context.scene;b=s.objects[BODY];m=bpy.data.materials[MAT];g=m.node_tree
 bs=next(n for n in g.nodes if n.type=='BSDF_PRINCIPLED');mix=g.nodes['V20 owned core lightens only overlapping vascular surface'];gain=g.nodes['V20 actual vascular field → material A/B gain']
 assert bs.inputs['Base Color'].links[0].from_node==mix
 assert mix.inputs[1].links[0].from_node.name=='Hue/Saturation/Value'
 att=g.nodes['V20 actual GN core R seen by cap shader'];assert att.attribute_name==CORE
 assert g.nodes['ARTIST warm vessels, core R 0.18 to 0.55'].inputs['Value'].links[0].from_node==att
 assert len(gain.outputs[0].drivers) if hasattr(gain.outputs[0],'drivers') else (gain.outputs[0].is_linked==True)
 assert b['sdf_v20_color_gain']==(0 if variant=='A' else EXPECTED_GAIN)
 assert len([n for n in g.nodes if n.type=='TEX_IMAGE'])==2
 gn=b.modifiers[0].node_group
 assert any(n.bl_idname=='GeometryNodeStoreNamedAttribute' and n.inputs['Name'].default_value==CORE for n in gn.nodes)
 raw=hashlib.sha256()
 for o in sorted([o for o in s.objects if o.type=='MESH'],key=lambda o:o.name):
  raw.update(o.name.encode());coords=np.empty(len(o.data.vertices)*3,np.float32);o.data.vertices.foreach_get('co',coords);raw.update(coords.tobytes())
 info={'scene_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_mesh_hash':raw.hexdigest(),'source_150_atlas_sha256':hashlib.sha256(bytes(bpy.data.images[ATLAS].packed_file.data)).hexdigest(),'cap_nodes':len(g.nodes),'GN_nodes':len(gn.nodes)}
 return s,b,info

def pose(s,b,name,mode,vox):
 b['sdf_mode']=mode;b['sdf_voxel_mm']=vox;b['sdf_tissue_gain']=1.;b['sdf_use_broad_halo']=1.
 if mode==2:
  sp=s.objects['SDF | editable sphere bite'];sp.location=(.82,-.70,-.42);sp.scale=(1.04,)*3
 b.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();d=bpy.context.evaluated_depsgraph_get();d.update();ev=b.evaluated_get(d);me=ev.to_mesh()
 points=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',points)
 field=np.empty(len(me.vertices),np.float32);me.attributes[CORE].data.foreach_get('value',field)
 bm=bmesh.new();bm.from_mesh(me);bad=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);bm.free()
 out={'pose':name,'vertex_count':len(me.vertices),'coords_sha256':hashlib.sha256(points.tobytes()).hexdigest(),'core_vertex_sha256':hashlib.sha256(field.tobytes()).hexdigest(),'nonmanifold_edges':bad,'positive_volume':vol>0}
 ev.to_mesh_clear();assert bad==0 and vol>0
 return out
states={}
for name,path in [('A',A),('B',B)]:
 s,b,info=load(path,name);res['scenes'][name]=info
 for tag,mode,vox in [('whole_coarse',0,.32),('plane_coarse',1,.32),('bite_edge_coarse',2,.32),('plane_fine',1,.20),('bite_edge_fine',2,.20)]:
  tm=time.monotonic();z=pose(s,b,tag,mode,vox);states.setdefault(tag,{})[name]=z
  print('SHARED_QA',name,tag,z['vertex_count'],round(time.monotonic()-tm,2),flush=True)
assert res['scenes']['A']['source_mesh_hash']==res['scenes']['B']['source_mesh_hash']
assert res['scenes']['A']['source_150_atlas_sha256']==res['scenes']['B']['source_150_atlas_sha256']
assert res['scenes']['A']['GN_nodes']==res['scenes']['B']['GN_nodes']
for tag,variants in states.items():
 assert variants['A']==variants['B'],tag
 res['poses'].append({'pose':tag,'same_body_and_core_point_attribute':True,'metrics':variants['A']})
res['status']='PASS_SHARED_VASCULAR_ATTRIBUTE_IN_SHADER_AND_BODY_UNCHANGED';res['peak_rss_kb']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
O.write_text(json.dumps(res,indent=2)+'\n');print('SHARED_COLOR_QA_PASS',len(res['poses']),flush=True)

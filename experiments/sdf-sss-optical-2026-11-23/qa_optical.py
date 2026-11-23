"""Independent native saved-scene Geometry/SSS graph audit; does not import builder."""
import bpy,bmesh,numpy as np,hashlib,json,sys,argparse,time,resource
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--scene',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--label',choices=['A','B'],required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);s=a.scene.resolve();output=a.out.resolve();assert s.is_file() and not output.exists()
bpy.ops.wm.open_mainfile(filepath=str(s),use_scripts=False);assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
scene=bpy.context.scene;b=scene.objects['Receptacle | canonical PR29 hull'];g=bpy.data.materials['SDF | inherited 150^3 tissue + own multiscale wetness'].node_tree
mat=bpy.data.materials['SDF | inherited 150^3 tissue + own multiscale wetness'];bs=next(n for n in g.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled')
assert len(g.nodes)==91 and len(b.modifiers[0].node_group.nodes)==79
assert len([x for x in scene.objects if x.get('role')=='achene'])==264
assert g.nodes['MATERIAL V20 | same real cell-suppression field'].attribute_name=='sdf_v20_cell_suppression'
assert g.nodes['MATERIAL V20 | same real vascular core'].attribute_name=='sdf_v20_core'
assert bs.inputs['Subsurface Weight'].links[0].from_node.name=='MATERIAL V20 | SSS weight existing 0.08 + delta'
assert bs.inputs['Base Color'].links[0].from_node.name=='Hue/Saturation/Value'
assert bs.inputs['Roughness'].links[0].from_node.name=='Math.059'
assert bs.inputs['Normal'].links[0].from_node.name=='Soft wet surface | shader only'
assert abs(bs.inputs['Subsurface Scale'].default_value-.012)<1e-5
assert abs(float(b['sdf_optical_gain'])-(0. if a.label=='A' else 1.))<1e-5
atlas=bpy.data.images['LIVE | ORIGINAL V0 native RGB volume atlas (150^3)'];saved_image_sha=hashlib.sha256(bytes(atlas.packed_file.data)).hexdigest()
raw=hashlib.sha256(repr([tuple(v.co) for v in b.data.vertices]).encode()).hexdigest()
record={'status':'UNVERIFIED','label':a.label,'scene_sha256':hashlib.sha256(s.read_bytes()).hexdigest(),'source_mesh_sha256':raw,'packed_150_sha256':saved_image_sha,'blender':bpy.app.version_string,'gain':float(b['sdf_optical_gain']),'principled':{'base_color_upstream':bs.inputs['Base Color'].links[0].from_node.name,'roughness_upstream':bs.inputs['Roughness'].links[0].from_node.name,'normal_upstream':bs.inputs['Normal'].links[0].from_node.name,'ss_scale_BU':float(bs.inputs['Subsurface Scale'].default_value),'sss_socket_upstream':bs.inputs['Subsurface Weight'].links[0].from_node.name},'states':[]}
plane=scene.objects['SDF | editable plane halfspace'];sphere=scene.objects['SDF | editable sphere bite'];unit_mm=scene.unit_settings.scale_length*1000
for vox,mode,oblique,edge,tag in [(.32,0,False,False,'whole'),(.32,1,False,False,'plane'),(.32,1,True,False,'plane-oblique'),(.32,2,False,False,'bite'),(.32,2,False,True,'bite-edge'),(.20,1,False,False,'plane'),(.20,2,False,True,'bite-edge')]:
 start=time.monotonic();b['sdf_voxel_mm']=vox;b['sdf_mode']=mode;b['sdf_tissue_gain']=1.;b['sdf_use_broad_halo']=1.
 plane.location=(0,.08 if oblique else 0,0);plane.rotation_euler=(np.deg2rad(29) if oblique else 0,0,np.deg2rad(32) if oblique else 0)
 sphere.location=(.82,-.70,-.42) if edge else (.60,-.70,.42);sphere.scale=(1.04,)*3 if edge else (.65,)*3
 b.update_tag();scene.frame_set(scene.frame_current);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update();ob=b.evaluated_get(dg);me=ob.to_mesh()
 n=len(me.vertices);coords=np.empty(n*3,np.float32);me.vertices.foreach_get('co',coords)
 field={}
 for key in ['sdf_v20_core','sdf_v20_halo','sdf_v20_cell_suppression','sdf_v20_height_mm']:
  val=np.empty(n,np.float32);me.attributes[key].data.foreach_get('value',val);field[key]=val
 import math
 vals=.08+.20*float(b['sdf_optical_gain'])*field['sdf_v20_cell_suppression']*(1.-.8*field['sdf_v20_core'])
 assert np.isfinite(vals).all() and vals.min()>=.0799 and vals.max()<.281
 bm=bmesh.new();bm.from_mesh(me);bad=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);bm.free();assert bad==0 and vol>0
 material=np.empty(len(me.polygons),np.int32);me.polygons.foreach_get('material_index',material);facecap=int((material==2).sum())
 if mode==0:assert facecap==0
 else:assert facecap>1000
 r={'name':tag,'voxel_mm':vox,'body_verts':n,'body_faces':len(me.polygons),'cap_faces':facecap,'body_coords_sha256':hashlib.sha256(coords.tobytes()).hexdigest(),'core_attr_sha256':hashlib.sha256(field['sdf_v20_core'].tobytes()).hexdigest(),'cell_attr_sha256':hashlib.sha256(field['sdf_v20_cell_suppression'].tobytes()).hexdigest(),'nonmanifold_edges':bad,'positive_volume':bool(vol>0),'estimated_sss_weight_from_point_attributes':{'min':float(vals.min()),'max':float(vals.max()),'mean':float(vals.mean()),'nonuniform':bool(vals.max()-vals.min()>.005)},'seconds':round(time.monotonic()-start,3)}
 if mode and a.label=='B':assert r['estimated_sss_weight_from_point_attributes']['nonuniform']
 record['states'].append(r);print('OPTICAL_QA',a.label,vox,tag,n,'ss min/max',round(vals.min(),3),round(vals.max(),3),'s',r['seconds'],flush=True);ob.to_mesh_clear()
assert saved_image_sha==hashlib.sha256(bytes(atlas.packed_file.data)).hexdigest()
record['status']='PASS_OPTICAL_AB_NATIVE_GEOMETRY_AND_SSS_LINK_TESTED_STATES';record['peak_rss_kb']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
output.write_text(json.dumps(record,indent=2)+'\n');print('OPTICAL_QA_PASS',a.label,len(record['states']),flush=True)

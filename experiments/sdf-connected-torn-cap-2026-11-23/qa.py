"""Independent saved-scene native mesh QA for physically attached cap extrusions."""
import bpy,bmesh,numpy as np,sys,json,hashlib,resource,time,argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--scene',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--poses',nargs='+',default=['whole','plane','edge'],choices=['whole','plane','oblique','bite','edge','edge-fine','plane-fine']);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
assert a.scene.is_file() and not a.out.exists()
bpy.ops.wm.open_mainfile(filepath=str(a.scene.resolve()),use_scripts=False)
assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
s=bpy.context.scene;body=s.objects['Receptacle | canonical PR29 hull'];gn=body.modifiers[0].node_group
assert any(n.name=='TEAR | actual connected tear flaps (not a normal bump)' and n.mode=='FACES' for n in gn.nodes)
rep={'scene_sha256':hashlib.sha256(a.scene.read_bytes()).hexdigest(),'gain':float(body['sdf_torn_extrude_gain']),'blender':bpy.app.version_string,'poses':[]}
for pose in a.poses:
 start=time.monotonic();bmode=0 if pose=='whole' else 1 if pose.startswith('plane') or pose=='oblique' else 2;voxel=.20 if pose.endswith('fine') else .32
 body['sdf_mode']=bmode;body['sdf_voxel_mm']=voxel;body['sdf_tissue_gain']=1.;body['sdf_use_broad_halo']=1.;body['sdf_cell_surface_gain']=1.
 plane=s.objects['SDF | editable plane halfspace'];sphere=s.objects['SDF | editable sphere bite'];oblique=pose=='oblique';plane.location=(0,.08 if oblique else 0,0);plane.rotation_euler=(np.deg2rad(29) if oblique else 0,0,np.deg2rad(32) if oblique else 0)
 if bmode==2:
  edge=pose.startswith('edge');sphere.location=(.82,-.70,-.42) if edge else (.60,-.70,.42);sphere.scale=(1.04,)*3 if edge else (.65,)*3
 body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update();ev=body.evaluated_get(dg);m=ev.to_mesh()
 n=len(m.vertices);x=np.empty(n*3,np.float32);m.vertices.foreach_get('co',x);x=x.reshape(-1,3);idx=np.empty(len(m.polygons),np.int32);m.polygons.foreach_get('material_index',idx)
 a_candidate=m.attributes.get('sdf_torn_candidate');assert a_candidate is not None and a_candidate.domain=='FACE';v=np.empty(len(m.polygons),np.bool_);a_candidate.data.foreach_get('value',v)
 bm=bmesh.new();bm.from_mesh(m)
 bad=sum(not e.is_manifold for e in bm.edges);vol=float(bm.calc_volume(signed=True));minarea=float(min(f.calc_area() for f in bm.faces))
 seen=set();components=0
 for vert in bm.verts:
  if vert.index in seen:continue
  components+=1;pending=[vert];seen.add(vert.index)
  while pending:
   current=pending.pop()
   for ed in current.link_edges:
    nb=ed.other_vert(current)
    if nb.index not in seen:seen.add(nb.index);pending.append(nb)
 bm.free()
 rec={'pose':pose,'voxel_mm':voxel,'verts':n,'faces':len(m.polygons),'cap_faces':int((idx==2).sum()),'candidate_faces':int(v.sum()),'xyz_sha':hashlib.sha256(x.tobytes()).hexdigest(),'nonmanifold_edges':bad,'connected_components':components,'signed_volume_BU3':vol,'min_face_area_BU2':minarea,'elapsed_sec':round(time.monotonic()-start,3)}
 print('TORN_QA',json.dumps(rec),flush=True)
 assert bad==0 and components==1 and vol>0 and minarea>1e-14,rec
 rep['poses'].append(rec);ev.to_mesh_clear()
rep['rss_kb']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
rep['status']='PASS_CLOSED_TESTED_POSES'
a.out.write_text(json.dumps(rep,indent=2)+'\n')

"""Independent measured saved-scene QA for closed vascular-anchored menisci A/B/C.

No source scripts executed in loaded scenes; direct Blender dependency graph and BVH.
This is not proof of physical fluid dynamics, radiometry or arbitrary cutter poses.
"""
from pathlib import Path
import bpy,bmesh,hashlib,sys,argparse,json,time,resource
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import numpy as np

P=argparse.ArgumentParser();P.add_argument('a',type=Path);P.add_argument('b',type=Path);P.add_argument('c',type=Path);P.add_argument('--voxel',type=float,required=True);P.add_argument('--out',type=Path,required=True);P.add_argument('--variants',nargs='+',choices=['A','B','C'],default=['A','B','C']);P.add_argument('--poses',nargs='+',choices=['whole','plane','plane-oblique','bite','edge-bite'],default=['whole','plane','plane-oblique','bite','edge-bite'])
a=P.parse_args(sys.argv[sys.argv.index('--')+1:]);assert not a.out.exists();SRC='Receptacle | canonical PR29 hull';MENS='SDF | separate vascular-attached lens pockets';TEMPLATE='SDF | original closed meniscus template (hidden)';ATLAS='LIVE | ORIGINAL V0 native RGB volume atlas (150^3)';cases=[('whole',0,False,False),('plane',1,False,False),('plane-oblique',1,True,False),('bite',2,False,False),('edge-bite',2,False,True)]
cases=[c for c in cases if c[0] in a.poses];report={'blender':bpy.app.version_string,'voxel_mm':a.voxel,'states':{},'limitations':['separate intersecting closed solid menisci; no fluid dynamics or physical union','tested poses only, not exhaustively verified triangle intersections','artist scale/color and sampling probability']};comparison={}
for variant,path in [('A',a.a),('B',a.b),('C',a.c)]:
 if variant not in a.variants:continue
 assert path.is_file();bpy.ops.wm.open_mainfile(filepath=str(path.resolve()),use_scripts=False);assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
 s=bpy.context.scene;body=s.objects[SRC];pool=s.objects[MENS];templ=s.objects[TEMPLATE];mm=s.unit_settings.scale_length*1000;assert abs(mm-22.22222276)<1e-5
 assert len(templ.data.vertices)==162 and len(templ.data.polygons)==192
 assert len([o for o in s.objects if o.get('role')=='achene'])==264
 packed=hashlib.sha256(bytes(bpy.data.images[ATLAS].packed_file.data)).hexdigest();raw=hashlib.sha256(np.array([v.co[:] for v in body.data.vertices],np.float32).tobytes()).hexdigest()
 assert body['sdf_meniscus_gain']==(0 if variant=='A' else 1)
 if 'root_packed' not in globals():root_packed,root_raw=packed,raw
 else:assert (packed,raw)==(root_packed,root_raw)
 poses=[]
 for pose,mode,oblique,edge in cases:
  t=time.monotonic();body['sdf_mode']=mode;body['sdf_voxel_mm']=a.voxel
  plane=s.objects['SDF | editable plane halfspace'];sphere=s.objects['SDF | editable sphere bite'];plane.location=(0,.08 if oblique else 0,0);plane.rotation_euler=(.506145483 if oblique else 0,0,.558505360 if oblique else 0)
  sphere.location=(.82,-.70,-.42) if edge else (.60,-.70,.42);sphere.scale=(1.04,)*3 if edge else (.65,)*3
  body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();deps.update()
  eb=body.evaluated_get(deps);ep=pool.evaluated_get(deps);mb=eb.to_mesh();mp=ep.to_mesh()
  points=np.zeros(len(mb.vertices)*3,np.float32);mb.vertices.foreach_get('co',points);body_hash=hashlib.sha256(points.tobytes()).hexdigest()
  verts=np.zeros(len(mp.vertices)*3,np.float32);mp.vertices.foreach_get('co',verts);lens_hash=hashlib.sha256(verts.tobytes()).hexdigest()
  rec={'n_body_vertices':len(mb.vertices),'body_sha256':body_hash,'lens_vertices':len(mp.vertices),'lens_faces':len(mp.polygons),'lens_sha256':lens_hash}
  expected=0 if variant=='A' or pose=='whole' else -1
  if expected==0:assert len(mp.vertices)==len(mp.polygons)==0,(variant,pose,len(mp.vertices))
  else:
   assert len(mp.vertices)%162==0 and len(mp.polygons)%192==0
   count=len(mp.vertices)//162;assert count==len(mp.polygons)//192 and 3<=count<70,(variant,pose,count)
   mmsh=bmesh.new();mmsh.from_mesh(mp);bad=sum(not e.is_manifold for e in mmsh.edges);vol=mmsh.calc_volume(signed=True);mmsh.free();assert bad==0 and vol>0,(variant,pose,bad,vol)
   body_bm=bmesh.new();body_bm.from_mesh(mb);tree=BVHTree.FromBMesh(body_bm)
   contacts=[]
   for i in range(count):
    base=Vector(mp.vertices[i*162+161].co);top=Vector(mp.vertices[i*162+160].co);direction=(top-base).normalized()
    nearest,_,_,bd=tree.find_nearest(base);nearest_top,_,_,td=tree.find_nearest(top)
    assert nearest is not None and nearest_top is not None
    base_inside_mm=(base-nearest).dot(direction)*mm;top_out_mm=(top-nearest_top).dot(direction)*mm
    contacts.append((base_inside_mm,top_out_mm))
   body_bm.free();mins=np.asarray(contacts,dtype=np.float64)
   # Contact is a detectable penetration of original sampled body surface,
   # *not* a Boolean solid union or fluid-simulation contact angle.
   assert (mins[:,0]<-.009).all() and (mins[:,1]>.025).all(),(variant,pose,mins.min(0),mins.max(0))
   rec.update({'lens_islands_closed':count,'lens_nonmanifold_edges':bad,'lens_positive_volume':vol>0,'body_contact_all_lenses':True,'base_below_surface_mm_range':[float(mins[:,0].min()),float(mins[:,0].max())],'top_above_surface_mm_range':[float(mins[:,1].min()),float(mins[:,1].max())]})
  # Main body topology independently in both cases.
  bm=bmesh.new();bm.from_mesh(mb);bad=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);bm.free();assert bad==0 and vol>0
  rec['body_nonmanifold_edges']=bad;rec['body_signed_volume']=vol;rec['seconds']=round(time.monotonic()-t,3)
  poses.append({'pose':pose,**rec});comparison.setdefault(pose,{})[variant]=rec
  print('QA',variant,a.voxel,pose,'body',rec['n_body_vertices'],'lenses',len(mp.vertices)//162,'s',rec['seconds'],flush=True)
  eb.to_mesh_clear();ep.to_mesh_clear()
 report['states'][variant]={'scene_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_body_sha256':raw,'source_atlas_sha256':packed,'poses':poses}
if all(v in a.variants for v in ['A','B','C']):
 for pose,triplet in comparison.items():
  for x in ['B','C']:
   assert triplet[x]['body_sha256']==triplet['A']['body_sha256'],(pose,x)
   assert triplet[x]['lens_sha256']==triplet['B']['lens_sha256'],(pose,x)
report['result']='PASS_TESTED_MENISCI_ATTACHMENTS_AND_BODY_UNCHANGED';report['max_rss_kb']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
report['source_original_scene_sha256']='0b79e33b0725f807524061b1afe79671f4fcf1c6b5c429bd8203cec8d6a21bd2'
a.out.write_text(json.dumps(report,indent=2)+'\n');print('QA_PASS',len(cases),report['max_rss_kb'],flush=True)

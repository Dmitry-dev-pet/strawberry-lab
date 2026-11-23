"""Independent saved-scene Geometry Nodes A/B checks for a cut-local wet film.
No embedded scripts and no dependence on code from the builder.
"""
import bpy, bmesh, hashlib, json, numpy as np, sys, time, argparse
from pathlib import Path
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser();p.add_argument('--off',required=True,type=Path);p.add_argument('--on',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert not a.out.exists()
BODY='Receptacle | canonical PR29 hull';FILM='SDF | live cut wet-film surface'
orig_body_geometry=None;orig_atlas=None
report={'status':'UNVERIFIED','blender':bpy.app.version_string,'variants':{},'tests':[]}
for v,path in [('A',a.off),('B',a.on)]:
 assert path.is_file()
 bpy.ops.wm.open_mainfile(filepath=str(path.resolve()),use_scripts=False)
 s=bpy.context.scene;b=s.objects[BODY];film=s.objects[FILM]
 assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
 assert b['sdf_wetfilm_gain']==(0.0 if v=='A' else 1.0)
 source=hashlib.sha256(repr([(ver.co[:]) for ver in b.data.vertices]).encode()).hexdigest()
 atlas=hashlib.sha256(bytes(bpy.data.images['LIVE | ORIGINAL V0 native RGB volume atlas (150^3)'].packed_file.data)).hexdigest()
 if orig_body_geometry is None:orig_body_geometry,orig_atlas=source,atlas
 assert source==orig_body_geometry and atlas==orig_atlas
 assert len(film.modifiers)==1 and film.modifiers[0].type=='NODES'
 rec={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'states':{}}
 for voxel in (.32,.20):
  for name,mode,edge in [('whole',0,False),('plane',1,False),('edge-bite',2,True)]:
   t=time.monotonic();b['sdf_mode']=mode;b['sdf_voxel_mm']=voxel
   sphere=s.objects['SDF | editable sphere bite'];sphere.location=(.82,-.70,-.42) if edge else (.60,-.70,.42);sphere.scale=(1.04,)*3 if edge else (.65,)*3
   b.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
   eb=b.evaluated_get(dg);em=film.evaluated_get(dg)
   body=eb.to_mesh();sheet=em.to_mesh()
   coordinates=np.zeros(len(body.vertices)*3,np.float32);body.vertices.foreach_get('co',coordinates);coordinates=coordinates.reshape((-1,3))
   bdig=hashlib.sha256(coordinates.tobytes()).hexdigest()
   coords=np.zeros(len(sheet.vertices)*3,np.float32);sheet.vertices.foreach_get('co',coords);coords=coords.reshape((-1,3))
   # For any cut, only cap should be represented in the wet layer.
   body_cap_faces=sum(x.material_index==2 for x in body.polygons)
   if v=='A' or name=='whole':assert len(sheet.vertices)==0 and len(sheet.polygons)==0,(v,name,voxel,len(sheet.vertices),len(sheet.polygons))
   else:
    assert len(sheet.vertices)>10 and len(sheet.polygons)>10,(v,name,voxel)
    assert len(sheet.polygons)<=body_cap_faces+100,(len(sheet.polygons),body_cap_faces)
    assert 'sdf_rest_position' in sheet.attributes and 'sdf_v20_halo' in sheet.attributes
    assert np.isfinite(coords).all()
    # Geometry follows cutter at a 0.025 mm normal offset, with expected float tolerance.
    dist=[]
    bm=bmesh.new();bm.from_mesh(body);tree=BVHTree.FromBMesh(bm)
    for index in np.linspace(0,len(coords)-1,min(120,len(coords)),dtype=int):
     closest,normal,face,dd=tree.find_nearest(tuple(map(float,coords[index])))
     assert dd is not None
     dist.append(dd*s.unit_settings.scale_length*1000)
    bm.free()
    med=float(np.median(dist))
    assert .005<med<.060,(v,name,voxel,med)
   rec['states'][f'{voxel}/{name}']={'body_vertices':len(body.vertices),'body_sha256':bdig,'body_cap_faces':body_cap_faces,'film_vertices':len(sheet.vertices),'film_faces':len(sheet.polygons),'sampled_film_body_gap_mm':float(np.median(dist)) if len(sheet.vertices)>0 else None,'seconds':round(time.monotonic()-t,3)}
   print('FILM_QA',v,voxel,name,'body',len(body.vertices),'cap',body_cap_faces,'film',len(sheet.vertices),len(sheet.polygons),'seconds',round(time.monotonic()-t,3),flush=True)
   eb.to_mesh_clear();em.to_mesh_clear()
 report['variants'][v]=rec
for pose,ra in report['variants']['A']['states'].items():
 rb=report['variants']['B']['states'][pose]
 assert ra['body_vertices']==rb['body_vertices'] and ra['body_sha256']==rb['body_sha256'],pose
 assert ra['body_cap_faces']==rb['body_cap_faces'],pose
report['status']='PASS_NATIVE_INDEPENDENT_WET_FILM_AB_TESTED_STATES'
report['base_body_unchanged']=True;report['original_material_atlas_unchanged']=True
report['limitations']=['Film is an open surface sheet (0 thickness), not watertight independently','Reflective translucency is ARTIST and visually unaccepted','Checks limited to whole/plane/side-bite at 0.32/0.20 mm; no all-pose guarantee']
a.out.write_text(json.dumps(report,indent=2)+'\n')
print('FILM_QA_PASS',report['status'],flush=True)

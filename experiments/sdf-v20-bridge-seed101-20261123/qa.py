"""Saved native scene, script autoexecution disabled: independent BMesh and A/B switch QA."""
import bpy,bmesh,sys,json,time,hashlib,resource,argparse
from pathlib import Path
import numpy as np
parser=argparse.ArgumentParser();parser.add_argument('--scene',required=True,type=Path);parser.add_argument('--out',required=True,type=Path);parser.add_argument('--voxel',required=True,type=float);parser.add_argument('--poses',required=True,nargs='+',choices=['whole','plane','plane-oblique','bite','bite-edge'])
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);SCENE=args.scene.resolve();OUT=args.out.resolve();assert SCENE.is_file() and not OUT.exists()
bpy.ops.wm.open_mainfile(filepath=str(SCENE),use_scripts=False)
s=bpy.context.scene;body=s.objects['Receptacle | canonical PR29 hull'];sphere=s.objects['SDF | editable sphere bite'];plane=s.objects['SDF | editable plane halfspace']
mm=s.unit_settings.scale_length*1000
assert abs(mm-22.22222276)<1e-5
assert len([o for o in s.objects if o.get('role')=='achene'])==264
assert s['SDF V20 bridge']
original_pack=hashlib.sha256(bytes(bpy.data.images['LIVE | ORIGINAL V0 native RGB volume atlas (150^3)'].packed_file.data)).hexdigest()
assert s.objects['Receptacle | canonical PR29 hull'].modifiers[0].node_group.nodes.get('V20 bridge: core and halo from same source 3D')
raw_source_sha=hashlib.sha256(repr([(v.co[:]) for v in body.data.vertices]).encode()).hexdigest()


def evalmesh():
 body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
 ob=body.evaluated_get(dg);me=ob.to_mesh();me.calc_loop_triangles()
 p=np.array([tuple(v.co) for v in me.vertices],dtype=np.float64)
 tr=np.asarray([t.vertices[:] for t in me.loop_triangles],dtype=np.int32)
 # Sanity that mesh has stable properties from active graph.
 assert len(me.vertices)>10000 and np.isfinite(p).all()
 attr={}
 for name in ['sdf_v20_core','sdf_v20_halo','sdf_v20_cell_suppression','sdf_v20_height_mm']:
  a=me.attributes[name];q=np.zeros(len(a.data),np.float32);a.data.foreach_get('value',q);attr[name]=q
 e=hashlib.sha256(p.tobytes()).hexdigest()
 return ob,me,p,tr,attr,e


def check_topology(me,p,tr):
 areas=np.linalg.norm(np.cross(p[tr[:,1]]-p[tr[:,0]],p[tr[:,2]]-p[tr[:,0]]),axis=1)*.5*mm**2
 bm=bmesh.new();bm.from_mesh(me)
 comp=0;seen=set()
 for v in bm.verts:
  if v in seen:continue
  comp+=1;seen.add(v)
  # Connected-component flood fill independent of original GN.
  todo=[v]
  while todo:
   u=todo.pop()
   for e in u.link_edges:
    w=e.other_vert(u)
    if w not in seen:seen.add(w);todo.append(w)
 bad=sum(not e.is_manifold for e in bm.edges)
 volume=bm.calc_volume(signed=True)
 bm.free()
 return {'components':comp,'nonmanifold_edges':bad,'volume':volume,'min_area_mm2':float(areas.min())}

cases=[('whole',0,False,False),('plane',1,False,False),('plane-oblique',1,True,False),('bite',2,False,False),('bite-edge',2,False,True)]
rec={'source':str(SCENE),'scene_sha256':hashlib.sha256(SCENE.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'source_geometry_sha':raw_source_sha,'original_150cube_atlas_sha256':original_pack,'states':[],'limitations':['Actual cap surface relief and seed center guard preserved; no v21 colored outline/wet fluid layer','Only tested poses and voxel sizes; not arbitrary-geometry guarantee']}
for voxel in [args.voxel]:
 for name,mode,oblique,edge in [c for c in cases if c[0] in args.poses]:
  start=time.monotonic()
  body['sdf_mode']=mode;body['sdf_voxel_mm']=voxel
  plane.location=(0,.08 if oblique else 0,0)
  plane.rotation_euler=(np.deg2rad(29) if oblique else 0,0,np.deg2rad(32) if oblique else 0)
  sphere.location=(.82,-.70,-.42) if edge else (.60,-.70,.42)
  sphere.scale=(1.04,)*3 if edge else (.65,)*3
  variants=[];vcoords=[]
  for label,gain,hal in [('off',0.,1.),('core',1.,0.),('halo',1.,1.)]:
   body['sdf_tissue_gain']=gain;body['sdf_use_broad_halo']=hal
   ev,me,p,tr,attr,digest=evalmesh()
   values=attr['sdf_v20_core'];halo=attr['sdf_v20_halo'];strength=attr['sdf_v20_height_mm']
   assert (halo>=values-1e-5).all()
   assert np.all(np.isfinite(halo)) and np.all(np.isfinite(values))
   assert strength.max()<.19 and strength.min()>-.05
   met={'label':label,'verts':len(p),'tris':len(tr),'coordinate_sha':digest,'max_field_height_mm':float(strength.max()),'min_field_height_mm':float(strength.min()),'max_core':float(values.max()),'max_halo':float(halo.max()),'mean_cell_suppression':float(attr['sdf_v20_cell_suppression'].mean()),'mean_vascular_core':float(values.mean()),'mean_vascular_halo':float(halo.mean())}
   if label=='halo':
    met.update(check_topology(me,p,tr))
    assert met['components']==1 and met['nonmanifold_edges']==0 and met['volume']>0 and met['min_area_mm2']>1e-10,met
   variants.append(met);vcoords.append(p)
   ev.to_mesh_clear()
  assert len({v['verts'] for v in variants})==1 and len({v['tris'] for v in variants})==1
  a,c,h=vcoords
  diff_core=np.linalg.norm(a-c,axis=1)*mm;diff_halo=np.linalg.norm(a-h,axis=1)*mm;diff_supp=np.linalg.norm(c-h,axis=1)*mm
  if mode==0:
   assert np.max(diff_core)==np.max(diff_halo)==np.max(diff_supp)==0.,(name,voxel)
  else:
   assert .005<np.max(diff_core)<.21 and .005<np.max(diff_halo)<.21,(name,voxel,np.max(diff_halo))
   # Halo must change at least some actual cap cells (same common R ridge)
   assert np.max(diff_supp)>1e-5,(name,voxel,np.max(diff_supp))
  rec['states'].append({'voxel_mm':voxel,'name':name,'variants':variants,'changed_vertices_core_vs_off':int((diff_core>1e-5).sum()),'changed_vertices_halo_vs_off':int((diff_halo>1e-5).sum()),'changed_vertices_core_vs_halo':int((diff_supp>1e-5).sum()),'max_displacement_core_vs_off_mm':float(diff_core.max()),'max_displacement_halo_vs_off_mm':float(diff_halo.max()),'max_core_vs_halo_mm':float(diff_supp.max()),'elapsed_s':round(time.monotonic()-start,3)})
  print('V20_BRIDGE_QA',voxel,name,'vertices',variants[2]['verts'],'max halo',round(float(diff_halo.max()),5),'max A/B',round(float(diff_supp.max()),5),'seconds',round(time.monotonic()-start,1),flush=True)
assert hashlib.sha256(bytes(bpy.data.images['LIVE | ORIGINAL V0 native RGB volume atlas (150^3)'].packed_file.data)).hexdigest()==original_pack
assert raw_source_sha==hashlib.sha256(repr([(v.co[:]) for v in body.data.vertices]).encode()).hexdigest()
body['sdf_mode']=0;body['sdf_voxel_mm']=.20;body['sdf_tissue_gain']=1.;body['sdf_use_broad_halo']=1.
rec['status']='PASS_OWN_V20_CORE_HALO_TESTED_STATES';rec['max_rss_kb']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
OUT.write_text(json.dumps(rec,indent=2))
print('V20_BRIDGE_QA_PASS',len(rec['states']),rec['max_rss_kb'],flush=True)

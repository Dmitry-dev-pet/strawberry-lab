"""Independent read-only numeric audit of real seed101 cap vascular field coverage.
No scene modifications, new pith colors, Frucht code or forced mesh changes.
"""
import bpy,hashlib,sys,json,time
import numpy as np
from pathlib import Path
scene,output=map(Path,sys.argv[sys.argv.index('--')+1:]);assert scene.is_file() and not output.exists()
assert hashlib.sha256(scene.read_bytes()).hexdigest()=='0b79e33b0725f807524061b1afe79671f4fcf1c6b5c429bd8203cec8d6a21bd2'
bpy.ops.wm.open_mainfile(filepath=str(scene.resolve()),use_scripts=False);assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
s=bpy.context.scene;b=s.objects['Receptacle | canonical PR29 hull'];plane=s.objects['SDF | editable plane halfspace'];sphere=s.objects['SDF | editable sphere bite']
mm=s.unit_settings.scale_length*1000;assert abs(mm-22.22222276)<1e-5
records=[]
for shot,mode,edge in [('plane',1,False),('edge-bite',2,True)]:
 b['sdf_mode']=mode;b['sdf_voxel_mm']=.32;b['sdf_tissue_gain']=1.;b['sdf_use_broad_halo']=1.
 if mode==2:sphere.location=(.82,-.70,-.42);sphere.scale=(1.04,)*3
 t=time.monotonic();b.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();deps.update()
 ev=b.evaluated_get(deps);me=ev.to_mesh();N=len(me.vertices);P=len(me.polygons)
 attrs={}
 for name in ('sdf_v20_core','sdf_v20_halo','sdf_v20_cell_suppression','sdf_v20_height_mm'):
  a=me.attributes.get(name);assert a and a.domain=='POINT';x=np.empty(N,np.float32);a.data.foreach_get('value',x);attrs[name]=x
 loop_idx=np.empty(len(me.loops),np.int32);me.loops.foreach_get('vertex_index',loop_idx)
 start=np.empty(P,np.int32);total=np.empty(P,np.int32);area=np.empty(P,np.float32);mat=np.empty(P,np.int32)
 me.polygons.foreach_get('loop_start',start);me.polygons.foreach_get('loop_total',total);me.polygons.foreach_get('area',area);me.polygons.foreach_get('material_index',mat)
 cap=(mat==2);assert cap.sum()>500
 values={key:np.add.reduceat(v[loop_idx],start)/total for key,v in attrs.items()}
 area_mm=area*mm*mm;cap_area=area_mm[cap];assert np.all(np.isfinite(cap_area)) and cap_area.sum()>100.
 rec={'pose':shot,'mesh_vertices':N,'total_faces':P,'cap_faces':int(cap.sum()),'cap_area_mm2':float(cap_area.sum()),'field_summary':{}}
 for key in ['sdf_v20_core','sdf_v20_halo']:
  field=values[key][cap];rec['field_summary'][key]={'mean':float(np.average(field,weights=cap_area)),'max':float(field.max()),'area_fraction':{str(x):float(cap_area[field>=x].sum()/cap_area.sum()) for x in (.1,.2,.3,.5)}}
 rec['max_geometric_cut_relief_mm']=float(attrs['sdf_v20_height_mm'].max());rec['elapsed_s']=round(time.monotonic()-t,2)
 assert (attrs['sdf_v20_halo']>=attrs['sdf_v20_core']-1e-5).all()
 print('COVERAGE',json.dumps(rec),flush=True);ev.to_mesh_clear();records.append(rec)
output.write_text(json.dumps({'status':'PASS_READONLY_SEED101_3D_VASCULAR_CAP_COVERAGE','source_scene_sha256':hashlib.sha256(scene.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'records':records,'limitations':'Cap area fractions from interpolated point scalars; threshold-dependent, not real measured fiber diameters; direct comparison to v16 older scene invalid.'},indent=2)+'\n')

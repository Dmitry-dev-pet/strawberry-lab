from pathlib import Path
import bpy,numpy as np,argparse,sys,json,hashlib
parser=argparse.ArgumentParser();parser.add_argument('--scene',required=True,type=Path);parser.add_argument('--field',required=True,type=Path);parser.add_argument('--out',required=True,type=Path);args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);s_path=args.scene.resolve();out=args.out.resolve();assert s_path.is_file() and args.field.is_file() and not out.exists();bpy.ops.wm.open_mainfile(filepath=str(s_path),use_scripts=False)
s=bpy.context.scene;body=s.objects['Receptacle | canonical PR29 hull'];mm=s.unit_settings.scale_length*1000
body['sdf_mode']=1;body['sdf_voxel_mm']=.32;body['sdf_tissue_gain']=1.;body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update();ev=body.evaluated_get(dg);me=ev.to_mesh()
arr=np.load(args.field);R,H=arr['core'],arr['halo']
lower=np.array([-25.,-25.,-2.]);upper=np.array([25.,25.,52.]);gsize=191

def trilin(a,p):
 t=np.maximum(0,np.minimum(191,(p-lower)/(upper-lower)*gsize));low=np.floor(t).astype(int);up=np.minimum(191,low+1);t=t-low
 ix,iy,iz=low;ux,uy,uz=up;tx,ty,tz=t
 a0=(a[iz,iy,ix]*(1-tx)+a[iz,iy,ux]*tx)*(1-ty)+(a[iz,uy,ix]*(1-tx)+a[iz,uy,ux]*tx)*ty
 a1=(a[uz,iy,ix]*(1-tx)+a[uz,iy,ux]*tx)*(1-ty)+(a[uz,uy,ix]*(1-tx)+a[uz,uy,ux]*tx)*ty
 return a0*(1-tz)+a1*tz

rest=me.attributes['sdf_rest_position'];core=me.attributes['sdf_v20_core'];halo=me.attributes['sdf_v20_halo'];indices=sorted({i for f in me.polygons if f.material_index==2 for i in f.vertices});idx=np.array(indices)[np.linspace(0,len(indices)-1,150,dtype=int)]
err=[];example=[]
for i in idx:
 rr=np.array(rest.data[int(i)].vector[:]);p=rr*mm+np.array([0,0,27]);r0=trilin(R,p);h0=trilin(H,p);rv=core.data[int(i)].value;hv=halo.data[int(i)].value;err.append([abs(r0-rv),abs(h0-hv)]);
 if len(example)<8 and r0>0.1:example.append({'index':int(i),'coord_mm':p.tolist(),'core_numeric':float(r0),'core_gn':float(rv),'halo_numeric':float(h0),'halo_gn':float(hv)})
err=np.asarray(err);print('FIELD_SAMPLE_ERRORS',{'max_core':err[:,0].max(),'max_halo':err[:,1].max(),'mean_core':err[:,0].mean(),'mean_halo':err[:,1].mean(),'within_1e-3':float((err<1e-3).all(axis=1).mean())},flush=True)
print('SAMPLES',example,flush=True)
ev.to_mesh_clear()

assert err.max()<.001
out.write_text(json.dumps({'status':'PASS_TWO_CHANNEL_TRILINEAR_V20','blender':bpy.app.version_string,'scene_sha256':hashlib.sha256(s_path.read_bytes()).hexdigest(),'n_probes':len(idx),'max_error_core':float(err[:,0].max()),'max_error_halo':float(err[:,1].max()),'max_error_threshold':.001,'field_sha256':hashlib.sha256(args.field.read_bytes()).hexdigest()},indent=2)+'\n')

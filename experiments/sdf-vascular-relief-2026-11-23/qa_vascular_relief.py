"""Independent numerical/mesh QA for owned PR50 -> vascular A/B."""
import bpy,bmesh,numpy as np,sys,json,time,math,hashlib,zipfile,io,resource
from pathlib import Path
BODY='Receptacle | canonical PR29 hull'; PLANE='SDF | editable plane halfspace'
def sha(a):return hashlib.sha256(a.tobytes()).hexdigest()
def read_attr(me,n,vector=False):
    a=np.empty(len(me.vertices)*(3 if vector else 1),np.float32);me.attributes[n].data.foreach_get('vector' if vector else 'value',a);return a.reshape(-1,3) if vector else a
def state(body,pose,voxel,gain):
    body['sdf_mode']={'whole':0,'plane':1,'oblique':1,'bite':2}[pose];body['sdf_voxel_mm']=voxel;body['cell_surface_gain']=1.;body['cell_surface_detail']=1;body['vascular_relief_gain']=gain
    p=bpy.data.objects[PLANE];p.location=(0,.08 if pose=='oblique' else 0,0);p.rotation_euler=(math.radians(29) if pose=='oblique' else 0,0,math.radians(32) if pose=='oblique' else 0)
    body.update_tag();bpy.context.scene.frame_set(bpy.context.scene.frame_current);bpy.context.view_layer.update()
def tri_sample(grid,p):
    v=np.clip((p-np.array([-25.,-25.,-2.]))/np.array([50.,50.,54.])*191,0,191);l=np.floor(v).astype(int);u=np.minimum(l+1,191);t=v-l;ans=np.zeros(len(p))
    for x in range(2):
      for y in range(2):
       for z in range(2):
        a=[x,y,z];ii=np.where(a,u,l);w=np.prod(np.where(a,t,1-t),axis=1);ans+=grid[ii[:,2],ii[:,1],ii[:,0]]*w
    return ans
def snapshot(body,mm):
    dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg)
    p=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',p);p=p.reshape(-1,3);me.calc_loop_triangles();idx=np.empty(len(me.loop_triangles)*3,np.int32);me.loop_triangles.foreach_get('vertices',idx);idx=idx.reshape(-1,3)
    bm=bmesh.new();bm.from_mesh(me);non=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True)*mm**3;bm.free();q=p[idx];cross=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);deg=int(np.sum(np.einsum('ij,ij->i',cross,cross)<1e-20));cap=np.zeros(len(p),bool);skin=cap.copy()
    ci=next(i for i,m in enumerate(me.materials) if m and m.name.startswith('SDF | inherited'))
    for f in me.polygons:(cap if f.material_index==ci else skin)[list(f.vertices)]=True
    r=dict(vertices=len(p),faces=len(me.polygons),triangles=len(idx),nonmanifold=non,volume_mm3=vol,degenerate_triangles=deg,coords_sha=sha(p),topology_sha=sha(idx))
    vals={}
    for name in ('sl_vascular_core','sl_vascular_halo','sl_vascular_cell_multiplier','sl_vascular_ridge_mm','sl_cell_height_mm','sl_cell_dome'):
        if name in me.attributes:vals[name]=read_attr(me,name)
    for name in ('sdf_rest_position','sl_cell_reference_position','sl_cell_reference_normal'):
        if name in me.attributes:vals[name]=read_attr(me,name,True)
    ev.to_mesh_clear();return r,p,cap,skin,vals
if __name__=='__main__':
    scene,archive,oldqa,out,voxel,*poses=sys.argv[sys.argv.index('--')+1:];voxel=float(voxel);assert not Path(out).exists();bpy.ops.wm.open_mainfile(filepath=scene,use_scripts=False);body=bpy.data.objects[BODY];mm=bpy.context.scene.unit_settings.scale_length*1000
    old=json.loads(Path(oldqa).read_text());assert old['voxel_mm']==voxel
    with zipfile.ZipFile(archive) as z:field=np.load(io.BytesIO(z.read('fields/seed101-own-core-halo-192.npz')));R,H=field['core'],field['halo']
    rows={}
    for pose in poses:
        t=time.monotonic();state(body,pose,voxel,0.);a,pa,cap,skin,va=snapshot(body,mm);ta=time.monotonic()-t;assert a['coords_sha']==old['poses'][pose]['1.0']['coords_sha'],('A differs from PR50',pose,a['coords_sha']);t=time.monotonic();state(body,pose,voxel,1.);b,pb,cb,sb,vb=snapshot(body,mm);tb=time.monotonic()-t
        assert a['topology_sha']==b['topology_sha'] and np.array_equal(cap,cb) and np.array_equal(skin,sb)
        for x in (a,b):assert x['nonmanifold']==0 and x['degenerate_triangles']==0 and x['volume_mm3']>0,x
        row={'A':a,'B':b,'A_matches_PR50':True,'seconds_A':ta,'seconds_B':tb}
        if pose=='whole':assert np.array_equal(pa,pb);row['whole_unchanged']=True
        else:
            d=np.linalg.norm(pb-pa,axis=1)*mm;ii=np.flatnonzero(cap);sample=ii[np.linspace(0,len(ii)-1,256,dtype=int)];rp=vb['sdf_rest_position'][sample]*mm+np.array([0,0,27.]);r=vb['sl_vascular_core'];h=vb['sl_vascular_halo'];s=vb['sl_vascular_cell_multiplier'];ridge=vb['sl_vascular_ridge_mm'];expected=np.clip((h-.04)/.44,0,1);expected=1-.88*expected**3*(expected*(expected*6-15)+10)
            errR=float(np.max(np.abs(tri_sample(R,rp)-r[sample])));errH=float(np.max(np.abs(tri_sample(H,rp)-h[sample])));errS=float(np.max(np.abs(expected-s)));errHeight=float(np.max(np.abs(va['sl_cell_height_mm']*s+ridge-vb['sl_cell_height_mm'])))
            skinmax=float(d[skin&~cap].max());seammax=float(d[skin&cap].max());strong=cap&(h>.48);weak=cap&(h<.04)
            assert errR<.001 and errH<.001 and errS<.00001 and errHeight<.00001,(errR,errH,errS,errHeight)
            assert skinmax<.0001 and seammax<.0001 and np.count_nonzero(d[cap]>.001)>100
            assert np.all(h+1e-5>=r) and s.min()>=.11999 and s.max()<=1.00001 and ridge.min()>=-1e-6 and ridge.max()<=.1651
            row.update(max_delta_mm=float(d.max()),mean_delta_cap_mm=float(d[cap].mean()),skin_max_mm=skinmax,seam_max_mm=seammax,moved_cap_points=int(np.sum(d[cap]>.001)),max_ridge_mm=float(ridge[cap].max()),cap_strong_halo_points=int(strong.sum()),mean_multiplier_strong=float(s[strong].mean()) if strong.any() else None,mean_multiplier_weak=float(s[weak].mean()) if weak.any() else None,trilinear_max_core_err=errR,trilinear_max_halo_err=errH,multiplier_max_error=errS,height_equation_max_mm_error=errHeight)
        rows[pose]=row;print(pose,json.dumps(row),flush=True)
    Path(out).write_text(json.dumps(dict(status='PASS',scene_sha=hashlib.sha256(Path(scene).read_bytes()).hexdigest(),voxel_mm=voxel,poses=rows,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),indent=2)+'\n')

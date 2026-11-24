"""Reopen saved scene and test native geometry independently of builder."""
import bpy,bmesh,numpy as np,sys,json,time,math,hashlib,resource
from pathlib import Path
BODY='Receptacle | canonical PR29 hull'; PLANE='SDF | editable plane halfspace'; SPHERE='SDF | editable sphere bite'

def set_state(body,gain,kind,voxel,detail=1):
    body['sdf_mode']={'whole':0,'plane':1,'oblique':1,'bite':2}[kind];body['sdf_voxel_mm']=voxel;body['cell_surface_gain']=gain;body['cell_surface_detail']=detail
    p=bpy.data.objects[PLANE];p.location=(0,.08 if kind=='oblique' else 0,0);p.rotation_euler=(math.radians(29) if kind=='oblique' else 0,0,math.radians(32) if kind=='oblique' else 0)
    body.update_tag();bpy.context.scene.frame_set(bpy.context.scene.frame_current);bpy.context.view_layer.update()

def coords(me):
    a=np.empty(3*len(me.vertices),np.float32);me.vertices.foreach_get('co',a);return a.reshape(-1,3)
def digest(a):return hashlib.sha256(a.tobytes()).hexdigest()
def metrics(body):
    t=time.monotonic();dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg);p=coords(me);mm=bpy.context.scene.unit_settings.scale_length*1000
    bm=bmesh.new();bm.from_mesh(me);non=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);bm.free();me.calc_loop_triangles();ids=np.empty(len(me.loop_triangles)*3,np.int32);me.loop_triangles.foreach_get('vertices',ids);q=p[ids.reshape(-1,3)];cross=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);zeros=int(np.sum(np.einsum('ij,ij->i',cross,cross)<1e-20));out=dict(vertices=len(p),faces=len(me.polygons),triangles=len(q),nonmanifold=non,volume_mm3=vol*mm**3,degenerate_triangles=zeros,coords_sha=digest(p),seconds=time.monotonic()-t)
    if 'sl_cell_reference_position' in me.attributes:
        x=np.empty(p.size,np.float32);me.attributes['sl_cell_reference_position'].data.foreach_get('vector',x);delta=np.linalg.norm(p-x.reshape(-1,3),axis=1)*mm;cut=np.zeros(len(p),bool);skin=np.zeros(len(p),bool)
        cap=next(i for i,m in enumerate(me.materials) if m and m.name.startswith('SDF | inherited'))
        for f in me.polygons:
            (cut if f.material_index==cap else skin)[list(f.vertices)]=True
        h=np.empty(len(p),np.float32);me.attributes['sl_cell_height_mm'].data.foreach_get('value',h)
        out.update(max_displacement_mm=float(delta.max()),median_cap_displacement_mm=float(np.median(delta[cut])),skin_only_max_displacement_mm=float(delta[skin&~cut].max()),seam_max_displacement_mm=float(delta[skin&cut].max()),cap_moved_points=int((delta[cut]>.001).sum()),height_max_mm=float(h.max()))
    ev.to_mesh_clear();return out
if __name__=='__main__':
    source,output,voxel,*poses=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.open_mainfile(filepath=source,use_scripts=False);body=bpy.data.objects[BODY];rows={}
    for pose in poses:
        row={}
        for gain in (0.,1.):
            t=time.monotonic();set_state(body,gain,pose,float(voxel));res=metrics(body);res['total_seconds']=time.monotonic()-t;row[str(gain)]=res;print(pose,gain,res,flush=True)
            assert res['nonmanifold']==0 and res['volume_mm3']>0 and res['degenerate_triangles']==0, res
        if pose=='whole':assert row['0.0']['coords_sha']==row['1.0']['coords_sha'],row
        else:
            assert row['1.0']['cap_moved_points']>100 and row['1.0']['skin_only_max_displacement_mm']<.0001 and row['1.0']['seam_max_displacement_mm']<.0001,row
        rows[pose]=row
    Path(output).write_text(json.dumps({'source_sha':hashlib.sha256(Path(source).read_bytes()).hexdigest(),'voxel_mm':float(voxel),'poses':rows,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},indent=2)+'\n')

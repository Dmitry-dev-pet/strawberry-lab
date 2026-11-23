"""Saved-scene independent check of original body and separate liquid patches."""
import bpy,bmesh,numpy as np,sys,json,time,math,hashlib
from pathlib import Path
BODY='Receptacle | canonical PR29 hull';JUICE='SL Juice | independent pool surface';PLANE='SDF | editable plane halfspace'
def sha(a):return hashlib.sha256(a.tobytes()).hexdigest()
def state(b,pose,voxel,gain):
    b['sdf_mode']={'whole':0,'plane':1,'oblique':1,'bite':2}[pose];b['sdf_voxel_mm']=voxel;b['cell_surface_gain']=1.;b['cell_surface_detail']=1;b['vascular_relief_gain']=1.;b['juice_surface_gain']=gain
    p=bpy.data.objects[PLANE];p.location=(0,.08 if pose=='oblique' else 0,0);p.rotation_euler=(math.radians(29) if pose=='oblique' else 0,0,math.radians(32) if pose=='oblique' else 0)
    b.update_tag();bpy.context.scene.frame_set(bpy.context.scene.frame_current);bpy.context.view_layer.update()
def pos(me):
    a=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',a);return a.reshape(-1,3)
def attr(me,n,vector=False):
    a=np.empty(len(me.vertices)*(3 if vector else 1),np.float32);me.attributes[n].data.foreach_get('vector' if vector else 'value',a);return a.reshape(-1,3) if vector else a
def body_snap(b):
    dg=bpy.context.evaluated_depsgraph_get();ev=b.evaluated_get(dg);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg);p=pos(me);me.calc_loop_triangles();idx=np.empty(len(me.loop_triangles)*3,np.int32);me.loop_triangles.foreach_get('vertices',idx);cap=np.zeros(len(p),bool);skin=cap.copy();ci=next(i for i,m in enumerate(me.materials) if m and m.name.startswith('SDF | inherited'))
    for f in me.polygons:(cap if f.material_index==ci else skin)[list(f.vertices)]=True
    r={'vertices':len(p),'faces':len(me.polygons),'coords_sha':sha(p),'topology_sha':sha(idx)};ev.to_mesh_clear();return r,p,cap,skin
def juice_snap(j,mm,p,cap,skin):
    dg=bpy.context.evaluated_depsgraph_get();ev=j.evaluated_get(dg);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg);r={'vertices':len(me.vertices),'faces':len(me.polygons)}
    if not len(me.vertices):ev.to_mesh_clear();return r
    q=pos(me);src=attr(me,'sl_juice_tissue_position',True);base=attr(me,'sl_cell_reference_position',True);n=attr(me,'sl_cell_reference_normal',True);n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-8);cl=attr(me,'sl_juice_clearance_mm');level=attr(me,'sl_juice_final_level_mm');envelope=attr(me,'sl_juice_envelope')
    def keys(x):return np.ascontiguousarray(x).view(np.dtype((np.void,12))).ravel()
    match=np.isin(keys(src),keys(p[cap&~skin]));assert match.all(),('Not exclusively cap interior',int((~match).sum()))
    err=float(np.max(np.abs(np.sum((q-src)*n,axis=1)*mm-cl)));lev_err=float(np.max(np.linalg.norm(q-(base+n*level[:,None]/mm),axis=1)*mm));assert err<.0001 and lev_err<.0001,(err,lev_err)
    bm=bmesh.new();bm.from_mesh(me);non=sum(len(e.link_faces)>2 for e in bm.edges);boundary=np.array([v.index for v in bm.verts if v.is_boundary],int);seen=set();components=0
    for v in bm.verts:
        if v in seen:continue
        components+=1;seen.add(v);stack=[v]
        while stack:
            for e in stack.pop().link_edges:
                for x in e.verts:
                    if x not in seen:seen.add(x);stack.append(x)
    bm.free();me.calc_loop_triangles();idx=np.empty(len(me.loop_triangles)*3,np.int32);me.loop_triangles.foreach_get('vertices',idx);qtri=q[idx.reshape(-1,3)];cross=np.cross(qtri[:,1]-qtri[:,0],qtri[:,2]-qtri[:,0]);deg=int(np.sum(np.einsum('ij,ij->i',cross,cross)<1e-20));assert non==0 and deg==0,(non,deg)
    r.update(components=components,over_two_face_edges=non,degenerate_triangles=deg,clearance_min_mm=float(cl.min()),clearance_max_mm=float(cl.max()),visible_points=int(np.sum(cl>.005)),buried_points=int(np.sum(cl<-.005)),boundary_points=len(boundary),boundary_above_005_mm=int(np.sum(cl[boundary]>.005)),boundary_max_mm=float(cl[boundary].max()) if len(boundary) else None,source_cap_points_only=True,clearance_equation_max_mm_error=err,position_equation_max_mm_error=lev_err,liquid_mesh_sha=sha(q))
    assert r['visible_points']>0 and r['buried_points']>0 and r['boundary_above_005_mm']==0,r;ev.to_mesh_clear();return r
if __name__=='__main__':
    scene,old,out,pose,voxel=sys.argv[sys.argv.index('--')+1:];assert not Path(out).exists();voxel=float(voxel);bpy.ops.wm.open_mainfile(filepath=scene,use_scripts=False);s=bpy.context.scene;b=s.objects[BODY];j=s.objects[JUICE];mm=s.unit_settings.scale_length*1000;old=json.loads(Path(old).read_text())['poses'][pose]['B'];rows={}
    for gain in (0.,1.):
        t=time.monotonic();state(b,pose,voxel,gain);br,p,cap,skin=body_snap(b);assert br['coords_sha']==old['coords_sha'] and br['topology_sha']==old['topology_sha'],('Body changed',br,old);jr=juice_snap(j,mm,p,cap,skin);assert (jr['faces']==0)==(gain==0 or pose=='whole'),jr;rows[str(gain)]={'body':br,'juice':jr,'seconds':time.monotonic()-t};print(gain,rows[str(gain)],flush=True)
    result=dict(status='PASS',pose=pose,voxel_mm=voxel,body_unchanged_vs_vascular=True,scene_sha256=hashlib.sha256(Path(scene).read_bytes()).hexdigest(),states=rows);Path(out).write_text(json.dumps(result,indent=2)+'\n')

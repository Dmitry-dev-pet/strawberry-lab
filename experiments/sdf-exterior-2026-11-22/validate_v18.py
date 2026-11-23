import bpy,bmesh,numpy as np,sys,time,json,hashlib,os,resource
from pathlib import Path
argv=sys.argv[sys.argv.index('--')+1:]
variant=argv[0]
root=Path('/mnt/data/strawberry_v18')
sc=bpy.context.scene
assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
assert sc.get('v18_variant')==variant
im=bpy.data.images['SDF proof v4 | 192^3 sparse volume and continuous branches']
assert im.packed_file
rows={'variant':variant,'scene_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'states':{}}

def run(tag,frame,name):
    sc.frame_set(frame)
    start=time.monotonic()
    obj=bpy.data.objects['Receptacle | sculpted skin and achene pits'] if tag=='whole' else bpy.data.objects['SDF visible body | '+tag]
    deps=bpy.context.evaluated_depsgraph_get()
    ev=obj.evaluated_get(deps);mesh=ev.to_mesh()
    print('EVAL',variant,name,'vertices',len(mesh.vertices),'faces',len(mesh.polygons),'time',round(time.monotonic()-start,3),flush=True)
    bm=bmesh.new();bm.from_mesh(mesh);bm.normal_update()
    nonman=sum(not e.is_manifold for e in bm.edges)
    vol=bm.calc_volume(signed=True) if bm.faces else 0
    minarea=min((f.calc_area() for f in bm.faces),default=0)
    bm.free()
    row={'vertices':len(mesh.vertices),'faces':len(mesh.polygons),'nonmanifold_edges':nonman,'signed_volume_mm3':round(vol,3),'min_face_area_mm2':minarea,'eval_sec':round(time.monotonic()-start,3)}
    if tag!='whole' and len(mesh.vertices)>0:
        for k in ('fruit_rest','v8_vascular_intensity','v8_cell_height_mm'): assert k in mesh.attributes,(name,k)
        idx=np.empty(len(mesh.polygons),dtype=np.int32);mesh.polygons.foreach_get('material_index',idx)
        row['cap_faces_material_2']=int((idx==2).sum())
        row['skin_faces_material_1']=int((idx==1).sum())
        attrs=np.empty(len(mesh.vertices),dtype=np.float32);mesh.attributes['v8_vascular_intensity'].data.foreach_get('value',attrs)
        row['vascular_field_p95']=round(float(np.percentile(attrs,95)),4)
        if name in ('plane','bite'):
            coords=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',coords)
            np.savez_compressed(root/f'v18{variant}-{name}-sample.npz',co=coords.reshape(-1,3),v=attrs,faceidx=idx)
    ev.to_mesh_clear()
    rows['states'][name]=row
    assert row['vertices']>10000,(name,row)
    assert nonman==0 and vol>0 and minarea>1e-10,(name,row)
    if tag!='whole':assert row['cap_faces_material_2']>1000,(name,row)
    print('STATE',json.dumps({'name':name,**row}),flush=True)

run('whole',1,'whole')
run('planar',20,'plane')
run('bite',40,'bite')
c=bpy.data.objects['SDF cutter | planar (move or rotate)'];loc,rot=c.location.copy(),c.rotation_euler.copy()
c.location.y+=3.;c.rotation_euler.x+=.1745329252
run('planar',20,'plane_moved')
c.location=loc;c.rotation_euler=rot
c=bpy.data.objects['SDF cutter | spherical bite (move or scale)'];loc,sca=c.location.copy(),c.scale.copy()
c.location.x-=4.;c.scale*=1.13
run('bite',40,'bite_moved')
c.location=loc;c.scale=sca
rows['max_rss_kb']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
(root/f'v18{variant}-qa.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
print('V18_QA_PASS',variant,flush=True)

"""Independent Blender 5.2.4 evaluated mesh/field QA for Strawb v19 A/B.

Reads saved source scene with autoexec disabled, never writes .blend.
Physiology and thresholds are ARTIST, not biological measurements.
"""
from pathlib import Path
import sys,bpy,bmesh,numpy as np,hashlib,json,time,math
from mathutils import Vector
P=Path('/mnt/data/strawberry-v19')
variant=sys.argv[sys.argv.index('--')+1]
assert variant in ('a','b')
f=P/f'strawberry-v19{variant}-pith-ring.blend'
expected={'a':'5959922e27f26b8501290e6a533725221c011569c79f40408dacadb5722fb46c','b':'f6792a2e52b8af80b1835aa8b7d81a475a646221f532e14464223a99fd6bda8a'}
assert hashlib.sha256(f.read_bytes()).hexdigest()==expected[variant]
t0=time.monotonic();bpy.ops.wm.open_mainfile(filepath=str(f),use_scripts=False)
assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
sc=bpy.context.scene
img=bpy.data.images[f'Strawberry v19{variant} | centered pith and vascular collar ARTIST']
assert img.packed_file and list(img.size)==[3072,2304]
field=bpy.data.node_groups['V8 | original rest-space vascular field (192^3)']
assert sum(n.inputs['Image'].default_value==img for n in field.nodes if n.bl_idname=='GeometryNodeImageTexture')==2
mat=bpy.data.materials['SDF v12 | continuous vascular fibers, restrained wetness (ARTIST)']
assert sum(n.image==img for n in mat.node_tree.nodes if n.bl_idname=='ShaderNodeTexImage')==2
N=192
px=np.empty((2304,3072,4),np.float32)
img.pixels.foreach_get(px.ravel())
volume=np.empty((N,N,N,3),np.float32)
for k in range(N):
 col=k%16;row=k//16
 volume[k]=px[row*N:(row+1)*N,col*N:(col+1)*N,:3]
# Interpolation matches shader/GN source XYZ mapping (nearest at voxel boundary).
def sample_trilinear(field3d, xyz):
 q=np.asarray(xyz,dtype=np.float32)
 x=np.clip((q[:,0]+18)*(191./36.),0,191)
 y=np.clip((q[:,1]+18)*(191./36.),0,191)
 z=np.clip((q[:,2]+1)*(191./51.),0,191)
 a=np.floor(x).astype(np.int32);b=np.floor(y).astype(np.int32);c=np.floor(z).astype(np.int32)
 ax=np.minimum(a+1,191);by=np.minimum(b+1,191);cz=np.minimum(c+1,191)
 fx=x-a;fy=y-b;fz=z-c
 v00=field3d[c,b,a]*(1-fx)+field3d[c,b,ax]*fx
 v01=field3d[c,by,a]*(1-fx)+field3d[c,by,ax]*fx
 v10=field3d[cz,b,a]*(1-fx)+field3d[cz,b,ax]*fx
 v11=field3d[cz,by,a]*(1-fx)+field3d[cz,by,ax]*fx
 return ((v00*(1-fy)+v01*fy)*(1-fz)+(v10*(1-fy)+v11*fy)*fz).astype(np.float32)

def states(mode,frame,key,center=False):
 sc.frame_set(frame)
 cutter=None
 if center:
  cutter=bpy.data.objects['SDF cutter | planar (move or rotate)']
  poly=cutter.data.polygons[1]
  normal=(cutter.matrix_world.to_3x3().inverted().transposed()@poly.normal).normalized()
  origin=cutter.matrix_world@cutter.data.vertices[poly.vertices[0]].co
  signed=normal.dot(Vector((0,0,25))-origin)
  cutter.location+=normal*signed
  bpy.context.view_layer.update()
 obj=bpy.data.objects['Receptacle | sculpted skin and achene pits'] if mode=='whole' else bpy.data.objects['SDF visible body | '+mode]
 deps=bpy.context.evaluated_depsgraph_get()
 ev=obj.evaluated_get(deps);m=ev.to_mesh()
 bm=bmesh.new();bm.from_mesh(m)
 nonmanifold=sum(not e.is_manifold for e in bm.edges)
 vol=float(bm.calc_volume(signed=True));bm.free()
 row={'evaluated_vertices':len(m.vertices),'polygons':len(m.polygons),'nonmanifold_edges':nonmanifold,'signed_volume_mm3_artist_scale':round(vol,3)}
 assert nonmanifold==0 and vol>0 and len(m.vertices)>10000,(variant,key,row)
 if mode!='whole':
  cap_ids=[p.index for p in m.polygons if p.material_index==2]
  assert len(cap_ids)>10000
  faces=np.array([m.polygons[idx].vertices[:] for idx in cap_ids],dtype=np.int32)
  assert faces.ndim==2 and faces.shape[1]==4,faces.shape
  areas=np.array([m.polygons[idx].area for idx in cap_ids],dtype=np.float32)
  corners=np.unique(faces)
  rest_all=np.empty(len(m.vertices)*3,np.float32)
  m.attributes['fruit_rest'].data.foreach_get('vector',rest_all)
  rest=rest_all.reshape(-1,3)
  v=np.empty(len(m.vertices),np.float32)
  m.attributes['v8_vascular_intensity'].data.foreach_get('value',v)
  sampled=sample_trilinear(volume[:,:,:,0],rest[corners])
  maxerr=float(np.max(np.abs(sampled-v[corners])))
  assert maxerr<.007,(maxerr,variant,key)
  b=sample_trilinear(volume[:,:,:,2],rest[corners])
  # Remap unique cap vertex to B, then quad midpoint in attribute values.
  b_all=np.zeros(len(m.vertices),np.float32);b_all[corners]=b
  R_quad=np.mean(v[faces],axis=1)
  B_quad=np.mean(b_all[faces],axis=1)
  area=float(areas.sum())
  row.update({'cap_polygons':len(cap_ids),'unique_cap_vertices':len(corners),'cap_area_mm2':round(area,3),
              'R_area_gt_0p3_pct':round(float(areas[R_quad>=.3].sum()/area*100),3),
              'B_area_gt_0p5_pct':round(float(areas[B_quad>=.5].sum()/area*100),3),
              'overlap_R0p3_B0p5_pct':round(float(areas[(B_quad>=.5)&(R_quad>=.3)].sum()/area*100),3),
              'R_cap_p95':round(float(np.percentile(v[corners],95)),4),
              'B_cap_p95':round(float(np.percentile(b,95)),4),
              'rest_R_interpolation_max_abs_error':round(maxerr,6)})
  assert row['B_area_gt_0p5_pct']<16,(variant,key,row)
  # Preserve enough central pith in the intentional centered planar diagnostic.
  if center:assert row['B_area_gt_0p5_pct']>2,(variant,key,row)
 ev.to_mesh_clear()
 if center:
  sc.frame_set(frame);cutter.location-=normal*signed
  bpy.context.view_layer.update()
 print('V19_QA_STATE',variant,key,json.dumps(row),flush=True)
 return row
out={'variant':variant,'scene_sha256':expected[variant],'source_v12_sha256':'300a2bfeaa86831220657b74fe8b00d4d7ec0b42f4ffefca863d6410c','states':{},'Blender':bpy.app.version_string}
for mode,frame,key,center in [('whole',1,'whole',False),('planar',20,'plane_oblique',False),('planar',20,'plane_centered',True),('bite',40,'bite_original',False)]:
 out['states'][key]=states(mode,frame,key,center)
c=bpy.data.objects['SDF cutter | spherical bite (move or scale)']
oldloc=c.location.copy();oldscale=c.scale.copy()
c.location.x-=4.;c.scale=c.scale*1.13
out['states']['bite_moved']=states('bite',40,'bite_moved')
c.location=oldloc;c.scale=oldscale
out['seconds']=round(time.monotonic()-t0,2)
(P/f'v19-qa-{variant}.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('V19_NATIVE_QA_PASS',variant,out['seconds'],flush=True)

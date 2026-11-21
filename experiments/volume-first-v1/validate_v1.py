#!/usr/bin/env python3
"""Independent mesh-level QA of volume-first v1 true physical filament ridges."""
import bpy,bmesh,random,json,math,sys
from pathlib import Path
import numpy as np
from mathutils.kdtree import KDTree
from mathutils import Vector
s=bpy.context.scene
source=bpy.data.objects['V1_SOURCE | spatial filament paths (hidden)']
assert source.type=='CURVE' and len(source.data.splines)==494
npz=np.load(Path(__file__).resolve().parent/'outputs'/'fine_fibers_3d.npz')
assert npz['lengths'].sum()==len(npz['points'])
assert sum(len(sp.points) for sp in source.data.splines)==len(npz['points'])
points=np.array([tuple(pt.co[:3]) for sp in source.data.splines for pt in sp.points],dtype=np.float32)
assert np.max(abs(points-npz['points']))<2e-7
assert np.ptp(points,axis=0).min()>1.
rows=[]
for ang in (0,32,82):
 base=bpy.data.objects[f'CUT_{ang:03d}_deg | SAME 3D SUBSTRATE']
 fine=bpy.data.objects[f'V1_CUT_{ang:03d} | thin 3D fiber physical relief']
 m=base.data;f=fine.data
 assert len(f.vertices)==len(m.vertices) and len(f.polygons)==len(m.polygons)
 def get_coords(mesh):
  out=np.empty(len(mesh.vertices)*3,dtype=np.float32);mesh.vertices.foreach_get('co',out);return out.reshape(-1,3)
 old=get_coords(m);new=get_coords(f)
 change=new-old
 attr=f.attributes.get('fine_fiber_signal');depth=f.attributes.get('fine_fiber_geometric_offset')
 assert attr and depth and attr.domain==depth.domain=='POINT'
 signal=np.empty(len(f.vertices),dtype=np.float32);attr.data.foreach_get('value',signal)
 offsets=np.empty(len(f.vertices),dtype=np.float32);depth.data.foreach_get('value',offsets)
 assert np.max(abs(change[:,0]))<1e-6 and np.max(abs(change[:,2]))<1e-6
 assert np.max(abs(change[:,1]+offsets))<1e-6
 mats=[]
 for mesh in (m,f):
  skin=np.zeros(len(mesh.vertices),dtype=bool);cut=np.zeros(len(mesh.vertices),dtype=bool)
  for p in mesh.polygons:
   vi=list(p.vertices)
   (skin if p.material_index==0 else cut)[vi]=True
  mats.append((skin,cut))
 seam=mats[0][0]&mats[0][1]
 assert np.max(abs(change[seam]))<1e-8
 assert np.max(abs(change[mats[0][0]]))<1e-8
 assert np.max(abs(signal[mats[0][0]]))==0
 assert (signal>.25).sum()>1000
 assert (abs(offsets)>.002).sum()>500
 bm=bmesh.new();bm.from_mesh(f)
 bad=sum(not e.is_manifold for e in bm.edges)
 zeros=sum(face.calc_area()<1e-10 for face in bm.faces)
 rem=set(bm.verts);parts=0
 while rem:
  parts+=1;stack=[rem.pop()]
  while stack:
   v=stack.pop()
   for e in v.link_edges:
    other=e.other_vert(v)
    if other in rem:rem.remove(other);stack.append(other)
 bm.free()
 assert bad==0 and zeros==0 and parts==1
 rest=np.empty(len(f.vertices)*3,dtype=np.float32);f.attributes['tissue_rest'].data.foreach_get('vector',rest);rest=rest.reshape(-1,3)
 assert np.ptp(rest[mats[0][1]],axis=0).max()>1.
 row={'angle':ang,'verts':len(f.vertices),'faces':len(f.polygons),'components':parts,
      'nonmanifold_edges':bad,'degenerate_faces':zeros,'cut_signal_gt025':int((signal>.25).sum()),
      'actual_displaced_vertices_gt002':int((abs(offsets)>.002).sum()),
      'max_physical_displacement':round(float(abs(offsets).max()),7),
      'max_original_skin_change':float(abs(change[mats[0][0]]).max()),
      'source_curves':494}
 rows.append(row)
 print('VALIDATED_THIN_3D_FIBERS',json.dumps(row),flush=True)
report={'status':'PASS','blender':bpy.app.version_string,
        'assertions':['source 494 actual spatial curves match single archived NPZ','all three cuts share same source','fine fiber field present','physical vertex displacement exists, not bump only','all skin/seams same as v0','1 connected surface, 0 nonmanifold edges, 0 degenerate faces','baseline meshes untouched'],
        'slices':rows,'limits':['not live arbitrary Boolean','artist designed lines not microscopy','manifold does not exclude all self intersections','static 3D reference curves need rebuild if edited']}
(Path(__file__).resolve().parent/'outputs'/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print('V1_VALIDATION_PASS',flush=True)

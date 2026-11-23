"""Run one fresh Blender process per pose to keep peak memory bounded."""
import bpy,bmesh,numpy as np,resource,json,sys,time,os
from pathlib import Path
ROOT=Path(os.environ.get('STRAWBERRY_V19_OUT',str(Path(__file__).resolve().parent))).expanduser().resolve()
arg=sys.argv[sys.argv.index('--')+1:]
v,pose=arg
assert v in ('a','b') and pose in ('whole','plane','bite','plane_moved','bite_moved')
s=bpy.context.scene
assert s['v19_variant']==v and bpy.context.preferences.filepaths.use_scripts_auto_execute==False
if pose=='plane_moved':
 ob=bpy.data.objects['SDF cutter | planar (move or rotate)']
 ob.location.y+=3.; ob.rotation_euler.x+=.1745329252
if pose=='bite_moved':
 ob=bpy.data.objects['SDF cutter | spherical bite (move or scale)']
 ob.location.x-=4.;ob.scale*=1.13
frame=1 if pose=='whole' else 40 if pose.startswith('bite') else 20
name='Receptacle | sculpted skin and achene pits' if pose=='whole' else 'SDF visible body | '+('bite' if pose.startswith('bite') else 'planar')
s.frame_set(frame)
t=time.perf_counter()
ob=bpy.data.objects[name]
ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
bm=bmesh.new();bm.from_mesh(m);nm=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);area=min(f.calc_area() for f in bm.faces);bm.free()
par=np.arange(len(m.vertices),dtype=np.int32)
def find(i):
 while par[i]!=i:
  par[i]=par[par[i]];i=int(par[i])
 return i
edges=np.empty(len(m.edges)*2,np.int32);m.edges.foreach_get('vertices',edges)
for a,b in edges.reshape(-1,2):
 pa,pb=find(int(a)),find(int(b))
 if pa!=pb:par[pb]=pa
for i in range(len(par)):par[i]=find(i)
_,counts=np.unique(par,return_counts=True)
parts=sorted([int(x) for x in counts],reverse=True)
cap=None
if pose!='whole':
 mats=np.empty(len(m.polygons),dtype=np.int32);m.polygons.foreach_get('material_index',mats);cap=int((mats==2).sum())
 for name in ('fruit_rest','v8_vascular_intensity'):
  assert name in m.attributes
row={'variant':v,'pose':pose,'frame':frame,'vertices':len(m.vertices),'faces':len(m.polygons),'nonmanifold_edges':nm,'volume_mm3':round(float(vol),4),'min_face_area_mm2':float(area),'connected_components':len(parts),'sizes_top12':parts[:12],'largest_fraction':round(parts[0]/len(m.vertices),6),'cap_faces':cap,'seconds_analysis':round(time.perf_counter()-t,2),'maxrss_kb':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
assert nm==0 and vol>0 and area>0
p=ROOT/f'v19{v}-{pose}-qa.json';p.write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
print('POSE_VERIFIED',json.dumps(row),flush=True)
ev.to_mesh_clear()

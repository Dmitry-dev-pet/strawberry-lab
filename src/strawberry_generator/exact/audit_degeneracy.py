"""One bounded center/oblique audit. Exact-zero metrics use coordinate float64 arithmetic.
A new zero-area render triangle is one whose coordinate multiset is absent from Fast.
No topology-only result is interpreted as physically clean geometry.
"""
from pathlib import Path
import sys,json,hashlib
from collections import Counter
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments/geometric-achene-pits-v1')]
from validate_pits import activate,activate_runtime,body_mesh,pose_knife,KNIFE,topology

def metrics(mesh):
 points=np.array([tuple(v.co) for v in mesh.vertices],dtype=np.float64)
 cap_edges=set();skin_edges=set()
 for f in mesh.polygons:
  target=cap_edges if f.material_index==1 else skin_edges;ids=list(f.vertices);target.update(tuple(sorted((a,b))) for a,b in zip(ids,ids[1:]+ids[:1]))
 seam=cap_edges&skin_edges;zero_edges=[e for e in seam if np.array_equal(points[e[0]],points[e[1]])]
 zero_faces=[]
 for f in mesh.polygons:
  p=points[list(f.vertices)];area=sum((np.cross(p[i]-p[0],p[i+1]-p[0]) for i in range(1,len(p)-1)),np.zeros(3))
  if np.dot(area,area)==0:zero_faces.append(f.index)
 mesh.calc_loop_triangles();zero_triangles=[]
 for t in mesh.loop_triangles:
  p=points[list(t.vertices)];area=np.cross(p[1]-p[0],p[2]-p[0])
  if np.dot(area,area)==0:zero_triangles.append(tuple(sorted(tuple(x) for x in p)))
 return {'zero_length_seam_edges':len(zero_edges),'zero_area_polygon_faces':len(zero_faces),'zero_area_render_triangles':len(zero_triangles)},Counter(zero_triangles)
result={}
for seed in [101,202]:
 path=ROOT/'build/generator-exact-v2'/f'seed{seed}.blend';bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False);s=bpy.context.scene;activate(s,'matched');r=activate_runtime();body=s.objects['Receptacle | canonical PR29 hull'];rows=[]
 for pose in [(0,0,0),(.08,29,32)]:
  bpy.ops.strawberry.exact_quality(exact=False);pose_knife(s.objects[KNIFE],pose);bpy.context.view_layer.update();fast=body_mesh(body);fm,fz=metrics(fast)
  assert bpy.ops.strawberry.exact_quality(exact=True)=={'FINISHED'};mesh=body_mesh(body);em,ez=metrics(mesh)
  rows.append({'pose':pose,'Fast':fm,'Exact':em,'inherited_zero_length_edges':fm['zero_length_seam_edges'],'inherited_zero_area_faces':fm['zero_area_render_triangles'],'inherited_zero_area_faces_basis':'Fast native render triangles','inherited_zero_area_native_polygons':fm['zero_area_polygon_faces'],'inherited_zero_area_render_triangles':fm['zero_area_render_triangles'],'newly_created_degenerate_faces':sum((ez-fz).values()),'new_steiner_face_guard':'raises on degenerate new Steiner child before displacement','definition':'New degenerate render-triangle coordinate multiset beyond native Fast tessellation; source-boundary signatures are not relabelled. Steiner children are separately guarded by fallback.','triangulation':r['session'].last['triangulation'],'BMesh_positive_connected_volume':topology(mesh),'physical_clean_geometry':not(em['zero_length_seam_edges'] or em['zero_area_render_triangles'])})
 result[str(seed)]={'scene_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'poses':rows}
(ROOT/'build/generator-exact-v2/degeneracy-audit.json').write_text(json.dumps({'status':'NOT_A_RELEASE_PASS','results':result,'conclusion':'seed101 center retains collapsed native boundary; BMesh manifoldness is insufficient for physical cleanliness. PR40 remains Fast-only.'},indent=2)+'\n')

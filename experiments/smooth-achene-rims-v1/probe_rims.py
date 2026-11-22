"""Read actual mesh shoulder edge length/dihedral, independent of bump/custom normals."""
from pathlib import Path
import sys,json,math
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'experiments/geometric-achene-pits-v1'))
from build_pits import saved_seats,BODY
scene_path,out=map(Path,sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.open_mainfile(filepath=str(scene_path.resolve()),use_scripts=False)
s=bpy.context.scene;mm=s.unit_settings.scale_length*1000;seats=saved_seats(s,mm)
kd=KDTree(len(seats))
for i,seat in enumerate(seats):kd.insert(seat.point,i)
kd.balance();bm=bmesh.new();bm.from_mesh(s.objects[BODY].data);bm.normal_update()
assert all(e.is_manifold and e.is_contiguous for e in bm.edges)
volume=bm.calc_volume(signed=True);assert volume>0
angles=[];lengths=[];counts={seat.obj.name:0 for seat in seats}
for edge in bm.edges:
 p=(edge.verts[0].co+edge.verts[1].co)/2;_,i,_=kd.find(p);a=seats[i].anchor
 d=(p-seats[i].point)*mm
 q=(d.dot(Vector(a.long_axis))/a.pit_length_radius_mm)**2+(d.dot(Vector(a.side_axis))/a.pit_width_radius_mm)**2
 if .35<q<1.25 and len(edge.link_faces)==2:
  angles.append(math.degrees(edge.calc_face_angle()));lengths.append(edge.calc_length()*mm);counts[seats[i].obj.name]+=1
bm.free()
r={'scene':str(scene_path),'vertices':len(s.objects[BODY].data.vertices),'raw_closed_positive_volume':True,'volume':volume,'shoulder_edges':len(angles),'seeds_sampled':sum(n>0 for n in counts.values()),'dihedral_degrees_p50_p95_max':np.percentile(angles,[50,95,100]).tolist(),'edge_length_mm_p50_p95_max':np.percentile(lengths,[50,95,100]).tolist(),'limitation':'Raw geometric dihedrals; denser edges mechanically reduce angles. Not a realism score.'}
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(r,indent=2)+'\n');print(r)

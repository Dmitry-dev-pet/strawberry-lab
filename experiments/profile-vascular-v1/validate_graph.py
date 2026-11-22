from pathlib import Path
import sys,json,hashlib
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];p=Path(sys.argv[sys.argv.index('--')+1]);out=Path(sys.argv[sys.argv.index('--')+2]);assert not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(p.resolve()),use_scripts=False)
s=bpy.context.scene;o=s.objects['ARTIST | 28 trunks + 264 seed-linked terminals'];nodes=json.loads(o['graph_manifest']);assert len(nodes)==292 and len(o.data.splines)==292
byid={n['id']:n for n in nodes};assert len(byid)==292
body=s.objects['Receptacle | canonical PR29 hull'];body.data.calc_loop_triangles();tree=BVHTree.FromPolygons([v.co for v in body.data.vertices],[t.vertices[:] for t in body.data.loop_triangles],all_triangles=True)
max_outside=-1e9;segments=0;lengths=[]
errors=[];parents=[];seen=[];mm=s.unit_settings.scale_length*1000
for n,sp in zip(nodes,o.data.splines):
 assert len(sp.points)==len(n['points'])
 for pt in sp.points:
  p0=Vector(pt.co[:3]);near,normal,_,_=tree.find_nearest(p0);max_outside=max(max_outside,(p0-near).dot(normal))
 length=0
 for a,b in zip(sp.points,sp.points[1:]):
  a,b=Vector(a.co[:3]),Vector(b.co[:3]);delta=b-a;length+=delta.length
  hit=tree.ray_cast(a,delta.normalized(),delta.length)
  assert hit[0] is None,'Centerline segment crosses hull'
  segments+=1
 lengths.append(length*mm)
 for actual,expected in zip(sp.points,n['points']):assert (Vector(actual.co[:3])-Vector(expected)).length<1e-6
 if 'seed_id' not in n:continue
 seed=s.objects[n['seed_id']];seen.append(seed.name);normal=Vector(seed['hull_normal_rest']);points=[seed.matrix_local@v.co for v in seed.data.vertices];expected=min(points,key=lambda p:p.dot(normal))
 errors.append((o.matrix_world@Vector(sp.points[-1].co[:3])-o.parent.matrix_world@expected).length*mm)
 trunk=byid[n['parent']];expected=Vector(trunk['points'][0]).lerp(Vector(trunk['points'][-1]),n['parent_t']);parents.append((Vector(sp.points[0].co[:3])-expected).length*mm)
assert max_outside<0
assert len(set(seen))==264 and max(errors)<1e-4 and max(parents)<1e-4
out.write_text(json.dumps({'status':'PASS','sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'interior_centerline_segments_ray_checked':segments,'max_signed_outside_reference_mm':max_outside*mm,'path_length_reference_mm_range':[min(lengths),max(lengths)],'geodesic_claim':False,'unique_seed_ids':264,'trunks':28,'actual_endpoint_max_error_mm':max(errors),'parent_connection_max_error_reference_mm':max(parents),'assumption':'ARTIST graph, no biological claim'},indent=2)+'\n')

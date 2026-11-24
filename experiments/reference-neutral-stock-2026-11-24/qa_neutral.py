"""Independent saved-scene checks of the shared native deformation, topology and seats.
Does not change the source .blend. Reuses only original mathematical contract.
"""
import bpy,bmesh,numpy as np,sys,json,hashlib,time
from pathlib import Path
from mathutils.bvhtree import BVHTree
here=Path(__file__).resolve().parent
sys.path[:0]=[str(here),str(here/'deps'/'src'),str(here.parents[1]/'src')]
from neutral_contract import ShapeState
NAMES=('SL Neutral Skin','SL Neutral Achenes','SL Anchor Set','SL Pit Seats')
def sha(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def file_sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def co(me):
 a=np.empty(3*len(me.vertices),np.float32);me.vertices.foreach_get('co',a);return a.reshape(-1,3)
def point_attr(me,name):
 a=me.attributes[name];vec=a.data_type=='FLOAT_VECTOR';typ=np.float32 if vec or a.data_type=='FLOAT' else np.int32
 out=np.empty(len(a.data)*(3 if vec else 1),typ);a.data.foreach_get('vector' if vec else 'value',out);return out.reshape(-1,3) if vec else out
def polys(me):return [tuple(p.vertices) for p in me.polygons]
def topology(me):
 bm=bmesh.new();bm.from_mesh(me);r={'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'inconsistent_edges':sum(not e.is_contiguous for e in bm.edges),'signed_volume_mm3':bm.calc_volume(signed=True)};bm.free();me.calc_loop_triangles();r['degenerate_triangles']=sum(t.area<1e-10 for t in me.loop_triangles);assert r['nonmanifold_edges']==r['inconsistent_edges']==r['degenerate_triangles']==0 and r['signed_volume_mm3']>0,r;return r

def main():
 src,receipt,out=map(Path,sys.argv[sys.argv.index('--')+1:]);r=json.loads(receipt.read_text());assert file_sha(src)==r['scene_sha'] and not out.exists();bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False)
 root=bpy.data.objects['SL Shape Controller | edit Custom Properties'];objs=[bpy.data.objects[n] for n in NAMES];count=r['recipe']['achene_count'];height=r['recipe']['height_mm'];raw={o.name:co(o.data) for o in objs};faces={o.name:polys(o.data) for o in objs};assert len(set(o.modifiers[0].node_group for o in objs))==1
 for o in objs:
  assert sha(raw[o.name])==r['objects'][o.name]['rest_sha'];assert np.array_equal(raw[o.name],point_attr(o.data,'sl_rest_position'));o.hide_set(False)
 assert root['anchor_digest']==r['anchor_digest'] and root['neutral_stock_key']==r['stock_key']
 ids=[row['id'] for row in r['anchor_rows']];assert len(set(ids))==count
 assert np.max(np.abs(raw[NAMES[2]]-np.array([row['anchor']['point'] for row in r['anchor_rows']])))<1e-5
 assert np.max(np.abs(raw[NAMES[3]]-np.array([row['seat_mm'] for row in r['anchor_rows']])))<1e-5
 records=[];identity=None;seed_idx=point_attr(objs[1].data,'sl_anchor_index');assert set(seed_idx)==set(range(count))
 seedfaces=[[] for _ in range(count)]
 for f in faces[NAMES[1]]:
  i=int(seed_idx[f[0]]);assert all(seed_idx[j]==i for j in f);start=r['anchor_rows'][i]['seed_vertex_start'];seedfaces[i].append(tuple(j-start for j in f))
 for name,state in [('neutral',ShapeState()),('deformed',ShapeState(.16,-.10,1.12)),('restored',ShapeState())]:
  t=time.perf_counter();root['shape_a']=state.a;root['shape_b']=state.b;root['shape_h']=state.h;root.update_tag();bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();meshes=[];q={'state':name,'shape':[state.a,state.b,state.h],'objects':{}}
  for o in objs:
   ev=o.evaluated_get(dg);me=ev.to_mesh();assert me is not None;meshes.append((ev,me));xyz=co(me);expected=state.forward(raw[o.name],height);err=float(np.max(np.abs(xyz-expected)));inv=float(np.max(np.abs(state.inverse(xyz,height)-raw[o.name])));assert err<3e-5 and inv<3e-5,(o.name,err,inv);assert np.array_equal(point_attr(me,'sl_rest_position'),raw[o.name]);assert np.array_equal(co(o.data),raw[o.name]);assert polys(me)==faces[o.name];assert root['anchor_digest']==r['anchor_digest'] and root['neutral_stock_key']==r['stock_key'];q['objects'][o.name]={'vertices':len(xyz),'faces':len(me.polygons),'max_forward_error_mm':err,'max_inverse_error_mm':inv,'position_sha':sha(xyz),'max_displacement_mm':float(np.linalg.norm(xyz-raw[o.name],axis=1).max())}
   if len(me.polygons):q['objects'][o.name].update(topology(me))
   if 'sl_anchor_index' in me.attributes:assert np.array_equal(point_attr(me,'sl_anchor_index'),point_attr(o.data,'sl_anchor_index'))
  body=meshes[0][1];seed=meshes[1][1];b=co(body);sv=co(seed);seat=co(meshes[3][1]);tree=BVHTree.FromPolygons(b.tolist(),faces[NAMES[0]]);contacts=0;seat_dist=[]
  for i,row in enumerate(r['anchor_rows']):
   start=row['seed_vertex_start'];end=start+row['seed_vertex_count'];v=sv[start:end];pairs=tree.overlap(BVHTree.FromPolygons(v.tolist(),seedfaces[i]));assert pairs,(name,i,'no contact');contacts+=1;hit=tree.find_nearest(seat[i]);assert hit[0] is not None;seat_dist.append(float(hit[3]));
  assert contacts==count and max(seat_dist)<.03,(name,max(seat_dist));q.update(achene_skin_contacts=contacts,max_seat_surface_distance_mm=max(seat_dist),elapsed_seconds=time.perf_counter()-t)
  coords_hashes=[x['position_sha'] for x in q['objects'].values()]
  if name=='neutral':identity=coords_hashes
  if name=='deformed':assert q['objects'][NAMES[0]]['max_displacement_mm']>2 and coords_hashes!=identity
  if name=='restored':assert coords_hashes==identity
  records.append(q)
  for ev,_ in meshes:ev.to_mesh_clear()
  print('PASS',count,name,contacts,q['max_seat_surface_distance_mm'],flush=True)
 result={'source_sha':r['scene_sha'],'count':count,'states':records,'all_pass':True,'blender_version':bpy.app.version_string};out.write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()

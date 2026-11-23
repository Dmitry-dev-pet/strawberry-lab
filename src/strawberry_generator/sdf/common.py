from pathlib import Path
import sys,math,json,time,hashlib
import bpy,bmesh,numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'experiments/profile-vascular-v1'),str(ROOT/'experiments/exact-tissue-zones-v1')]
from profile_probe import forward,inverse
from atlas import TissueAtlas,ATLAS
BODY='Receptacle | canonical PR29 hull';PLANE='SDF | editable plane halfspace';SPHERE='SDF | editable sphere bite';REST='sdf_rest_position'

def state(mode,voxel=.20,oblique=False):
 s=bpy.context.scene;b=s.objects[BODY];p=s.objects[PLANE];p.location=(0,.08 if oblique else 0,0);p.rotation_euler=(math.radians(29) if oblique else 0,0,math.radians(32) if oblique else 0);b['sdf_mode']=mode;b['sdf_voxel_mm']=voxel;b.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()

def evaluated(obj):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get());copy=me.copy();ev.to_mesh_clear();return copy

def mesh_metrics(me):
 bm=bmesh.new();bm.from_mesh(me);nonmanifold=sum(not e.is_manifold for e in bm.edges);seen=set();components=0
 for start in bm.verts:
  if start in seen:continue
  components+=1;stack=[start];seen.add(start)
  while stack:
   v=stack.pop()
   for e in v.link_edges:
    u=e.other_vert(v)
    if u not in seen:seen.add(u);stack.append(u)
 volume=bm.calc_volume(signed=True);bm.free();p=np.array([v.co[:] for v in me.vertices],dtype=np.float64);edges=np.array([e.vertices[:] for e in me.edges]);zero_edges=int(np.sum(np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1)==0));me.calc_loop_triangles();ids=np.array([t.vertices[:] for t in me.loop_triangles]);q=p[ids];cross=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);zero_tri=int(np.sum(np.einsum('ij,ij->i',cross,cross)==0))
 return {'vertices':len(p),'triangles':len(ids),'nonmanifold_edges':nonmanifold,'components':components,'signed_volume':volume,'zero_edges':zero_edges,'zero_render_triangles':zero_tri}

def digest_geometry():
 return {o.name:hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(f.vertices) for f in o.data.polygons]) if o.type=='MESH' else [[(tuple(p.co),p.radius) for p in sp.points] for sp in o.data.splines]).encode()).hexdigest() for o in bpy.context.scene.objects if o.type in {'MESH','CURVE'} and not o.name.startswith('SDF |')}

def atlas_sha():return hashlib.sha256(bytes(bpy.data.images[ATLAS].packed_file.data)).hexdigest()

def tissue_probes(me):
 s=bpy.context.scene;params=json.loads(s['SDF params']);attr=me.attributes[REST];atlas=TissueAtlas(bpy.data.images[ATLAS]);cap=next(m for m in me.materials if m and m.name.startswith('SDF | inherited'));index=list(me.materials).index(cap);indices=sorted({i for f in me.polygons if f.material_index==index for i in f.vertices});samples=[]
 for i in indices[::max(1,len(indices)//3)][:3]:
  physical=me.vertices[i].co;rest=Vector(attr.data[i].vector);reference=Vector(inverse(physical,params));error=(rest-reference).length;assert error<1e-6,error
  x,y,z=atlas.grid(rest);ix,iy,iz=map(int,[x,y,z]);rgb=atlas.rgb[iz,iy,ix].tolist()
  samples.append({'physical':list(physical),'stored_rest':list(rest),'inverse_error_model_units':error,'nearest_RGB_voxel':rgb,'trilinear_atlas_green':atlas.sample_green(rest)})
 assert len(samples)==3
 return samples

def pit_depths(me):
 s=bpy.context.scene;params=json.loads(s['SDF params']);mm=s.unit_settings.scale_length*1000;tree=BVHTree.FromPolygons([v.co for v in me.vertices],[f.vertices[:] for f in me.polygons],all_triangles=False);depth=[]
 for o in s.objects:
  if o.get('role')!='achene':continue
  a=np.array(o['nonlinear_original_anchor']);n=np.array(o['hull_normal_rest']);J=np.column_stack([(np.array(forward(a+np.eye(3)[i]*1e-5,params))-np.array(forward(a-np.eye(3)[i]*1e-5,params)))/(2e-5) for i in range(3)]);normal=Vector(np.linalg.solve(J.T,n)).normalized();point=Vector(forward(a,params));hit=tree.ray_cast(point+normal*.08,-normal,.25)[0]
  if hit is not None:depth.append((point-hit).dot(normal)*mm)
 assert len(depth)==264
 return {'anchors':264,'depth_mm_min':min(depth),'depth_mm_median':float(np.median(depth)),'depth_mm_max':max(depth),'positive_depth_count':sum(x>0 for x in depth)}

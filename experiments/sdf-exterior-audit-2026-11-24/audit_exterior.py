"""Read-only whole-fruit exterior audit of the pinned integrated Strawberry Lab scene."""
import bpy, numpy as np, math, json, sys, hashlib, time
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from collections import Counter
src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert not out.exists();assert hashlib.sha256(src.read_bytes()).hexdigest()=='790dc4adbd9025b56e7833c2cedb8ada83c0e9b738ac294f96889fbb52e0e215'
bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False); s=bpy.context.scene;b=s.objects['Receptacle | canonical PR29 hull'];mm=s.unit_settings.scale_length*1000;params=json.loads(s['SDF params']) if isinstance(s['SDF params'],str) else list(s['SDF params']);a0,b0,h=params
assert np.allclose(np.array(b.matrix_world),np.eye(4));seeds=sorted((o for o in s.objects if o.get('role')=='achene'),key=lambda o:o.name);assert len(seeds)==264
# Same existing forward map as experiments/profile-vascular-v1/profile_probe.py.
def forward(p):
 x,y,z=p; k=1+a0*math.exp(-((z-.5)/.36)**2)+b0*math.exp(-((z+.3)/.4)**2);return np.array([x*k,y*k,z*h])
anchors=[]
for o in seeds:
 q=np.array(o['nonlinear_original_anchor']);n=np.array(o['hull_normal_rest']);J=np.column_stack([(forward(q+np.eye(3)[i]*1e-5)-forward(q-np.eye(3)[i]*1e-5))/(2e-5) for i in range(3)]);anchors.append((Vector(forward(q)),Vector(np.linalg.solve(J.T,n)).normalized()))
# Closed seed solid BVHs. This scene stores geometry in physical body coordinates.
seed_trees=[]
for o in seeds:
 o.data.calc_loop_triangles(); seed_trees.append(BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[tuple(t.vertices) for t in o.data.loop_triangles],all_triangles=True))
def distribution(x):
 return dict(min=float(np.min(x)),p10=float(np.quantile(x,.1)),median=float(np.median(x)),p90=float(np.quantile(x,.9)),max=float(np.max(x)))
def inspect(mesh,label):
 t0=time.monotonic(); mesh.calc_loop_triangles(); tree=BVHTree.FromPolygons([v.co for v in mesh.vertices],[tuple(t.vertices) for t in mesh.loop_triangles],all_triangles=True);d=[];contacts=[]
 for (p,n),st in zip(anchors,seed_trees):
  hit=tree.ray_cast(p+.08*n,-n,.25)[0]; d.append((p-hit).dot(n)*mm if hit is not None else None);contacts.append(len(tree.overlap(st)))
 assert all(x is not None for x in d),d
 arr=np.array([v.co for v in mesh.vertices]);return dict(label=label,verts=len(arr),triangles=len(mesh.loop_triangles),pit_depth_mm=distribution(d),positive_depths=sum(x>0 for x in d),depths_mm=d,seed_triangle_contact_count=sum(x>0 for x in contacts),seed_contact_triangle_pairs=distribution(contacts),seed_contact_pair_counts=contacts,dimensions_mm=((arr.max(0)-arr.min(0))*mm).tolist(),seconds=time.monotonic()-t0)
results=[inspect(b.data,'raw source')]
for vox in (.32,.20):
 b['sdf_mode']=0;b['sdf_voxel_mm']=vox;b.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update();ev=b.evaluated_get(dg);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg);results.append(inspect(me,f'whole SDF {vox:.2f} mm'));ev.to_mesh_clear();print('QA',results[-1]['label'],results[-1]['pit_depth_mm'],results[-1]['seed_triangle_contact_count'],flush=True)
skin=b.data.materials[0];g=skin.node_tree;bs=next(n for n in g.nodes if n.type=='BSDF_PRINCIPLED');
def sock(i):
 if i.is_linked:return {'link':i.links[0].from_node.name,'socket':i.links[0].from_socket.name}
 v=i.default_value;return {'value':list(v) if hasattr(v,'__len__') and not isinstance(v,str) else v}
inputs={k:sock(bs.inputs[k]) for k in ['Base Color','Roughness','Normal','Coat Weight','Coat Roughness','Coat Normal','Subsurface Weight','Subsurface Scale']};ramp=g.nodes['Color Ramp.003'];rough=[{'position':x.position,'rgba':list(x.color)} for x in ramp.color_ramp.elements];attributes=[n.attribute_name for n in g.nodes if n.type=='ATTRIBUTE'];nodes=[{'name':n.name,'label':n.label,'type':n.bl_idname} for n in g.nodes];
# Trace the actual upstream dependencies of material sockets, rather than rely on labels.
def parents(n, seen=None):
 seen=set() if seen is None else seen
 if n.name in seen:return seen
 seen.add(n.name)
 for i in n.inputs:
  for link in i.links:parents(link.from_node,seen)
 return seen
branches={k:sorted(parents(bs.inputs[k].links[0].from_node)) if bs.inputs[k].is_linked else [] for k in inputs}; report={'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'mm_per_bu':mm,'params':params,'role_counts':dict(Counter(str(o.get('role')) for o in s.objects)),'object_count':len(s.objects),'seed_count':len(seeds),'seed_vertices_distribution':distribution([len(o.data.vertices) for o in seeds]),'skin_material':skin.name,'skin_inputs':inputs,'roughness_ramp':rough,'skin_attributes':attributes,'skin_nodes':nodes,'socket_dependencies':branches,'results':results};out.write_text(json.dumps(report,indent=2)+'\n');print('DONE',out,flush=True)

"""Independently reopen control/candidate and compare evaluated geometry and material graphs."""
import bpy,numpy as np,sys,json,hashlib,math,time
from pathlib import Path
A,B,pose,out=sys.argv[sys.argv.index('--')+1:];out=Path(out);assert not out.exists()
PIN='790dc4adbd9025b56e7833c2cedb8ada83c0e9b738ac294f96889fbb52e0e215';BODY='Receptacle | canonical PR29 hull';JUICE='SL Juice | independent pool surface';SKIN='SDF | source skin at true rest_position';P='SL Skin Optics | '
sha=lambda b:hashlib.sha256(b).hexdigest();file_sha=lambda p:sha(Path(p).read_bytes())
assert file_sha(A)==PIN

def value(x):
 if isinstance(x,(str,int,float,bool,type(None))):return x
 if isinstance(x,bpy.types.ID):return [x.bl_rna.identifier,x.name]
 try:return [value(y) for y in x]
 except TypeError:return str(x)
def graphs():
 d={}
 def walk(g,k):
  if k in d:return
  nodes={}
  for n in g.nodes:
   r=dict(type=n.bl_idname,inputs=[(s.identifier,value(getattr(s,'default_value',None))) for s in n.inputs],outputs=[(s.identifier,value(getattr(s,'default_value',None))) for s in n.outputs],props={p:value(getattr(n,p)) for p in ('operation','feature','voronoi_dimensions','noise_dimensions','blend_type','distribution','subsurface_method','data_type','attribute_name','image','node_tree','clamp','interpolation_type','target_element','transform_space') if hasattr(n,p)})
   if n.type=='VALTORGB':r['ramp']=[(e.position,list(e.color)) for e in n.color_ramp.elements]
   nodes[n.name]=r
  d[k]=dict(nodes=nodes,links=sorted([l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in g.links))
  for n in g.nodes:
   if n.type=='GROUP' and n.node_tree:walk(n.node_tree,'group:'+n.node_tree.name)
 for m in bpy.data.materials:
  if m.node_tree:walk(m.node_tree,'material:'+m.name)
 for g in bpy.data.node_groups:
  if g.bl_idname=='GeometryNodeTree':walk(g,'group:'+g.name)
 return d

def arr(collection,prop,n,dtype):
 a=np.empty(len(collection)*n,dtype);collection.foreach_get(prop,a);return a

def mesh(o,dg):
 ev=o.evaluated_get(dg);m=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg);m.calc_loop_triangles();x=arr(m.vertices,'co',3,np.float32);idx=arr(m.loop_triangles,'vertices',3,np.int32);mat=arr(m.polygons,'material_index',1,np.int32);attrs={}
 for a in m.attributes:
  if a.name not in ['achene_pit','sdf_rest_position','sl_cell_dome','sl_cell_reference_position','sl_cell_reference_normal','sl_vascular_core','sl_vascular_halo','sl_ring_relative','sl_juice_clearance_mm','sl_juice_tissue_position','sl_juice_final_level_mm','sl_juice_envelope']:continue
  n,prop=(3,'vector') if a.data_type=='FLOAT_VECTOR' else (1,'value');attrs[a.name]=sha(arr(a.data,prop,n,np.float32).tobytes())
 pit=None
 if o.name==BODY and 'achene_pit' in m.attributes:
  q=arr(m.attributes['achene_pit'].data,'value',1,np.float32);pit={'points':len(q),'gt_001':int((q>.01).sum()),'gt_070':int((q>.70).sum()),'min':float(q.min()),'max':float(q.max())}
 r=dict(vertices=len(m.vertices),faces=len(m.polygons),coords_sha=sha(x.tobytes()),topology_sha=sha(idx.tobytes()),face_material_sha=sha(mat.tobytes()),materials=[v.name if v else None for v in m.materials],attributes=attrs,matrix=[list(x) for x in ev.matrix_world],pit=pit)
 ev.to_mesh_clear();return r

def snap(p):
 bpy.ops.wm.open_mainfile(filepath=p,use_scripts=False);s=bpy.context.scene;b=s.objects[BODY]
 b['sdf_mode']={'whole':0,'plane':1,'bite':2}[pose];b['sdf_voxel_mm']=.32;b['cell_surface_gain']=1.;b['cell_surface_detail']=1;b['vascular_relief_gain']=1.;b['juice_surface_gain']=1.
 q=s.objects['SDF | editable plane halfspace'];q.location=(0,0,0);q.rotation_euler=(0,0,0);b.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
 gs=graphs();obs={}
 for o in sorted(s.objects,key=lambda o:o.name):
  if o.type=='MESH' and (o.name in (BODY,JUICE) or o.get('role') in ('achene','sepal','pedicel')):obs[o.name]=mesh(o,dg)
 images={i.name:sha(bytes(i.packed_file.data)) for i in bpy.data.images if i.packed_file}
 return gs,obs,images

t=time.monotonic();ga,ma,ia=snap(A);gb,mb,ib=snap(B);assert ma==mb,('mesh mismatch',[k for k in ma if ma[k]!=mb.get(k)])
assert ia==ib;assert ga.keys()==gb.keys();key='material:'+SKIN
new=sorted(set(gb[key]['nodes'])-set(ga[key]['nodes']));assert len(new)==16 and all(x.startswith(P) for x in new)
assert all(ga[k]==gb[k] for k in ga if k!=key)
assert ga[key]['nodes']=={k:v for k,v in gb[key]['nodes'].items() if k not in new}
oldlinks=ga[key]['links'];newlinks=gb[key]['links'];removed=[x for x in oldlinks if x not in newlinks];added=[x for x in newlinks if x not in oldlinks];assert len(removed)==1 and removed[0][2:]==['Principled BSDF','Roughness'],removed
assert sorted(x[3] for x in added if x[2]=='Principled BSDF')==['Coat Weight','Roughness'];assert all(x[0] in new or x[2] in new for x in added)
result=dict(status='PASS',pose=pose,voxel_mm=.32,source_sha=file_sha(A),scene_sha=file_sha(B),geometry_objects_compared=len(ma),exact_geometry_and_attributes=True,graph_trees_compared=len(ga),other_graphs_identical=True,packed_images_identical=len(ia),new_nodes=new,changed_sockets=['Coat Weight','Roughness'],body=mb[BODY],juice=mb[JUICE],mesh_object_digest=sha(json.dumps(mb,sort_keys=True).encode()),seconds=time.monotonic()-t)
out.write_text(json.dumps(result,indent=2)+'\n');print('PASS',pose,len(ma),len(ga),'trees',len(ia),'packed images',result['seconds'],flush=True)

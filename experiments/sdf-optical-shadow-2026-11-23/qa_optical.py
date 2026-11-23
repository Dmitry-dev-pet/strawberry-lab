"""Independent saved-scene QA for a shader/visibility-only experiment.
Compare evaluated body and liquid geometry with the pinned PR50 Juice QA.
Also compare all material node input defaults/links, including nested trees.
"""
from pathlib import Path
import bpy,sys,json,hashlib,numpy as np
src,scene,prior,pose,out=sys.argv[sys.argv.index('--')+1:];prior=Path(prior);out=Path(out);assert not out.exists()
sys.path.insert(0,str(prior.parent));from qa_juice_surface import state,BODY,JUICE,body_snap,juice_snap
PIN='2fcc5a8e65273d3ac0f633f887e4f5522da9642c375f5d4499e891bc2889d394'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def val(x):
 if isinstance(x,(str,int,float,bool,type(None))):return x
 if isinstance(x,bpy.types.ID):return [x.bl_rna.identifier,x.name]
 try:return [val(y) for y in x]
 except TypeError:return str(x)
def graph(g,visited,key):
 if key in visited:return
 nodes=[]
 for n in sorted(g.nodes,key=lambda n:n.name):
  entry={'name':n.name,'type':n.bl_idname,'input':[(s.identifier,val(getattr(s,'default_value',None))) for s in n.inputs],'props':{p:val(getattr(n,p,None)) for p in ('operation','feature','voronoi_dimensions','blend_type','distribution','subsurface_method','data_type','attribute_name','image','node_tree') if hasattr(n,p)}}
  if n.type=='VALTORGB':entry['ramp']=[(e.position,list(e.color)) for e in n.color_ramp.elements]
  nodes.append(entry)
 links=sorted((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in g.links)
 visited[key]={'nodes':nodes,'links':links}
 for n in g.nodes:
  if n.type=='GROUP' and n.node_tree:graph(n.node_tree,visited,"group:"+n.node_tree.name)
def materials():
 d={}
 for m in sorted(bpy.data.materials,key=lambda m:m.name):
  if m.node_tree:graph(m.node_tree,d,"material:"+m.name)
 return hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest(),len(d)
def mesh_topology(o):
 dg=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dg);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg);me.calc_loop_triangles();idx=np.empty(len(me.loop_triangles)*3,np.int32);me.loop_triangles.foreach_get("vertices",idx);result=hashlib.sha256(idx.tobytes()).hexdigest();ev.to_mesh_clear();return result
def visibility():
 return {o.name:[o.visible_camera,o.visible_diffuse,o.visible_glossy,o.visible_transmission,o.visible_volume_scatter,o.visible_shadow] for o in bpy.context.scene.objects}
assert sha(src)==PIN
bpy.ops.wm.open_mainfile(filepath=src,use_scripts=False);ma=materials();va=visibility();assert ma[1]>=7;state(bpy.data.objects[BODY],pose,.32,1.);old_juice_topology=mesh_topology(bpy.data.objects[JUICE])
bpy.ops.wm.open_mainfile(filepath=scene,use_scripts=False);mb=materials();vb=visibility();assert ma==mb
expected={k:list(v) for k,v in va.items()};assert expected[JUICE][-1];expected[JUICE][-1]=False;assert vb==expected
s=bpy.context.scene;b=bpy.data.objects[BODY];j=bpy.data.objects[JUICE];state(b,pose,.32,1.)
br,p,cap,skin=body_snap(b);jr=juice_snap(j,s.unit_settings.scale_length*1000,p,cap,skin);old=json.loads((prior.parent/f'qa-{pose}.json').read_text());assert old['scene_sha256']==PIN
assert br==old['states']['1.0']['body'],('body mismatch',br,old['states']['1.0']['body'])
new_juice_topology=mesh_topology(j);assert new_juice_topology==old_juice_topology
assert jr==old['states']['1.0']['juice'],('juice mismatch',jr,old['states']['1.0']['juice'])
report={'status':'PASS','pose':pose,'voxel_mm':.32,'source_sha256':PIN,'scene_sha256':sha(scene),'same_material_graph_digest':ma[0],'material_trees_compared':ma[1],'only_visibility_change':'juice visible_shadow True->False','juice_topology_sha256':new_juice_topology,'body':br,'juice':jr}
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

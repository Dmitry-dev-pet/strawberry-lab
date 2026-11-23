"""Independently reopen the control/candidate, verify the cap-only material diff,
and compare actual evaluated geometry against earlier verified receipts."""
import bpy,sys,json,hashlib,numpy as np
from pathlib import Path
src,scene,pose,prior,old_script,out=sys.argv[sys.argv.index('--')+1:];src=Path(src);scene=Path(scene);out=Path(out);assert not out.exists()
sys.path.insert(0,str(Path(old_script).parent));from qa_juice_surface import state,BODY,JUICE
PIN='361696819fd44733d560e3f59b101cd11f59862e7ebd7b7f83ce94fd07909963';PREFIX='SL Pigment | ';CAP='SDF | inherited 150^3 tissue + own multiscale wetness'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def arrsha(a):return hashlib.sha256(a.tobytes()).hexdigest()
def value(x):
 if isinstance(x,(str,int,float,bool,type(None))):return x
 if isinstance(x,bpy.types.ID):return [x.bl_rna.identifier,x.name]
 try:return [value(y) for y in x]
 except TypeError:return str(x)
def inventory(skip):
 d={}
 def walk(g,key):
  if key in d:return
  nodes=[]
  for n in sorted(g.nodes,key=lambda x:x.name):
   if skip and n.name.startswith(PREFIX):continue
   entry={'name':n.name,'type':n.bl_idname,'inputs':[(s.identifier,value(getattr(s,'default_value',None))) for s in n.inputs],'props':{p:value(getattr(n,p)) for p in ('operation','feature','voronoi_dimensions','blend_type','distribution','subsurface_method','data_type','attribute_name','image','node_tree','interpolation_type','clamp','mode') if hasattr(n,p)}}
   if n.type=='VALTORGB':entry['ramp']=[(e.position,list(e.color)) for e in n.color_ramp.elements]
   nodes.append(entry)
  links=sorted((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in g.links if not(skip and (l.from_node.name.startswith(PREFIX) or l.to_node.name.startswith(PREFIX))))
  d[key]={'nodes':nodes,'links':links}
  for n in g.nodes:
   if n.type=='GROUP' and n.node_tree:walk(n.node_tree,'group:'+n.node_tree.name)
 for m in bpy.data.materials:
  if m.node_tree:walk(m.node_tree,'material:'+m.name)
 return d
def vis():return {o.name:[o.visible_camera,o.visible_diffuse,o.visible_glossy,o.visible_transmission,o.visible_volume_scatter,o.visible_shadow] for o in bpy.context.scene.objects}
def smooth(x,a,b):
 t=np.clip((x-a)/(b-a),0,1);return t*t*t*(t*(6*t-15)+10)
def snap(obj,fields=False):
 dg=bpy.context.evaluated_depsgraph_get();ev=obj.evaluated_get(dg);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg);n=len(me.vertices);p=np.empty(n*3,np.float32);me.vertices.foreach_get('co',p);me.calc_loop_triangles();idx=np.empty(len(me.loop_triangles)*3,np.int32);me.loop_triangles.foreach_get('vertices',idx);report={'vertices':n,'faces':len(me.polygons),'coords_sha':arrsha(p),'topology_sha':arrsha(idx)};stats=None
 if fields and pose!='whole':
  mi=next(i for i,m in enumerate(me.materials) if m and m.name==CAP);mask=np.zeros(n,bool)
  for f in me.polygons:
   if f.material_index==mi:mask[list(f.vertices)]=True
  data={};hashes={}
  for name in ['sdf_rest_position','sl_cell_dome','sl_vascular_core','sl_vascular_halo','sl_vascular_cell_multiplier']:
   a=me.attributes[name];assert a.domain=='POINT';v=np.empty(n*(3 if name=='sdf_rest_position' else 1),np.float32);a.data.foreach_get('vector' if name=='sdf_rest_position' else 'value',v);assert np.isfinite(v).all();hashes[name]=arrsha(v);data[name]=v.reshape(n,-1)[mask]
  r=np.linalg.norm(data['sdf_rest_position'][:,:2],axis=1);z=data['sdf_rest_position'][:,2];effective=data['sl_cell_dome'][:,0]*data['sl_vascular_cell_multiplier'][:,0];cell=smooth(effective,0,.85);halo=.28*smooth(data['sl_vascular_halo'][:,0],.10,.65);core=.32*smooth(data['sl_vascular_core'][:,0],.19,.72);pith=.90*(1-smooth(r/(.055+.125*np.exp(-1.6*(z-.02)**2)),.40,1.40))
  stats={'cap_vertices':int(mask.sum()),'attribute_hashes':hashes,'weights':{k:{'min':float(v.min()),'max':float(v.max()),'mean':float(v.mean()),'positive_fraction':float((v>1e-5).mean())} for k,v in [('cell',cell),('halo',halo),('core',core),('pith',pith)]}}
  assert all(stats['weights'][k]['max']>0 for k in ('cell','halo','core'));assert pose!='plane' or stats['weights']['pith']['max']>0
 ev.to_mesh_clear();return report,stats
assert sha(src)==PIN
bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False);old=inventory(False);oldvis=vis();state(bpy.data.objects[BODY],pose,.32,1.);oldbody,oldfields=snap(bpy.data.objects[BODY],True);oldjuice,_=snap(bpy.data.objects[JUICE]);g=bpy.data.materials[CAP].node_tree;pr=next(n for n in g.nodes if n.type=='BSDF_PRINCIPLED');l=pr.inputs['Base Color'].links[0];removed=(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier);old['material:'+CAP]['links'].remove(removed)
bpy.ops.wm.open_mainfile(filepath=str(scene),use_scripts=False);assert inventory(True)==old,'Old nodes, parameters or unrelated links changed';assert vis()==oldvis
new=[];links=[]
for m in bpy.data.materials:
 if not m.node_tree:continue
 for n in m.node_tree.nodes:
  if n.name.startswith(PREFIX):new.append((m.name,n.name,n.bl_idname))
 for l in m.node_tree.links:
  if l.from_node.name.startswith(PREFIX) and not l.to_node.name.startswith(PREFIX):links.append((m.name,l.to_node.bl_idname,l.to_socket.name))
assert len(new)==27 and all(x[0]==CAP for x in new);assert links==[(CAP,'ShaderNodeBsdfPrincipled','Base Color')],links
state(bpy.data.objects[BODY],pose,.32,1.);bs,fields=snap(bpy.data.objects[BODY],True);js,_=snap(bpy.data.objects[JUICE]);assert bs==oldbody and js==oldjuice and fields==oldfields
prev=json.loads((Path(prior)/f'qa-{pose}.json').read_text());assert prev['scene_sha256']==PIN and prev['body']==bs;assert js['vertices']==prev['juice']['vertices'] and js['faces']==prev['juice']['faces'];
if js['vertices']:assert js['coords_sha']==prev['juice']['liquid_mesh_sha'] and js['topology_sha']==prev['juice_topology_sha256']
result={'status':'PASS','pose':pose,'voxel_mm':.32,'source_sha':PIN,'candidate_sha':sha(scene),'old_material_trees':len(old),'only_replaced_socket':links,'removed_link':removed,'new_nodes':new,'visibility_unchanged':True,'body':bs,'juice':js,'unchanged_attributes_and_derived_weights':fields};out.write_text(json.dumps(result,indent=2)+'\n');print('PASS',pose,fields and fields['weights'],flush=True)

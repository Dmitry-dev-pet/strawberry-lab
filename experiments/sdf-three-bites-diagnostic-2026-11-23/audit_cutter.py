import bpy,sys,json,hashlib,statistics,math
from pathlib import Path
from mathutils import Vector
scene_path=Path(sys.argv[sys.argv.index('--')+1]); out=Path(sys.argv[sys.argv.index('--')+2]);assert scene_path.exists() and not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(scene_path),use_scripts=False)
s=bpy.context.scene;data={'scene_sha256':hashlib.sha256(scene_path.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'length_scale_mm_per_unit':s.unit_settings.scale_length*1000,'cutters':[],'sdf_body':[],'materials':[]}
for o in s.objects:
 if any(w in o.name.lower() for w in ['bite','sphere','cutter','knife','plane','halfspace']):
  rec={'name':o.name,'type':o.type,'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'location':tuple(o.location),'scale':tuple(o.scale),'matrix_world':[list(r) for r in o.matrix_world],'modifier_types':[m.type for m in o.modifiers]}
  if o.type=='MESH':
   v=[Vector(x.co) for x in o.data.vertices]; r=[x.length for x in v]
   rec.update({'verts':len(v),'faces':len(o.data.polygons),'local_xyz_min':[min(x[i] for x in v) for i in range(3)],'local_xyz_max':[max(x[i] for x in v) for i in range(3)],'local_radius_quantiles':[round(sorted(r)[int((len(r)-1)*q)],6) for q in [0,.1,.5,.9,1]],'radius_cv':round(statistics.pstdev(r)/statistics.mean(r),6) if r else None})
  data['cutters'].append(rec)
b=s.objects['Receptacle | canonical PR29 hull']; data['sdf_body']={'name':b.name,'props':{k:b[k] for k in b.keys() if k.startswith('sdf_') and isinstance(b[k],(int,float,str))},'mods':[]}
for m in b.modifiers:
 item={'name':m.name,'type':m.type}
 if m.type=='NODES' and m.node_group:
  g=m.node_group;item['group_name']=g.name;item['node_count']=len(g.nodes)
  item['cut_nodes']=[{'name':n.name,'id':n.bl_idname,'params':{k: (n.inputs[k].default_value if isinstance(n.inputs[k].default_value,(int,float,str)) else str(n.inputs[k].default_value)) for k in ['Voxel Size','Scale','Threshold','Level'] if k in n.inputs and not n.inputs[k].is_linked}} for n in g.nodes if any(w in n.bl_idname.lower() for w in ['sdf','grid'])]
  item['object_infos']=[{'name':n.name,'target':n.inputs['Object'].default_value.name if n.inputs.get('Object') and n.inputs['Object'].default_value else None} for n in g.nodes if n.bl_idname=='GeometryNodeObjectInfo']
 item['cut_nodes']=item.get('cut_nodes',[])[:40];item['object_infos']=item.get('object_infos',[])[:20]
 data['sdf_body']['mods'].append(item)
mat=bpy.data.materials.get('SDF | inherited 150^3 tissue + own multiscale wetness')
if mat:
 princ=[n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'];data['materials']=[{'material':mat.name,'node_count':len(mat.node_tree.nodes),'principled':[{x:{'linked':bool(p.inputs[x].is_linked),'value':str(p.inputs[x].default_value)[:60]} for x in ['Base Color','Subsurface Weight','Subsurface Scale','Roughness','Coat Weight','Transmission Weight'] if x in p.inputs} for p in princ]}]
out.write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str));print('CUTTER_AUDIT_PASS',json.dumps({'cutters':[{k:v for k,v in c.items() if k in ['name','type','verts','faces','radius_cv','local_radius_quantiles']} for c in data['cutters']],'sdf':data['sdf_body']['props']},ensure_ascii=False),flush=True)

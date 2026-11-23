"""Independent saved-scene material-diff and evaluated geometry QA."""
import bpy,sys,json,hashlib,numpy as np
from pathlib import Path
src,scene,variant,pose,prior,old_script,out=sys.argv[sys.argv.index('--')+1:];src=Path(src);scene=Path(scene);out=Path(out);assert not out.exists()
sys.path.insert(0,str(Path(old_script).parent));from qa_juice_surface import state,BODY,JUICE
PIN='361696819fd44733d560e3f59b101cd11f59862e7ebd7b7f83ce94fd07909963';PREFIX='SL Field Optical | '
TARGET={'B':('SL Juice | clear dielectric ARTIST','Base Color',7),'C':('SDF | inherited 150^3 tissue + own multiscale wetness','Subsurface Scale',3)}
def hashfile(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hasharr(a):return hashlib.sha256(a.tobytes()).hexdigest()
def value(x):
    if isinstance(x,(str,int,float,bool,type(None))):return x
    if isinstance(x,bpy.types.ID):return [x.bl_rna.identifier,x.name]
    try:return [value(y) for y in x]
    except TypeError:return str(x)
def inventory(skip_new):
    d={}
    def walk(g,key):
        if key in d:return
        nodes=[]
        for n in sorted(g.nodes,key=lambda x:x.name):
            if skip_new and n.name.startswith(PREFIX):continue
            entry={'name':n.name,'type':n.bl_idname,'inputs':[(s.identifier,value(getattr(s,'default_value',None))) for s in n.inputs],'props':{p:value(getattr(n,p)) for p in ('operation','feature','voronoi_dimensions','blend_type','distribution','subsurface_method','data_type','attribute_name','image','node_tree','interpolation_type','clamp','mode') if hasattr(n,p)}}
            if n.type=='VALTORGB':entry['ramp']=[(e.position,list(e.color)) for e in n.color_ramp.elements]
            nodes.append(entry)
        links=sorted((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in g.links if not(skip_new and (l.from_node.name.startswith(PREFIX) or l.to_node.name.startswith(PREFIX))))
        d[key]={'nodes':nodes,'links':links}
        for n in g.nodes:
            if n.type=='GROUP' and n.node_tree:walk(n.node_tree,'group:'+n.node_tree.name)
    for m in bpy.data.materials:
        if m.node_tree:walk(m.node_tree,'material:'+m.name)
    return d

def snap(obj,attrname=None):
    dg=bpy.context.evaluated_depsgraph_get();ev=obj.evaluated_get(dg);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg)
    n=len(me.vertices);pos=np.empty(n*3,np.float32);me.vertices.foreach_get('co',pos);me.calc_loop_triangles();idx=np.empty(len(me.loop_triangles)*3,np.int32);me.loop_triangles.foreach_get('vertices',idx)
    r={'vertices':n,'faces':len(me.polygons),'coords_sha':hasharr(pos),'topology_sha':hasharr(idx)};stats=None
    if n and attrname:
        a=me.attributes[attrname];assert a.domain=='POINT';v=np.empty(n*(3 if attrname=='sdf_rest_position' else 1),np.float32);a.data.foreach_get('vector' if attrname=='sdf_rest_position' else 'value',v);assert np.isfinite(v).all()
        if attrname=='sl_juice_clearance_mm':
            t=np.clip(v,0,.20)/.10;old=np.array([.94,.87,.80]);c=old[None,:]**t[:,None];stats={'positive_points':int((v>0).sum()),'input_min_max_mm':[float(v.min()),float(v.max())],'derived_rgb_min':c.min(0).tolist(),'derived_rgb_max':c.max(0).tolist(),'attr_sha':hasharr(v)}
        else:
            v=v.reshape(-1,3);rad=np.linalg.norm(v[:,:2],axis=1);t=np.clip((rad-.12)/(.75-.12),0,1);y=.006+.014*(t**3*(t*(6*t-15)+10));stats={'rest_radius_min_max_BU':[float(rad.min()),float(rad.max())],'derived_scale_min_max_BU':[float(y.min()),float(y.max())],'attr_sha':hasharr(v)}
    ev.to_mesh_clear();return r,stats

def vis():return {o.name:[o.visible_camera,o.visible_diffuse,o.visible_glossy,o.visible_transmission,o.visible_volume_scatter,o.visible_shadow] for o in bpy.context.scene.objects}
assert hashfile(src)==PIN
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),use_scripts=False);oldmat=inventory(False);oldvis=vis()
bpy.ops.wm.open_mainfile(filepath=str(scene.resolve()),use_scripts=False);newmat=inventory(True);assert newmat==oldmat,'Existing shader nodes or links changed';assert vis()==oldvis
matname,socket,num=TARGET[variant];new=[];outgoing=[]
for m in bpy.data.materials:
    if not m.node_tree:continue
    for n in m.node_tree.nodes:
        if n.name.startswith(PREFIX):new.append((m.name,n.name,n.bl_idname))
    for l in m.node_tree.links:
        if l.from_node.name.startswith(PREFIX) and not l.to_node.name.startswith(PREFIX):outgoing.append((m.name,l.to_node.bl_idname,l.to_socket.name))
assert len(new)==num and all(x[0]==matname for x in new);assert outgoing==[(matname,'ShaderNodeBsdfPrincipled',socket)],outgoing
s=bpy.context.scene;b=bpy.data.objects[BODY];j=bpy.data.objects[JUICE];state(b,pose,.32,1.)
bs,ss=snap(b,'sdf_rest_position' if variant=='C' else None);js,ts=snap(j,'sl_juice_clearance_mm' if variant=='B' else None)
old=json.loads((Path(prior)/f'qa-{pose}.json').read_text());assert old['scene_sha256']==PIN;assert bs==old['body'];assert js['vertices']==old['juice']['vertices'] and js['faces']==old['juice']['faces']
if js['vertices']:
    assert js['coords_sha']==old['juice']['liquid_mesh_sha'];assert js['topology_sha']==old['juice_topology_sha256']
report={'status':'PASS','variant':variant,'pose':pose,'voxel_mm':.32,'source_sha256':PIN,'scene_sha256':hashfile(scene),'preserved_material_trees':len(oldmat),'added_nodes':new,'only_existing_socket_link':outgoing,'visibility_unchanged':True,'body':bs,'juice':js,'derived_field_statistics':ts or ss}
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

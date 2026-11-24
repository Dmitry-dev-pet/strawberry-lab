"""Independent ARTIST cavity and attached tissue on neutral-stock Exact only.
Adapt our earlier ring-lumen/protrusion construction to the same shape map and
half-voxel computational frame. Original source graphs/geometry not imported.
"""
import bpy,bmesh,math,sys,hashlib,json,time
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
PIN='95b40e781ee948f9496ba5277ac08be0bb305435de1b498031b51c669be1b5c2'
EXACT='SL Exact | common labelled body'; ROOT='SL Shape Controller | edit Custom Properties'; SKIN='SL Neutral Skin'
LUMEN='SL Exact | neutral cavity source'; PROTRUSIONS='SL Exact | neutral attached tissue'; WALL='SL Exact | cavity wall ARTIST'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mesh_obj(name,verts,faces,shape):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));assert all(e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);assert vol>0;bm.to_mesh(me);bm.free()
 o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);o.hide_render=True;o.hide_set(True);o.display_type='WIRE';mod=o.modifiers.new('SL Common forward shape','NODES');mod.node_group=shape;return o,vol

def make_lumen(shape):
 n,nt=64,48;verts=[];faces=[]
 def section(t,theta):
  z=30.+7.5*math.cos(t);r=math.sin(t);c=.30*math.sin(2*t);d=.18*math.sin(3*t);irreg=1+.13*math.sin(3*theta+1.3*t)+.07*math.cos(5*theta-2.1*t)
  return (c+2.2*r*irreg*math.cos(theta),d+1.5*r*irreg*math.sin(theta),z)
 verts.append(section(0,0))
 for i in range(1,nt):
  for j in range(n):verts.append(section(math.pi*i/nt,2*math.pi*j/n))
 bottom=len(verts);verts.append(section(math.pi,0))
 for j in range(n):faces.append((0,1+j,1+(j+1)%n))
 for i in range(nt-2):
  for j in range(n):
   a=1+i*n+j;b=1+i*n+(j+1)%n;faces.append((a,a+n,b+n,b))
 for j in range(n):faces.append((bottom,1+(nt-2)*n+(j+1)%n,1+(nt-2)*n+j))
 return mesh_obj(LUMEN,verts,faces,shape)

def make_protrusions(cavity,shape):
 tree=BVHTree.FromPolygons([v.co for v in cavity.data.vertices],[list(f.vertices) for f in cavity.data.polygons]);rng=np.random.default_rng(73191);verts=[];faces=[];records=[];sites=[]
 def inside(p):
  q,n,_,_=tree.find_nearest(p);return float((q-p).dot(n))
 for _ in range(800):
  if len(sites)==18:break
  z=float(rng.uniform(24.4,35.7));theta=float(rng.uniform(0,2*math.pi));axis=Vector((0,0,z));d=Vector((math.cos(theta),math.sin(theta),0.));anchor,normal,_,dist=tree.ray_cast(axis,d,10)
  if anchor is None or (anchor-axis).length<1.0 or any((anchor-old).length<1.35 for old in sites):continue
  root=anchor+d*.85;end=anchor.lerp(axis,float(rng.uniform(.48,.69)))+Vector((0,0,float(rng.uniform(-.35,.55))))
  if inside(root)>-.45 or inside(end)<.32:continue
  sites.append(anchor);tangent=Vector((-d.y,d.x,0));bend=float(rng.uniform(-.22,.22));m=(root+end)*.5+tangent*bend+Vector((0,0,.25));radius=float(rng.uniform(.43,.54));tip=float(rng.uniform(.20,.25));points=[];widths=[]
  for t in map(float,np.linspace(0,1,16)):
   points.append(root*(1-t)**2+m*(2*t*(1-t))+end*t*t);widths.append(tip+(radius-tip)*(1-t)**.9)
  start=len(verts);side=12
  for i,(p,r) in enumerate(zip(points,widths)):
   direction=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized();u=direction.cross(Vector((0,0,1))).normalized();v=direction.cross(u).normalized()
   for j in range(side):
    th=2*math.pi*j/side;verts.append(tuple(p+r*(math.cos(th)*u+math.sin(th)*v)))
  faces.append(tuple(start+j for j in reversed(range(side))))
  for i in range(len(points)-1):
   for j in range(side):
    a=start+i*side+j;q=start+i*side+(j+1)%side;faces.append((a,q,q+side,a+side))
  faces.append(tuple(start+(len(points)-1)*side+j for j in range(side)))
  records.append({'anchor_mm':list(anchor),'root_mm':list(root),'tip_mm':list(end),'root_outside_cavity_mm':-inside(root),'tip_inside_cavity_mm':inside(end),'root_radius_mm':radius,'tip_radius_mm':tip})
 assert len(records)==18,len(records)
 o,vol=mesh_obj(PROTRUSIONS,verts,faces,shape);return o,vol,records

def main():
 src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)==PIN and not out.exists();t=time.perf_counter();bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),use_scripts=False)
 s=bpy.context.scene;root=bpy.data.objects[ROOT];assert (root['shape_a'],root['shape_b'],root['shape_h'])==(0.,0.,1.) and abs(s.unit_settings.scale_length-.001)<1e-8
 body=bpy.data.objects[EXACT];shape=body.modifiers[0].node_group
 cav,cv=make_lumen(shape);pro,pv,records=make_protrusions(cav,shape)
 hull=bpy.data.objects[SKIN].data;tree=BVHTree.FromPolygons([v.co for v in hull.vertices],[list(f.vertices) for f in hull.polygons]);margins=[]
 for o in (cav,pro):
  for v in o.data.vertices:
   p,n,_,_=tree.find_nearest(v.co);margins.append(float((p-v.co).dot(n)))
 assert min(margins)>1.,min(margins)
 g=body.modifiers[1].node_group;N,L=g.nodes,g.links
 def one(label):return next(n for n in N if n.label==label)
 def add(typ,label):n=N.new(typ);n.label=n.name='Lumen | '+label;return n
 def w(a,b):
  if isinstance(a,bpy.types.NodeSocket):
   for old in list(b.links):L.remove(old)
   L.new(a,b)
  else:b.default_value=a
 def m(op,a,b,label):n=add('ShaderNodeMath',label);n.operation=op;w(a,n.inputs[0]);w(b,n.inputs[1]);return n.outputs[0]
 def boolean(a,b,label):n=add('GeometryNodeSDFGridBoolean',label);n.operation='DIFFERENCE';w(a,n.inputs['Grid 1']);w(b,n.inputs['Grid 2']);assert len(n.inputs['Grid 2'].links)==1;return n.outputs['Grid']
 vox=one('exact_voxel_mm').outputs[0];shift=one('Body in shifted computational frame').inputs['Translation'].links[0].from_socket
 def grid(o):
  n=add('GeometryNodeObjectInfo',o.name);n.transform_space='RELATIVE';n.inputs['Object'].default_value=o
  q=add('GeometryNodeTransform',o.name+' same half-cell phase');w(n.outputs['Geometry'],q.inputs['Geometry']);w(shift,q.inputs['Translation'])
  r=add('GeometryNodeMeshToSDFGrid',o.name+' SDF');w(q.outputs['Geometry'],r.inputs['Mesh']);w(vox,r.inputs['Voxel Size']);return r.outputs[0]
 cavgrid=grid(cav);progrid=grid(pro);effective=boolean(cavgrid,progrid,'effective cavity = cavity minus attached solids')
 diff=one('Common source difference');original=diff.inputs['Grid 1'].links[0].from_socket;perforated=boolean(original,effective,'body minus effective cavity before user cutter');w(perforated,diff.inputs['Grid 1'])
 # Keep the uncut OUTER reference unchanged for pit measurements and skin fade.
 # Determine material dominance from the three operand fields in the same frame.
 sample=add('GeometryNodeSampleGrid','sample effective cavity signed field');sample.data_type='FLOAT';w(effective,sample.inputs['Grid']);w(one('Cutter signed operand').inputs['Position'].links[0].from_socket,sample.inputs['Position'])
 old=one('sl_exact_cutter_signed_mm');cutstore=one('sl_cut_face');store=add('GeometryNodeStoreNamedAttribute','store effective cavity signed operand');store.data_type='FLOAT';store.domain='FACE';store.inputs['Name'].default_value='sl_cavity_signed_mm';w(old.outputs['Geometry'],store.inputs['Geometry']);w(sample.outputs['Value'],store.inputs['Value'])
 def attr(name,dtype='FLOAT'):
  a=add('GeometryNodeInputNamedAttribute',name);a.data_type=dtype;a.inputs['Name'].default_value=name;return a.outputs['Attribute']
 outer=attr('sl_exact_body_signed_mm');user=m('MULTIPLY',attr('sl_exact_cutter_signed_mm'),-1.,'negative user operand');lumen=m('MULTIPLY',attr('sl_cavity_signed_mm'),-1.,'negative cavity operand');cap=m('GREATER_THAN',user,m('MAXIMUM',outer,lumen,'outer or cavity'),'user dominant');wall=m('MULTIPLY',m('GREATER_THAN',lumen,outer,'cavity above outer'),m('SUBTRACT',1.,m('GREATER_THAN',user,lumen,'user above cavity'),'cavity at least user'),'cavity dominant')
 wallstore=add('GeometryNodeStoreNamedAttribute','wall face flag');wallstore.data_type='BOOLEAN';wallstore.domain='FACE';wallstore.inputs['Name'].default_value='sl_cavity_wall_face';w(store.outputs['Geometry'],wallstore.inputs['Geometry']);w(wall,wallstore.inputs['Value']);w(wallstore.outputs['Geometry'],cutstore.inputs['Geometry']);w(cap,cutstore.inputs['Value'])
 mat=bpy.data.materials.new(WALL);mat.diffuse_color=(.64,.32,.28,1);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.64,.32,.28,1);bs.inputs['Roughness'].default_value=.55
 previous=one('SL Split | cut tissue');target=next(n for n in N if n.label=='achene_pit' and n.bl_idname=='GeometryNodeStoreNamedAttribute');sm=add('GeometryNodeSetMaterial','separate diagnostic cavity wall');sm.inputs['Material'].default_value=mat;w(previous.outputs['Geometry'],sm.inputs['Geometry']);w(attr('sl_cavity_wall_face','BOOLEAN'),sm.inputs['Selection']);w(sm.outputs['Geometry'],target.inputs['Geometry'])
 for i,n in enumerate(N):n.location=((i//8)*220,-(i%8)*180)
 root['sl_lumen_source']='Independent neutral-space artistic cavity with wall-attached tissue; Exact cuts only';s['scope']='Exact cut-only cavity and attached tissue; Fast and whole display unchanged; diagnostic ARTIST geometry';root['exact_mode']=0;root['split_mode']=0;root['tissue_gain']=0.;root.update_tag();bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()),compress=True)
 r={'source_sha':PIN,'scene_sha':sha(out),'anchor_digest':root['anchor_digest'],'dependency_key':root['sl_vascular_dependency_key'],'cavity_source_volume_mm3':cv,'protrusion_source_volume_mm3':pv,'min_sampled_outer_margin_mm':min(margins),'cavity_vertices':len(cav.data.vertices),'protrusion_vertices':len(pro.data.vertices),'sites':records,'scope':'Exact cuts only; same shape and half-voxel phase; Fast and whole display bypass; ARTIST','elapsed_seconds':time.perf_counter()-t};out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print('BUILT',r['scene_sha'],len(records),cv,pv,min(margins),flush=True)
if __name__=='__main__':main()

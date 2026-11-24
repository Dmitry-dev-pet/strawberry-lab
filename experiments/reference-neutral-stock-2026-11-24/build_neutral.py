"""Neutral exterior stock: owned surface/pit/achene algorithms and shared native shape map.
Diagnostic clay only. All procedural shapes/dimensions not measured at source are ARTIST.
"""
import sys,json,hashlib,time,math
from pathlib import Path
from dataclasses import asdict
import bpy,numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent/"deps"/"src"),str(Path(__file__).resolve().parents[2]/"src")]
from neutral_contract import *
from exterior_shape import PitField
from build_strawberry_exterior import achene_prototype
from fruit_platform import make_context
from fruit_morphometry import load_catalog

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest_array(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def coords(me):
 a=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',a);return a.reshape(-1,3)
def attr(me,name,kind,values):
 a=me.attributes.new(name,kind,'POINT');a.data.foreach_set('vector' if kind=='FLOAT_VECTOR' else 'value',np.ascontiguousarray(values).ravel());return a
def mesh(name,vs,faces,mat=None):
 m=bpy.data.meshes.new(name);m.from_pydata(vs,[],faces);m.update()
 if mat is not None:m.materials.append(mat)
 if len(m.polygons):m.polygons.foreach_set('use_smooth',[True]*len(faces))
 o=bpy.data.objects.new(name,m);bpy.context.scene.collection.objects.link(o);attr(m,'sl_rest_position','FLOAT_VECTOR',coords(m));return o
def clay(name,rgb):
 m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*rgb,1);bs.inputs['Roughness'].default_value=.65;return m

def skin_mesh(shape,stock,mat):
 field=PitField(stock.anchors);vs=[];mask=[];depths=[];rings=MERIDIAN_STEPS-1;n=AZIMUTH_STEPS
 for j in range(1,MERIDIAN_STEPS):
  mer=math.pi*j/MERIDIAN_STEPS
  for i in range(n):
   a=math.tau*i/n;p=shape.point(mer,a);depth,w=field.sample(p)
   if depth:p=tuple(x-depth*y for x,y in zip(p,shape.normal(mer,a)))
   vs.append(p);mask.append(w);depths.append(depth)
 top=len(vs);vs.extend((shape.point(0.,0.),shape.point(math.pi,0.)));mask.extend((0.,0.));depths.extend((0.,0.));faces=[]
 for j in range(rings-1):
  for i in range(n):
   k=(i+1)%n;faces.append((j*n+i,(j+1)*n+i,(j+1)*n+k,j*n+k))
 last=(rings-1)*n
 for i in range(n):
  k=(i+1)%n;faces.extend(((top,i,k),(top+1,last+k,last+i)))
 o=mesh('SL Neutral Skin',vs,faces,mat);attr(o.data,'achene_pit','FLOAT',np.array(mask,np.float32));attr(o.data,'sl_pit_depth_mm','FLOAT',np.array(depths,np.float32));return o

def seed_mesh(skin,stock,mat):
 tree=BVHTree.FromPolygons([v.co for v in skin.data.vertices],[list(f.vertices) for f in skin.data.polygons]);protos=[achene_prototype(i,mat) for i in range(5)];vs=[];faces=[];ix=[];floors=[];rows=[]
 for i,a in enumerate(stock.anchors):
  p=Vector(a.point);n=Vector(a.normal);hit,_,_,_=tree.ray_cast(p+n*2,-n,5)
  assert hit is not None,i
  depth=(p-hit).dot(n);assert depth>0,(i,depth)
  center=hit+n*(.19*a.thickness_mm);basis=Matrix((Vector(a.side_axis),Vector(a.long_axis),n)).transposed();scale=Matrix.Diagonal(Vector((a.width_mm,a.length_mm,a.thickness_mm)))
  proto=protos[i%5];v=[tuple(center+basis@scale@q.co) for q in proto.vertices];f=[tuple(int(j) for j in q.vertices) for q in proto.polygons]
  pts=np.asarray(v);signed=sum(float(np.dot(pts[k[0]],np.cross(pts[k[j]],pts[k[j+1]])))/6 for k in f for j in range(1,len(k)-1))
  if signed<0:f=[tuple(reversed(q)) for q in f]
  contacts=tree.overlap(BVHTree.FromPolygons(v,f));assert contacts,(i,'no seed/skin triangle intersection')
  start=len(vs);vs.extend(v);faces.extend(tuple(start+j for j in q) for q in f);ix.extend([i]*len(v));floors.append(tuple(hit));rows.append({'id':stock.anchor_id(i),'index':i,'anchor':asdict(a),'seat_mm':list(hit),'seat_depth_mm':float(depth),'contact_pairs':len(contacts),'seed_vertex_start':start,'seed_vertex_count':len(v)})
 for m in protos:bpy.data.meshes.remove(m)
 o=mesh('SL Neutral Achenes',vs,faces,mat);attr(o.data,'sl_anchor_index','INT',np.array(ix,np.int32));return o,floors,rows

def shared_map(root,height):
 g=bpy.data.node_groups.new('SL | common shape map v1','GeometryNodeTree');g.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');N,L=g.nodes,g.links
 def n(t,label):q=N.new(t);q.label=label;return q
 def wire(x,y):
  if isinstance(x,(float,int)):y.default_value=x
  else:L.new(x,y)
 def m(op,a,b):
  q=n('ShaderNodeMath',op);q.operation=op;wire(a,q.inputs[0]);wire(b,q.inputs[1]);return q.outputs[0]
 def driven(key):
  q=n('ShaderNodeValue',key);q.outputs[0].default_value=root[key];d=q.outputs[0].driver_add('default_value').driver;d.type='AVERAGE';v=d.variables.new();v.name='value';v.type='SINGLE_PROP';v.targets[0].id=root;v.targets[0].data_path='["'+key+'"]';return q.outputs[0]
 inp=n('NodeGroupInput','Neutral stock');out=n('NodeGroupOutput','Deformed stock');p=n('GeometryNodeInputPosition','Original mesh coordinates');s=n('ShaderNodeSeparateXYZ','Rest XYZ');wire(p.outputs[0],s.inputs[0]);x,y,z=(s.outputs[k] for k in ('X','Y','Z'));a,b,h=(driven(k) for k in ('shape_a','shape_b','shape_h'));t=m('SUBTRACT',m('MULTIPLY',z,2/height),1)
 def bell(c,w):
  u=m('DIVIDE',m('SUBTRACT',t,c),w);return m('POWER',math.e,m('MULTIPLY',m('MULTIPLY',u,u),-1))
 r=m('ADD',1,m('ADD',m('MULTIPLY',a,bell(.5,.36)),m('MULTIPLY',b,bell(-.3,.4))))
 comb=n('ShaderNodeCombineXYZ','Shared forward map');wire(m('MULTIPLY',x,r),comb.inputs['X']);wire(m('MULTIPLY',y,r),comb.inputs['Y']);wire(m('MULTIPLY',z,h),comb.inputs['Z']);q=n('GeometryNodeSetPosition','Transform all vertices from neutral coordinates');wire(inp.outputs[0],q.inputs['Geometry']);wire(comb.outputs[0],q.inputs['Position']);wire(q.outputs[0],out.inputs[0])
 for i,q in enumerate(N):q.location=((i//6)*210,-(i%6)*150)
 return g

def camera_setup(s):
 target=Vector((0,0,24));cam=bpy.data.objects.new('Diagnostic camera',bpy.data.cameras.new('Diagnostic camera'));s.collection.objects.link(cam);cam.location=(66,-105,68);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=66;s.camera=cam
 s.render.engine='BLENDER_WORKBENCH';sh=s.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.background_type='WORLD';s.world=bpy.data.worlds.new('Diagnostic world');s.world.color=(.12,.12,.12);s.render.resolution_x=s.render.resolution_y=600;s.render.resolution_percentage=100

def main():
 catalog,count,out=sys.argv[sys.argv.index('--')+1:];count=int(count);out=Path(out);assert not out.exists();t=time.perf_counter();bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=.001
 ctx=make_context(load_catalog(catalog),'Camarosa','neutral-101',seed=101);stock=make_stock(ctx,count);shape=ExteriorShape(stock.params);skin=skin_mesh(shape,stock,clay('Diagnostic clay | skin',(.58,.58,.58)));seeds,floors,rows=seed_mesh(skin,stock,clay('Diagnostic clay | achenes',(.27,.27,.27)));anchors=mesh('SL Anchor Set',[a.point for a in stock.anchors],[]);seats=mesh('SL Pit Seats',floors,[])
 for o in (anchors,seats):
  attr(o.data,'sl_anchor_index','INT',np.arange(count,dtype=np.int32));attr(o.data,'sl_rest_normal','FLOAT_VECTOR',np.array([a.normal for a in stock.anchors],np.float32));o.hide_render=True;o.hide_set(True)
 root=bpy.data.objects.new('SL Shape Controller | edit Custom Properties',None);s.collection.objects.link(root)
 for key,val,lo,hi in [('shape_a',0.,-.25,.30),('shape_b',0.,-.25,.30),('shape_h',1.,.85,1.20)]:root[key]=val;root.id_properties_ui(key).update(min=lo,max=hi)
 root['anchor_digest']=stock.anchor_digest;root['neutral_stock_key']=stock.stock_key;root['context_id']=stock.instance_id;root['count']=count;root['shape_map_version']=MAP_VERSION;g=shared_map(root,stock.params.height_mm)
 for o in (skin,seeds,anchors,seats):
  mod=o.modifiers.new('SL Common forward shape','NODES');mod.node_group=g;o['neutral_stock_key']=stock.stock_key;o['role']=o.name
 s['scope']='Neutral exterior geometry only; clay diagnostic; no cut, internal tissues or production material';s['anchor_digest']=stock.anchor_digest;s['neutral_stock_key']=stock.stock_key;camera_setup(s);bpy.context.view_layer.objects.active=root;root.select_set(True);bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()),compress=True)
 r={'scope':s['scope'],'context_plan_digest':stock.context_plan_digest,'recipe':asdict(stock.params),'anchor_digest':stock.anchor_digest,'stock_key':stock.stock_key,'shape_key_neutral':stock.shape_key(ShapeState()),'shape_key_deformed':stock.shape_key(ShapeState(.16,-.10,1.12)),'future_vascular_dependency_key':stock.vessel_dependency_key({'placeholder':True}),'shape_nodes':len(g.nodes),'objects':{o.name:{'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'rest_sha':digest_array(coords(o.data))} for o in (skin,seeds,anchors,seats)},'anchor_rows':rows,'seed_contacts':len(rows),'seat_depth_mm':[min(r['seat_depth_mm'] for r in rows),max(r['seat_depth_mm'] for r in rows)],'scene_sha':sha(out),'build_seconds':time.perf_counter()-t};out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print('BUILT',count,r['seed_contacts'],r['seat_depth_mm'],r['build_seconds'],flush=True)
if __name__=='__main__':main()

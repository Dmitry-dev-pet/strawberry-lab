"""Own wall-attached protrusion diagnostic for a previously checked SDF lumen.
Solid swept tapered shapes are subtracted from the lumen grid before the tissue
Boolean, not added as detached tubes. Shape parameters ARTIST.
"""
import bpy,bmesh,math,sys,hashlib,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
PIN='ccd9d4b5e93d000bdaee27a83afa95581fe19a69533493a0f96ce12917574b45';BODY='Receptacle | canonical PR29 hull';LUMEN='SL Lumen | editable enclosed cavity';NAME='SL Lumen | attached tissue protrusions ARTIST'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def install():
 s=bpy.context.scene;b=s.objects[BODY];c=s.objects[LUMEN];mm=s.unit_settings.scale_length*1000
 tree=BVHTree.FromPolygons([v.co for v in c.data.vertices],[list(f.vertices) for f in c.data.polygons]);rng=np.random.default_rng(73191);verts=[];faces=[];records=[]
 def signed(p):
  q,n,_,_=tree.find_nearest(p/mm);return float((q-p/mm).dot(n)*mm)
 # Independent artist selection of sparse attachment sites over the middle
 # of our own small lumen. Reject sites too close to previous roots.
 sites=[]
 for _ in range(800):
  if len(sites)==18:break
  z=float(rng.uniform(-2.6,8.7));theta=float(rng.uniform(0,2*math.pi));axis=Vector((0,0,z));d=Vector((math.cos(theta),math.sin(theta),0.));hit,normal,_,dist=tree.ray_cast(axis/mm,d,10/mm)
  if hit is None:continue
  anchor=hit*mm
  if (anchor-axis).length<1.0 or any((anchor-old).length<1.35 for old in sites):continue
  root=anchor+d*.85;end=anchor.lerp(axis,float(rng.uniform(.48,.69)))+Vector((0,0,float(rng.uniform(-.35,.55))))
  if signed(root)>-.45 or signed(end)<.32:continue
  sites.append(anchor);tangent=Vector((-d.y,d.x,0));bend=float(rng.uniform(-.22,.22));m=(root+end)*.5+tangent*bend+Vector((0,0,.25));radius=float(rng.uniform(.43,.54));tip=float(rng.uniform(.20,.25));points=[];widths=[]
  for t in map(float,np.linspace(0,1,16)):
   points.append(root*(1-t)**2+m*(2*t*(1-t))+end*t*t);widths.append(tip+(radius-tip)*(1-t)**.9)
  start=len(verts);side=12
  for i,(p,r) in enumerate(zip(points,widths)):
   direction=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized();u=direction.cross(Vector((0,0,1))).normalized();v=direction.cross(u).normalized()
   for j in range(side):
    th=2*math.pi*j/side;verts.append(tuple((p+r*(math.cos(th)*u+math.sin(th)*v))/mm))
  faces.append(tuple(start+j for j in reversed(range(side))))
  for i in range(len(points)-1):
   for j in range(side):
    a=start+i*side+j;q=start+i*side+(j+1)%side;faces.append((a,q,q+side,a+side))
  faces.append(tuple(start+(len(points)-1)*side+j for j in range(side)))
  records.append({'anchor_mm':list(anchor),'root_mm':list(root),'tip_mm':list(end),'root_outside_cavity_mm':-signed(root),'tip_inside_cavity_mm':signed(end),'root_radius_mm':radius,'tip_radius_mm':tip})
 assert len(sites)==18,len(sites)
 me=bpy.data.meshes.new(NAME);me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));assert all(e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True)*mm**3;assert vol>0;bm.to_mesh(me);bm.free();obj=bpy.data.objects.new(NAME,me);s.collection.objects.link(obj);obj.hide_render=True;obj.hide_set(True);obj.display_type='WIRE'
 g=b.modifiers[0].node_group;N,L=g.nodes,g.links
 def n(t,label):q=N.new(t);q.name=q.label='Lumen protrusions | '+label;return q
 old=N['Lumen | same voxel size'];dif=N['Lumen | subtract BEFORE editable cutter'];prox=N['Lumen | distance to original cavity'];voxel=old.inputs['Voxel Size'].links[0].from_socket
 info=n('GeometryNodeObjectInfo','closed attached tissue inputs');info.transform_space='RELATIVE';info.inputs['Object'].default_value=obj
 grid=n('GeometryNodeMeshToSDFGrid','source solids to same voxel grid');L.new(info.outputs['Geometry'],grid.inputs['Mesh']);L.new(voxel,grid.inputs['Voxel Size'])
 carve=n('GeometryNodeSDFGridBoolean','remove tissue from cavity');carve.operation='DIFFERENCE';L.new(old.outputs[0],carve.inputs['Grid 1']);L.new(grid.outputs[0],carve.inputs['Grid 2']);
 for link in list(dif.inputs['Grid 2'].links):L.remove(link)
 L.new(carve.outputs[0],dif.inputs['Grid 2']);assert len(dif.inputs['Grid 2'].links)==1
 # The exposed wall classification now uses the actual modified cavity boundary,
 # including protrusions, rather than painting protrusion tips as skin/cut cap.
 remesh=n('GeometryNodeGridToMesh','effective cavity surface for wall classification');remesh.inputs['Adaptivity'].default_value=0.;remesh.inputs['Threshold'].default_value=0.;L.new(carve.outputs[0],remesh.inputs['Grid']);L.new(remesh.outputs['Mesh'],prox.inputs['Geometry'])
 return {'added_nodes':4,'source_protrusions':len(records),'source_solid_mesh_vertices':len(verts),'source_solid_volume_mm3':vol,'sites':records,'construction':'lumen grid minus closed protrusion grid; tissue minus effective lumen before user cutter','wall_classifier':'effective cavity mesh','source_artistic':True}
if __name__=='__main__':
 src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)==PIN and not out.exists();bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False);r=install();bpy.ops.wm.save_as_mainfile(filepath=str(out));r.update(source_sha=PIN,scene_sha=sha(out));out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='sites'}),flush=True)

"""Independent ARTIST lumen-only SDF experiment, no reference assets or coefficients."""
import bpy,bmesh,math,sys,hashlib,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
PIN='361696819fd44733d560e3f59b101cd11f59862e7ebd7b7f83ce94fd07909963';BODY='Receptacle | canonical PR29 hull';LUMEN='SL Lumen | editable enclosed cavity';WALL='SL Lumen | moist inner wall ARTIST'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def make_lumen(mm):
 # Independent cavity in current physical mm: 15mm long, about 2.2/1.5mm
 # max transverse semi-axes. Smooth angular/radial modulation, closed poles.
 n=64;nt=48;verts=[];faces=[]
 def section(t,theta):
  z=3.+7.5*math.cos(t);r=math.sin(t);c=.30*math.sin(2*t);d=.18*math.sin(3*t);irreg=1+.13*math.sin(3*theta+1.3*t)+.07*math.cos(5*theta-2.1*t)
  return ((c+2.2*r*irreg*math.cos(theta))/mm,(d+1.5*r*irreg*math.sin(theta))/mm,z/mm)
 verts.append(section(0,0))
 for i in range(1,nt):
  for j in range(n):verts.append(section(math.pi*i/nt,2*math.pi*j/n))
 bottom=len(verts);verts.append(section(math.pi,0))
 for j in range(n):faces.append((0,1+j,1+(j+1)%n))
 for i in range(nt-2):
  for j in range(n):
   a=1+i*n+j;b=1+i*n+(j+1)%n;faces.append((a,a+n,b+n,b))
 for j in range(n):faces.append((bottom,1+(nt-2)*n+(j+1)%n,1+(nt-2)*n+j))
 me=bpy.data.meshes.new('SL Lumen | original irregular closed mesh');me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));assert all(e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True)*mm**3;assert vol>0;bm.to_mesh(me);bm.free();obj=bpy.data.objects.new(LUMEN,me);bpy.context.scene.collection.objects.link(obj);obj.hide_render=True;obj.hide_set(True);obj.display_type='WIRE';return obj,vol

def install(body,mm):
 o,vol=make_lumen(mm);hull=BVHTree.FromPolygons([v.co for v in body.data.vertices],[list(f.vertices) for f in body.data.polygons]);margin=[]
 for v in o.data.vertices:
  p,n,_,_=hull.find_nearest(v.co);margin.append((p-v.co).dot(n)*mm)
 assert min(margin)>1.,min(margin)
 g=body.modifiers[0].node_group;N,L=g.nodes,g.links
 def n(t,name):q=N.new(t);q.name=q.label=name;return q
 def w(a,b):
  if isinstance(a,(int,float,bool)):b.default_value=a
  else:L.new(a,b)
 def m(op,a,b):q=n('ShaderNodeMath','Lumen | '+op);q.operation=op;w(a,q.inputs[0]);w(b,q.inputs[1]);return q.outputs[0]
 fruit=N['Fruit mesh to SDF'];voxel=fruit.inputs['Voxel Size'].links[0].from_socket;user=N['SDF difference, no mesh seam triangulator'];whole=N['Grid to Mesh'];info=n('GeometryNodeObjectInfo','Lumen | source closed cavity');info.transform_space='RELATIVE';info.inputs['Object'].default_value=o
 cav=n('GeometryNodeMeshToSDFGrid','Lumen | same voxel size');w(info.outputs['Geometry'],cav.inputs['Mesh']);w(voxel,cav.inputs['Voxel Size']);dif=n('GeometryNodeSDFGridBoolean','Lumen | subtract BEFORE editable cutter');dif.operation='DIFFERENCE';w(fruit.outputs[0],dif.inputs['Grid 1']);w(cav.outputs[0],dif.inputs['Grid 2']);w(dif.outputs[0],user.inputs['Grid 1']);w(dif.outputs[0],whole.inputs['Grid'])
 # Classify cavity surface by the closest source cutter. Keep the normal cap
 # material at cap faces closer to the user cutter, and leave exterior untouched.
 prox=n('GeometryNodeProximity','Lumen | distance to original cavity');prox.target_element='FACES';w(info.outputs['Geometry'],prox.inputs['Geometry']);cd=prox.outputs['Distance'];ud=N['Geometry Proximity'].outputs['Distance'];active=N['0 whole / cut'].inputs['Switch'].links[0].from_socket
 close=m('LESS_THAN',cd,m('MULTIPLY',voxel,1.7));closer=m('LESS_THAN',cd,ud);choose=m('MAXIMUM',m('SUBTRACT',1.,active),closer);wallsel=m('MULTIPLY',close,choose)
 mat=bpy.data.materials.new(WALL);mat.use_nodes=True;bs=next(q for q in mat.node_tree.nodes if q.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(.59,.115,.073,1.);bs.inputs['Roughness'].default_value=.31;bs.inputs['Subsurface Weight'].default_value=.08;bs.inputs['Subsurface Scale'].default_value=.012;bs.inputs['Coat Weight'].default_value=.18
 cut=N['Cut material by active cutter proximity'];smooth=N['Set Shade Smooth'];wall=n('GeometryNodeSetMaterial','Lumen | separate inner-wall material');wall.inputs['Material'].default_value=mat;w(cut.outputs[0],wall.inputs['Geometry']);w(wallsel,wall.inputs['Selection']);w(wall.outputs[0],smooth.inputs['Mesh']);return dict(cavity_source_vertices=len(o.data.vertices),cavity_source_faces=len(o.data.polygons),cavity_source_volume_mm3=vol,cavity_min_hull_margin_mm=float(min(margin)),wall_material=WALL,added_geometry_nodes=12)
if __name__=='__main__':
 src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)==PIN and not out.exists();bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False);b=bpy.data.objects[BODY];r=install(b,bpy.context.scene.unit_settings.scale_length*1000);bpy.ops.wm.save_as_mainfile(filepath=str(out));r.update(source_sha=PIN,scene_sha=sha(out));out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)

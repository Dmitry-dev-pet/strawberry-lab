"""Independent geometry QA for single-gain source-space SDF surface relief A/B."""
import bpy,bmesh,sys,hashlib,json
from pathlib import Path
import numpy as np
BODY='Receptacle | canonical PR29 hull'

def state(s,body,mode,voxel):
 body['sdf_mode']=mode;body['sdf_voxel_mm']=voxel
 body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()

def signature_scene(path):
 bpy.ops.wm.open_mainfile(filepath=str(path.resolve()),use_scripts=False)
 s=bpy.context.scene;body=s.objects[BODY];mm=s.unit_settings.scale_length*1000
 assert abs(mm-22.22222276)<1e-5
 gain=float(body['sdf_cut_relief_gain']);g=body.modifiers[0].node_group
 a=next(n for n in g.nodes if n.bl_idname=='GeometryNodeInputNamedAttribute' and n.inputs['Name'].default_value=='sdf_rest_position')
 noise=g.nodes['ARTIST bulk 3D cell relief variations'];assert noise.inputs['Vector'].is_linked
 assert g.nodes['ARTIST surface microdisplacement'].outputs['Vector'].is_linked
 raw=hashlib.sha256()
 for o in sorted((x for x in s.objects if x.type=='MESH'),key=lambda o:o.name):
  raw.update(o.name.encode());raw.update(repr([(v.co[:]) for v in o.data.vertices]).encode())
 packed=hashlib.sha256(bytes(bpy.data.images['LIVE | ORIGINAL V0 native RGB volume atlas (150^3)'].packed_file.data)).hexdigest()
 results={}
 for voxel in [.32,.20]:
  for mode,name in [(0,'whole'),(1,'plane'),(2,'bite')]:
   state(s,body,mode,voxel)
   if mode==2:
    # edge cutter pose used in PR48 (same for A/B).
    sp=s.objects['SDF | editable sphere bite'];sp.location=(.82,-.70,-.42);sp.scale=(1.04,)*3
    body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
   ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();mesh.calc_loop_triangles()
   p=np.array([v.co[:] for v in mesh.vertices],dtype=np.float64)
   triangles=np.array([t.vertices[:] for t in mesh.loop_triangles],dtype=np.int32)
   areas=np.linalg.norm(np.cross(p[triangles[:,1]]-p[triangles[:,0]],p[triangles[:,2]]-p[triangles[:,0]]),axis=1)*.5*(mm**2)
   bm=bmesh.new();bm.from_mesh(mesh)
   nonman=sum(not e.is_manifold for e in bm.edges)
   volume=bm.calc_volume(signed=True)
   comps=0;seen=set()
   for v in bm.verts:
    if v in seen:continue
    comps+=1;seen.add(v);stack=[v]
    while stack:
     current=stack.pop()
     for e in current.link_edges:
      w=e.other_vert(current)
      if w not in seen:seen.add(w);stack.append(w)
   bm.free()
   res={'mesh_vertices':len(p),'mesh_triangles':len(triangles),'coords_sha':hashlib.sha256(p.tobytes()).hexdigest(),'components':comps,'nonmanifold_edges':nonman,'signed_volume':volume,'min_triangle_area_mm2':float(areas.min()),'cut_material_faces':sum(f.material_index==1 for f in mesh.polygons)}
   assert comps==1 and nonman==0 and volume>0 and areas.min()>1e-10,res
   results[f'{voxel}/{name}']={'metrics':res,'vertices':p}
   ev.to_mesh_clear()
 return {'gain':gain,'raw_geometry_sha':raw.hexdigest(),'packed_atlas_sha':packed,'states':results,'mm':mm}

_args=sys.argv[sys.argv.index('--')+1:];assert len(_args) in (3,4)
A,B,out=map(Path,_args[:3]);expected_gain=float(_args[3]) if len(_args)==4 else 1.0;assert not out.exists()
a=signature_scene(A);b=signature_scene(B)
assert a['gain']==0 and b['gain']==expected_gain
assert a['raw_geometry_sha']==b['raw_geometry_sha'] and a['packed_atlas_sha']==b['packed_atlas_sha']
changes=[]
for key in a['states']:
 av=a['states'][key];bv=b['states'][key]
 assert av['metrics']['mesh_vertices']==bv['metrics']['mesh_vertices']
 assert av['metrics']['mesh_triangles']==bv['metrics']['mesh_triangles']
 delta=np.linalg.norm(av['vertices']-bv['vertices'],axis=1)*a['mm']
 maxd=float(delta.max());num=int((delta>1e-5).sum());median=float(np.median(delta[delta>1e-5])) if num else 0
 if key.endswith('/whole'):assert num==0,(key,num,maxd)
 else:assert num>500 and 0.005<maxd<0.15,(key,num,maxd)
 changes.append({'pose':key,'max_displacement_mm':maxd,'moved_vertices':num,'median_of_moved_mm':median,'A':av['metrics'],'B':bv['metrics']})
result={'status':'PASS_NATIVE_RESTSPACE_GEO_AB','blender':bpy.app.version_string,'source_A':hashlib.sha256(A.read_bytes()).hexdigest(),'source_B':hashlib.sha256(B.read_bytes()).hexdigest(),'raw_mesh_equal':True,'atlas_equal':True,'states':changes,'caveats':['Geometry displacement not proven histological','No exhaustive self-intersection/physical seeds cutter intersection for new displaced body']}
out.write_text(json.dumps(result,indent=2)+'\n');print('GEOMETRY_AB_PASS '+json.dumps([{'state':z['pose'],'moved':z['moved_vertices'],'max_mm':round(z['max_displacement_mm'],5)} for z in changes]),flush=True)

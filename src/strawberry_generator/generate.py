"""Blender CLI: recipe -> independently reseeded pits/achenes/artist graph -> editable scene."""
from pathlib import Path
import argparse,sys,json,hashlib,math
from dataclasses import replace,asdict
from random import Random
import bpy,bmesh
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments/geometric-achene-pits-v1'),str(ROOT/'experiments/integration-live-exterior-v1')]
from strawberry_generator.recipe import Recipe
from fruit_platform import make_context,standard_registry
from fruit_morphometry import load_catalog
from exterior_shape import PitField
from build_integration import HullInMillimetres,cut_with
from build_strawberry_exterior import achene_prototype
from build_pits import Seat,local_refine,floor_hit,fit_seat_exposure,REFERENCE,DIRECTION,BODY
from validate_pits import activate_runtime,activate,topology
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,required=True);parser.add_argument('--recipe',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--render',action='store_true')
 args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);recipe=Recipe(**json.loads(args.recipe.read_text()));args.out.mkdir(parents=True,exist_ok=False)
 pin=json.loads((ROOT/'experiments/live-profile-seed-strands-v1/readback.json').read_text())['full_downloaded_sha256']['live-profile.blend'];assert sha(args.input)==pin
 context=make_context(load_catalog(ROOT/'data/morphometry/measurements-v1.json'),'Camarosa',f'generated-seed-{recipe.seed}',seed=recipe.seed)
 bpy.ops.wm.open_mainfile(filepath=str(args.input.resolve()),use_scripts=False);s=bpy.context.scene;body=s.objects[BODY];root=body.parent;mesh=body.data;mm=s.unit_settings.scale_length*1000
 oldmask=[x.value for x in mesh.attributes['achene_pit'].data];oldattr=mesh.attributes.new('generator_old_pit_mask','FLOAT','POINT')
 for d,v in zip(oldattr.data,oldmask):d.value=v
 for vertex,base in zip(mesh.vertices,mesh.attributes[REFERENCE].data):vertex.co=base.vector
 mesh.update();mesh.calc_loop_triangles();hull=HullInMillimetres(mesh,context);assert abs(mm-hull.mm_per_unit)<1e-5
 raw=hull.anchors();rng=Random(recipe.seed+802);anchors=[]
 for anchor in raw:
  anchors.append(replace(anchor,point=tuple(hull.to_model(anchor.point)*mm),pit_length_radius_mm=anchor.pit_length_radius_mm*.72,pit_width_radius_mm=anchor.pit_width_radius_mm*.72,pit_depth_mm=rng.uniform(.16,.21)))
 field=PitField(anchors);col=bpy.data.collections['Exterior | 264 editable achenes'];seedmat=next(o for o in col.objects if o.get('role')=='achene').data.materials[0]
 for obj in list(col.objects):bpy.data.objects.remove(obj,do_unlink=True)
 prototypes=[achene_prototype(i,seedmat) for i in range(5)];seats=[]
 for i,a in enumerate(anchors):
  obj=bpy.data.objects.new(f'Achene {i+1:03}',prototypes[i%5].copy());col.objects.link(obj);obj.parent=root;obj['role']='achene';obj['population_seed']=recipe.seed;obj['achene_id']=f'{context.instance_id}:achene:{i+1:03}'
  obj.rotation_mode='QUATERNION';obj.rotation_quaternion=Matrix((a.side_axis,a.long_axis,a.normal)).transposed().to_quaternion();obj.scale=(a.width_mm/mm,a.length_mm/mm,a.thickness_mm/mm);obj.location=Vector(a.center)/mm
  point=Vector(a.point)/mm;normal=Vector(a.normal);obj['hull_anchor_rest']=list(point);obj['nonlinear_original_anchor']=list(point);obj['hull_normal_rest']=list(normal);cut_with(obj,s.objects['LIVE CUT | Boolean subtraction volume (hidden in render)'])
  seats.append(Seat(obj,point,normal,a))
 bm=bmesh.new();bm.from_mesh(mesh);counts=local_refine(bm,mesh,seats,mm);assert len(bm.verts)<180000
 base=bm.verts.layers.float_vector.get(REFERENCE);normal=bm.verts.layers.float_vector.get(DIRECTION);mask=bm.verts.layers.float.get('achene_pit');rest=bm.verts.layers.float_vector.get('nonlinear_source_rest')
 depths=[]
 for v in bm.verts:
  v[base]=v.co;depth,weight=field.sample(tuple(v.co*mm));v.co-=Vector(v[normal]).normalized()*(depth/mm);v[mask]=weight;v[rest]=v.co;depths.append(depth)
 bm.normal_update();assert all(e.is_manifold and e.is_contiguous for e in bm.edges);bm.to_mesh(mesh);bm.free();mesh.update();mesh.normals_split_custom_set([(0,0,0)]*len(mesh.loops));mesh.calc_loop_triangles()
 from build_pits import tree_for_mesh
 tree=tree_for_mesh(mesh);pit_depths=[]
 for seat in seats:
  hit=floor_hit(tree,seat.point,seat.normal,mm);depth=(seat.point-hit).dot(seat.normal)*mm;assert .10<depth<.33,(seat.obj.name,depth);pit_depths.append(depth)
  seat.obj.location=hit+seat.normal*(.19*seat.anchor.thickness_mm/mm);fit_seat_exposure(tree,seat,mm)
  obj=seat.obj;transform=Matrix.LocRotScale(obj.location,obj.rotation_quaternion,obj.scale);obj.data.transform(transform);obj.matrix_basis=Matrix.Identity(4)
  attr=obj.data.attributes.new('nonlinear_source_rest','FLOAT_VECTOR','POINT')
  for v,d in zip(obj.data.vertices,attr.data):d.vector=v.co
 # Rebuild the existing artist object, preserving native layer/material routing.
 graph=s.objects['ARTIST | 28 trunks + 264 seed-linked terminals'];curve=graph.data;curve.splines.clear();nodes=[];rootp=Vector((0,0,.85));trunks=[]
 def emit(points,key,parent,**meta):
  sp=curve.splines.new('POLY');sp.points.add(len(points)-1)
  for i,(v,p) in enumerate(zip(sp.points,points)):v.co=(*p,1);v.radius=1-.65*i/(len(points)-1)
  nodes.append(dict(id=key,parent=parent,points=[list(p) for p in points],**meta))
 for j in range(28):
  angle=2*math.pi*j/28;end=Vector((.045*math.cos(angle),.045*math.sin(angle),-.95));trunks.append(end);emit([rootp,end],f'trunk-{j:02}','root')
 for seat in seats:
  obj=seat.obj;end=min((v.co for v in obj.data.vertices),key=lambda p:p.dot(seat.normal));j=round((math.atan2(end.y,end.x)%(2*math.pi))*28/(2*math.pi))%28;t=min(1,max(0,(rootp.z-end.z)/(rootp.z-trunks[j].z)));start=rootp.lerp(trunks[j],t)
  emit([start.lerp(end,k/16) for k in range(17)],'terminal:'+obj.name,f'trunk-{j:02}',seed_id=obj.name,parent_t=t,attachment='actual seed underside vertex')
 graph['nonlinear_source_points']=json.dumps([n['points'][i] for n in nodes for i in range(len(n['points']))]);graph['graph_manifest']=json.dumps(nodes)
 # No old-only pit remains: outside the fresh PitField, the canonical hull equals its unpitted baseline.
 restored=[i for i,(old,new) in enumerate(zip(mesh.attributes['generator_old_pit_mask'].data,mesh.attributes['achene_pit'].data)) if old.value>.001 and new.value==0]
 assert restored and max((mesh.vertices[i].co-mesh.attributes[REFERENCE].data[i].vector).length for i in restored)<1e-6
 s['FruitContext']=context.instance_id;s['Unified context record']=json.dumps({'instance_id':context.instance_id,'seed':context.seed,'detail':context.detail,'research_plan_digest':standard_registry().plan(context).digest(),'recipe':asdict(recipe),'evidence':'ARTIST scatter/profile/pits/graph; inherited tissue atlas'})
 s['Generator recipe']=json.dumps(asdict(recipe));s['Generator Fast only']=True
 text=bpy.data.texts['TISSUE_ZONES__RUN.py'];code=text.as_string()
 needle='        SESSION.error = None\n        if self.exact:';assert code.count(needle)==1
 code=code.replace(needle,"        SESSION.error = None\n        if self.exact and context.scene.get('Generator Fast only'):\n            self.report({'WARNING'},'Generator v1 is Fast-only: new pit mesh failed Exact seam QA')\n            return {'CANCELLED'}\n        if self.exact:")
 needle='        layout = self.layout\n        if context.view_layer.name in CUT_LAYERS:';assert code.count(needle)==1
 code=code.replace(needle,"        layout = self.layout\n        if context.scene.get('Generator Fast only'):\n            layout.label(text='Generator v1: Fast only', icon='INFO')\n            layout.label(text='New pit mesh: Exact seam validation pending')\n            return\n        if context.view_layer.name in CUT_LAYERS:")
 text.clear();text.write(code);runtime=activate_runtime()
 for key,value in [('live_profile_a',recipe.a),('live_profile_b',recipe.b),('live_profile_h',recipe.h)]:setattr(s,key,value)
 assert bpy.ops.strawberry.apply_profile()=={'FINISHED'};activate(s,'whole');assert topology(body.data)>0
 from strawberry_generator.qa import validate
 qa=validate(s,anchors);(args.out/'qa.json').write_text(json.dumps(qa,indent=2)+'\n')
 path=args.out/'strawberry.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path.resolve()),compress=True)
 positions=[tuple(o['nonlinear_original_anchor']) for o in sorted(col.objects,key=lambda o:o.name)];digest=hashlib.sha256(repr(positions).encode()).hexdigest()
 receipt={'recipe':asdict(recipe),'context_instance':context.instance_id,'source_sha256':pin,'scene_sha256':sha(path),'anchor_digest':digest,'canonical_body_digest':hashlib.sha256(repr([tuple(v.vector) for v in mesh.attributes['nonlinear_source_rest'].data]).encode()).hexdigest(),'body_vertices':len(mesh.vertices),'old_only_pit_vertices_restored':len(restored),'sampled_new_pit_depth_mm':[min(pit_depths),max(pit_depths)],'new_field_max_vertex_depth_mm':max(depths),'actual_dimensions_mm':[(max(v.co[i] for v in mesh.vertices)-min(v.co[i] for v in mesh.vertices))*mm for i in range(3)],'quality':'FAST_ONLY_VERIFIED; EXACT_DISABLED','provenance':'Canonical PR29 unpitted hull and150^3atlas inherited; scatter/pits/seed mesh/28+264artistgraph regenerated. Fixed264 only.'}
 (args.out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');(args.out/'anchors.json').write_text(json.dumps([dict(id=f'Achene {i+1:03}',**asdict(a)) for i,a in enumerate(anchors)],indent=2)+'\n')
 print(receipt,flush=True)
 if args.render:
  from strawberry_generator.render import render
  render(s,args.out)
if __name__=='__main__':main()

from pathlib import Path
import sys,json,hashlib
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments/geometric-achene-pits-v1')]
from validate_pits import BODY,DIAGNOSTIC_COUNTS,diagnostic_digest,packed_atlas_digest,topology,body_mesh,pose_knife,KNIFE,activate_runtime,measure,flush_callback,activate,immutable_snapshot
from build_pits import REFERENCE,DIRECTION
baseline,scene_path,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert not out.exists()
REST='Strawberry | PR29 rest space'
def raw_points(o):
    if o.type=='MESH':return np.array([tuple(v.co) for v in o.data.vertices])
    if o.type=='CURVE':return np.array([tuple(p.co[:3]) for spline in o.data.splines for p in spline.points])
def world(o):
    p=raw_points(o);m=np.array(o.matrix_world);return p@m[:3,:3].T+m[:3,3]
def tree(points,mesh):
    mesh.calc_loop_triangles();return BVHTree.FromPolygons([Vector(p) for p in points],[t.vertices[:] for t in mesh.loop_triangles],all_triangles=True)
bpy.ops.wm.open_mainfile(filepath=str(baseline.resolve()),use_scripts=False)
s=bpy.context.scene;original={o.name:world(o) for o in s.objects if o.type in {'MESH','CURVE'}}
raw={o.name:raw_points(o) for o in s.objects if o.type in {'MESH','CURVE'}}
diagnostics={n:diagnostic_digest(s.objects[n],c) for n,c in DIAGNOSTIC_COUNTS.items()};atlas=packed_atlas_digest();materials=immutable_snapshot(s)["materials"]
bpy.ops.wm.open_mainfile(filepath=str(scene_path.resolve()),use_scripts=False)
s=bpy.context.scene;root=s.objects[REST];b=s.objects[BODY];knife=s.objects[KNIFE];mm=s.unit_settings.scale_length*1000
F=np.array(root.matrix_world);max_error=0
for name,p in original.items():
    o=s.objects[name];assert np.array_equal(raw_points(o),raw[name]),name
    expected=p@F[:3,:3].T+F[:3,3];max_error=max(max_error,float(np.max(np.abs(world(o)-expected))))
assert max_error<2e-6,max_error
for n,c in DIAGNOSTIC_COUNTS.items():assert diagnostic_digest(s.objects[n],c)==diagnostics[n]
assert packed_atlas_digest()==atlas
assert immutable_snapshot(s)["materials"]==materials
bindings={mat.name:[(n.name,n.object.name if n.object else None) for n in mat.node_tree.nodes if n.type=="TEX_COORD"] for mat in bpy.data.materials if mat.node_tree}
assert any(obj==REST for nodes in bindings.values() for _,obj in nodes)
body_tree=tree(world(b),b.data);counts={};fractions=[];buried=[]
for o in s.objects:
    if o.get('role')!='achene':continue
    points=world(o);counts[o.name]=len(tree(points,o.data).overlap(body_tree));assert counts[o.name]>0
    signed=[]
    for p in points:
        near,normal,_,_=body_tree.find_nearest(Vector(p));signed.append((Vector(p)-near).dot(normal)*mm)
    fractions.append(sum(v>0 for v in signed)/len(signed));buried.append(-min(signed))
assert len(counts)==264 and min(fractions)>=.4 and min(buried)>=.055,(min(fractions),min(buried))
body_world_digest=hashlib.sha256(world(b).astype('float64').tobytes()).hexdigest()
anchor_world=np.array([tuple(root.matrix_world@Vector(s.objects[n]['hull_anchor_rest'])) for n in sorted(counts)])
assert not np.array_equal(world(b),original[BODY])
width=root['unified_width_factor'];root['unified_width_factor']=width*.98;root.update_tag();bpy.context.view_layer.update()
assert not np.array_equal(world(b),original[BODY]@F[:3,:3].T)
root['unified_width_factor']=width;root.update_tag();bpy.context.view_layer.update()
assert np.max(np.abs(world(b)-(original[BODY]@F[:3,:3].T+F[:3,3])))<2e-6
runtime=activate_runtime();assert bpy.ops.strawberry.exact_quality(exact=True)=={'FINISHED'}
poses=[]
for pose in [(-.1,0,-23),(.08,29,32)]:
    pose_knife(knife,pose);bpy.context.view_layer.update()
    if bpy.app.timers.is_registered(runtime['timer']):flush_callback(runtime)
    else:runtime['session'].refresh()
    assert runtime['session'].error is None
    mesh=body_mesh(b);m,_=measure(s,b,mesh);poses.append({'pose':pose,'exact':m,'world_volume':m['volume_model_units_cubed']*np.linalg.det(F[:3,:3])})
    assert bpy.ops.strawberry.exact_quality(exact=False)=={'FINISHED'};assert topology(body_mesh(b))>0
    assert bpy.ops.strawberry.exact_quality(exact=True)=={'FINISHED'}
for mode in ['whole','matched','flesh-only','fibers-only']:
    layer,graph=activate(s,mode)
    assert b.visible_get()==(mode!='fibers-only')
    if mode=='whole':assert len(body_mesh(b).vertices)==len(b.data.vertices)
    if mode in ['matched','flesh-only']:
        if bpy.app.timers.is_registered(runtime['timer']):flush_callback(runtime)
        assert topology(body_mesh(b))>0
# Native Object coordinates and Exact rest coordinates must use the same inverse F.
errors=[]
for p in [Vector((.1,.2,.3)),Vector((-.4,.1,-.5)),Vector((0,0,.7))]:
    recovered=root.matrix_world.inverted()@(root.matrix_world@p);errors.append((recovered-p).length)
assert max(errors)<1e-6
activate(s,'matched')
assert bpy.ops.strawberry.exact_quality(exact=False)=={'FINISHED'}
assert packed_atlas_digest()==atlas
result={'status':'PASS','scene_sha256':hashlib.sha256(scene_path.read_bytes()).hexdigest(),'world_mapping_max_error_model_units':max_error,'actual_world_mesh_contacts':counts,'min_exposed_vertex_fraction':min(fractions),'min_world_buried_mm':min(buried),'world_body_digest':body_world_digest,'world_anchor_digest':hashlib.sha256(anchor_world.tobytes()).hexdigest(),'original_diagnostic_digests':diagnostics,'packed_atlas_digest':atlas,'inverse_rest_max_error':max(errors),'material_graphs_unchanged':True,'texture_coordinate_bindings':bindings,'two_cut_poses':poses,'four_native_layers':True,'live_width_driver_roundtrip':True,'vascular_attachment_constraint':'UNRESOLVED;539 !=264','limits':'Affine template deformation; reference-mm texture/relief stretches under F. No new scatter/topology/histology.'}
out.write_text(json.dumps(result,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else list(v))+'\n');print('Unified world mapping,264contacts,twoFast/Exactposes,fourlayers PASS')

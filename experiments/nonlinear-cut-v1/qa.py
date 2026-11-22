from pathlib import Path
import sys,json,hashlib
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments/geometric-achene-pits-v1'),str(ROOT/'experiments/profile-vascular-v1')]
from validate_pits import body_mesh,topology,pose_knife,KNIFE,activate
from profile_probe import forward,inverse
p=Path(sys.argv[sys.argv.index('--')+1]);out=Path(sys.argv[sys.argv.index('--')+2]);assert not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(p.resolve()),use_scripts=False);s=bpy.context.scene;cfg=json.loads(s['Nonlinear parameters']);params=(cfg['a'],cfg['b'],cfg['h']);b=s.objects['Receptacle | canonical PR29 hull'];mm=s.unit_settings.scale_length*1000
old=np.array([tuple(x.vector) for x in b.data.attributes['nonlinear_source_rest'].data]);new=np.array([tuple(v.co) for v in b.data.vertices]);expected=np.array([forward(p,params) for p in old]);assert np.max(abs(new-expected))<2e-7
fit=np.linalg.lstsq(np.c_[old,np.ones(len(old))],new,rcond=None)[0];residual=float(np.sqrt(np.mean(np.sum((new-np.c_[old,np.ones(len(old))]@fit)**2,axis=1))));assert residual>.01
inv_error=max(float(np.linalg.norm(inverse(n,params)-o)) for n,o in zip(new[::31],old[::31]));assert inv_error<1e-6
b.data.calc_loop_triangles();tree=BVHTree.FromPolygons([v.co for v in b.data.vertices],[t.vertices[:] for t in b.data.loop_triangles],all_triangles=True);contacts={}
for o in s.objects:
 if o.get('role')!='achene':continue
 o.data.calc_loop_triangles();t=BVHTree.FromPolygons([o.matrix_local@v.co for v in o.data.vertices],[t.vertices[:] for t in o.data.loop_triangles],all_triangles=True);contacts[o.name]=len(t.overlap(tree));assert contacts[o.name]>0,o.name
assert len(contacts)==264
obj=s.objects['ARTIST | 28 trunks + 264 seed-linked terminals'];nodes=json.loads(obj['graph_manifest']);errors=[]
for sp,n in zip(obj.data.splines,nodes):
 if 'seed_id' not in n:continue
 seed=s.objects[n['seed_id']];end=Vector(sp.points[-1].co[:3]);errors.append(min((end-v.co).length for v in seed.data.vertices)*mm)
assert len(errors)==264 and max(errors)<1e-4
poses=[]
activate(s,'matched')
for pose in [(-.1,0,-23),(.08,29,32)]:
 pose_knife(s.objects[KNIFE],pose);bpy.context.view_layer.update();poses.append({'pose':pose,'positive_volume':topology(body_mesh(b)),'rest_samples':[list(inverse(q,params)) for q in [(0,0,.2),(.2,.1,-.3)]]})
for mode in ['whole','matched','flesh-only','fibers-only']:activate(s,mode)
assert all('Exact disabled' in t.as_string() for t in bpy.data.texts if t.name.endswith('.py') and ('EXACT' in t.name or 'TISSUE_ZONES' in t.name))
out.write_text(json.dumps({'status':'FAST_ONLY_PASS','scene_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'best_affine_rms':residual,'inverse_max_error':inv_error,'contacts':contacts,'terminal_vertex_error_mm':max(errors),'poses':poses,'native_layers':list(s.view_layers.keys()),'Exact':'DISABLED','source_digests':json.loads(s['Nonlinear source digests'])},indent=2)+'\n')

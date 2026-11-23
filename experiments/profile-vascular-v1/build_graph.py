"""Bounded ARTIST root/28-trunk/264-terminal integration on PR35; affine shapes retained."""
from pathlib import Path
import bpy,sys,json,math,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments/unified-strawberry-context-v1')]
from controls import SharedDeformation
from fruit_platform import make_context
from fruit_morphometry import load_catalog
out=ROOT/'build/profile-vascular-final';reports=[]
for variant,expected,w,h in [('elongated','4bbb4313111b0e19ffa31ba701bee5dfa66246effb31347bb1a031dfdc0cda2f',.8,1.15),('round','509adc2b40714ea34e9066ff7e589a523e66048b722264d6009020ab654b18bd',1.1,.9)]:
 source=ROOT.parent/'strawberry-unified-context/build/unified-context-v1'/f'{variant}.blend'
 assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
 target=out/f'{variant}.blend';assert not target.exists()
 control=SharedDeformation(make_context(load_catalog(ROOT/'data/morphometry/measurements-v1.json'),'Camarosa','unified-'+variant),w,h)
 bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);s=bpy.context.scene;root=s.objects['Strawberry | PR29 rest space'];mm=s.unit_settings.scale_length*1000
 original=s.objects['V4 | hook0.85 | BRANCHES'];mat=original.data.materials[0]
 col=bpy.data.collections['Diagnostics | original paths and 539 markers']
 curve=bpy.data.curves.new('ARTIST | rooted 264-terminal graph','CURVE');curve.dimensions='3D';curve.resolution_u=1;curve.bevel_depth=.003;curve.bevel_resolution=2;curve.materials.append(mat)
 obj=bpy.data.objects.new('ARTIST | 28 trunks + 264 seed-linked terminals',curve);col.objects.link(obj);obj.parent=root
 rootp=Vector((0,0,.85));trunks=[];nodes=[]
 def emit(points,key,parent):
  sp=curve.splines.new('POLY');sp.points.add(len(points)-1)
  for i,(p,pt) in enumerate(zip(points,sp.points)):pt.co=(*p,1);pt.radius=1-.65*i/(len(points)-1)
  nodes.append({'id':key,'parent':parent,'points':[list(p) for p in points]})
 for j in range(28):
  a=2*math.pi*j/28;end=Vector((.045*math.cos(a),.045*math.sin(a),-.95));trunks.append(end);emit([rootp,end],f'trunk-{j:02}','root')
 errors=[];inside=[];body=s.objects['Receptacle | canonical PR29 hull'];body.data.calc_loop_triangles();tree=BVHTree.FromPolygons([v.co for v in body.data.vertices],[t.vertices[:] for t in body.data.loop_triangles],all_triangles=True)
 for seed in sorted((o for o in s.objects if o.get('role')=='achene'),key=lambda o:o.name):
  normal=Vector(seed['hull_normal_rest']);pts=[seed.matrix_local@v.co for v in seed.data.vertices];end=min(pts,key=lambda p:p.dot(normal))
  angle=math.atan2(end.y,end.x)%(2*math.pi);j=round(angle*28/(2*math.pi))%28
  t=min(1,max(0,(rootp.z-end.z)/(rootp.z-trunks[j].z)));start=rootp.lerp(trunks[j],t)
  points=[start.lerp(end,k/16) for k in range(17)];emit(points,'terminal:'+seed.name,f'trunk-{j:02}')
  nodes[-1].update(seed_id=seed.name,attachment='deepest actual seed mesh vertex along saved normal',parent_t=t)
  errors.append((root.matrix_world@points[-1]-root.matrix_world@end).length*mm)
  for p in points:
   near,n,_,_=tree.find_nearest(p);inside.append((p-near).dot(n)*mm)
 assert max(errors)<1e-5
 # Preserve all original geometry, while making the NEW graph the default diagnostic display.
 for name in ['V3 | 28-sag0.25 | CARRIERS','V4 | hook0.85 | BRANCHES']:
  s.objects[name].hide_render=True;s.objects[name].hide_viewport=False
 for o in bpy.data.collections['Markers | 539 diagnostic anchors'].objects:o.hide_render=True;o.hide_viewport=False
 obj['graph_manifest']=json.dumps(nodes);obj['evidence']='ARTIST; no biological validation; source existing264seed IDs';obj['root_rest']=list(rootp)
 s['Vascular graph status']='ARTIST 264-terminal graph; original539diagnostics retained hidden. Nonlinear morphology NOT integrated.'
 bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
 report={'variant':variant,'source_sha256':expected,'scene_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'context':control.record(),'trunks':28,'terminals':264,'endpoint_error_mm':max(errors),'max_sample_outside_mm':max(inside),'nodes':nodes,'nonlinear_status':'NOT INTEGRATED: Exact and atlas require nonlinear inverse rest field; affine presets retained'}
 (out/f'{variant}-graph.json').write_text(json.dumps(report,indent=2)+'\n');reports.append({k:v for k,v in report.items() if k!='nodes'})
(out/'build.json').write_text(json.dumps(reports,indent=2)+'\n')

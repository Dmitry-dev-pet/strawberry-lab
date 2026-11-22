"""Strict PR35 source data/transform preservation, independent of new graph."""
import bpy,sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments/geometric-achene-pits-v1')]
from validate_pits import immutable_snapshot
source,target,out=map(Path,sys.argv[sys.argv.index('--')+1:])
def snapshot():
 s=bpy.context.scene;r={}
 for o in s.objects:
  if o.type not in {'MESH','CURVE'}:continue
  data=([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons]) if o.type=='MESH' else [[(tuple(p.co),p.radius,p.tilt) for p in sp.points] for sp in o.data.splines]
  r[o.name]={'geometry':hashlib.sha256(repr(data).encode()).hexdigest(),'world':[list(row) for row in o.matrix_world],'parent':o.parent.name if o.parent else None,'basis':[list(row) for row in o.matrix_basis]}
 return r,immutable_snapshot(s)['materials']
bpy.ops.wm.open_mainfile(filepath=str(source.resolve()),use_scripts=False);a,ma=snapshot()
bpy.ops.wm.open_mainfile(filepath=str(target.resolve()),use_scripts=False);b,mb=snapshot()
assert set(b)-set(a)=={'ARTIST | 28 trunks + 264 seed-linked terminals'}
for key,value in a.items():assert value==b[key],key
assert ma==mb
out.write_text(json.dumps({'status':'PASS','all_original_mesh_curve_objects':len(a),'source_geometry_transform_digests':a,'materials_equal':True,'intentional_display_change':'Old diagnostic curves/markers hidden in renders only; original geometry/IDs retained'},indent=2)+'\n')

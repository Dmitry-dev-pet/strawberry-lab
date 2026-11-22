"""Reopen owned baseline and generated output; verify canonical provenance and physical scene."""
from pathlib import Path
import sys,json,hashlib
import bpy
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments/geometric-achene-pits-v1')]
from validate_pits import DIAGNOSTIC_COUNTS,activate_runtime,packed_atlas_digest
from exterior_shape import AcheneAnchor
from strawberry_generator.qa import validate

def provenance():
 s=bpy.context.scene;r={}
 for name,count in DIAGNOSTIC_COUNTS.items():
  o=s.objects[name]
  if o.type=='CURVE':
   assert len(o.data.splines)==count
   r[name]=(o['nonlinear_source_points'],[[p.radius for p in sp.points] for sp in o.data.splines])
  else:r[name]=([tuple(v.vector) for v in o.data.attributes['nonlinear_source_rest'].data],[tuple(f.vertices) for f in o.data.polygons])
 return hashlib.sha256(repr(r).encode()).hexdigest(),packed_atlas_digest()
source,folder,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(source.resolve()),use_scripts=False);expected=provenance()
path=folder/'strawberry.blend';receipt=json.loads((folder/'receipt.json').read_text());assert hashlib.sha256(path.read_bytes()).hexdigest()==receipt['scene_sha256']
bpy.ops.wm.open_mainfile(filepath=str(path.resolve()),use_scripts=False);assert provenance()==expected
s=bpy.context.scene;mesh=s.objects['Receptacle | canonical PR29 hull'].data;mm=s.unit_settings.scale_length*1000
rawdims=[(max(v.co[i] for v in mesh.vertices)-min(v.co[i] for v in mesh.vertices))*mm for i in range(3)]
anchors=[AcheneAnchor(**{k:v for k,v in item.items() if k!='id'}) for item in json.loads((folder/'anchors.json').read_text())]
activate_runtime();report=validate(s,anchors);report.update(old_diagnostic_canonical_digest=expected[0],atlas_unchanged=True,actual_uncut_raw_dimensions_mm=rawdims)
# Exact is enabled only after the shared physical-zero/CDT gates.
from validate_pits import activate
activate(s,'matched');assert bpy.ops.strawberry.exact_quality(exact=True)=={'FINISHED'}
bpy.ops.strawberry.exact_quality(exact=False)
report['Exact_activation_verified']=True
out.write_text(json.dumps(report,indent=2)+'\n')

"""Read-only evidence inventory for an Exact adapter; no scene writes or handlers."""
import bpy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def inspect(path):
 bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
 rows=[]
 for obj in bpy.context.scene.objects:
  if obj.type not in {'MESH','CURVE'}:continue
  if not any(x in obj.name for x in ('M1c','M1e','Receptacle','V3','V4')):continue
  rows.append({'name':obj.name,'type':obj.type,'vertices':len(obj.data.vertices) if obj.type=='MESH' else None,'splines':len(obj.data.splines) if obj.type=='CURVE' else None,'attributes':list(obj.data.attributes.keys()) if obj.type=='MESH' else [],'modifiers':[(m.name,m.type) for m in obj.modifiers],'materials':[m.name if m else None for m in obj.data.materials]})
 groups=[{'name':g.name,'nodes':len(g.nodes)} for g in bpy.data.node_groups]
 return {'file':path.name,'scene':bpy.context.scene.name,'scale_length':bpy.context.scene.unit_settings.scale_length,'objects':rows,'groups':groups,'text_names':list(bpy.data.texts.keys())}
report={name:inspect(ROOT/'build/inputs'/name) for name in ('m1e5-exact-original.blend','m1e6-nativeGN-production.blend','pr30-corrected.blend')}
p=ROOT/'build/m1e5-assessment/saved-source-inventory.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

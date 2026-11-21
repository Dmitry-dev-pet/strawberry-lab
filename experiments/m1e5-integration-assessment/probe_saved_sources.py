"""Read-only evidence inventory for an Exact adapter; no scene writes or handlers."""
import bpy,json,sys,argparse,hashlib
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
EXPECTED={
 'm1e5-exact-original.blend':'2082a81c0d2607faabdefefe0403deed997c703f2c3a1dfe96ea0338e6c4efb2',
 'm1e6-nativeGN-production.blend':'119dd13b7e7fa7ed130fba844e02c698095b7d601fea6227bb00d7fa7149d33f',
 'pr30-corrected.blend':'0b8af93c399d0077f51f864f7b9f55673b822a1755e2badcc626f5bfc6256bca',
}
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--inputs',type=Path,default=ROOT/'build/inputs')
 ap.add_argument('--out',type=Path,default=ROOT/'build/m1e5-assessment/saved-source-inventory.json')
 args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
 # Verify every identity before opening a scene or attributing any evidence.
 for name,wanted in EXPECTED.items():
  actual=hashlib.sha256((args.inputs/name).read_bytes()).hexdigest()
  if actual!=wanted:raise ValueError(f'Input SHA256 mismatch: {name}')
 report={name:inspect(args.inputs/name) for name in EXPECTED}
 args.out.parent.mkdir(parents=True,exist_ok=True)
 args.out.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()

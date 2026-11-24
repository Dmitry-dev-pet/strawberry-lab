import bpy, json, sys,collections
from pathlib import Path
p=Path(sys.argv[sys.argv.index('--')+1]);out=Path(sys.argv[sys.argv.index('--')+2]);bpy.ops.wm.open_mainfile(filepath=str(p),use_scripts=False)
# factual inventory only, not node topology or values
rows=[]
for o in bpy.data.objects:
 if o.name.startswith('SCHNELL KIWI |') or o.name in ['KIWI | Körper','KIWI | Samen und Haare','KIWI | Griffel und Kelch']:
  mods=[]
  for m in o.modifiers:
   if m.type!='NODES' or m.node_group is None:continue
   g=m.node_group;co=collections.Counter(n.bl_idname for n in g.nodes)
   mods.append(dict(modifier=m.name,group=g.name,node_count=len(g.nodes),sdf={k:v for k,v in co.items() if 'Grid' in k or 'Boolean' in k or 'Bake' in k or 'DeleteGeometry' in k},bake_blocks=[len(b.data_blocks) for b in m.bakes]))
  if mods:rows.append(dict(object=o.name,modifiers=mods))
root=bpy.data.node_groups.get('KIWI • Frucht komplett');r=collections.Counter(n.bl_idname for n in root.nodes) if root else {}
data=dict(file=p.name,blender=bpy.app.version_string,root={k:v for k,v in r.items() if 'Boolean' in k or 'Grid' in k},objects=rows)
out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');print(json.dumps(data,ensure_ascii=False))

from pathlib import Path
import ast,hashlib,json
import bpy
root=Path(__file__).resolve().parents[3];p=root/'build/source-seam-v1';result={}
for seed in [101,202]:
 source=root.parent/'strawberry-generator/build/generator-v1-final'/f'seed{seed}/strawberry.blend'
 bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);old=bpy.data.texts['TISSUE_ZONES__RUN.py'].as_string()
 bpy.ops.wm.open_mainfile(filepath=str(p/f'seed{seed}.blend'),use_scripts=False);new=bpy.data.texts['TISSUE_ZONES__RUN.py'].as_string()
 label="        layout.label(text='Physical blade offset: +0.001 mm rest-Y')\n"
 assert new.count(label)==1 and new.replace(label,'')==old
 funcs={}
 for name in ['cap_patch','make_mesh']:
  nodes=[next(n for n in ast.walk(ast.parse(code)) if isinstance(n,ast.FunctionDef) and n.name==name) for code in [old,new]]
  assert ast.dump(nodes[0],include_attributes=False)==ast.dump(nodes[1],include_attributes=False)
  funcs[name]=hashlib.sha256(ast.dump(nodes[0],include_attributes=False).encode()).hexdigest()
 result[str(seed)]={'runtime_only_panel_label_changed':True,'original_CDT_and_make_mesh_AST_sha256':funcs}
(p/'code-parity.json').write_text(json.dumps(result,indent=2)+'\n')

import bpy,importlib.util
from pathlib import Path
p=Path(__file__).with_name('layer_controls_ui.py')
spec=importlib.util.spec_from_file_location('layer_controls_ui',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert bpy.data.texts['LAYER_LAB_UI__RUN_IN_BLENDER.py'].as_string()==p.read_text(encoding='utf-8')
m.register()
s1=bpy.data.scenes['LAYER A | common cut y=0'];s2=bpy.data.scenes['LAYER B | flesh-only cut y=0']
if bpy.context.window:bpy.context.window.scene=s2

def excludes(s,key):return m.get_by_suffix(s,key).exclude
assert not excludes(s2,'30 | VASCULAR') and excludes(s2,'31 | VASCULAR')
s2.sll_branches='OFF';assert excludes(s2,'30 | VASCULAR') and excludes(s2,'31 | VASCULAR')
s2.sll_branches='CLIP';assert excludes(s2,'30 | VASCULAR') and not excludes(s2,'31 | VASCULAR')
s2.sll_seeds='OFF';assert excludes(s2,'40 | SEED') and excludes(s2,'41 | SEED')
s2.sll_core='FULL';assert not excludes(s2,'20 | CORE') and excludes(s2,'21 | CORE')
s2.sll_show_flesh=False;assert excludes(s2,'10 | FLESH')
s2.sll_ghost=True;assert not excludes(s2,'50 | OUTLINE')
if bpy.context.window:bpy.context.window.scene=s1
assert not excludes(s1,'31 | VASCULAR') and excludes(s1,'30 | VASCULAR')
assert s1.sll_branches=='CLIP' and s1.sll_show_flesh
print('LAYER_UI_CALLBACKS_PASS 7 independent scene controls',flush=True)

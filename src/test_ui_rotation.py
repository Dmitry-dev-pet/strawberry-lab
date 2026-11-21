import bpy,importlib.util,math,json
from pathlib import Path
root=Path(__file__).parent
script=(root/'m1e5_live_exact.py').read_text(encoding='utf8')
assert bpy.data.texts['M1e5 - Enable Live Exact.py'].as_string()==script
original_blend_file=bpy.data.filepath
assert original_blend_file
# Simulate the user pressing Text > Run Script twice: callbacks/classes must not duplicate.
for i in range(2):
    exec(compile(script,'M1e5 - Enable Live Exact.py','exec'),{'__name__':'__main__'})
print('M1E5_UI_HANDLERS',sum(fn.__name__=='_on_frame' for fn in bpy.app.handlers.frame_change_post),sum(fn.__name__=='_on_depsgraph' for fn in bpy.app.handlers.depsgraph_update_post),flush=True)
assert sum(fn.__name__=='_on_frame' for fn in bpy.app.handlers.frame_change_post)==1
assert sum(fn.__name__=='_on_depsgraph' for fn in bpy.app.handlers.depsgraph_update_post)==1
assert hasattr(bpy.types,'STRAWBERRY_PT_m1e5')
s=bpy.context.scene;k=bpy.data.objects['M1e | independently moving knife (cube half space)']
# Operator exposed on UI: forced regenerations, Fast mode, Exact mode.
assert bpy.ops.strawberry_lab.m1e5_fast()=={'FINISHED'}
assert s['m1e5_mode']=='FAST_GN_ALWAYS_LIVE'
assert bpy.ops.strawberry_lab.m1e5_enable()=={'FINISHED'}
assert s['m1e5_mode']=='EXACT_SCRIPT_ENABLED'
assert bpy.ops.strawberry_lab.m1e5_refresh()=={'FINISHED'}
# Rotate knife around Z: local refinement should be independent of cut angle.
s.frame_set(21)
old=k.rotation_euler.copy();k.rotation_euler.z+=math.radians(18.)
bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get();dg.update()
snap=bpy.data.objects['M1e5 | EXACT live-local CutSurface'];me=snap.evaluated_get(dg).to_mesh()
assert len(me.vertices)>5000 and len(me.vertices)<180000
print('M1E5_ROTATION_TEST',json.dumps({'angle_delta':18,'verts':len(me.vertices),'frame':s.frame_current}),flush=True)
k.rotation_euler=old;bpy.context.view_layer.update()
# Check same addon can persist past re-opening known saved .blend.
bpy.ops.wm.open_mainfile(filepath=original_blend_file)
assert bpy.context.scene['m1e5_mode']=='EXACT_SCRIPT_ENABLED','persistent load_post did not resume opt-in addon on scene load'
assert not bpy.data.objects['M1e5 | EXACT live-local CutSurface'].hide_render
print('M1E5_TEXT_DOUBLE_CLICK_UI_ROTATION_RELOAD_PASS',flush=True)

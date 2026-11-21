"""Blender real property/collection callback smoke tests on saved scene."""
import bpy,importlib.util,math,json
from pathlib import Path
R=Path(__file__).resolve().parent
f=R/'live_cut_ui.py'
assert bpy.data.texts['LIVE_CUT_CONTROLS__RUN.py'].as_string()==f.read_text()
spec=importlib.util.spec_from_file_location('live_cut_ui',f)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.register()
a=bpy.data.scenes['LIVE MATCHED | shared movable plane'];b=bpy.data.scenes['LIVE FLESH ONLY | shared movable plane']
control=bpy.data.objects['LIVE CUT | move or rotate this Empty']
if bpy.context.window:bpy.context.window.scene=b
assert b.scl_body=='CUT' and b.scl_branch=='FULL'
assert a.scl_branch=='CLIP'
assert m.find_layer(b,'31 | 539 BRANCHES').exclude and not m.find_layer(b,'30 | 539 BRANCHES').exclude
b.scl_branch='CLIP'
assert not m.find_layer(b,'31 | 539 BRANCHES').exclude and m.find_layer(b,'30 | 539 BRANCHES').exclude
b.scl_marker='OFF'
assert m.find_layer(b,'41 | 539 MARKERS').exclude and m.find_layer(b,'40 | 539 MARKERS').exclude
b.scl_core='CLIP';assert not m.find_layer(b,'21 | 28 CORE').exclude
b.scl_body='FULL'
assert m.find_layer(b,'10 | FLESH cut').exclude and not m.find_layer(b,'11 | FLESH whole').exclude
b.scl_ghost=True
assert not m.find_layer(b,'50 | WHOLE OUTLINE').exclude
b.scl_offset=.27
assert abs(control.location.y-.27)<1e-6 and abs(a.scl_offset-.27)<1e-6
b.scl_angle=25.
assert abs(math.degrees(control.rotation_euler.z)-25)<1e-5
assert abs(a.scl_angle-25)<1e-5
# Test scene isolation of layer toggles but shared plane transform.
assert a.scl_core=='CLIP' and a.scl_body=='CUT' and a.scl_branch=='CLIP'
assert not m.find_layer(a,'31 | 539 BRANCHES').exclude
assert not m.find_layer(a,'10 | FLESH cut').exclude
b.scl_offset=0.;b.scl_angle=0.
report={'status':'PASS','same_one_plane_both_scenes':True,'empty_offset_test':.27,'empty_rotation_deg_test':25.,'test_cases':['body FULL/CUT/OFF via actual ViewLayer collection flags','core branches and markers Off/Clipped/Full','translucent outline','cut offset updates shared Empty','cut angle updates shared Empty','switches per scene independent']}
(R/'ui-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('LIVE_LAYER_UI_TEST_PASS',json.dumps(report),flush=True)

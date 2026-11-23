"""Native Fast render after WHOLE/profile change versus fresh selected-layer control."""
from pathlib import Path
import sys,json
import bpy
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments/geometric-achene-pits-v1')]
from validate_pits import activate,activate_runtime,pose_knife,KNIFE,body_mesh,topology
scene,layer,case,png=sys.argv[sys.argv.index('--')+1:];png=Path(png);assert not png.exists()
bpy.ops.wm.open_mainfile(filepath=str(Path(scene).resolve()),use_scripts=False);s=bpy.context.scene;activate_runtime();activate(s,'matched');assert topology(body_mesh(s.objects['Receptacle | canonical PR29 hull']))>0
if case=='candidate':activate(s,'whole')
cfg=json.loads(s['Nonlinear parameters']);values=(-.12,.18,.96) if cfg['a']>0 else (.23,-.12,1.08)
for key,value in zip(['live_profile_a','live_profile_b','live_profile_h'],values):setattr(s,key,value)
assert bpy.ops.strawberry.apply_profile()=={'FINISHED'};pose_knife(s.objects[KNIFE],(.08,29,32));bpy.context.view_layer.update()
if case=='control':bpy.context.window.view_layer=s.view_layers[layer];bpy.context.view_layer.update()
s.render.resolution_percentage=10;s.cycles.samples=1;s.render.filepath=str(png.resolve());bpy.ops.render.render(write_still=True,layer=layer)
png.with_suffix('.json').write_text(json.dumps({'quality':'nativeFast','profile_changed':True,'case':case,'target_layer':layer,'selected_layer':bpy.context.view_layer.name},indent=2)+'\n')

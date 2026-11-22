from pathlib import Path
import sys,json,inspect
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments/geometric-achene-pits-v1')]
from validate_pits import activate_runtime
import validate_cross_layer_render as regression
regression.activate_runtime=activate_runtime
source=inspect.getsource(regression.render)
source=source.replace('    runtime = activate_runtime()', '    bpy.context.window.view_layer = scene.view_layers["MATCHED"]\n    bpy.context.view_layer.update()\n    runtime = activate_runtime()')
needle='    knife.location.y += 0.25';assert source.count(needle)==1
source=source.replace(needle,"""    for key,value in zip(('live_profile_a','live_profile_b','live_profile_h'),(-.12,.18,.96)):
        setattr(scene,key,value)
    assert bpy.ops.strawberry.apply_profile()=={'FINISHED'}
"""+needle)
exec(source,regression.__dict__)
scene,layer,case,png=sys.argv[sys.argv.index('--')+1:];png=Path(png);assert not png.exists()
_,receipt=regression.render(Path(scene).resolve(),png.resolve(),layer,case=='candidate')
png.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n')

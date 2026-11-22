from pathlib import Path
import sys,json
import bpy
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(Path(__file__).parent),str(ROOT/'src'),str(ROOT/'experiments/geometric-achene-pits-v1')]
from probe import metrics
from validate_pits import activate,body_mesh,pose_knife,KNIFE
result={}
for seed in [101,202]:
 source=ROOT.parent/'strawberry-generator/build/generator-v1-final'/f'seed{seed}/strawberry.blend';bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);s=bpy.context.scene;activate(s,'matched');knife=s.objects[KNIFE];knife.delta_location.y=.001/(s.unit_settings.scale_length*1000);body=s.objects['Receptacle | canonical PR29 hull'];assert body.modifiers[0].solver=='MANIFOLD';rows=[]
 for pose in [(0,0,0),(.08,29,32),(-.26,0,0)]:
  pose_knife(knife,pose);bpy.context.view_layer.update();m=metrics(body_mesh(body));rows.append({'requested_pose':pose,'physical_knife_matrix':[list(row) for row in knife.matrix_world],'bias_rest_y_mm':.001,**m})
 result[str(seed)]=rows
(ROOT/'build/source-seam-v1/bias-probe.json').write_text(json.dumps(result,indent=2)+'\n')

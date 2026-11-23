"""Independent interactive-control geometry update after loading with scripts disabled."""
import sys,hashlib,json
from pathlib import Path
import bpy,bmesh
scene,output=map(Path,sys.argv[sys.argv.index('--')+1:]);assert scene.is_file() and not output.exists()
bpy.ops.wm.open_mainfile(filepath=str(scene.resolve()),use_scripts=False)
s=bpy.context.scene;body=s.objects['Receptacle | canonical PR29 hull'];body['sdf_mode']=1;body['sdf_voxel_mm']=.32

def evaluated():
 body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
 ob=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ob.to_mesh();geometry=hashlib.sha256(repr([tuple(v.co) for v in me.vertices]).encode()).hexdigest();bm=bmesh.new();bm.from_mesh(me);nonman=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);bm.free();count=len(me.vertices);ob.to_mesh_clear();assert nonman==0 and vol>0;return geometry,count
values=[]
for gain in (.35,0.0,.35):
 body['sdf_cut_relief_gain']=gain
 digest,count=evaluated();values.append({'gain':gain,'digest':digest,'vertices':count})
assert values[0]['digest']!=values[1]['digest'] and values[0]['digest']==values[2]['digest']
old=values[2]['digest'];plane=s.objects['SDF | editable plane halfspace'];plane.rotation_euler.z=.5
new,_=evaluated();assert new!=old
result={'status':'PASS_LIVE_CONTROL','scene_sha256':hashlib.sha256(scene.read_bytes()).hexdigest(),'script_execution_disabled':True,'gain_round_trip':values,'cutter_rotation_changes_mesh':True,'blender':bpy.app.version_string}
output.write_text(json.dumps(result,indent=2)+'\n');print('PASS_LIVE_CONTROL',len(values),flush=True)

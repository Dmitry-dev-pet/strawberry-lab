"""Check native wet-film object follows changing cutters and on/off without Blender autoexec."""
import bpy,json,sys,hashlib
from pathlib import Path
p=Path(sys.argv[sys.argv.index('--')+1]).resolve();out=Path(sys.argv[sys.argv.index('--')+2]).resolve();assert p.is_file() and not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(p),use_scripts=False);assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
s=bpy.context.scene;b=s.objects['Receptacle | canonical PR29 hull'];film=s.objects['SDF | live cut wet-film surface']
def snapshot(label):
 b.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update();o=film.evaluated_get(dg);me=o.to_mesh();n=len(me.polygons);coords=hashlib.sha256(repr([tuple(v.co) for v in me.vertices]).encode()).hexdigest();o.to_mesh_clear();print('LIVE_FILM',label,n,coords[:12],flush=True);return {'name':label,'faces':n,'sha':coords}
b['sdf_voxel_mm']=.32;b['sdf_mode']=1;plane=s.objects['SDF | editable plane halfspace'];plane.rotation_euler=(0,0,0)
records=[snapshot('plane-original')];b['sdf_wetfilm_gain']=0;records.append(snapshot('film-disabled'));b['sdf_wetfilm_gain']=1;records.append(snapshot('film-restored'))
plane.rotation_euler=(.25,0,.20);records.append(snapshot('plane-rotated'))
b['sdf_mode']=2;sphere=s.objects['SDF | editable sphere bite'];sphere.location=(.82,-.70,-.42);sphere.scale=(1.04,)*3;records.append(snapshot('bite-edge'))
assert records[0]['faces']>0 and records[1]['faces']==0 and records[0]==dict(records[2],name='plane-original')
assert records[3]['sha']!=records[2]['sha'] and records[4]['sha']!=records[3]['sha']
out.write_text(json.dumps({'status':'PASS_DYNAMIC_WET_FILM','scene_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'scripts_disabled':True,'states':records},indent=2)+'\n')
print('LIVE_FILM_PASS',flush=True)

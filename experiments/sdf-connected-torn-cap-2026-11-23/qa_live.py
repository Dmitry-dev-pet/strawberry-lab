"""Independent native live-GN cutter & gain QA with saved script-autoexec OFF."""
import bpy,sys,hashlib,json,numpy as np, argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--scene',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert a.scene.is_file() and not a.out.exists()
bpy.ops.wm.open_mainfile(filepath=str(a.scene.resolve()),use_scripts=False);assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
s=bpy.context.scene;b=s.objects['Receptacle | canonical PR29 hull'];sp=s.objects['SDF | editable sphere bite'];plane=s.objects['SDF | editable plane halfspace'];b['sdf_voxel_mm']=.32;b['sdf_mode']=2;sp.location=(.82,-.70,-.42);sp.scale=(1.04,)*3

def sample(name):
 b.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();d=bpy.context.evaluated_depsgraph_get();d.update();o=b.evaluated_get(d);m=o.to_mesh();x=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',x);r={'name':name,'gain':float(b['sdf_torn_extrude_gain']),'mode':int(b['sdf_mode']),'verts':len(m.vertices),'faces':len(m.polygons),'sha':hashlib.sha256(x.tobytes()).hexdigest()};o.to_mesh_clear();print('TORN_LIVE',r,flush=True);return r
b['sdf_torn_extrude_gain']=1;on=sample('on');b['sdf_torn_extrude_gain']=0;off=sample('off');b['sdf_torn_extrude_gain']=1;restored=sample('restored');assert on['sha']==restored['sha'] and on['sha']!=off['sha'] and on['verts']>off['verts']
sp.location=(.73,-.62,-.45);sp.scale=(.97,)*3;moved=sample('moved sphere');assert moved['sha']!=on['sha']
b['sdf_mode']=1;plane.location=(0,0,0);plane.rotation_euler=(0,0,0);flat_on=sample('plane gain on');b['sdf_torn_extrude_gain']=0;flat_off=sample('plane gain off');assert flat_on['sha']==flat_off['sha']
b['sdf_mode']=0;whole=sample('whole');assert whole['verts']>0
rec={'status':'PASS_NATIVE_LIVE_EXTRUDED_TISSUE','source_sha256':hashlib.sha256(a.scene.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'autoexec':False,'records':[on,off,restored,moved,flat_on,flat_off,whole]};a.out.write_text(json.dumps(rec,indent=2)+'\n')

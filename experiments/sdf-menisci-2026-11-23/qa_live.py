"""Scripts-disabled native Geometry Nodes menisci live control contract."""
import bpy,hashlib,json,sys,argparse
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--scene',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert a.scene.is_file() and not a.out.exists()
bpy.ops.wm.open_mainfile(filepath=str(a.scene.resolve()),use_scripts=False);assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
s=bpy.context.scene;b=s.objects['Receptacle | canonical PR29 hull'];pocket=s.objects['SDF | separate vascular-attached lens pockets'];b['sdf_voxel_mm']=.32;b['sdf_mode']=1
plane=s.objects['SDF | editable plane halfspace'];plane.rotation_euler=(0,0,0);plane.location=(0,0,0)
def snapshot(name):
 b.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update();o=pocket.evaluated_get(dg);m=o.to_mesh();v=np.zeros(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',v);rec={'name':name,'verts':len(m.vertices),'faces':len(m.polygons),'sha':hashlib.sha256(v.tobytes()).hexdigest()};o.to_mesh_clear();print('LIVE',name,rec['verts'],rec['sha'][:12],flush=True);return rec
records=[]
for name,gain in [('original',1.),('disabled',0.),('restored',1.)]:
 b['sdf_meniscus_gain']=gain;records.append(snapshot(name))
assert records[0]['verts']>0 and records[1]['verts']==0 and records[2]['sha']==records[0]['sha'] and records[2]['faces']==records[0]['faces']
plane.rotation_euler=(.25,0,.2);records.append(snapshot('rotated plane'));assert records[-1]['sha']!=records[0]['sha']
b['sdf_mode']=2;sph=s.objects['SDF | editable sphere bite'];sph.location=(.82,-.70,-.42);sph.scale=(1.04,)*3;records.append(snapshot('open-side bite'));assert records[-1]['verts']>0 and records[-1]['sha']!=records[-2]['sha']
result={'status':'PASS_NATIVE_LIVE_MENISCI','scene_sha256':hashlib.sha256(a.scene.read_bytes()).hexdigest(),'scripts_disabled':True,'blender':bpy.app.version_string,'records':records,'limits':'Only tested plane rotation and moved sphere, not arbitrary poses'}
a.out.write_text(json.dumps(result,indent=2)+'\n');print('PASS_NATIVE_LIVE_MENISCI',flush=True)

"""Native saved .blend live property and cutter-motion QA, scripts disabled."""
import bpy,sys,json,hashlib,numpy as np
from pathlib import Path
src=Path(sys.argv[sys.argv.index('--')+1]);dest=Path(sys.argv[sys.argv.index('--')+2]);assert src.is_file() and not dest.exists()
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),use_scripts=False);assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
s=bpy.context.scene;b=s.objects['Receptacle | canonical PR29 hull'];plane=s.objects['SDF | editable plane halfspace']
b['sdf_mode']=1;b['sdf_voxel_mm']=.32;b['sdf_tissue_gain']=1;b['sdf_use_broad_halo']=1
plane.location=(0,0,0);plane.rotation_euler=(0,0,0)

def sample(label):
 b.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();d=bpy.context.evaluated_depsgraph_get();d.update();o=b.evaluated_get(d);me=o.to_mesh();x=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',x);rec={'name':label,'verts':len(me.vertices),'xyz_sha':hashlib.sha256(x.tobytes()).hexdigest()};o.to_mesh_clear();return rec
b['sdf_cell_surface_gain']=1;on=sample('on')
b['sdf_cell_surface_gain']=0;off=sample('off')
b['sdf_cell_surface_gain']=1;restored=sample('restored')
assert on['xyz_sha']==restored['xyz_sha'] and off['xyz_sha']!=on['xyz_sha'] and off['xyz_sha']=='a165e4d603ea0e5238ca81c65a43f28d2de688e6b285df6d743c9e79d940955c'
plane.rotation_euler=(.35,0,.25);rotated=sample('rotated');assert rotated['xyz_sha']!=on['xyz_sha']
sph=s.objects['SDF | editable sphere bite'];b['sdf_mode']=2;sph.location=(.82,-.70,-.42);sph.scale=(1.04,)*3;bite=sample('edge bite');assert bite['xyz_sha']!=rotated['xyz_sha']
r={'status':'PASS_NATIVE_CELL_COHERENCE_DYNAMIC_GAIN_AND_CUTTER','scene_sha':hashlib.sha256(src.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'scripts_disabled':True,'records':[on,off,restored,rotated,bite]}
dest.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

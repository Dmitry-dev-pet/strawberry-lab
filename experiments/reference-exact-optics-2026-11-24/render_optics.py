"""Matched original Cycles dry/wet renders; temporary diagnostic light rig only."""
import bpy,sys,json,hashlib,time
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'deps'));sys.path.insert(0,str(H))
from qa_split import setup,ROOT
from build_optics import sha
src,pose,gain,mode,out=sys.argv[sys.argv.index('--')+1:];gain=float(gain);mode=int(mode);out=Path(out);assert not out.exists();bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()),use_scripts=False);setup('plane' if pose=='macro' else pose,.32);r=bpy.data.objects[ROOT]
for k,v in {'exact_mode':1,'exact_voxel_mm':.32,'tissue_gain':1.,'cap_refine_level':2,'juice_gain':gain,'juice_optics_mode':mode}.items():r[k]=v
r.update_tag();bpy.context.view_layer.update();s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=12;s.cycles.seed=1729;s.cycles.use_denoising=True;s.cycles.transparent_max_bounces=16;s.cycles.max_bounces=8
s.render.resolution_x=s.render.resolution_y=480;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(out.resolve());cam=s.camera
# Camera and illumination are identical in A/B; do not save modified scene.
if pose=='plane':
 target=Vector((0,0,24));cam.location=(0,-125,34);cam.data.ortho_scale=55
elif pose=='macro':
 target=Vector((5,0,29));cam.location=(5,-120,38);cam.data.ortho_scale=14
else:
 target=Vector((5,-3,29));cam.location=(68,-108,59);cam.data.ortho_scale=55
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
for o in list(s.objects):
 if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
# scene is physically scaled in mm; area lights in Blender coordinate units.
def light(name,pos,power,size,size_y):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='RECTANGLE';d.size=size;d.size_y=size_y;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,25))-o.location).to_track_quat('-Z','Y').to_euler()
light('Diagnostic softbox left',(-28,-40,63),90000,24,38);light('Diagnostic strip right',(27,-36,28),60000,8,29);light('Diagnostic fill',(6,18,55),45000,32,32)
if s.world is None:s.world=bpy.data.worlds.new('Diagnostic world')
s.world.use_nodes=True;s.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.25,.25,.25,1);s.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.4
s.view_settings.view_transform='AgX';bpy.context.view_layer.update();t=time.perf_counter();bpy.ops.render.render(write_still=True);assert out.exists();out.with_suffix('.json').write_text(json.dumps({'scene_sha':sha(src),'image_sha':sha(out),'pose':pose,'juice_gain':gain,'juice_optics_mode':mode,'tissue_gain':1.,'exact_voxel_mm':.32,'cap_refine_level':2,'engine':'CYCLES','samples':12,'seed':1729,'resolution':[480,480],'camera_matrix':[list(x) for x in cam.matrix_world],'ortho_scale':cam.data.ortho_scale,'lights':[(o.name,o.data.energy,list(o.location)) for o in s.objects if o.type=='LIGHT'],'render_seconds':time.perf_counter()-t},indent=2)+'\n')

import bpy,time,os,json,bmesh,math,hashlib
from mathutils import Vector
from pathlib import Path
P=Path(os.environ.get('STRAWBERRY_SDF_OUT',str(Path(__file__).resolve().parents[2]/'build/sdf-vertical-slice')))
BLEND=P/'strawberry-sdf-vertical-slice-v4.blend'
bpy.ops.wm.open_mainfile(filepath=str(BLEND),use_scripts=False)
sc=bpy.context.scene
assert not bpy.context.preferences.filepaths.use_scripts_auto_execute, 'Autoexecute should be disabled'
image=bpy.data.images['SDF proof v4 | 192^3 sparse volume and continuous branches']
assert image.packed_file and tuple(image.size)==(3072,2304)
mat=bpy.data.materials['SDF proof v4 | sparse branches + cell sheen']
assert all(n.image==image for n in mat.node_tree.nodes if n.bl_idname=='ShaderNodeTexImage')
assert sum(n.bl_idname=='ShaderNodeTexVoronoi' for n in mat.node_tree.nodes)==3
report={'version':4,'source_sha256':hashlib.sha256(BLEND.read_bytes()).hexdigest(),'atlas_sha256':hashlib.sha256((P/'tissue-v4-192.png').read_bytes()).hexdigest(),'scripts_autoexecute':bpy.context.preferences.filepaths.use_scripts_auto_execute,'packed_atlas':list(image.size),'states':{}}
for fr,tag in ((1,'whole'),(20,'planar'),(40,'bite')):
 sc.frame_set(fr)
 obj=bpy.data.objects['Receptacle | sculpted skin and achene pits'] if tag=='whole' else bpy.data.objects['SDF visible body | '+tag]
 dg=bpy.context.evaluated_depsgraph_get()
 ev=obj.evaluated_get(dg);me=ev.to_mesh()
 count={'vertices':len(me.vertices),'faces':len(me.polygons),'rest_present':('fruit_rest' in me.attributes)}
 bm=bmesh.new();bm.from_mesh(me);count['nonmanifold_edges']=sum(not e.is_manifold for e in bm.edges);bm.free();ev.to_mesh_clear()
 assert count['nonmanifold_edges']==0
 if tag!='whole':assert count['rest_present']
 report['states'][tag]=count
 print('V4_REOPEN_VALIDATION',tag,count,flush=True)
for kind,fr in (('planar',20),('bite',40)):
 scene=sc
 scene.frame_set(fr)
 seed=bpy.data.objects['SDF visible seeds | '+kind]
 cutter=bpy.data.objects['SDF cutter | '+('planar (move or rotate)' if kind=='planar' else 'spherical bite (move or scale)')]
 dg=bpy.context.evaluated_depsgraph_get()
 s_eval=seed.evaluated_get(dg);mesh=s_eval.to_mesh()
 to_local=cutter.matrix_world.inverted_safe()@seed.matrix_world
 intrusions=0
 for v in mesh.vertices:
  q=to_local@v.co
  inside=(max(abs(q.x),abs(q.y),abs(q.z))<.999 if kind=='planar' else q.length<.999)
  if inside:intrusions+=1
 kept=len(mesh.vertices)//178
 s_eval.to_mesh_clear()
 assert intrusions==0
 report['states'][kind]['remaining_seeds']=kept
 report['states'][kind]['seed_vertices_inside_cutter']=intrusions
print('V4_REOPEN_QA_PASS',json.dumps(report,ensure_ascii=False),flush=True)
(P/'validation-v4.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
sc.render.engine='CYCLES'
sc.cycles.device='CPU';sc.cycles.samples=36
sc.render.resolution_x=860;sc.render.resolution_y=860
sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'
for fr,name in ((20,'plane'),(40,'bite')):
 sc.frame_set(fr)
 sc.render.filepath=str(P/('sdf-v4-'+name+'.png'))
 t=time.monotonic();bpy.ops.render.render(write_still=True)
 print('V4_RENDER',name,round(time.monotonic()-t,2),os.path.getsize(sc.render.filepath),flush=True)
sc.frame_set(20)
cam=sc.camera;cam.data.ortho_scale=31.0
target=Vector((0,0,24))
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
sc.render.filepath=str(P/'sdf-v4-macro.png')
t=time.monotonic();bpy.ops.render.render(write_still=True)
print('V4_RENDER','macro',round(time.monotonic()-t,2),os.path.getsize(sc.render.filepath),flush=True)
print('ALL_V4_DONE',flush=True)

import bpy,json,sys,bmesh,hashlib
from pathlib import Path
p=Path(__file__).resolve().parents[2]/'build/sdf-vertical-slice'
scene=bpy.context.scene
assert not bpy.context.preferences.filepaths.use_scripts_auto_execute,'unexpected autoexec enabled'
records={}
for f,kind in ((1,'whole'),(20,'planar'),(40,'bite')):
 scene.frame_set(f)
 if kind=='whole':
  o=bpy.data.objects['Receptacle | sculpted skin and achene pits']
 else:
  o=bpy.data.objects['SDF visible body | '+kind]
 dg=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dg);me=ev.to_mesh()
 bm=bmesh.new();bm.from_mesh(me)
 nm=sum(not e.is_manifold for e in bm.edges);bm.free()
 attrs=list(me.attributes.keys())
 nv=len(me.vertices)
 ev.to_mesh_clear()
 records[kind]={'vertices':len(o.data.vertices) if kind=='whole' else None,'evaluated_vertices':nv,'nonmanifold_edges':nm,'fruit_rest_on_cut':('fruit_rest' in attrs)}
 assert nm==0,records[kind]
 if kind!='whole': assert records[kind]['fruit_rest_on_cut']
image=bpy.data.images['SDF proof | shared 128cubed tissue atlas']
assert image.packed_file and tuple(image.size)==(2048,1024)
r={'status':'REOPEN_WITH_DISABLED_SCRIPTS_PASS','engine':bpy.app.version_string,'packed_atlas':True,'atlas_dimensions':list(image.size),'scene':records,'blend_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()}
(p/'validation-reopen-v3.json').write_text(json.dumps(r,indent=2))
print('REOPEN_PASS',json.dumps(r),flush=True)

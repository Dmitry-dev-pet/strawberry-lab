"""Isolated Blender 5.2.4 native-geometry QA, one v17 alternative per invocation.
Open a real saved .blend with scripts disabled. Never save changes to source.
"""
import bpy,bmesh,numpy as np,json,hashlib,sys,time
from pathlib import Path
ROOT=Path('/mnt/data/strawberry-v17')
variant=sys.argv[sys.argv.index('--')+1]
assert variant in ('v17a','v17b')
f=ROOT/f'strawberry-{variant}-restfield.blend'
sha=hashlib.sha256(f.read_bytes()).hexdigest()
expected={'v17a':'5571464c89a4aad5ba050a14706ac20e202f6d3c3ecdd4e48b964893f028c2a9',
          'v17b':'edf8afa6c1ecca9a4a589f8bf6e53b8f9e38721c8c2180896f74c3fefe2fa03c'}
assert sha==expected[variant]
t0=time.monotonic()
bpy.ops.wm.open_mainfile(filepath=str(f),use_scripts=False)
assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
scene=bpy.context.scene
image=bpy.data.images[f'Strawberry {variant} | original 192^3 RGB rest-space (ARTIST)']
assert image.packed_file and list(image.size)==[3072,2304]
material=bpy.data.materials['SDF v12 | continuous vascular fibers, restrained wetness (ARTIST)']
gn=bpy.data.node_groups['V8 | original rest-space vascular field (192^3)']
assert sum(n.image==image for n in material.node_tree.nodes if n.bl_idname=='ShaderNodeTexImage')==2
assert sum(n.inputs['Image'].default_value==image for n in gn.nodes if n.bl_idname=='GeometryNodeImageTexture')==2
result={'blender':bpy.app.version_string,'saved_scene_sha256':sha,'version':variant,'autoexec':False,'states':{}}
plane=bpy.data.objects['SDF cutter | planar (move or rotate)'];bite=bpy.data.objects['SDF cutter | spherical bite (move or scale)']
for name,mode,frame in (('whole','whole',1),('plane','planar',20),('bite','bite',40),('plane_moved','planar',20),('bite_moved','bite',40)):
 if name=='plane_moved':
  oldloc=plane.location.copy();oldrot=plane.rotation_euler.copy();plane.location.y+=3.;plane.rotation_euler.x+=.1745329252
 if name=='bite_moved':
  oldloc=bite.location.copy();oldscale=bite.scale.copy();bite.location.x-=4.;bite.scale=bite.scale*1.13
 scene.frame_set(frame)
 obj=bpy.data.objects['Receptacle | sculpted skin and achene pits'] if mode=='whole' else bpy.data.objects['SDF visible body | '+mode]
 deps=bpy.context.evaluated_depsgraph_get();ev=obj.evaluated_get(deps);m=ev.to_mesh()
 bm=bmesh.new();bm.from_mesh(m)
 bad=sum(not ed.is_manifold for ed in bm.edges);volume=bm.calc_volume(signed=True)
 bm.free()
 row={'vertices':len(m.vertices),'faces':len(m.polygons),'nonmanifold_edges':bad,'signed_volume':round(volume,4)}
 assert bad==0 and volume>0,(variant,name,row)
 if mode!='whole':
  for attr in ('fruit_rest','v8_vascular_intensity','v8_cell_height_mm'):
   assert attr in m.attributes
  c=np.empty(len(m.polygons),np.int32);m.polygons.foreach_get('material_index',c)
  row['cap_faces']=int((c==2).sum())
  assert row['cap_faces']>20000
 result['states'][name]=row
 ev.to_mesh_clear()
 if name=='plane_moved':plane.location=oldloc;plane.rotation_euler=oldrot
 if name=='bite_moved':bite.location=oldloc;bite.scale=oldscale
 print('QA_STATE_PASS',variant,name,json.dumps(row),flush=True)
result['elapsed_seconds']=round(time.monotonic()-t0,2)
(ROOT/f'v17-core-qa-{variant}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('QA_V17_CORE_ALL_5_PASS',variant,flush=True)

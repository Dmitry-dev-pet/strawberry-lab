"""Independent saved-scene QA for v13; evaluates real meshes in Blender 5.2.2.
Does not write/re-save source or input fruit scenes. Strictly experimental ARTIST.
"""
import bpy,bmesh,hashlib,json,time,os
import numpy as np
from pathlib import Path
P=Path(os.environ.get("STRAWBERRY_SDF_OUT",str(Path(__file__).resolve().parent)))
FILE=P/"strawberry-sdf-vertical-slice-v13-spatial-fibrils.blend"
assert FILE.is_file()
bpy.ops.wm.open_mainfile(filepath=str(FILE),use_scripts=False)
sc=bpy.context.scene
image=bpy.data.images["SDF proof v13 | 192^3 coherent directional fibrils (ARTIST)"]
field=bpy.data.node_groups["V8 | original rest-space vascular field (192^3)"]
samplers=[n for n in field.nodes if n.bl_idname=="GeometryNodeImageTexture"]
assert len(samplers)==2 and all(n.inputs["Image"].default_value==image for n in samplers)
mat=bpy.data.materials["SDF v12 | continuous vascular fibers, restrained wetness (ARTIST)"]
assert sum(n.image==image for n in mat.node_tree.nodes if n.bl_idname=="ShaderNodeTexImage")==2
assert image.packed_file
rep={"saved_scene_sha256":hashlib.sha256(FILE.read_bytes()).hexdigest(),
     "image_atlas":list(image.size),"autoexec_enabled":bool(bpy.context.preferences.filepaths.use_scripts_auto_execute),
     "test_states":{},"physical_ab":{}}
assert not rep["autoexec_enabled"]
def state(tag,frame,lab):
 sc.frame_set(frame)
 body=bpy.data.objects["Receptacle | sculpted skin and achene pits"] if tag=="whole" else bpy.data.objects["SDF visible body | "+tag]
 deps=bpy.context.evaluated_depsgraph_get()
 ev=body.evaluated_get(deps); mesh=ev.to_mesh()
 bm=bmesh.new(); bm.from_mesh(mesh)
 bad=sum(not ed.is_manifold for ed in bm.edges)
 volume=float(bm.calc_volume(signed=True))
 bm.free()
 line={"vertices":len(mesh.vertices),"faces":len(mesh.polygons),"nonmanifold_edges":bad,"volume":round(volume,3)}
 assert bad==0 and volume>0 and len(mesh.vertices)>10000,(tag,lab,line)
 if tag!="whole":
  for a in ("fruit_rest","v8_vascular_intensity","v13_ridge_height_mm"):
   assert a in mesh.attributes, (a,tag)
  n=len(mesh.vertices)
  v=np.empty(n,np.float32);h=np.empty(n,np.float32)
  mesh.attributes["v8_vascular_intensity"].data.foreach_get("value",v)
  mesh.attributes["v13_ridge_height_mm"].data.foreach_get("value",h)
  line["vascular_p95"]=round(float(np.percentile(v,95)),5)
  line["ridge_abs_max_mm"]=round(float(np.abs(h).max()),5)
  line["ridge_vertices_gt_0_01mm"]=int(np.count_nonzero(np.abs(h)>.01))
  seed=bpy.data.objects["SDF visible seeds | "+tag]
  cutter=bpy.data.objects["SDF cutter | "+("planar (move or rotate)" if tag=="planar" else "spherical bite (move or scale)")]
  se=seed.evaluated_get(deps); sm=se.to_mesh()
  inv=cutter.matrix_world.inverted_safe()@seed.matrix_world
  invaded=0
  for vertex in sm.vertices:
   co=inv@vertex.co
   if tag=="planar": inside=max(abs(co.x),abs(co.y),abs(co.z))<.999
   else:inside=co.length<.999 # conservative v10 scalloped sphere min radius~0.9
   invaded+=int(inside)
  line["visible_seed_solids"]=len(sm.vertices)//178
  line["seed_vertices_inside_cutter_conservative"]=invaded
  se.to_mesh_clear()
  # Exact scattering guards already tested on original v12. v13 never
  # modifies seed masks or cutter geometry; report, do not mask defects.
  assert line["ridge_vertices_gt_0_01mm"]>200 and line["ridge_abs_max_mm"]>.02
  assert invaded==0,(tag,lab,invaded)
 ev.to_mesh_clear()
 rep["test_states"][lab]=line
 print("V13_QA",lab,json.dumps(line),flush=True)
state("whole",1,"whole")
state("planar",20,"plane")
state("bite",40,"bite")
for tag in ("planar","bite"):
 sc.frame_set(20 if tag=="planar" else 40)
 g=bpy.data.node_groups["SDF cutter + rest-space | "+tag]
 gain=g.nodes["V13_FIBER_HEIGHT_STRENGTH"]
 obj=bpy.data.objects["SDF visible body | "+tag]
 def positions():
  deps=bpy.context.evaluated_depsgraph_get()
  ev=obj.evaluated_get(deps);m=ev.to_mesh()
  p=np.empty(len(m.vertices)*3,dtype=np.float32)
  m.vertices.foreach_get("co",p)
  ev.to_mesh_clear()
  return p.reshape(-1,3)
 orig=float(gain.outputs["Value"].default_value)
 pos=positions()
 gain.outputs["Value"].default_value=0.
 zero=positions()
 gain.outputs["Value"].default_value=orig
 assert pos.shape==zero.shape
 change=np.linalg.norm(pos-zero,axis=1)
 row={"max_real_displacement_mm":round(float(change.max()),5),
      "changed_vertices_gt_0_01mm":int(np.count_nonzero(change>.01)),
      "mean_displacement_mm":round(float(change.mean()),6)}
 assert row["max_real_displacement_mm"]>.02 and row["changed_vertices_gt_0_01mm"]>200
 rep["physical_ab"][tag]=row
 print("V13_REAL_GEOMETRY",tag,json.dumps(row),flush=True)
plane=bpy.data.objects["SDF cutter | planar (move or rotate)"]
p_loc=plane.location.copy();p_rot=plane.rotation_euler.copy()
plane.location.y+=3.0;plane.rotation_euler.x+=.1745329252
state("planar",20,"moved_plane")
plane.location=p_loc;plane.rotation_euler=p_rot
bite=bpy.data.objects["SDF cutter | spherical bite (move or scale)"]
b_loc=bite.location.copy();b_scale=bite.scale.copy()
bite.location.x-=4.;bite.scale=b_scale*1.13
state("bite",40,"moved_bite")
bite.location=b_loc;bite.scale=b_scale
(P/"v13-validation.json").write_text(json.dumps(rep,ensure_ascii=False,indent=2)+"\n")
print("V13_QA_COMPLETE_PASS",flush=True)

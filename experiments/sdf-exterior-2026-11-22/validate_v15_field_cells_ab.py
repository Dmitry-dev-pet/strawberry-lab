"""V15 independent post-reopen native-mesh, field and geometry A/B diagnostics.

Test actual positions: same SDF source, frame, model and field, only fiber
cell-flattening mask differs.  No v15 scenes or reference files overwritten.
"""
import bpy,bmesh,numpy as np,os,json,time,hashlib
from pathlib import Path
from mathutils.bvhtree import BVHTree
P=Path(os.environ["STRAWBERRY_SDF_OUT"])
names={"A":"strawberry-sdf-vertical-slice-v15a-uncoupled-cells.blend",
       "B":"strawberry-sdf-vertical-slice-v15b-restfield-coupled-cells.blend"}
report={"versions":{},"cross_variant_geometry":{}}
meshes={}
for variant,filename in names.items():
 file=P/filename
 bpy.ops.wm.open_mainfile(filepath=str(file),use_scripts=False)
 assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
 sc=bpy.context.scene
 img=bpy.data.images["SDF proof v4 | 192^3 sparse volume and continuous branches"]
 assert img.packed_file and list(img.size)==[3072,2304]
 field=bpy.data.node_groups["V8 | original rest-space vascular field (192^3)"]
 samplers=[n for n in field.nodes if n.bl_idname=="GeometryNodeImageTexture"]
 assert len(samplers)==2 and all(n.inputs["Image"].default_value==img for n in samplers)
 data={"scene_sha256":hashlib.sha256(file.read_bytes()).hexdigest(),"states":{}}
 for tag in ("planar","bite"):
  g=bpy.data.node_groups["SDF cutter + rest-space | "+tag]
  mask=next(n for n in g.nodes if n.bl_idname=="ShaderNodeMapRange" and n.label.startswith("No cell relief"))
  gain=g.nodes["V8_CELL_STRENGTH"]
  assert abs(gain.outputs["Value"].default_value-3.2)<1e-4
  assert abs(mask.inputs["To Max"].default_value-(1.0 if variant=="A" else .06))<1e-4
 def snapshot(tag,frame,name):
  sc.frame_set(frame)
  obj=bpy.data.objects["Receptacle | sculpted skin and achene pits"] if tag=="whole" else bpy.data.objects["SDF visible body | "+tag]
  deps=bpy.context.evaluated_depsgraph_get()
  ev=obj.evaluated_get(deps);mesh=ev.to_mesh()
  bm=bmesh.new();bm.from_mesh(mesh)
  nonmanifold=sum(not e.is_manifold for e in bm.edges)
  volume=float(bm.calc_volume(signed=True))
  min_area=min(face.calc_area() for face in bm.faces)
  bm.free()
  row={"vertices":len(mesh.vertices),"triangulated_faces_original":len(mesh.polygons),"nonmanifold_edges":nonmanifold,
       "volume":round(volume,3),"smallest_face_area":float(min_area)}
  assert nonmanifold==0 and volume>0 and min_area>1e-10,(variant,name,row)
  if tag!="whole":
   for a in ("fruit_rest","v8_vascular_intensity","v8_cell_height_mm"):
    assert a in mesh.attributes,(variant,name,a)
   count=len(mesh.vertices)
   coords=np.empty(count*3,dtype=np.float32);mesh.vertices.foreach_get("co",coords)
   vascular=np.empty(count,dtype=np.float32);mesh.attributes["v8_vascular_intensity"].data.foreach_get("value",vascular)
   h=np.empty(count,dtype=np.float32);mesh.attributes["v8_cell_height_mm"].data.foreach_get("value",h)
   row["cell_physical_max_mm"]=round(float(np.abs(h).max()),6)
   row["high_field_verts"]=int((vascular>.3).sum())
   row["cell_gt_0_03mm"]=int((np.abs(h)>.03).sum())
   row["rest_field_p95"]=round(float(np.percentile(vascular,95)),6)
   if name in ("plane","bite"):
    meshes[variant,tag]={"co":coords.reshape(-1,3),"vascular":vascular,"cell_height":h}
  data["states"][name]=row
  ev.to_mesh_clear()
  print("V15_MESH",variant,name,json.dumps(row),flush=True)
 snapshot("whole",1,"whole")
 snapshot("planar",20,"plane")
 snapshot("bite",40,"bite")
 planar=bpy.data.objects["SDF cutter | planar (move or rotate)"]
 oldloc=planar.location.copy();oldrot=planar.rotation_euler.copy()
 planar.location.y+=3.0;planar.rotation_euler.x+=.1745329252
 snapshot("planar",20,"plane_moved")
 planar.location=oldloc;planar.rotation_euler=oldrot
 bite=bpy.data.objects["SDF cutter | spherical bite (move or scale)"]
 oldloc=bite.location.copy();oldscale=bite.scale.copy()
 bite.location.x-=4.;bite.scale=oldscale*1.13
 snapshot("bite",40,"bite_moved")
 bite.location=oldloc;bite.scale=oldscale
 report["versions"][variant]=data
for tag in ("planar","bite"):
 a=meshes["A",tag];b=meshes["B",tag]
 assert a["co"].shape==b["co"].shape
 assert np.allclose(a["vascular"],b["vascular"],atol=1e-5)
 vascular=a["vascular"]
 change=np.linalg.norm(a["co"]-b["co"],axis=1)
 amp_a=np.abs(a["cell_height"]);amp_b=np.abs(b["cell_height"])
 high=(vascular>.3)&(amp_a>.015)
 low=(vascular<.02)&(amp_a>.015)
 assert high.sum()>50 and low.sum()>50,(tag,int(high.sum()),int(low.sum()))
 ratio_h=float(np.mean(amp_b[high])/np.mean(amp_a[high]))
 ratio_l=float(np.mean(amp_b[low])/np.mean(amp_a[low]))
 row={"high_field_test_vertices":int(high.sum()),"low_field_test_vertices":int(low.sum()),
      "mean_high_field_relief_ratio_B_to_A":ratio_h,
      "mean_low_field_relief_ratio_B_to_A":ratio_l,
      "real_vertex_max_difference_mm":float(change.max()),
      "changed_verts_gt_0_01mm":int((change>.01).sum())}
 assert ratio_h<.65 and .96<ratio_l<1.04 and change.max()>.01,(tag,row)
 report["cross_variant_geometry"][tag]=row
 print("V15_COUPLING_EFFECT",tag,json.dumps(row),flush=True)
(P/"v15-validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print("V15_INDEPENDENT_QA_PASS",flush=True)

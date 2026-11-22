"""Independent validation of v14A field-only and v14B field+physical tear.
Read/reopen saved Blender 5.2.2 scenes with scripts disabled. No scene writes.
"""
import bpy,bmesh,numpy as np,hashlib,json,time,os
from pathlib import Path
from mathutils.bvhtree import BVHTree
P=Path(os.environ["STRAWBERRY_SDF_OUT"])
files={"A":P/"strawberry-sdf-vertical-slice-v14a-branch-field.blend",
       "B":P/"strawberry-sdf-vertical-slice-v14b-branch-tear.blend"}
rows={}
for version,path in files.items():
 assert path.is_file()
 bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
 assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
 sc=bpy.context.scene
 atlas=bpy.data.images["SDF v14 | nonperiodic achene-linked 3D fibrous field (ARTIST)"]
 assert atlas.packed_file and list(atlas.size)==[3072,2304]
 field=bpy.data.node_groups["V8 | original rest-space vascular field (192^3)"]
 assert sum(n.inputs["Image"].default_value==atlas for n in field.nodes if n.bl_idname=="GeometryNodeImageTexture")==2
 mat=bpy.data.materials["SDF v12 | continuous vascular fibers, restrained wetness (ARTIST)"]
 assert sum(n.image==atlas for n in mat.node_tree.nodes if n.bl_idname=="ShaderNodeTexImage")==2
 bitegroup=bpy.data.node_groups["SDF cutter + rest-space | bite"]
 gain=bitegroup.nodes["V14_TEAR_GAIN"]
 assert float(gain.outputs["Value"].default_value)==(0. if version=="A" else 1.)
 rows[version]={"scene_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"states":{}}
 def test(tag,frame,name):
  sc.frame_set(frame)
  obj=bpy.data.objects["Receptacle | sculpted skin and achene pits"] if tag=="whole" else bpy.data.objects["SDF visible body | "+tag]
  deps=bpy.context.evaluated_depsgraph_get()
  ev=obj.evaluated_get(deps);m=ev.to_mesh()
  bm=bmesh.new();bm.from_mesh(m);bm.normal_update()
  nonman=sum(not e.is_manifold for e in bm.edges)
  vol=float(bm.calc_volume(signed=True))
  minface=float(min(face.calc_area() for face in bm.faces))
  bm.free()
  record={"vertices":len(m.vertices),"faces":len(m.polygons),"volume":round(vol,3),
    "nonmanifold_edges":nonman,"min_face_area":round(minface,11)}
  assert nonman==0 and vol>0 and minface>1e-10,(version,name,record)
  if tag!="whole":
   assert "fruit_rest" in m.attributes
   assert "v8_vascular_intensity" in m.attributes
   if tag=="bite":
    attr=m.attributes.get("v14_tear_height_mm")
    assert attr
    heights=np.empty(len(m.vertices),np.float32);attr.data.foreach_get("value",heights)
    record["height_abs_max_mm"]=round(float(np.abs(heights).max()),6)
    record["height_nonzero_gt_0_02mm"]=int((np.abs(heights)>.02).sum())
    if version=="A":assert record["height_abs_max_mm"]==0
    else:assert record["height_nonzero_gt_0_02mm"]>500
  ev.to_mesh_clear()
  rows[version]["states"][name]=record
  print("V14_STATE",version,name,json.dumps(record),flush=True)
 test("whole",1,"whole")
 test("planar",20,"plane")
 test("bite",40,"bite")
 plane=bpy.data.objects["SDF cutter | planar (move or rotate)"]
 loc,rot=plane.location.copy(),plane.rotation_euler.copy()
 plane.location.y+=3.0;plane.rotation_euler.x+=.1745329252
 test("planar",20,"plane_moved")
 plane.location=loc;plane.rotation_euler=rot
 cutter=bpy.data.objects["SDF cutter | spherical bite (move or scale)"]
 loc,scale=cutter.location.copy(),cutter.scale.copy()
 cutter.location.x-=4.;cutter.scale*=1.13
 test("bite",40,"bite_moved")
 cutter.location=loc;cutter.scale=scale
 # Optional independent local cutter intrusion checks on the actual scalloped
 # mesh (not a unit-sphere distance approximation). Expensive only for B.
 if version=="B":
  entries={}
  for mode,frame in (("planar",20),("bite",40)):
   cut=bpy.data.objects["SDF cutter | "+("planar (move or rotate)" if mode=="planar" else "spherical bite (move or scale)")]
   seed=bpy.data.objects["SDF visible seeds | "+mode]
   bm=bmesh.new();bm.from_mesh(cut.data);bm.normal_update()
   assert sum(not ed.is_manifold for ed in bm.edges)==0
   tree=BVHTree.FromBMesh(bm)
   for pose in ("initial","moved"):
    if pose=="moved":
     if mode=="planar":
      cut.location.y+=3.;cut.rotation_euler.x+=.1745329252
     else:
      cut.location.x-=4.;cut.scale*=1.13
    sc.frame_set(frame)
    deps=bpy.context.evaluated_depsgraph_get()
    ev=seed.evaluated_get(deps);mesh=ev.to_mesh()
    tx=cut.matrix_world.inverted_safe()@seed.matrix_world
    inside=0
    for v in mesh.vertices:
     q=tx@v.co
     near=tree.find_nearest(q)
     if near and near[0] is not None:
      pos,norm,idx,distance=near
      if (q-pos).dot(norm)<-.0002:inside+=1
    record={"tested_vertices":len(mesh.vertices),"cutter_mesh_vertices":len(cut.data.vertices),"inside_vertices":inside}
    assert inside==0,(mode,pose,record)
    ev.to_mesh_clear()
    entries[mode+"_"+pose]=record
   bm.free()
  rows[version]["actual_cutter_seed_contacts"]=entries
(P/"v14-validation.json").write_text(json.dumps(rows,indent=2,ensure_ascii=False)+"\n")
print("V14_QA_PASS",flush=True)

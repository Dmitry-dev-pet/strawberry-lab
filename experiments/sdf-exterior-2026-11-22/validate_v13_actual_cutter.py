"""v13 real displaced cutter surface proximity check, not radius~1 proxy.
Check retained achene vertices against actual v10 scalloped 6050-vertex cutter mesh,
using nearest-surface normal sign in cutter-local space. Not full triangle intersection.
"""
import bpy,bmesh,hashlib,os,json,time
from mathutils.bvhtree import BVHTree
from pathlib import Path
P=Path(os.environ["STRAWBERRY_SDF_OUT"])
scfile=P/"strawberry-sdf-vertical-slice-v13-spatial-fibrils.blend"
bpy.ops.wm.open_mainfile(filepath=str(scfile),use_scripts=False)
sc=bpy.context.scene
rows={}
for mode,frame in (("planar",20),("bite",40)):
 cutter=bpy.data.objects["SDF cutter | "+("planar (move or rotate)" if mode=="planar" else "spherical bite (move or scale)")]
 seed=bpy.data.objects["SDF visible seeds | "+mode]
 cm=cutter.data;bm=bmesh.new();bm.from_mesh(cm);bm.normal_update()
 assert sum(not edge.is_manifold for edge in bm.edges)==0
 assert bm.calc_volume(signed=True)>0
 bvh=BVHTree.FromBMesh(bm)
 for tag in ("original","moved"):
  if tag=="moved":
   if mode=="planar":
    cutter.location.y+=3.;cutter.rotation_euler.x+=.1745329252
   else:cutter.location.x-=4.;cutter.scale*=1.13
  sc.frame_set(frame)
  dg=bpy.context.evaluated_depsgraph_get()
  ev=seed.evaluated_get(dg);em=ev.to_mesh()
  to_cut=cutter.matrix_world.inverted_safe()@seed.matrix_world
  intrusions=0; nearest_checked=0;max_inward=0.
  for vertex in em.vertices:
   q=to_cut@vertex.co
   got=bvh.find_nearest(q)
   if got and got[0] is not None:
    loc,norm,index,dist=got
    dot=(q-loc).dot(norm)
    nearest_checked+=1
    if dot < -.0002:
     intrusions+=1;max_inward=min(max_inward,dot)
  row={"seed_vertices":len(em.vertices),"cutter_mesh_verts":len(cm.vertices),"actual_cutter_sign_inside_vertices":intrusions,"max_inward_distance":round(max_inward,5)}
  assert intrusions==0,(mode,tag,row)
  rows[mode+"_"+tag]=row
  ev.to_mesh_clear()
 bm.free()
print("V13_ACTUAL_CUTTER_CONTACT_PASS",json.dumps(rows),flush=True)
(P/"v13-actual-cutter-contact.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n")

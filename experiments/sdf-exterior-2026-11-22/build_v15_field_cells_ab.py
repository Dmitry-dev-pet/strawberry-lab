"""V15: isolate the published Frucht-like coupling ALREADY present in our v8/v12 cut engine.

A/B from exactly the same unchanged v12 .blend and same native 192³ rest-space
vascular image.  Both use identical 3.2x *physical* cut-cell Voronoi relief;
A disables the vessel field mask, B smoothly suppresses cells over the vessel
field at 94% in strongest R.  NO new fibers/volumes, NO external assets,
NO changing the cutter/material/seed positions. Research parameters ARTIST.
"""
import bpy,os,json,hashlib,time
from pathlib import Path
P=Path(os.environ["STRAWBERRY_SDF_OUT"])
SRC=P/"strawberry-sdf-vertical-slice-v12-continuous-wet.blend"
A=P/"strawberry-sdf-vertical-slice-v15a-uncoupled-cells.blend"
B=P/"strawberry-sdf-vertical-slice-v15b-restfield-coupled-cells.blend"
assert SRC.is_file() and not A.exists() and not B.exists(),"Source missing or refusing overwrite"
t=time.monotonic()
bpy.ops.wm.open_mainfile(filepath=str(SRC),use_scripts=False)
scene=bpy.context.scene
image=bpy.data.images["SDF proof v4 | 192^3 sparse volume and continuous branches"]
assert image.packed_file and list(image.size)==[3072,2304]
sample=bpy.data.node_groups["V8 | original rest-space vascular field (192^3)"]
samplers=[n for n in sample.nodes if n.bl_idname=="GeometryNodeImageTexture"]
assert len(samplers)==2 and all(n.inputs["Image"].default_value==image for n in samplers)
groups=[]
for tag in ("planar","bite"):
 g=bpy.data.node_groups["SDF cutter + rest-space | "+tag]
 ctrl=g.nodes["V8_CELL_STRENGTH"]
 gate=next(n for n in g.nodes if n.bl_idname=="ShaderNodeMapRange" and n.label.startswith("No cell relief on same pale vascular"))
 assert ctrl.outputs["Value"].default_value==1.
 assert abs(gate.inputs["To Min"].default_value-1.)<1e-5
 assert abs(gate.inputs["To Max"].default_value-.12)<1e-5
 assert gate.inputs["Value"].is_linked
 assert gate.inputs["Value"].links[0].from_node.name.startswith("V8 | vessel sample")
 ctrl.outputs["Value"].default_value=3.2
 groups.append((tag,g,gate))
for tag,g,gate in groups:
 gate.inputs["To Max"].default_value=1.
 g["v15_variable"]="Only vascular cell-mask coupling differs between A and B; same 3.2x cell geometry, source rest-space 192³"
scene["v15_biology"]="ARTIST field and Voronoi; no biological cell dimensions are being claimed"
scene["v15_variant"]="A: stronger 3D Voronoi cellular geometry WITHOUT rest-space vascular flattening"
scene.frame_set(20)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(A))
for tag,g,gate in groups:
 gate.inputs["To Max"].default_value=.06
scene["v15_variant"]="B: same stronger cells WITH 94%-at-peak 3D vascular flat mask"
bpy.ops.wm.save_as_mainfile(filepath=str(B))
m={"source":"v12, unchanged","source_sha256":hashlib.sha256(SRC.read_bytes()).hexdigest(),
   "blends":{"A":{"name":A.name,"sha256":hashlib.sha256(A.read_bytes()).hexdigest()},
             "B":{"name":B.name,"sha256":hashlib.sha256(B.read_bytes()).hexdigest()}},
   "atlas":image.name,"atlas_size":list(image.size),
   "voxel_field":"same packed v4 192³; red channel sampled by native GN and shader in same rest coordinates",
   "experiment":{"common_v8_cell_strength":3.2,"A_vascular_flatten_ToMax":1.0,
                 "B_vascular_flatten_ToMax":0.06,"common_vascular_flatten_FromMin":1.0},
   "materials_unchanged":True,"cutters_unchanged":True,"no_new_3d_fibers":True,
   "elapsed_s":round(time.monotonic()-t,2),"visual_status":"unreviewed",
   "biology":"ARTIST; not verified histology"}
(P/"v15-build.json").write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n")
print("V15_BUILT="+json.dumps(m,ensure_ascii=False),flush=True)

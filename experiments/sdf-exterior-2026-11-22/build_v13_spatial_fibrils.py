"""Strawberry Lab v13: directional 3-D cortical fibril field + physical exposed ridges.

Independent ARTIST study.  Reuses the v12 SDF/seed controls without altering
cutter positions, source achene meshes, materials, G/B atlas channels or base file.
New R-channel field is defined in 3-D rest space and sampled on all cuts.
Its effect on actual cut vertices is measured separately from shader color.
This is not measured histology; no Frucht nodes, materials or source were copied.
"""
from __future__ import annotations
import bpy, math, json, hashlib, time, os
import numpy as np
from pathlib import Path
P=Path(os.environ.get("STRAWBERRY_SDF_OUT",str(Path(__file__).resolve().parent)))
SRC=P/"strawberry-sdf-vertical-slice-v12-continuous-wet.blend"
DST=P/"strawberry-sdf-vertical-slice-v13-spatial-fibrils.blend"
ATLAS=P/"tissue-v13-192-spatial-fibrils.png"
assert SRC.is_file() and not DST.exists() and not ATLAS.exists(), "Source missing or would overwrite"
t0=time.monotonic()
bpy.ops.wm.open_mainfile(filepath=str(SRC),use_scripts=False)
sc=bpy.context.scene
original=bpy.data.images["SDF proof v4 | 192^3 sparse volume and continuous branches"]
assert original.packed_file and tuple(original.size)==(3072,2304)
n=192; cols=16; rows=12
raw=np.empty((rows*n,cols*n,4), dtype=np.float32)
original.pixels.foreach_get(raw.ravel())
xs=np.linspace(-18.,18.,n,dtype=np.float32)
ys=np.linspace(-18.,18.,n,dtype=np.float32)
zs=np.linspace(-1.,50.,n,dtype=np.float32)
X,Y=np.meshgrid(xs,ys)
R=np.sqrt(X*X+Y*Y)+1e-5
TH=np.arctan2(Y,X)
envelope=np.clip((R-1.6)/1.25,0,1)*np.clip((17.4-R)/2.0,0,1)
# A 3-D *coherent*, non-camera-based set of winding radial fibril sheets:
# 38 narrow ribbons emerging from the receptacle core and traveling to cortex.
# Winding varies smoothly with z, so every cutter sees the same structures.
stat={"slices":n,"fibril_family_count":38,"rest_bounds_mm":[[-18,18],[-18,18],[-1,50]],
      "preserved_green_blue":True,"artist":True}
for k,z in enumerate(zs):
    phase=19.*TH + .30*R + .46*np.sin(.19*z+.16*R) + .19*np.sin(3.*TH+.11*z)
    lateral=np.abs(np.sin(phase))*R/19.
    width=.120+.025*math.sin(.28*float(z))
    coherent=np.exp(-.5*(lateral/width)**2)
    # A second fainter, broader family prevents strictly periodic white bars.
    phase2=7.*TH-.12*R+.24*np.sin(.14*z+.3*R)
    lateral2=np.abs(np.sin(phase2))*R/7.
    secondary=np.exp(-.5*(lateral2/.17)**2)
    longitudinal=.85+.15*np.sin(.29*z+.27*R+2*TH)
    directional=(.54*coherent+.17*secondary)*envelope*longitudinal
    ty=k//cols;tx=k%cols
    tile=raw[ty*n:(ty+1)*n,tx*n:(tx+1)*n,:]
    # Keep seed-linked original branch paths; do NOT replace with cross-section
    # noise or copy an external strawberry atlas.
    tile[:,:,0]=np.clip(np.maximum(tile[:,:,0]*.87, directional),0,1)
assert np.all(np.isfinite(raw))
new=bpy.data.images.new("SDF proof v13 | 192^3 coherent directional fibrils (ARTIST)",
                        width=cols*n,height=rows*n,alpha=True,float_buffer=False)
new.colorspace_settings.name="Non-Color"
new.pixels.foreach_set(raw.ravel())
new.update()
new.filepath_raw=str(ATLAS);new.file_format="PNG";new.save();new.pack()
# Replace both material and native GN image accesses to guarantee shared source.
replaced={"shader":0,"gn":0}
for mat in bpy.data.materials:
    if not mat.use_nodes:continue
    for node in mat.node_tree.nodes:
        if node.bl_idname=="ShaderNodeTexImage" and node.image==original:
            node.image=new;replaced["shader"]+=1
for group in bpy.data.node_groups:
    if group.bl_idname!="GeometryNodeTree":continue
    for node in group.nodes:
        if node.bl_idname=="GeometryNodeImageTexture" and node.inputs["Image"].default_value==original:
            node.inputs["Image"].default_value=new;replaced["gn"]+=1
assert replaced["shader"]>=2 and replaced["gn"]==2,replaced
for typ in ("planar","bite"):
    g=bpy.data.node_groups["SDF cutter + rest-space | "+typ]
    nodes,links=g.nodes,g.links
    end=next(n for n in nodes if n.bl_idname=="NodeGroupOutput")
    old=next(iter(end.inputs["Geometry"].links)).from_socket
    source=nodes["V8 | vessel sample from SAME 192cubed atlas"]
    cap=nodes["Compare"]
    shape=nodes["Geometry Proximity.001"]
    assert source.node_tree==bpy.data.node_groups["V8 | original rest-space vascular field (192^3)"]
    # Physical ridge from that same 3-D field, instead of another arbitrary
    # surface-only Voronoi map. Attenuated at the original skin/cut junction.
    ridge=nodes.new("ShaderNodeMapRange")
    ridge.name="V13 | coherent fiber ridge in millimetres"
    ridge.clamp=True;ridge.interpolation_type="SMOOTHSTEP"
    for key,val in (("From Min",.07),("From Max",.58),("To Min",-.013),("To Max",.062)):
        ridge.inputs[key].default_value=val
    links.new(source.outputs["vascular_intensity"],ridge.inputs["Value"])
    fade=nodes.new("ShaderNodeMapRange")
    fade.name="V13 | protect skin and rim"
    fade.clamp=True;fade.interpolation_type="SMOOTHSTEP"
    for key,val in (("From Min",.22),("From Max",.80),("To Min",0.),("To Max",1.)):
        fade.inputs[key].default_value=val
    links.new(shape.outputs["Distance"],fade.inputs["Value"])
    band=nodes.new("ShaderNodeMath");band.operation="MULTIPLY"
    links.new(ridge.outputs["Result"],band.inputs[0])
    links.new(fade.outputs["Result"],band.inputs[1])
    sel=nodes.new("ShaderNodeMath");sel.operation="MULTIPLY"
    links.new(band.outputs[0],sel.inputs[0]);links.new(cap.outputs["Result"],sel.inputs[1])
    gain=nodes.new("ShaderNodeValue");gain.name="V13_FIBER_HEIGHT_STRENGTH"
    gain.outputs["Value"].default_value=1.
    h=nodes.new("ShaderNodeMath");h.operation="MULTIPLY"
    links.new(sel.outputs[0],h.inputs[0]);links.new(gain.outputs["Value"],h.inputs[1])
    attr=nodes.new("GeometryNodeStoreNamedAttribute");attr.data_type="FLOAT";attr.domain="POINT"
    attr.inputs["Name"].default_value="v13_ridge_height_mm"
    links.new(old,attr.inputs["Geometry"]);links.new(h.outputs[0],attr.inputs["Value"])
    norm=nodes.new("GeometryNodeInputNormal")
    vec=nodes.new("ShaderNodeVectorMath");vec.operation="SCALE"
    links.new(norm.outputs["Normal"],vec.inputs[0]);links.new(h.outputs[0],vec.inputs["Scale"])
    setp=nodes.new("GeometryNodeSetPosition")
    setp.name="V13 | native continuous exposed ridges"
    links.new(attr.outputs["Geometry"],setp.inputs["Geometry"])
    links.new(vec.outputs["Vector"],setp.inputs["Offset"])
    links.new(setp.outputs["Geometry"],end.inputs["Geometry"])
    g["v13_contract"]="same rest-space R field in cap geometry and material; selective physical 0.06mm ARTIST"
sc["v13_hypothesis"]="New rest-space narrow directional 3D fibrils drive both cut color and actual exposed-mesh relief, not just wet shader sheen."
sc["v13_provenance"]="Independent ARTIST rest-space fibril sheets; base v12 copied unchanged, no private Frucht media/assets."
sc["v13_visual_status"]="UNREVIEWED, do not merge into main"
sc.frame_set(20)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(DST))
receipt={"version":"v13","parent":"v12","base_sha256":hashlib.sha256(SRC.read_bytes()).hexdigest(),
 "blend_sha256":hashlib.sha256(DST.read_bytes()).hexdigest(),
 "atlas_sha256":hashlib.sha256(ATLAS.read_bytes()).hexdigest(),"replaced":replaced,
 "field":stat,"build_s":round(time.monotonic()-t0,2)}
(P/"v13-build.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
print("V13_BUILD="+json.dumps(receipt,ensure_ascii=False),flush=True)

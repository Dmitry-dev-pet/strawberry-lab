"""Strawberry Lab v14: sparse non-periodic seed-linked 3-D fibril field +
physical cut-lip tear, standalone A/B from untouched v12.

Owned independent procedural source.  All unmeasured parameters ARTIST.
Not a Frucht reconstruction.  No new third-party nodes, assets or media.
"""
import bpy, numpy as np, hashlib, time, json, os, math
from pathlib import Path
P=Path(os.environ["STRAWBERRY_SDF_OUT"])
SRC=P/"strawberry-sdf-vertical-slice-v12-continuous-wet.blend"
A=P/"strawberry-sdf-vertical-slice-v14a-branch-field.blend"
B=P/"strawberry-sdf-vertical-slice-v14b-branch-tear.blend"
ATLAS=P/"tissue-v14-seed-linked-branches-192.png"
for file in (SRC,): assert file.is_file(),file
assert not any(f.exists() for f in (A,B,ATLAS)),"Existing outputs; refusing overwrite"
ts=time.monotonic()
bpy.ops.wm.open_mainfile(filepath=str(SRC),use_scripts=False)
sc=bpy.context.scene
base=bpy.data.images["SDF proof v4 | 192^3 sparse volume and continuous branches"]
assert base.packed_file and tuple(base.size)==(3072,2304)
n=192; cols=16; rows=12
pixels=np.empty((rows*n,cols*n,4),np.float32)
base.pixels.foreach_get(pixels.ravel())
xs=np.linspace(-18,18,n,dtype=np.float32)
ys=np.linspace(-18,18,n,dtype=np.float32)
zs=np.linspace(-1,50,n,dtype=np.float32)
step=np.array([xs[1]-xs[0],ys[1]-ys[0],zs[1]-zs[0]],np.float32)
# The source v12 GL-free seed reference stores rest-space anchors per real achene
# mesh, not per old 539 virtual diagnostic branch.
seed=bpy.data.objects["SDF visible seeds | planar"]
ach=seed.data.attributes["achene_center"]
verts=len(seed.data.vertices)
assert verts%264==0
stride=verts//264
anchors=np.array([ach.data[i*stride].vector[:] for i in range(264)],np.float32)
assert np.all(np.isfinite(anchors))
rng=np.random.default_rng(141126)
# Select 27 actual achenes near the original longitudinal plane plus 45
# widely spaced anchors across the same source berry; deterministic but
# NOT a periodic ring of samples. This is ARTIST topology, not histology.
selected_near=np.argsort(np.abs(anchors[:,1]))[:27].tolist()
rest=np.array([i for i in range(264) if i not in selected_near])
selected_far=rng.choice(rest,size=45,replace=False).tolist()
selected=selected_near+selected_far
# float raster via continuous XYZ 192^3, identical for any cut angle.
field=np.zeros((n,n,n),np.float32)
raster_points=0
raster_attempted=0
raster_skipped=0
def dab(q,amp,width):
 global raster_points,raster_attempted,raster_skipped
 raster_attempted+=1
 q=np.asarray(q,dtype=np.float32)
 fx=(q[0]+18)/step[0];fy=(q[1]+18)/step[1];fz=(q[2]+1)/step[2]
 ix,iy,iz=[int(round(float(x))) for x in (fx,fy,fz)]
 # radius <= 0.47mm; spatially coherent thin branches, not colored dots
 a=max(0,ix-4);b=min(n,ix+5)
 c=max(0,iy-4);d=min(n,iy+5)
 e=max(0,iz-4);h=min(n,iz+5)
 if a>=b or c>=d or e>=h:raster_skipped+=1;return
 d2=((xs[None,None,a:b]-q[0])**2
     +(ys[None,c:d,None]-q[1])**2
     +(zs[e:h,None,None]-q[2])**2)
 kernel=amp*np.exp(-.5*d2/(width*width))
 dst=field[e:h,c:d,a:b]
 np.maximum(dst,kernel,out=dst)
 raster_points+=1
def bezier(p0,p1,p2,p3,t):
 t=float(t);u=1.-t
 return u*u*u*p0+3*u*u*t*p1+3*u*t*t*p2+t*t*t*p3
stem_count=0;twig_count=0
for rank,idx in enumerate(selected):
 target=anchors[idx]
 # We connect sparse source-achene destinations to a genuinely 3D curved
 # rest-space trunk, with wide variations in tangents and arrival positions.
 z=float(target[2])
 a=np.array([rng.uniform(-1.0,1.0),rng.uniform(-1.,1.), max(0.,z-rng.uniform(10,17))],np.float32)
 p1=np.array([target[0]*.12+rng.uniform(-2,2),target[1]*.14+rng.uniform(-2,2),z-rng.uniform(6.2,9.0)],np.float32)
 p2=np.array([target[0]*.72+rng.uniform(-2.1,2.1),target[1]*.66+rng.uniform(-2,2),z-rng.uniform(1.3,4.2)],np.float32)
 b=np.array([target[0]*.96,target[1]*.96,z-.22],np.float32)
 intensity=float(rng.uniform(.35,.63))
 width=float(rng.uniform(.22,.40))
 tvals=np.linspace(0,1,76,dtype=np.float32)
 coords=[bezier(a,p1,p2,b,t) for t in tvals]
 for k,q in enumerate(coords):
  t=float(tvals[k])
  # Nonuniform width smoothly tapers toward terminal, high at lower bundle
  # and low at exposed branch tip. Kernel is Gaussian, not cell geometry.
  dab(q,intensity*(.9+.1*math.cos(2*math.pi*t)),width*(1.12-.32*t))
 stem_count+=1
 # 1-3 naturally branching twigs along each fiber, sharing EXACT parent
 # control-point positions. Each has its own random 3D direction.
 count=int(rng.integers(1,4))
 for j in range(count):
  t0=float(rng.uniform(.27,.79))
  q0=bezier(a,p1,p2,b,t0)
  tangent=bezier(a,p1,p2,b,min(1.,t0+.035))-bezier(a,p1,p2,b,max(0.,t0-.035))
  tangent=tangent/(float(np.linalg.norm(tangent))+1e-9)
  rv=rng.normal(0,1,3).astype(np.float32)
  rv=rv-tangent*np.dot(rv,tangent)
  rv=rv/(float(np.linalg.norm(rv))+1e-9)
  length=float(rng.uniform(1.4,4.0))
  q3=q0+rv*length+tangent*length*.45
  q1=q0+rv*length*.22+tangent*.55
  q2=q0+rv*length*.67+tangent*length*.40
  for t in np.linspace(0,1,27):
   q=bezier(q0,q1,q2,q3,t)
   dab(q,float(intensity*.68*(1-.37*t)),width*.65*(1-.20*t))
  twig_count+=1
assert raster_attempted == raster_points + raster_skipped
# Physical pixel maps are shared in shader and Geometry Nodes: replace
# existing R by a 0.22× background plus new sparse nonperiodic structure.
old_dist=[]
new_dist=[]
for k in range(n):
 ty,tx=divmod(k,cols)
 tile=pixels[ty*n:(ty+1)*n,tx*n:(tx+1)*n,:]
 old_r=tile[:,:,0]
 old_dist.append(float(np.mean(old_r)))
 new=np.maximum(old_r*.22, field[k]*.83)
 tile[:,:,0]=np.clip(new,0,1)
 new_dist.append(float(np.mean(tile[:,:,0])))
assert np.isfinite(pixels).all()
atlas=bpy.data.images.new("SDF v14 | nonperiodic achene-linked 3D fibrous field (ARTIST)",
                         width=cols*n,height=rows*n,alpha=True,float_buffer=False)
atlas.colorspace_settings.name="Non-Color"
atlas.pixels.foreach_set(pixels.ravel());atlas.update()
atlas.file_format="PNG";atlas.filepath_raw=str(ATLAS);atlas.save();atlas.pack()
changed={"shader":0,"gn":0}
for mat in bpy.data.materials:
 if not mat.use_nodes:continue
 for node in mat.node_tree.nodes:
  if node.bl_idname=="ShaderNodeTexImage" and node.image==base:
   node.image=atlas;changed["shader"]+=1
for g in bpy.data.node_groups:
 if g.bl_idname!="GeometryNodeTree":continue
 for nd in g.nodes:
  if nd.bl_idname=="GeometryNodeImageTexture" and nd.inputs["Image"].default_value==base:
   nd.inputs["Image"].default_value=atlas;changed["gn"]+=1
assert changed=={"shader":2,"gn":2},changed
# First A/B: a fully genuine 3D source field on BOTH planar and bite cuts.
# Second A/B: a new *physical* (not shader-only) torn lip on bite only.
g=bpy.data.node_groups["SDF cutter + rest-space | bite"]
nodes,ln=g.nodes,g.links
out=next(nd for nd in nodes if nd.bl_idname=="NodeGroupOutput")
old=out.inputs["Geometry"].links[0].from_socket
cap=nodes["Compare"]
proximity=nodes["Geometry Proximity.001"]
vascular=nodes["V8 | vessel sample from SAME 192cubed atlas"]
coord=nodes.new("GeometryNodeInputNamedAttribute")
coord.data_type="FLOAT_VECTOR";coord.inputs["Name"].default_value="fruit_rest"
def mathop(name,operation,a=None,b=None,val=None):
 nd=nodes.new("ShaderNodeMath");nd.name="V14 | "+name;nd.operation=operation
 if a is not None:ln.new(a,nd.inputs[0])
 if b is not None:ln.new(b,nd.inputs[1])
 if val is not None:nd.inputs[1].default_value=val
 return nd.outputs["Value"]
# Noise is continuous, aperiodic 3D rest-space, not copied Frucht texture.
low=nodes.new("ShaderNodeTexNoise")
low.noise_dimensions="3D";low.inputs["Scale"].default_value=1.45
low.inputs["Detail"].default_value=3.2;low.inputs["Roughness"].default_value=.59
ln.new(coord.outputs["Attribute"],low.inputs["Vector"])
high=nodes.new("ShaderNodeTexNoise")
high.noise_dimensions="3D";high.inputs["Scale"].default_value=5.1
high.inputs["Detail"].default_value=2.4;high.inputs["Roughness"].default_value=.58
ln.new(coord.outputs["Attribute"],high.inputs["Vector"])
coarse=mathop("coarse tear", "MULTIPLY",mathop("coarse zero","SUBTRACT",low.outputs["Fac"],val=.50),val=.64)
small=mathop("fine tear","MULTIPLY",mathop("fine zero","SUBTRACT",high.outputs["Fac"],val=.50),val=.21)
signal=mathop("nonperiodic tear surface","ADD",coarse,small)
# The explicitly-measured source-skin proximity makes this a *rim-local*
# discontinuous-flesh effect, not a universal bump everywhere on cap.
rim=nodes.new("ShaderNodeMapRange")
rim.name="V14 | exposed rim 0-1.85mm mask"
rim.clamp=True;rim.interpolation_type="SMOOTHSTEP"
for key,val in (("From Min",.02),("From Max",1.85),("To Min",1.),("To Max",0.)):
 rim.inputs[key].default_value=val
ln.new(proximity.outputs["Distance"],rim.inputs["Value"])
cap_rim=mathop("cut-only rim mask","MULTIPLY",rim.outputs["Result"],cap.outputs["Result"])
# Tear amplitude responds to the SAME true field that colors cut fibrous
# channels; does not use stand-alone 2-D noise for vascular intensity.
weighted=mathop("vessel dependent gain","MULTIPLY",vascular.outputs["vascular_intensity"],val=.8)
weighted=mathop("1 plus vessel","ADD",weighted,val=1.)
offset=mathop("tear*field","MULTIPLY",signal,weighted)
offset=mathop("tear*rim","MULTIPLY",offset,cap_rim)
gain=nodes.new("ShaderNodeValue");gain.name="V14_TEAR_GAIN"
gain.label="0 = field-only control, 1 = genuine ragged lip"
gain.outputs["Value"].default_value=0.
height=mathop("tear*gain","MULTIPLY",offset,gain.outputs["Value"])
store=nodes.new("GeometryNodeStoreNamedAttribute")
store.name="V14 | expose signed rim tear height";store.data_type="FLOAT";store.domain="POINT"
store.inputs["Name"].default_value="v14_tear_height_mm"
ln.new(old,store.inputs["Geometry"]);ln.new(height,store.inputs["Value"])
normal=nodes.new("GeometryNodeInputNormal")
nvec=nodes.new("ShaderNodeVectorMath");nvec.operation="SCALE"
ln.new(normal.outputs["Normal"],nvec.inputs[0]);ln.new(height,nvec.inputs["Scale"])
setpos=nodes.new("GeometryNodeSetPosition");setpos.name="V14 | physical torn lip near bite rim"
ln.new(store.outputs["Geometry"],setpos.inputs["Geometry"])
ln.new(nvec.outputs["Vector"],setpos.inputs["Offset"])
ln.new(setpos.outputs["Geometry"],out.inputs["Geometry"])
g["v14_geometry"]="ARTIST irregular cut-local rim displacement using same 3D rest vascular field, native GN, not wet shader."
sc["v14_direction"]="Sparse nonperiodic 3D seed-connected fibrils, optional physical bite lip tearing."
sc["v14_biology"]="ARTIST; not derived from plant micrographs or source vessel thicknesses"
sc["v14_source"]="v12 untouched; v13 stripes rejected; own independent source"
sc.frame_set(40)
bpy.context.preferences.filepaths.save_version=0
# Scene A includes all nodes but tear control 0, so is a valid field-only
# comparison: the only difference A -> B is one exposed scalar.
gain.outputs["Value"].default_value=0.0
sc["v14_variant"]="A: field only; no physical tear displacement"
bpy.ops.wm.save_as_mainfile(filepath=str(A))
gain.outputs["Value"].default_value=1.0
sc["v14_variant"]="B: same field + physical torn lip, V14_TEAR_GAIN=1"
bpy.ops.wm.save_as_mainfile(filepath=str(B))
metadata={
 "hypothesis":"not periodic stripes; sparse seed-linked 3D branches + local field-conditioned torn bite lip",
 "source":"v12","source_sha256":hashlib.sha256(SRC.read_bytes()).hexdigest(),
 "blends":[{"variant":"A","sha256":hashlib.sha256(A.read_bytes()).hexdigest()},
           {"variant":"B","sha256":hashlib.sha256(B.read_bytes()).hexdigest()}],
 "atlas_sha256":hashlib.sha256(ATLAS.read_bytes()).hexdigest(),
 "atlas_shape":[192,192,192],"atlas_shader_gn_replacements":changed,
 "seed_anchors_total":264,"seed_anchors_used":len(selected),
 "fibrils_seed_linked":stem_count,"terminal_branches":twig_count,"raster_dabs":raster_points,"raster_attempted":raster_attempted,"raster_skipped":raster_skipped,
 "shader_green_blue":"unchanged unquantized values before PNG save",
 "original_r_global_mean":float(np.mean(old_dist)),"v14_r_global_mean":float(np.mean(new_dist)),
 "tear_gain_A_B":[0,1],"tear_rim_coverage_mm":1.85,
 "biology":"ARTIST, not validated strawberry histology",
 "seconds":round(time.monotonic()-ts,2),
 "visual_status":"UNREVIEWED"
}
(P/"v14-build.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+"\n")
print("V14_BUILD="+json.dumps(metadata,ensure_ascii=False),flush=True)

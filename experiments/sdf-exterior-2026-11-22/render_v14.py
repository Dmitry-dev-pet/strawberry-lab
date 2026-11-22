"""True Cycles: v14A/B at identical v12 camera, light, samples, frames."""
import bpy,sys,time,json,hashlib,os
from pathlib import Path
from mathutils import Vector
P=Path(os.environ["STRAWBERRY_SDF_OUT"])
args=sys.argv[sys.argv.index("--")+1:]
variant,shot=args
assert variant in ("v14a","v14b") and shot in ("plane","bite","macro")
sc=bpy.context.scene
sc.render.engine="CYCLES";sc.cycles.device="CPU";sc.cycles.samples=36
sc.render.resolution_x=860;sc.render.resolution_y=860;sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG"
sc.render.film_transparent=False
sc.frame_set(40 if shot=="bite" else 20)
if shot=="macro":
 sc.camera.data.ortho_scale=31.
 target=Vector((0,0,24))
 sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat("-Z","Y").to_euler()
out=P/("sdf-"+variant+"-matched-"+shot+".png")
assert not out.exists(),"Already exists; refuse overwrite"
sc.render.filepath=str(out)
t=time.monotonic()
bpy.ops.render.render(write_still=True)
r={"variant":variant,"shot":shot,"frame":sc.frame_current,"samples":36,"resolution":[860,860],
   "render_seconds":round(time.monotonic()-t,2),"sha256":hashlib.sha256(out.read_bytes()).hexdigest(),
   "bytes":out.stat().st_size}
(P/("v14-"+variant+"-"+shot+"-render.json")).write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
print("V14_CYCLES_PROOF="+json.dumps(r),flush=True)

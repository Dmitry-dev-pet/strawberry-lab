"""Genuine matched Cycles from re-opened saved v15a and v15b.
Uses exactly v12's 860x860, 36 samples, camera/light/shot poses; no AI.
"""
import bpy,sys,time,json,hashlib,os
from pathlib import Path
from mathutils import Vector
P=Path(os.environ["STRAWBERRY_SDF_OUT"])
args=sys.argv[sys.argv.index("--")+1:];variant,kind=args
assert variant in ("v15a","v15b") and kind in ("plane","bite","macro")
sc=bpy.context.scene
sc.render.engine="CYCLES";sc.cycles.device="CPU";sc.cycles.samples=36
sc.render.resolution_x=860;sc.render.resolution_y=860;sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG";sc.render.film_transparent=False
sc.frame_set(40 if kind=="bite" else 20)
if kind=="macro":
 sc.camera.data.ortho_scale=31.
 target=Vector((0,0,24))
 sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat("-Z","Y").to_euler()
out=P/("sdf-"+variant+"-matched-"+kind+".png")
assert not out.exists(),str(out)
sc.render.filepath=str(out)
start=time.monotonic();bpy.ops.render.render(write_still=True)
rec={"variant":variant,"shot":kind,"frame":sc.frame_current,"cycles_samples":36,
 "resolution":[860,860],"sec":round(time.monotonic()-start,2),
 "sha256":hashlib.sha256(out.read_bytes()).hexdigest(),"bytes":out.stat().st_size}
(P/("v15-"+variant+"-"+kind+"-render.json")).write_text(json.dumps(rec,ensure_ascii=False,indent=2)+"\n")
print("V15_CYCLES="+json.dumps(rec),flush=True)

"""Genuine Blender Cycles frame renderer v13, matching existing v12 A/B setup."""
import bpy,sys,time,json,hashlib,os
from pathlib import Path
from mathutils import Vector
p=Path(os.environ["STRAWBERRY_SDF_OUT"])
kind=sys.argv[sys.argv.index("--")+1]
assert kind in ("plane","bite","macro")
sc=bpy.context.scene
sc.render.engine="CYCLES";sc.cycles.device="CPU";sc.cycles.samples=36
sc.render.resolution_x=860;sc.render.resolution_y=860;sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG";sc.render.film_transparent=False
sc.frame_set(20 if kind!="bite" else 40)
if kind=="macro":
    sc.camera.data.ortho_scale=31.
    target=Vector((0,0,24))
    sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat("-Z","Y").to_euler()
out=p/("sdf-v13-matched-"+kind+".png")
assert not out.exists(),"Refusing to overwrite prior result"
sc.render.filepath=str(out)
ts=time.monotonic()
bpy.ops.render.render(write_still=True)
record={"kind":kind,"frame":sc.frame_current,"samples":sc.cycles.samples,
 "resolution":[860,860],"seconds":round(time.monotonic()-ts,2),
 "bytes":out.stat().st_size,"sha256":hashlib.sha256(out.read_bytes()).hexdigest(),
 "scene":"strawberry-sdf-vertical-slice-v13-spatial-fibrils.blend"}
(p/("v13-render-"+kind+".json")).write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n")
print("V13_CYCLES_RENDER="+json.dumps(record),flush=True)

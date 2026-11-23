"""Contact sheet from authentic Cycles PNGs. No AI imaging, no render synthesis."""
import bpy,numpy as np,os,json,hashlib
from pathlib import Path
P=Path(os.environ["STRAWBERRY_SDF_OUT"])
out=P/"comparison-v12-v14a-v14b-three-shots.png"
assert not out.exists()
w=h=860
arr=np.zeros((3*h,3*w,4),dtype=np.float32)
for row,shot in enumerate(("macro","bite","plane")):
 for col,ver in enumerate(("v12","v14a","v14b")):
  src=P/("sdf-"+ver+"-matched-"+shot+".png")
  img=bpy.data.images.load(str(src),check_existing=False)
  data=np.empty(h*w*4,np.float32)
  img.pixels.foreach_get(data)
  arr[row*h:(row+1)*h,col*w:(col+1)*w]=data.reshape(h,w,4)
  bpy.data.images.remove(img)
m=bpy.data.images.new("v12 / v14A / v14B : plane / bite / macro (Cycles)",width=3*w,height=3*h,alpha=True,float_buffer=False)
m.colorspace_settings.name="sRGB"
m.pixels.foreach_set(arr.ravel());m.update()
m.filepath_raw=str(out);m.file_format="PNG";m.save()
rec={"path":str(out),"sha256":hashlib.sha256(out.read_bytes()).hexdigest(),
 "bytes":out.stat().st_size,"layout_columns":["v12","v14a","v14b"],
 "layout_rows_top_to_bottom":["plane","bite","macro"],"source":"unmodified genuine Blender Cycles frames 860px/36 samples"}
(P/"v14-contact-sheet.json").write_text(json.dumps(rec,indent=2)+"\n")
print("V14_CONTACT_SHEET="+json.dumps(rec),flush=True)

import bpy,numpy as np,json,hashlib,os
from pathlib import Path
P=Path(os.environ["STRAWBERRY_SDF_OUT"])
arrs={}
for shot in ("plane","bite","macro"):
 for tag in ("v12","v14a","v14b"):
  f=P/("sdf-"+tag+"-matched-"+shot+".png")
  assert f.is_file()
  img=bpy.data.images.load(str(f),check_existing=False)
  assert tuple(img.size)==(860,860)
  px=np.empty(860*860*4,dtype=np.float32)
  img.pixels.foreach_get(px)
  arrs[tag,shot]=px.reshape(860,860,4)[:,:,:3].copy()
  bpy.data.images.remove(img)
report={"pixels_per_frame":860*860,"comparisons":{}}
for shot in ("plane","bite","macro"):
 for left,right in (("v12","v14a"),("v14a","v14b")):
  a=arrs[left,shot];b=arrs[right,shot]
  diff=np.max(np.abs(a-b),axis=2)
  label=shot+":"+left+"-"+right
  report["comparisons"][label]={"mae_rgb":float(np.mean(np.abs(a-b))),
     "pct_pixels_over_0_01":round(float((diff>.01).mean()*100),3),
     "pct_pixels_over_0_05":round(float((diff>.05).mean()*100),3),
     "max_rgb_difference":float(np.max(diff))}
(P/"v14-pixel-ab.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print("V14_IMAGE_AB="+json.dumps(report),flush=True)

"""v15 genuine Cycles pixel A/B diagnostic + 3x3 contact sheet (no AI images)."""
import bpy,numpy as np,hashlib,json,os
from pathlib import Path
P=Path(os.environ["STRAWBERRY_SDF_OUT"])
imgs={};n=860
for version in ("v12","v15a","v15b"):
 for shot in ("plane","bite","macro"):
  f=P/("sdf-"+version+"-matched-"+shot+".png")
  assert f.exists(),f
  image=bpy.data.images.load(str(f),check_existing=False)
  assert tuple(image.size)==(n,n)
  pixels=np.empty(n*n*4,np.float32)
  image.pixels.foreach_get(pixels)
  imgs[version,shot]=pixels.reshape(n,n,4)
  bpy.data.images.remove(image)
rows={}
for shot in ("plane","bite","macro"):
 for a,b in (("v12","v15a"),("v15a","v15b"),("v12","v15b")):
  first=imgs[a,shot][:,:,:3];second=imgs[b,shot][:,:,:3]
  dist=np.abs(first-second)
  maxc=dist.max(axis=2)
  rows[shot+":"+a+"→"+b]={
      "mae_rgb":float(dist.mean()),
      "pct_pixels_over_001":round(float((maxc>.01).mean()*100),3),
      "pct_pixels_over_005":round(float((maxc>.05).mean()*100),3),
      "max_channel_difference":float(maxc.max())}
# Bottom-to-top: macro, bite, plane; columns left-right v12, A, B.
sheet=np.zeros((n*3,n*3,4),np.float32)
for y,shot in enumerate(("macro","bite","plane")):
 for x,version in enumerate(("v12","v15a","v15b")):
  sheet[y*n:(y+1)*n,x*n:(x+1)*n,:]=imgs[version,shot]
out=P/"comparison-v12-v15a-v15b-three-shots.png"
assert not out.exists(),str(out)
canvas=bpy.data.images.new("v15 A/B native Cycles sheet",width=n*3,height=n*3,alpha=True,float_buffer=False)
canvas.colorspace_settings.name="sRGB"
canvas.pixels.foreach_set(sheet.ravel())
canvas.update();canvas.filepath_raw=str(out);canvas.file_format="PNG";canvas.save()
rec={"pixels_per_frame":n*n,"metrics":rows,
     "contact_sheet":{"name":out.name,"bytes":out.stat().st_size,"sha256":hashlib.sha256(out.read_bytes()).hexdigest(),
      "columns":["v12 original","v15A uncoupled","v15B field coupled"],"rows":["plane","bite","macro"]},
      "all_sources":"genuine Blender 5.2.2 Cycles 860x860 36 samples original camera/light/fixed frames",
      "biological_credibility":"not evaluated"}
(P/"v15-image-ab.json").write_text(json.dumps(rec,ensure_ascii=False,indent=2)+"\n")
print("V15_IMAGE_AB="+json.dumps(rec,ensure_ascii=False),flush=True)

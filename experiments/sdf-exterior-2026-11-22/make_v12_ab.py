import bpy,numpy as np,json,hashlib
from pathlib import Path
P=Path(__import__('os').environ.get('STRAWBERRY_SDF_OUT',str(Path(__file__).resolve().parents[2]/'build/sdf-vertical-slice')))
N=860;H=860;W=N*2+8
proof=[]
for tag in ("plane","bite"):
  out=np.empty((H,W,4),dtype=np.float32);out[:]=(0.1,0.1,0.1,1.)
  arrays=[]
  for i,ver in enumerate(("v10","v12")):
    im=bpy.data.images.load(str(P/("sdf-"+ver+"-matched-"+tag+".png")),check_existing=False)
    assert list(im.size)==[N,H]
    data=np.empty((H,N,4),np.float32);im.pixels.foreach_get(data.ravel())
    out[:,i*(N+8):i*(N+8)+N,:]=data
    arrays.append(data.copy())
    bpy.data.images.remove(im)
  delta=np.abs(arrays[1][:,:,:3]-arrays[0][:,:,:3])
  img=bpy.data.images.new("v11-ab-"+tag,width=W,height=H,alpha=True)
  img.pixels.foreach_set(out.ravel())
  img.filepath_raw=str(P/("comparison-v10-v12-"+tag+".png"))
  img.file_format='PNG';img.save();bpy.data.images.remove(img)
  p=P/("comparison-v10-v12-"+tag+".png")
  proof.append({"tag":tag,"file":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"bytes":p.stat().st_size,"mean_abs_rgb_change":round(float(np.mean(delta)),5),"p95_max_color_change":round(float(np.percentile(np.max(delta,axis=-1),95)),5)})
(P/'v12-image-qa.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
print('V12_AB='+json.dumps(proof,ensure_ascii=False),flush=True)

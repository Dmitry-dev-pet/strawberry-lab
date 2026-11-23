import os
"""Combine ONLY actual Cycles renders v4 / v5 / v6, no alteration or synthetic pixels."""
import bpy,numpy as np,json,hashlib
from pathlib import Path
P=Path(os.environ.get('STRAWBERRY_SDF_OUT',str(Path(__file__).resolve().parents[2]/'build/sdf-vertical-slice')))
out=[]
for name in ('plane','bite','macro'):
 imgs=[]
 for version in ('v4','v5','v6'):
  path=P/('sdf-'+version+'-'+name+'.png')
  assert path.is_file(),path
  im=bpy.data.images.load(str(path),check_existing=False)
  assert list(im.size)==[860,860]
  x=np.empty(860*860*4,dtype=np.float32)
  im.pixels.foreach_get(x)
  imgs.append(x.reshape(860,860,4))
 combined=np.concatenate(imgs,axis=1)
 result=bpy.data.images.new('Real Cycles v4 v5 v6 '+name,width=2580,height=860,alpha=True,float_buffer=False)
 result.pixels.foreach_set(combined.ravel());result.update()
 dest=P/('comparison-v4-v5-v6-'+name+'.png')
 result.filepath_raw=str(dest);result.file_format='PNG';result.save()
 out.append({'kind':name,'path':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'pixels':[2580,860]})
 print('TRIPTYCH',name,dest.stat().st_size,flush=True)
(P/'triptych-manifest.json').write_text(json.dumps({'order':'left=v4 | center=v5 diagnostic | right=v6 restrained','generated_from':'genuine Blender Cycles PNG, same camera and studio for whole-body and bite; all macros use same scale','files':out},indent=2))
print('TRIPTYCH_DONE',flush=True)

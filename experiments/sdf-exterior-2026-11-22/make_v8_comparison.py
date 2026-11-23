import bpy,numpy as np,json,hashlib,os
from pathlib import Path
P=Path(os.environ.get('STRAWBERRY_SDF_OUT',str(Path(__file__).resolve().parents[2]/'build/sdf-vertical-slice')))
out=[]
for name in ('plane','bite','macro'):
 frames=[]
 for version in ('v4','v8'):
  path=P/('sdf-'+version+'-'+name+'.png')
  im=bpy.data.images.load(str(path),check_existing=False)
  assert tuple(im.size)==(860,860)
  arr=np.empty(860*860*4,dtype=np.float32)
  im.pixels.foreach_get(arr)
  frames.append(arr.reshape(860,860,4))
 combined=np.concatenate(frames,axis=1)
 result=bpy.data.images.new('Original v4 vs v8 '+name,width=1720,height=860,alpha=True,float_buffer=False)
 result.pixels.foreach_set(combined.ravel());result.update()
 f=P/('comparison-v4-v8-'+name+'.png')
 result.filepath_raw=str(f);result.file_format='PNG';result.save()
 out.append({'name':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'pixels':[1720,860]})
 print('COMPARISON',name,f.stat().st_size,flush=True)
(P/'v8-comparison-manifest.json').write_text(json.dumps({'side_by_side':'left v4, right v8','inputs':'native Blender Cycles source PNGs, same camera/lights','files':out},indent=2))
print('COMPARISON_DONE',flush=True)

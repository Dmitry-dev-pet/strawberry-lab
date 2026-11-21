import bpy,numpy as np,json,hashlib
from pathlib import Path
report={}
for a in [0,32,82]:
 ob=bpy.data.objects[f'V1_CUT_{a:03d} | thin 3D fiber physical relief'];m=ob.data
 n=len(m.vertices);xyz=np.empty(n*3,dtype='<f4');m.vertices.foreach_get('co',xyz)
 sig=np.empty(n,dtype='<f4');m.attributes['fine_fiber_signal'].data.foreach_get('value',sig)
 off=np.empty(n,dtype='<f4');m.attributes['fine_fiber_geometric_offset'].data.foreach_get('value',off)
 report[str(a)]={'vertices_sha256':hashlib.sha256(xyz.tobytes()).hexdigest(),
 'signal_sha256':hashlib.sha256(sig.tobytes()).hexdigest(),
 'offset_sha256':hashlib.sha256(off.tobytes()).hexdigest()}
mat=bpy.data.materials['V1 FLESH | physical 3D filament bundle ridges + wet glints']
report['mix']=list(mat.node_tree.nodes['Mix (Legacy).001'].inputs[2].default_value)
report['strength']=mat.node_tree.nodes['Map Range'].inputs['To Max'].default_value
print('FINGERPRINT',json.dumps(report,sort_keys=True))

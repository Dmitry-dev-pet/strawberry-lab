"""Independent saved-scene field/mesh comparison. Requires prior PR50 QA helpers."""
import sys,json,hashlib,bpy,numpy as np
from pathlib import Path
src,scene,field,pose,oldqa,helpers,out=sys.argv[sys.argv.index('--')+1:];out=Path(out);assert not out.exists();sys.path.insert(0,str(Path(helpers)/'vascular-lab'));sys.path.insert(0,str(Path(helpers)/'juice-lab'));from qa_vascular_relief import snapshot,tri_sample;from qa_juice_surface import state,BODY,JUICE,juice_snap
f=np.load(field);R,H=f['core'],f['halo'];assert np.isfinite(f['ring_relative']).all() and np.all(H>=R)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(src)=='361696819fd44733d560e3f59b101cd11f59862e7ebd7b7f83ce94fd07909963'
def snap(path):
 bpy.ops.wm.open_mainfile(filepath=path,use_scripts=False);s=bpy.context.scene;b=s.objects[BODY];j=s.objects[JUICE];assert not j.visible_shadow;mm=s.unit_settings.scale_length*1000;state(b,pose,.32,1.);r,p,c,k,v=snapshot(b,mm);jr=juice_snap(j,mm,p,c,k);return r,p,c,k,v,jr,mm
A,pa,ca,ka,va,ja,mm=snap(src);prev=json.loads((Path(oldqa)/('qa-'+pose+'.json')).read_text());assert A['coords_sha']==prev['body']['coords_sha'] and A['topology_sha']==prev['body']['topology_sha'] and ja==prev['juice'];B,pb,cb,kb,vb,jb,_=snap(scene);assert A['topology_sha']==B['topology_sha'] and np.array_equal(ca,cb) and np.array_equal(ka,kb)
for r in (A,B):assert r['nonmanifold']==0 and r['degenerate_triangles']==0 and r['volume_mm3']>0,r
res=dict(status='PASS',pose=pose,source_sha=sha(src),scene_sha=sha(scene),A=A,B=B,juice_A=ja,juice_B=jb,old_A_receipt_match=True,topology_identical=True)
if pose=='whole':assert np.array_equal(pa,pb) and jb['faces']==0;res['whole_identical']=True
else:
 d=np.linalg.norm(pa-pb,axis=1)*mm;ids=np.flatnonzero(cb);idx=ids[np.linspace(0,len(ids)-1,512,dtype=int)];rp=vb['sdf_rest_position'][idx]*mm+[0,0,27];errR=float(np.max(np.abs(tri_sample(R,rp)-vb['sl_vascular_core'][idx])));errH=float(np.max(np.abs(tri_sample(H,rp)-vb['sl_vascular_halo'][idx])));assert errR<.001 and errH<.001,(errR,errH);assert np.array_equal(va['sdf_rest_position'],vb['sdf_rest_position']);seam=float(d[ca&ka].max());skin=float(d[ka&~ca].max());assert seam<.0001 and skin<.0001 and np.sum(d[cb]>.001)>100;res.update(max_delta_mm=float(d.max()),skin_delta_mm=skin,seam_delta_mm=seam,core_error=errR,halo_error=errH,cap_moved=int(np.sum(d[cb]>.001)),rest_position_identical=True)
out.write_text(json.dumps(res,indent=2)+'\n');print(json.dumps(res),flush=True)

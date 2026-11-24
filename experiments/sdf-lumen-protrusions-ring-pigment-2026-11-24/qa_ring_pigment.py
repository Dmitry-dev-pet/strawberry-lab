"""Saved-scene ring pigment geometry regression and independent B-channel checks."""
import bpy,numpy as np,sys,json,hashlib
from pathlib import Path
scene,prior,field,pose,root,out=sys.argv[sys.argv.index('--')+1:];out=Path(out);assert not out.exists();root=Path(root)
sys.path[:0]=[str(root/'juice-lab'),str(root/'vascular-lab')];from qa_juice_surface import state,body_snap,juice_snap,BODY,JUICE,attr;from qa_vascular_relief import tri_sample
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=json.loads(Path(prior).read_text());assert old['pose']==pose and old['scene_sha']=='0498a4bb9daf0fbdb15630a052539283e89f117bbe074c2b8762868ba0deb1b0';assert sha(field)=='65cdd1b27fa6569ced1da7dde1c10f921f9933a1aadee963c7cc6c73330e193f'
bpy.ops.wm.open_mainfile(filepath=scene,use_scripts=False);s=bpy.context.scene;b=s.objects[BODY];j=s.objects[JUICE];mm=s.unit_settings.scale_length*1000;assert not j.visible_shadow;state(b,pose,.32,1.)
r,p,c,k=body_snap(b);jr=juice_snap(j,mm,p,c,k);assert all(r[t]==old['B'][t] for t in ('vertices','faces','coords_sha','topology_sha'));assert jr==old['juice_B'];res=dict(status='PASS',pose=pose,source_sha=old['scene_sha'],scene_sha=sha(scene),body=r,juice=jr,geometry_identical_to_ring_receipt=True)
cap=bpy.data.materials['SDF | inherited 150^3 tissue + own multiscale wetness'];n=[q for q in cap.node_tree.nodes if q.name.startswith('SL Ring Pigment | ')];assert len(n)==18;external=[(l.to_node.bl_idname,l.to_socket.name) for l in cap.node_tree.links if l.from_node in n and l.to_node not in n];assert external==[('ShaderNodeBsdfPrincipled','Base Color')],external;res['new_shader_outgoing_links']=external
if pose!='whole':
 dg=bpy.context.evaluated_depsgraph_get();ev=b.evaluated_get(dg);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg);v=attr(me,'sl_ring_relative');rp=attr(me,'sdf_rest_position',True);ids=np.flatnonzero(c);idx=ids[np.linspace(0,len(ids)-1,512,dtype=int)];f=np.load(field);error=float(np.max(np.abs(tri_sample(f['ring_relative'],rp[idx]*mm+[0,0,27])-v[idx])));assert error<.001 and np.isfinite(v).all(),error
 res.update(independent_B_samples=512,ring_relative_error=error,ring_relative_cap_min=float(v[c].min()),ring_relative_cap_max=float(v[c].max()),ring_inside_fraction=float((v[c]<.5).mean()));ev.to_mesh_clear()
out.write_text(json.dumps(res,indent=2)+'\n');print(json.dumps(res),flush=True)

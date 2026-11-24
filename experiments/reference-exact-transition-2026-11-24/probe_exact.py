"""Independent aggregate inspection harness for owner-private original Kiwi runtime.
No reference graph, geometry, assets or implementation serialized. No commercial features.
"""
import bpy, bmesh, sys, time, json, os, traceback, hashlib, collections
import numpy as np
from pathlib import Path
sys.path.insert(0,os.environ['FRUCHT_PRIVATE_PARENT'])
import frucht_free as addon
from frucht_free import api,automatik,fast,jobs,schnitt,schnitte,form,aufloesung,teile
out=Path(os.environ['FRUCHT_PROBE_OUT']); start=time.monotonic(); records=[]; stage=0; last=start; plane=None; piece=None

def log(event,**kw):
 r=dict(event=event,elapsed_s=round(time.monotonic()-start,3),**kw);records.append(r)
 (out/'runtime.json').write_text(json.dumps(records,indent=2,ensure_ascii=False,default=str)+'\n')
 print('PROBE '+json.dumps(r,ensure_ascii=False,default=str),flush=True)

def invoke(fn,*args,**kw):
 r=fn(*args,**kw);log('call',function=fn.__name__,args=args,kwargs=kw,ok=r.get('ok'),busy=r.get('busy'),error=r.get('error'),name=r.get('name'));return r

def matrix(m):return [[round(float(x),7) for x in row] for row in m]
def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()

def mesh_info(o):
 dg=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dg);gs=ev.evaluated_geometry();m=gs.mesh
 if m is None:return {'vertices':0,'faces':0}
 xyz=np.empty(3*len(m.vertices),np.float32);m.vertices.foreach_get('co',xyz);xyz=xyz.reshape(-1,3)
 m.calc_loop_triangles();tri=np.empty(3*len(m.loop_triangles),np.int32);m.loop_triangles.foreach_get('vertices',tri)
 mats=collections.Counter(p.material_index for p in m.polygons);matnames=[x.name if x else None for x in m.materials]
 bm=bmesh.new();bm.from_mesh(m);adj=collections.Counter()
 for e in bm.edges:
  if len(e.link_faces)==2:
   i,j=sorted(f.material_index for f in e.link_faces)
   if i!=j:adj[f'{i}:{j}']+=1
 info=dict(vertices=len(m.vertices),faces=len(m.polygons),position_sha=digest(xyz),triangle_sha=digest(tri),boundary_edges=sum(len(e.link_faces)==1 for e in bm.edges),over_two_face_edges=sum(len(e.link_faces)>2 for e in bm.edges),mixed_material_edges=dict(adj),material_faces=[dict(index=i,name=matnames[i] if i<len(matnames) else None,faces=n) for i,n in sorted(mats.items())],bounds=[xyz.min(0).tolist(),xyz.max(0).tolist()] if len(xyz) else None)
 bm.free();return info

def routes(o):
 m=o.modifiers.get('Anzeige')
 if not m or not m.node_group:return []
 return [n.inputs['Object'].default_value.name for n in m.node_group.nodes if n.bl_idname=='GeometryNodeObjectInfo' and n.inputs['Object'].default_value is not None]

def cache_info():
 a={}
 for key in ('VORRAT_GANZ','VORRAT_BLAETTER','FLEISCHFORM','FLEISCH_QUELLE'):
  o=bpy.data.objects.get(getattr(fast,key,''));a[key]=dict(present=o is not None,bakes=[len(b.data_blocks) for m in o.modifiers if m.type=='NODES' for b in m.bakes] if o else [])
 return a

def whole_state(label):
 bpy.context.view_layer.update();g=api._griff();assert g is not None
 ctl=bpy.data.objects[fast.EBENE];body=bpy.data.objects[fast.KORPER];source=bpy.data.objects.get(f'{fast.S} | Schnittfläche')
 r=dict(label=label,mode=schnitt.modus(),routing=routes(g),body=mesh_info(g),flesh_visible=bool(source and not source.hide_viewport),cache=cache_info(),basis_valid=schnitt.basis_gueltig(),inside_valid=schnitt.innen_gueltig(),exact_allowed=schnitte.echt_moeglich(),actual_cell_input=bool(fast.baum_eingang(body,'Echte Zellen').value),actual_cut_input=bool(fast.baum_eingang(body,'Schnitt').value),controller_basis=matrix(ctl.matrix_basis),cutters=[{'name':o.name,'matrix_local':matrix(o.matrix_local)} for o in schnitte.schneider()],plane_sync_needed=schnitte.ebene_anders())
 if source and not source.hide_viewport:r['separate_flesh']=mesh_info(source)
 log('whole_state',**r);return r

def piece_state(label):
 bpy.context.view_layer.update();xs=[]
 for o in sorted(teile.stuecke(),key=lambda x:x.name):
  d=json.loads(o['frucht_stueck']);e=bpy.data.objects.get(d.get('echt',''));r=dict(name=o.name,quality=d.get('qualitaet'),cuts=len(d.get('schnitte',[])),body=mesh_info(o),display_inputs=routes(o),saved_exact_present=e is not None,stand=d.get('stand'))
  if e:r['exact_bake_blocks']=[len(b.data_blocks) for m in e.modifiers if m.type=='NODES' for b in m.bakes];r['exact_bake_targets']=[m.bake_target for m in e.modifiers if m.type=='NODES']
  xs.append(r)
 log('pieces',label=label,pieces=xs);return xs

def end(ok):
 log('end',ok=ok,stage=stage);bpy.ops.wm.quit_blender();return None

for o in list(bpy.context.scene.objects):bpy.data.objects.remove(o,do_unlink=True)
addon.register();automatik.PAUSE[0]=True
bpy.context.scene.frucht_aufloesung=40.
log('start',blender=bpy.app.version_string,build_hash=bpy.app.build_hash.decode(),resolution_percent=40,auto_switch_paused=True)

def tick():
 global stage,last,plane,piece
 try:
  if time.monotonic()-start>170:return end(False)
  if api._busy():
   if time.monotonic()-last>10:log('busy',stage=stage,job=jobs.status());last=time.monotonic()
   return .25
  last=time.monotonic()
  if stage==0:
   assert invoke(api.create,'kiwi')['ok'];stage=1
  elif stage==1:
   whole_state('placeholder');assert invoke(api.set_mode,'fast')['ok'];stage=2
  elif stage==2:
   whole_state('whole_fast');r=invoke(api.cut_add,'plane',location=(0,0,.3));assert r['ok'];plane=r['name'];stage=3
  elif stage==3:
   whole_state('plane_fast');assert invoke(api.set_mode,'exact')['ok'];stage=4
  elif stage==4:
   r=whole_state('plane_exact');assert r['mode']=='GENAU' and r['actual_cell_input'];assert invoke(api.cut_move,plane,location=(0,0,.3),rotation=(0,65,0))['ok'];stage=5
  elif stage==5:
   whole_state('plane_moved_api_exact');stage=6;return 2.
  elif stage==6:
   whole_state('plane_moved_api_exact_after_2s');needed=schnitte.ebene_anders();log('explicit_original_sync',needed_before=needed,returned=schnitte.ebene_abgleichen());bpy.context.view_layer.update();stage=7
  elif stage==7:
   whole_state('plane_moved_after_original_sync');assert invoke(api.set_mode,'fast')['ok'];stage=8
  elif stage==8:
   whole_state('rotated_fast');assert invoke(api.cut_move,plane,location=(0,0,.3),rotation=(0,0,0))['ok'];stage=9
  elif stage==9:
   whole_state('reset_plane_fast');assert invoke(api.set_mode,'exact')['ok'];stage=10
  elif stage==10:
   whole_state('reset_plane_exact');assert invoke(api.set_mode,'fast')['ok'];stage=11
  elif stage==11:
   assert invoke(api.cut_remove,plane)['ok'];assert invoke(api.blade,location=(0,0,0),rotation=(0,0,0))['ok'];stage=12
  elif stage==12:
   r=invoke(api.split);assert r['ok'],r.get('error');stage=13
  elif stage==13:
   xs=piece_state('split_preview');assert len(xs)==2 and all(x['quality']=='schnell' for x in xs);piece=xs[0]['name'];assert invoke(api.finalize,target=piece)['ok'];stage=14
  elif stage==14:
   xs=piece_state('one_finalized');p=next(x for x in xs if x['name']==piece);assert p['quality']=='echt' and p['saved_exact_present'] and any(p['exact_bake_blocks']);assert len([x for x in xs if x['quality']=='schnell'])==1
   o=bpy.data.objects[piece];o.location.x+=1.;bpy.context.view_layer.update();stage=15
  elif stage==15:
   piece_state('finalized_piece_translated');return end(True)
  return .5
 except Exception:
  log('exception',stage=stage,traceback=traceback.format_exc());return end(False)
bpy.app.timers.register(tick,first_interval=1.)

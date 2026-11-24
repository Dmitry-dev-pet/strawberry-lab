"""Read-only reference experiment, isolated from project scenes; no imported reference content in the harness."""
import bpy,sys,time,json,os,traceback,hashlib
from pathlib import Path
sys.path.insert(0,os.environ['FRUCHT_PRIVATE_PARENT'])
import frucht_free as addon
from frucht_free import api,automatik,fast,jobs,schnitt,schnitte,form,aufloesung
out=Path(os.environ['FRUCHT_PROBE_OUT']); start=time.monotonic(); reports=[]; stage=0; last=start

def log(event,**data):
    r=dict(event=event,elapsed_s=round(time.monotonic()-start,3),**data);reports.append(r);print('PROBE '+json.dumps(r,ensure_ascii=False,default=str),flush=True);(out/'runtime.json').write_text(json.dumps(reports,indent=2,ensure_ascii=False,default=str)+'\n')
def invoke(fn,*args,**kw):
    r=fn(*args,**kw);log('call',function=fn.__name__,args=args,kwargs=kw,ok=r.get('ok'),busy=r.get('busy'),error=r.get('error'),name=r.get('name'));return r

def snapshot(name):
    bpy.context.view_layer.update();g=api._griff();dg=bpy.context.evaluated_depsgraph_get();assert g is not None
    obj=[]
    for o in [g]+list(g.children_recursive):
        try:
            a=o.evaluated_get(dg);gs=a.evaluated_geometry();m=gs.mesh;pc=gs.instances_pointcloud();obj.append(dict(name=o.name,mesh_vertices=len(m.vertices) if m else 0,mesh_faces=len(m.polygons) if m else 0,instances=len(pc.points) if pc else 0,hidden_render=o.hide_render,dimensions=[round(float(x),5) for x in a.dimensions]))
        except Exception as e:obj.append(dict(name=o.name,error=str(e)))
    cache={}
    for key in ('VORRAT_GANZ','VORRAT_BLAETTER','FLEISCHFORM','FLEISCH_QUELLE'):
        o=bpy.data.objects.get(getattr(fast,key,''));cache[key]=dict(present=o is not None,bakes=[len(b.data_blocks) for m in o.modifiers if m.type=='NODES' for b in m.bakes] if o else [])
    seeds=api._kerne_von(g);log('snapshot',name=name,mode=schnitt.modus(),objects=obj,seed_and_hair_instance_count=seeds[0],instance_mesh_reference_count=seeds[1],cache=cache,basis_valid=schnitt.basis_gueltig(),inside_valid=schnitt.innen_gueltig(),exact_allowed=schnitte.echt_moeglich(),cut_count=len(schnitte.schneider()))

def save(name):
    p=out/(name+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(p));log('private_snapshot',name=name,size=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def end(ok):
    log('end',ok=ok);bpy.ops.wm.quit_blender();return None
for o in list(bpy.context.scene.objects):bpy.data.objects.remove(o,do_unlink=True)
addon.register();automatik.PAUSE[0]=True
sc=bpy.context.scene;sc.frucht_aufloesung=40.;log('start',blender=bpy.app.version_string,build_hash=bpy.app.build_hash.decode(),resolution_percent=sc.frucht_aufloesung)
plane=None; bite=None

def tick():
    global stage,last,plane,bite
    try:
        if time.monotonic()-start>145:return end(False)
        if jobs.laeuft() or form._SCHLANGE or form._PLAN['t'] is not None or aufloesung.wartet():
            if time.monotonic()-last>10:log('busy',stage=stage,job=jobs.status());last=time.monotonic()
            return .25
        last=time.monotonic()
        if stage==0:
            r=invoke(api.create,'kiwi');assert r['ok'];stage=1
        elif stage==1:
            snapshot('whole_placeholder');r=invoke(api.set_form,radius=3.0);assert r['ok'];stage=2
        elif stage==2:
            snapshot('whole_radius_changed');r=invoke(api.set_form,radius=2.55);assert r['ok'];stage=3
        elif stage==3:
            snapshot('whole_reset_radius');r=invoke(api.light);assert r['ok'];save('original-kiwi-whole');r=invoke(api.set_mode,'fast');assert r['ok'];stage=4
        elif stage==4:
            snapshot('whole_fast');r=invoke(api.cut_add,'plane',location=(0,0,.3));assert r['ok'];plane=r['name'];stage=5
        elif stage==5:
            snapshot('plane_fast');r=invoke(api.set_mode,'exact');assert r['ok'];stage=6
        elif stage==6:
            snapshot('plane_exact');save('original-kiwi-plane-exact');r=invoke(api.cut_move,plane,rotation=(0,90,0));assert r['ok'];stage=7
        elif stage==7:
            snapshot('plane_rotated_exact');r=invoke(api.set_mode,'fast');assert r['ok'];stage=8
        elif stage==8:
            r=invoke(api.cut_remove,plane);assert r['ok'];r=invoke(api.cut_add,'bite');assert r['ok'];bite=r['name'];stage=9
        elif stage==9:
            snapshot('bite_fast');r=invoke(api.set_mode,'exact');log('exact_bite_rejected',expected=not r['ok'],reason=r.get('error'));assert not r['ok'];save('original-kiwi-bite-fast');return end(True)
        return .5
    except Exception:
        log('exception',stage=stage,traceback=traceback.format_exc());return end(False)
bpy.app.timers.register(tick,first_interval=1.)

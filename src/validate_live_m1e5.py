#!/usr/bin/env python3
"""Blender actual new-session/reopened M1e5 + callback-driven live cutter tests."""
import bpy,bmesh,sys,json,math,time,importlib.util
from mathutils import Vector
from pathlib import Path
p=Path(__file__).parent
body=bpy.data.objects['M1c | SDF cutter + rest-space tissue']
snapshot=bpy.data.objects['M1e5 | EXACT live-local CutSurface']
knife=bpy.data.objects['M1e | independently moving knife (cube half space)']
helper=bpy.data.objects['M1e5 | live SDF source for localized mesh']
scene=bpy.context.scene
assert scene.get('m1e5_mode')=='FAST_GN_ALWAYS_LIVE'
assert not body.hide_render and snapshot.hide_render,'Unsafe default: exact should be opt-in'
assert 'M1e5 - Enable Live Exact.py' in bpy.data.texts
spec=importlib.util.spec_from_file_location('m1e5_live_exact',str(p/'m1e5_live_exact.py'))
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
started=time.perf_counter();mod.register()
assert scene['m1e5_mode']=='EXACT_SCRIPT_ENABLED'
assert body.hide_render and not snapshot.hide_render
rows=[]
def inspect(tag):
    dg=bpy.context.evaluated_depsgraph_get();dg.update()
    eb=snapshot.evaluated_get(dg)
    me=eb.to_mesh()
    bm=bmesh.new();bm.from_mesh(me)
    bad=sum(not e.is_manifold for e in bm.edges)
    unseen=set(bm.verts);component_count=0
    while unseen:
        component_count+=1
        st=[unseen.pop()]
        while st:
            v=st.pop()
            for ed in v.link_edges:
                z=ed.other_vert(v)
                if z in unseen:unseen.remove(z);st.append(z)
    bm.free()
    assert bad==0,(tag,bad)
    assert len(me.vertices)<180000,(tag,len(me.vertices))
    assert 'fruit_rest' in me.attributes and 'm1e4_fiber' in me.attributes
    seed=bpy.data.objects['GN live achenes (with actual surface pits)']
    es=seed.evaluated_get(dg);ms=es.to_mesh()
    result={'label':tag,'frame':scene.frame_current,'vertices':len(me.vertices),'faces':len(me.polygons),
            'nonmanifold_edges':bad,'components':component_count,'seed_vertices':len(ms.vertices),
            'refresh_count':mod._STATE['refresh_count'],'refresh_s':mod._STATE['last_seconds'],
            'selection':mod._STATE['last_result']['selected_faces']}
    es.to_mesh_clear();eb.to_mesh_clear()
    rows.append(result);print('M1E5_CHECK',json.dumps(result),flush=True)
    return result

# Moving the timeline triggers frame-change callback automatically; NO explicit refresh calls.
for fr in (1,15,30,21):
    prior=mod._STATE['refresh_count']
    scene.frame_set(fr)
    assert mod._STATE['refresh_count']>prior,(fr,mod._STATE['last_error'])
    r=inspect('timeline-'+str(fr))
    assert r['components']==(2 if fr==1 else 1),r

# Same frame, manual cutter move must update from depsgraph change handler.
original=knife.location.copy();prior=mod._STATE['refresh_count']
knife.location.y+=.3
bpy.context.view_layer.update()
bpy.context.evaluated_depsgraph_get().update()
assert mod._STATE['refresh_count']>prior,('manual move callback not triggered',mod._STATE)
r=inspect('manual-knife-offset')
assert r['nonmanifold_edges']==0
assert r['vertices']!=rows[-2]['vertices'] or r['seed_vertices']!=rows[-2]['seed_vertices'],'Knife move must change actual cut geometry'
# Identical scene evaluation must NOT rebuild after own snapshot mesh causes depsgraph update.
prior=mod._STATE['refresh_count'];bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
assert mod._STATE['refresh_count']==prior,'Reentry/event-loop not guarded'
knife.location=original
bpy.context.view_layer.update()
assert mod._STATE['refresh_count']==prior+1,'Knife reset not refreshing'
inspect('manual-restore')
# Turn off local exact: the original GN cut MUST remain independently live on pose updates.
mod.disable()
assert not body.hide_render and snapshot.hide_render
prior=mod._STATE['refresh_count'];scene.frame_set(30)
assert mod._STATE['refresh_count']==prior,'Disabled handler still rebuilds'
dg=bpy.context.evaluated_depsgraph_get();dg.update()
eb=body.evaluated_get(dg);me=eb.to_mesh()
assert len(me.vertices)>10000
print('M1E5_FAST_FALLBACK',len(me.vertices),flush=True)
eb.to_mesh_clear()
mod.unregister()
assert not mod._STATE['installed']
report={'status':'PASS','blender':bpy.app.version_string,'scenes':rows,
        'checks':['file defaults to Fast live GN safe mode','opt-in python handler enables exact',
                  'frame handlers automatically rebuild detailed mesh','manual knife transform triggers depsgraph handler',
                  'no recursive rebuild','all evaluated meshes manifold',
                  'Fast fallback remains live without Python handler'],
        'limitations':['Python+GN hybrid, NOT GN-only','not 60fps real-time; edits cost measurable CPU time',
                       'Blender Text must be Run once unless addon installed','tube clipping approximate'],
        'elapsed_s':round(time.perf_counter()-started,3)}
(p/'validation-live.json').write_text(json.dumps(report,indent=2)+'\n')
print('M1E5_CALLBACKS_PASS',json.dumps(report),flush=True)

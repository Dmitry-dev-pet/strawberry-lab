"""Verify actual user-editable GN modifier parameters in Blender 5.2."""
import bpy,bmesh,time,json,sys
from pathlib import Path
scene=bpy.context.scene;scene.frame_set(15)
ob=bpy.data.objects['M1c | SDF cutter + rest-space tissue'];mod=ob.modifiers[0];g=mod.node_group
items={i.name:i for i in g.interface.items_tree if i.item_type=='SOCKET' and i.in_out=='INPUT'}
keys={'Cut edge width':.008,'Cut edge segments':3,'Fiber reach':.066,'Fiber intensity':.53,'Cell relief':.019,'Cavity relief':.01}
assert set(keys).issubset(items)
for name,val in keys.items():
 actual=getattr(mod.properties.inputs,items[name].identifier).value
 assert abs(actual-val)<1e-5,(name,actual,val)
def stats(tag):
 dg=bpy.context.evaluated_depsgraph_get();dg.update();ev=ob.evaluated_get(dg);me=ev.to_mesh();at=me.attributes['m1e4_fiber'];v=[at.data[i].value for i in range(len(at.data))]
 bm=bmesh.new();bm.from_mesh(me);bad=sum(not e.is_manifold for e in bm.edges);bm.free()
 res={'name':tag,'vertices':len(me.vertices),'faces':len(me.polygons),'bad_edges':bad,'fiber_max':max(v),'fiber_count_gt_0_11':sum(a>.11 for a in v)}
 print('CONTROL_TEST',json.dumps(res),flush=True)
 ev.to_mesh_clear();return res
base=stats('original-default')
param=getattr(mod.properties.inputs,items['Cut edge segments'].identifier);param.value=1
ob.update_tag(refresh={'OBJECT','DATA','TIME'});bpy.context.view_layer.update()
low=stats('segments1');assert low['vertices']<base['vertices'] and low['bad_edges']==0
param.value=3;ob.update_tag();bpy.context.view_layer.update()
assert stats('segments-restored')['vertices']==base['vertices']
param=getattr(mod.properties.inputs,items['Fiber intensity'].identifier);param.value=0
ob.update_tag();bpy.context.view_layer.update()
zero=stats('fiber-zero');assert zero['fiber_max']==0
param.value=.53;ob.update_tag();bpy.context.view_layer.update()
again=stats('fiber-restored');assert again['fiber_max']>.2
print('M1E6_EDITABLE_GN_CONTROLS_PASS')

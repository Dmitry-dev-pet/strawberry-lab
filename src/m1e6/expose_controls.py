import bpy,sys
from pathlib import Path
s=bpy.context.scene
ob=bpy.data.objects['M1c | SDF cutter + rest-space tissue'];g=ob.modifiers[0].node_group
n=g.nodes;ln=g.links
inp=next(x for x in n if x.bl_idname=='NodeGroupInput')

def control(name,socket_type,defval,minval,maxval,desc):
 s=g.interface.new_socket(name=name,in_out='INPUT',socket_type=socket_type)
 s.default_value=defval;s.min_value=minval;s.max_value=maxval;s.description=desc
 return inp.outputs[name]
bevel=control('Cut edge width','NodeSocketFloat',.008,.001,.020,'Selected GN bevel width, no Python exact rebuilding')
seg=control('Cut edge segments','NodeSocketInt',3,1,5,'Bevel topology segments on interior cut edges')
reach=control('Fiber reach','NodeSocketFloat',.066,.025,.160,'3D distance at which vascular color field fades out')
intensity=control('Fiber intensity','NodeSocketFloat',.53,0.,1.,'Maximum pre-shader 3D filament field value')
cutrelief=control('Cell relief','NodeSocketFloat',.019,0.,.04,'True cut displacement amplitude in native units')
cvrelief=control('Cavity relief','NodeSocketFloat',.01,0.,.03,'Geometry relief of internal cavity walls')
b=n['M1e6 | LOCAL Mesh Bevel with selected edges']
for name in ['Start Left Offset','Start Right Offset','End Left Offset','End Right Offset']:ln.new(bevel,b.inputs[name])
ln.new(seg,b.inputs['Segments'])
ln.new(reach,n['M1e6 | strand falloff'].inputs['From Max'])
ln.new(intensity,n['M1e6 | strand falloff'].inputs['To Min'])
ln.new(cutrelief,n['M1e3 | physical cell relief'].inputs[1])
ln.new(cvrelief,n['M1e3 | cavity relief strength'].inputs[1])
# Blender 5.2 removed NodesModifier ID properties. Explicitly set its RNA
# per-socket values, otherwise newly added group inputs initialize as zero.
permod={'Cut edge width':.008,'Cut edge segments':3,'Fiber reach':.066,'Fiber intensity':.53,'Cell relief':.019,'Cavity relief':.01}
for item in g.interface.items_tree:
 if item.item_type=='SOCKET' and item.in_out=='INPUT' and item.name in permod:
  getattr(ob.modifiers[0].properties.inputs,item.identifier).value=permod[item.name]
ob['m1e6_controls']='Modifier > Geometry Nodes: Cut edge width, segments, Fiber reach/intensity, Cell relief, Cavity relief'
ob['m1e6_caveat']='Native Mesh Bevel edge-local, not selected Subdivide Mesh; high fidelity via original M1e5 hybrid'
assert len([i for i in g.interface.items_tree if i.item_type=='SOCKET' and i.in_out=='INPUT'])==7
s.frame_set(15)
bpy.context.view_layer.update()
out=Path(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else Path('/mnt/data/strawberry-m1e6/m1e6-nativeGN-with-controls.blend')
out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out))
print('M1E6_CONTROLLED_SCENE_SAVED',str(out.resolve()),flush=True)

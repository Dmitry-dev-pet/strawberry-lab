import bpy, numpy as np
from mathutils import Vector
s=bpy.context.scene;b=s.objects['Receptacle | canonical PR29 hull'];g=bpy.data.materials['SDF | source skin at true rest_position'].node_tree
for name in ['Attribute','Map Range','Noise Texture.001','Color Ramp.002','Color Ramp.003','Principled BSDF','Vector Math.001','Separate XYZ']:
 n=g.nodes[name]; print('NODE',n.name,n.label,n.type)
 if n.type=='VALTORGB': print([(x.position,tuple(x.color)) for x in n.color_ramp.elements])
 for i in n.inputs:
  if i.is_linked:print('LINK',i.name,i.links[0].from_node.name,i.links[0].from_socket.name)
  elif hasattr(i,'default_value') and i.enabled and (n.type!='BSDF_PRINCIPLED' or i.name in ['Coat Weight','Coat Roughness','Roughness']):
   x=i.default_value;print('VAL',i.name,list(x) if hasattr(x,'__len__') and not isinstance(x,str) else x)
print('CAM',s.camera.name,tuple(s.camera.location),s.camera.data.lens,'target',s.camera.matrix_world.to_quaternion()@Vector((0,0,-1)))
print('BODY',b.location,b.dimensions,b['sdf_mode'],b['sdf_voxel_mm'])
for k in ['sdf_mode','sdf_voxel_mm']:print(k,b[k])
b['sdf_mode']=0;b['sdf_voxel_mm']=.32;b.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();o=b.evaluated_get(dg);m=o.to_mesh(preserve_all_data_layers=True,depsgraph=dg);a=m.attributes['achene_pit'];x=np.empty(len(a.data),np.float32);a.data.foreach_get('value',x);print('PIT',np.quantile(x,[0,.25,.5,.75,.9,.95,.99,1]),'positive',np.sum(x>.01),len(x));o.to_mesh_clear()

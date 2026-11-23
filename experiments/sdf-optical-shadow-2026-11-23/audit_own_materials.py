import bpy,json
from pathlib import Path
s=bpy.context.scene
for mat in bpy.data.materials:
 if not mat.use_nodes: continue
 if not(mat.name.startswith('SDF | inherited') or mat.name.startswith('SL Juice')):continue
 print('MAT',mat.name,'nodes',len(mat.node_tree.nodes))
 for n in mat.node_tree.nodes:
  if n.type in ['BSDF_PRINCIPLED','OUTPUT_MATERIAL','BSDF_TRANSPARENT','LIGHT_PATH','MIX_SHADER']:
   print(n.name,n.type)
   for sock in n.inputs:
    if not sock.enabled:continue
    v=getattr(sock,'default_value',None)
    if v is not None and hasattr(v,'__len__') and not isinstance(v,str):v=list(v)
    print(sock.name, v, 'LINK', [(l.from_node.name,l.from_socket.name) for l in sock.links])
  if n.type in ['ATTRIBUTE','TEX_VORONOI','BUMP','TEX_IMAGE','TEX_NOISE']:
   print(n.name,n.type,getattr(n,'attribute_name',None),getattr(n,'feature',None),getattr(n,'image',None))
   print('  in',[(x.name,[(l.from_node.name,l.from_socket.name) for l in x.links]) for x in n.inputs if x.is_linked]);print('  out',[(x.name,[(l.to_node.name,l.to_socket.name) for l in x.links]) for x in n.outputs if x.is_linked])
print('CYCLES',[(n,getattr(s.cycles,n,None)) for n in ['max_bounces','transparent_max_bounces','transmission_bounces','caustics_reflective','caustics_refractive']]);print('unit scale',s.unit_settings.scale_length)

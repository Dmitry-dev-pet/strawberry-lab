#!/usr/bin/env python3
"""Read an M1c .blend in Blender and validate *evaluated* SDF geometry.

Checks manifoldness, cut vs skin face material assignment, rest-position attribute
and the declared editable SDF nodes. This checks topology, NOT photorealism.

Run: blender -b strawberry-m1c-half.blend --python validate_sdf_scene.py
"""
import bpy,bmesh,json
ob=bpy.data.objects.get('M1c | SDF cutter + rest-space tissue')
if not ob:raise RuntimeError('Missing M1c editable GN object')
mod=next((m for m in ob.modifiers if m.type=='NODES'),None)
if not mod or not mod.node_group:raise RuntimeError('Missing Geometry Nodes modifier')
g=mod.node_group
required={'GeometryNodeMeshToSDFGrid':2,'GeometryNodeSDFGridBoolean':1,'GeometryNodeGridToMesh':1,'GeometryNodeStoreNamedAttribute':1,'GeometryNodeSetMaterial':2,'GeometryNodeSetPosition':1}
counts={t:sum(n.bl_idname==t for n in g.nodes) for t in required}
if any(counts[t]<needed for t,needed in required.items()):raise RuntimeError('Missing critical GN nodes: '+repr(counts))
boolean=next(n for n in g.nodes if n.bl_idname=='GeometryNodeSDFGridBoolean')
if boolean.operation!='DIFFERENCE':raise RuntimeError('Wrong SDF boolean mode')
bpy.context.view_layer.update()
mo=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh=mo.to_mesh()
bm=bmesh.new();bm.from_mesh(mesh)
nonman=sum(not e.is_manifold for e in bm.edges);bm.free()
attr=mesh.attributes.get('fruit_rest')
if nonman or attr is None or attr.data_type!='FLOAT_VECTOR' or attr.domain!='POINT':raise RuntimeError('Mesh not manifold / missing rest-attribute')
material_faces={str(i):sum(p.material_index==i for p in mesh.polygons) for i in {p.material_index for p in mesh.polygons}}
if len(material_faces)<2 or min(material_faces.values())<100:raise RuntimeError('SDF did not classify both cut and outer surfaces')
# Rest-space attribute should be BEFORE any movement and equal the point's
# original fruit-coordinate for this untransformed diagnostic scene.
errs=[]
for i in range(0,len(mesh.vertices),max(1,len(mesh.vertices)//120)):
    p=mesh.vertices[i].co; q=attr.data[i].vector
    err=sum((p[j]-q[j])**2 for j in range(3))**.5
    if err>.019:errs.append(round(err,3))
if errs:raise RuntimeError('Rest mapping not tied to original mesh coordinates: '+str(errs[:10]))
mat=bpy.data.materials.get('M1c | rest-space pith/cortex + wet Voronoi surface')
if not mat or not mat.use_nodes:raise RuntimeError('Missing wet tissue shader')
sh=mat.node_tree.nodes
vor=sum(n.bl_idname=='ShaderNodeTexVoronoi' for n in sh)
imgnodes=[n for n in sh if n.bl_idname=='ShaderNodeTexImage' and n.image]
if vor<3 or len(imgnodes)!=2 or any(not i.image.packed_file for i in imgnodes):raise RuntimeError('Missing multiscale wetness or packed atlas image')
r={'status':'PASS','geometry':{'vertices':len(mesh.vertices),'triangles':sum(len(p.vertices)-2 for p in mesh.polygons),'nonmanifold_edges':nonman,'classified_material_faces':material_faces},'rest_positions':'stable: original coordinates stored on points','sdf_nodes':counts,'wet_voronoi_layers':vor,'packed_atlas_samples':len(imgnodes)}
mo.to_mesh_clear()
print('M1C_VALIDATION',json.dumps(r),flush=True)
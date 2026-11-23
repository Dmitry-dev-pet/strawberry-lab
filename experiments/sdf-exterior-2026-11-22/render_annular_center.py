import bpy,math,time,json,os
from pathlib import Path
from mathutils import Vector
P=Path(os.environ.get('STRAWBERRY_SDF_OUT',str(Path(__file__).resolve().parents[2]/'build/sdf-vertical-slice')))
sc=bpy.context.scene;sc.frame_set(20)
c=bpy.data.objects['SDF cutter | planar (move or rotate)']
face=next(f for f in c.data.polygons if f.index==1)
normal=(c.matrix_world.to_3x3().inverted().transposed()@face.normal).normalized()
point=c.matrix_world@c.data.vertices[face.vertices[0]].co
signed=normal.dot(Vector((0,0,25))-point)
c.location+=normal*signed  # shift cutting face until (0,0,25) lies on it
bpy.context.view_layer.update()
print('CUT_CENTER',json.dumps({'offset_mm':round(signed,3),'pose':list(round(v,3) for v in c.location)}),flush=True)
mat=bpy.data.materials['SDF proof v8 | cut cells flattened on SAME vessel atlas']
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=25
sc.render.resolution_x=720;sc.render.resolution_y=720;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'
sc.render.filepath=str(P/'sdf-v9-central-plane-color.png')
bpy.ops.render.render(write_still=True)
tree=mat.node_tree
sep=next(n for n in tree.nodes if n.bl_idname=='ShaderNodeSeparateColor')
e=tree.nodes.new('ShaderNodeEmission')
tree.links.new(sep.outputs['Blue'],e.inputs['Color'])
out=next(n for n in tree.nodes if n.bl_idname=='ShaderNodeOutputMaterial')
tree.links.new(e.outputs['Emission'],out.inputs['Surface'])
sc.render.filepath=str(P/'sdf-v9-central-plane-blue.png')
bpy.ops.render.render(write_still=True)
print('CUT_CENTER_RENDER_DONE',flush=True)

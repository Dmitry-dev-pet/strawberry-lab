"""Original Strawberry Lab diagnostic: source-identical 1-bite control vs 3-bite SDF.
Copyright boundary: does not import/copy any Frucht nodes, geometry, or assets.
Builds a live (but expensive) Boolean pre-bake control, a baked 3-sphere cutter with
broken ORIGINAL 1-sphere seed mask, and an experimental analytic 3-sphere mask.
NOT A GENERAL ARBITRARY-CUTTER SEED FIX. All dimensions ARTIST.
"""
import argparse,bpy,bmesh,hashlib,json,math
from pathlib import Path
from mathutils import Vector
parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--outdir',type=Path,required=True)
a=parser.parse_args(__import__('sys').argv[__import__('sys').argv.index('--')+1:]);src=a.source.resolve();out=a.outdir.resolve()
PIN='4732b465b103f9a0b4ab262dfeae51e26a8865aa586c3779d472d86eed845399'
assert src.is_file() and hashlib.sha256(src.read_bytes()).hexdigest()==PIN and not out.exists()
assert bpy.app.version[:2]==(5,2)
out.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False);assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
s=bpy.context.scene;body=s.objects['Receptacle | canonical PR29 hull'];cut=s.objects['SDF | editable sphere bite'];seeds=[o for o in s.objects if o.get('role')=='achene'];assert len(seeds)==264 and len(cut.data.vertices)==6050 and not cut.modifiers
body['sdf_mode']=2;body['sdf_voxel_mm']=.20;body['sdf_tissue_gain']=1.;body['sdf_use_broad_halo']=1.;body['sdf_cell_surface_gain']=1.
cut.location=(.82,-.70,-.42);cut.scale=(1.04,)*3;s.frame_set(s.frame_current);bpy.context.view_layer.update()

def save(name):
 p=out/(name+'.blend');assert not p.exists();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(p),compress=True)
 return {'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size_bytes':p.stat().st_size}
A=save('bite-A-one')
centers=[(-.39,-.04,.22),(.36,.07,.11),(-.05,-.02,-.42)];r=.78
base=cut.data.copy()
for i,c in enumerate(centers):
 data=base.copy()
 for v in data.vertices:v.co=Vector(c)+v.co*r
 if i==0:cut.data=data
 else:
  operand=bpy.data.objects.new('OWN three-bites | control sphere '+str(i+1),data);s.collection.objects.link(operand);operand.matrix_world=cut.matrix_world.copy();operand.hide_render=True;operand.display_type='WIRE'
  mod=cut.modifiers.new('OWN three-bites | Boolean union '+str(i+1),'BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=operand
bpy.data.meshes.remove(base)
# Reference operation: bake a native Boolean union once so each achene's modifier doesn't recompute it.
bpy.ops.object.select_all(action='DESELECT');cut.select_set(True);bpy.context.view_layer.objects.active=cut
for mod in tuple(cut.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
for ob in list(s.objects):
 if ob.name.startswith('OWN three-bites | control sphere'):bpy.data.objects.remove(ob,do_unlink=True)
bm=bmesh.new();bm.from_mesh(cut.data);nonmanifold=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True);bm.free()
assert nonmanifold==0 and volume>0 and abs(volume/(4*math.pi/3)-1)<.10
cut['cutter_authoring']='OWN 3 intersecting smooth sphere cutters baked; single editable knife object; all ARTIST'
B=save('bite-B-three-unguarded')
# The native inherited seed mask uses LENGTH(Position - knife location) < knife scale,
# which MUST be replaced for this specific 3-sphere model. Keep cutter rotation & uniform scale live.
g=seeds[0].modifiers[0].node_group;assert len(g.nodes)==21 and all(sd.modifiers[0].node_group==g for sd in seeds)
ob=g.nodes['SDF | editable sphere bite'];rel=g.nodes['Vector Math.001'];scale=g.nodes['Separate XYZ.001'];stat=g.nodes['Minimum distance to sphere'];test=g.nodes['Math.001']
assert stat.inputs['Attribute'].links[0].from_node.name=='Per-vertex distance to sphere' and test.inputs[1].links[0].from_node==scale

def node(kind,name):
 n=g.nodes.new(kind);n.name=n.label=name;return n
invscale=node('ShaderNodeMath','BITE3 | inverse cutter uniform scale');invscale.operation='DIVIDE';invscale.inputs[0].default_value=1.;g.links.new(scale.outputs['X'],invscale.inputs[1])
local=node('ShaderNodeVectorMath','BITE3 | normalized relative vertex');local.operation='SCALE';g.links.new(rel.outputs['Vector'],local.inputs[0]);g.links.new(invscale.outputs[0],local.inputs['Scale'])
rotate=node('ShaderNodeVectorRotate','BITE3 | inverse current cutter rotation');rotate.rotation_type='EULER_XYZ';rotate.invert=True;g.links.new(local.outputs['Vector'],rotate.inputs['Vector']);g.links.new(ob.outputs['Rotation'],rotate.inputs['Rotation'])
vals=[]
for i,c in enumerate(centers):
 sub=node('ShaderNodeVectorMath','BITE3 | offset to ball '+str(i+1));sub.operation='SUBTRACT';g.links.new(rotate.outputs['Vector'],sub.inputs[0]);sub.inputs[1].default_value=c
 dist=node('ShaderNodeVectorMath','BITE3 | radius to ball '+str(i+1));dist.operation='LENGTH';g.links.new(sub.outputs['Vector'],dist.inputs[0]);vals.append(dist.outputs['Value'])
mn=node('ShaderNodeMath','BITE3 | min distances 1,2');mn.operation='MINIMUM';g.links.new(vals[0],mn.inputs[0]);g.links.new(vals[1],mn.inputs[1]);mn3=node('ShaderNodeMath','BITE3 | min distances all 3');mn3.operation='MINIMUM';g.links.new(mn.outputs[0],mn3.inputs[0]);g.links.new(vals[2],mn3.inputs[1])
g.links.remove(stat.inputs['Attribute'].links[0]);g.links.new(mn3.outputs[0],stat.inputs['Attribute']);g.links.remove(test.inputs[1].links[0]);test.inputs[1].default_value=r
g['guard_limit']='ONLY current 3-sphere analytic union, not arbitrary closed mesh; conservatively hides seeds near polygon boundary'
C=save('bite-C-three-fixed')
assert len(g.nodes)==32
rec={'status':'BUILD_NATIVE_ORIGINAL_1_V_3_BITES','blender':bpy.app.version_string,'source_sha256':PIN,'A':A,'B_baked_broken_seed_guard':B,'C_three_fixed_guard':C,'cutter':{'mode':'three overlapping regular spheres exact mesh union','centers_local':centers,'radius_local':r,'mesh_verts':len(cut.data.vertices),'mesh_faces':len(cut.data.polygons),'nonmanifold_edges':nonmanifold,'local_volume':volume,'volume_ratio_to_single_sphere':volume/(4*math.pi/3)},'GN_seed_nodes':len(g.nodes),'source_150_and_192_atlases':'unchanged source bytes','status_limit':'experimental guard supports THIS analytic 3-sphere knife only, not general arbitrary cutter'}
(out/'build.json').write_text(json.dumps(rec,indent=2));print('BITE3_PORTABLE_BUILT',json.dumps(rec),flush=True)

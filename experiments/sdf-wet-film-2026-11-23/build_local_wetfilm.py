"""Original ARTIST patchy film variation C from wetfilm-B, one existing 3D rest-space mask.
No modifications of body, seeds, existing material atlas or core/halo fields.
"""
import bpy,hashlib,sys,argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert a.source.is_file() and not a.out.exists()
bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()),use_scripts=False)
body=bpy.context.scene.objects['Receptacle | canonical PR29 hull'];film=bpy.context.scene.objects['SDF | live cut wet-film surface'];g=film.modifiers[0].node_group
mat=bpy.data.materials['SDF | separate cut wet film (ARTIST)'];sg=mat.node_tree
sep=g.nodes['Separate existing cut faces from skin'];off=g.nodes['ARTIST | sheet offset normal 0.025mm']
links=[x for x in g.links if x.from_node==sep and x.to_node==off]
assert len(links)==1
g.links.remove(links[0])
rest=g.nodes.new('GeometryNodeInputNamedAttribute');rest.name=rest.label='Same source rest position';rest.data_type='FLOAT_VECTOR';rest.inputs['Name'].default_value='sdf_rest_position'
vor=g.nodes.new('ShaderNodeTexVoronoi');vor.name=vor.label='ARTIST 3D local wet patches';vor.voronoi_dimensions='3D';vor.feature='DISTANCE_TO_EDGE';vor.inputs['Scale'].default_value=46.0;g.links.new(rest.outputs['Attribute'],vor.inputs['Vector'])
math=g.nodes.new('ShaderNodeMath');math.name=math.label='Keep narrow wet patches';math.operation='GREATER_THAN';math.inputs[1].default_value=.065;g.links.new(vor.outputs['Distance'],math.inputs[0]);
delg=g.nodes.new('GeometryNodeDeleteGeometry');delg.name=delg.label='Local water film only';delg.domain='FACE';g.links.new(sep.outputs['Selection'],delg.inputs['Geometry']);g.links.new(math.outputs[0],delg.inputs['Selection']);g.links.new(delg.outputs['Geometry'],off.inputs['Geometry'])
# The whole-film precedent whitened the entire red cut face; lower coverage + omit transmission.
bs=sg.nodes['ARTIST | damp reflective translucent tissue film'];bs.inputs['Base Color'].default_value=(.94,.81,.78,1)
bs.inputs['Transmission Weight'].default_value=0
bs.inputs['Coat Weight'].default_value=.12
bs.inputs['Coat Roughness'].default_value=.07
sg.nodes['ARTIST | transparent film mixing baseline'].inputs[0].default_value=.15
sg.nodes['ARTIST | halo highlights modulation'].inputs[1].default_value=.06
sg.nodes['ARTIST | wet roughness .055..145'].inputs[0].default_value=.04
assert float(body['sdf_wetfilm_gain'])==1.0
film['film_description']='Sparse open 3D cell-edge wet surface patches, offset .025mm, ARTIST; not closed liquid'
bpy.context.scene['wetfilm_variant']='C sparse surface glints (original existing same-rest 3D Voronoi), not Frucht node copy'
body.update_tag();bpy.context.scene.frame_set(bpy.context.scene.frame_current);bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()),compress=True)
print(json.dumps({'variant':'C','scene_sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'bytes':a.out.stat().st_size,'rest_domain':'sdf_rest_position','Voronoi_scale':46.,'wet_patch_dist':.065,'physical_sheet_offset_mm':.025,'source_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest()}))

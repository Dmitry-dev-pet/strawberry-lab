"""Finalize restrained geometrical cut cells from two native Cycles trial strengths."""
import bpy,hashlib,json,time,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
P=Path(os.environ.get('STRAWBERRY_SDF_OUT',str(ROOT/'build/sdf-vertical-slice')))
src=P/'strawberry-sdf-vertical-slice-v5.blend'
dst=P/'strawberry-sdf-vertical-slice-v6.blend'
assert src.is_file() and not dst.exists()
bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False)
scene=bpy.context.scene
for mode in ('planar','bite'):
 group=bpy.data.node_groups['SDF cutter + rest-space | '+mode]
 node=group.nodes['V5_CELL_RELIEF_STRENGTH']
 node.outputs['Value'].default_value=.18
 group['v6_restrained_cell_strength']=.18
cut=bpy.data.materials['SDF proof v5 | cell sculpt + restrained wet highlights']
cut.name='SDF proof v6 | subtle actual cells / wet pulp'
nodes=cut.node_tree.nodes
bump=next(n for n in nodes if n.bl_idname=='ShaderNodeBump')
bump.inputs['Strength'].default_value=.09
bump.inputs['Distance'].default_value=.014
bs=next(n for n in nodes if n.bl_idname=='ShaderNodeBsdfPrincipled')
bs.inputs['Coat Weight'].default_value=.065
bs.inputs['Coat Roughness'].default_value=.24
scene['v6_scope']='ARTIST subtle physically displaced cells on cuts; source v5=strong geometry control; rest-space fibers v4, all original cutters'
scene['v6_visual_acceptance']='WIP: less caviar than v5, still does not match Frucht wet fiber anatomy; no scientific claims'
scene['v6_authority']='src in GitHub draft PR43, binary on owner Drive; not merged'
scene.frame_set(20)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(dst))
data={'version':'v6','parent_sha':hashlib.sha256(src.read_bytes()).hexdigest(),
'blend_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),
'new_mesh_relief_strength':.18,'render_shading':'subtle cell bump, wet film roughness','cell_scaling':'ARTIST',
'original_v4_tissue_atlas_sha256':hashlib.sha256((P/'tissue-v4-192.png').read_bytes()).hexdigest()}
(P/'v6-manifest.json').write_text(json.dumps(data,indent=2)+'\n')
print('V6_SAVED',json.dumps(data),flush=True)

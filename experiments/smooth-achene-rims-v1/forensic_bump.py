"""Single lookdev calibration: only the legacy achene-pit bump strength is zeroed."""
from pathlib import Path
import sys,json,hashlib
import bpy
source,out=map(Path,sys.argv[sys.argv.index('--')+1:])
assert hashlib.sha256(source.read_bytes()).hexdigest()=='24a3f7a2b9b157aac3b5a8aa30aa1b84d2404be64df67f74705665de3dbf74b4'
assert not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(source.resolve()),use_scripts=False)
mat=bpy.data.objects['Receptacle | canonical PR29 hull'].data.materials[0]
matches=[node for node in mat.node_tree.nodes if node.type=='BUMP' and any(link.from_node.type=='ATTRIBUTE' and link.from_node.attribute_name=='achene_pit' for link in node.inputs['Height'].links)]
assert len(matches)==1
node=matches[0];old=node.inputs['Strength'].default_value;node.inputs['Strength'].default_value=0
out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()),compress=True)
out.with_suffix('.json').write_text(json.dumps({'purpose':'forensic only; not accepted model','changed_node':node.name,'old_pit_bump_strength':old,'new_strength':0,'microtexture_normal_input_still_linked':node.inputs['Normal'].is_linked,'scene_sha256':hashlib.sha256(out.read_bytes()).hexdigest()},indent=2)+'\n')

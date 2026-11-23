"""Read-only audit of true material link paths. Does not modify the Blender scene."""
import bpy,sys,json,argparse,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--scene',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert a.scene.is_file() and not a.out.exists()
bpy.ops.wm.open_mainfile(filepath=str(a.scene.resolve()),use_scripts=False)
m=bpy.data.materials['SDF | inherited 150^3 tissue + own multiscale wetness'];g=m.node_tree
bs=next(n for n in g.nodes if n.type=='BSDF_PRINCIPLED');node=g.nodes.get('Math.039');assert node
outgoing=[(l.to_node.name,l.to_socket.name) for l in node.outputs[0].links]
base=[(l.from_node.name,l.from_socket.name) for l in bs.inputs['Base Color'].links]
assert outgoing==[('Math.056','Value')],outgoing
assert base==[('Hue/Saturation/Value','Color')],base
assert g.nodes.get('Mix (Legacy).004') is None
image_names=sorted({n.image.name for n in g.nodes if n.type=='TEX_IMAGE' and n.image})
report={'status':'PASS_NO_V21_COLOR_OUTLINE_PATH','blender':bpy.app.version_string,'scene_sha256':hashlib.sha256(a.scene.read_bytes()).hexdigest(),'material':m.name,'total_nodes':len(g.nodes),'original_v21_identifier':'Math.039','math_039_operation':node.operation,'math_039_outgoing':outgoing,'principled_base_color':base,'v21_Mix_Legacy_004_present':False,'tex_images':image_names,'conclusion':'The v21 color-outline knob is absent here. Math.039 feeds wetness roughness and Bump, NOT color. Do not copy 0.10 to 0.02.'}
a.out.write_text(json.dumps(report,indent=2)+'\n');print(report['status'],flush=True)

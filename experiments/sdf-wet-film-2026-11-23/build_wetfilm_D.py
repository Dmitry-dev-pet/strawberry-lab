"""One-factor follow-up to sparse surface C: coarse patches not pixel-scale noise."""
import bpy,argparse,sys,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert a.source.is_file() and not a.out.exists()
bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()),use_scripts=False)
s=bpy.context.scene;f=s.objects['SDF | live cut wet-film surface'];g=f.modifiers[0].node_group
v=g.nodes['ARTIST 3D local wet patches'];v.inputs['Scale'].default_value=12.
g.nodes['Keep narrow wet patches'].inputs[1].default_value=.06
mg=bpy.data.materials['SDF | separate cut wet film (ARTIST)'].node_tree
mg.nodes['ARTIST | transparent film mixing baseline'].inputs[0].default_value=.09
mg.nodes['ARTIST | halo highlights modulation'].inputs[1].default_value=.025
s['wetfilm_variant']='D coarse 3D patches, weak translucent sheen, no transmission; negative control if unconvincing'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()),compress=True)
print('D scene SHA',hashlib.sha256(a.out.read_bytes()).hexdigest())

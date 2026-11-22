from pathlib import Path
import sys,json,hashlib
import bpy
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
from strawberry_generator.seam_fix.policy import apply_policy
pins=json.loads((ROOT/'src/strawberry_generator/readback.json').read_text())['full_downloaded_sha256']
for seed in [101,202]:
 source=ROOT.parent/'strawberry-generator/build/generator-v1-final'/f'seed{seed}/strawberry.blend';assert hashlib.sha256(source.read_bytes()).hexdigest()==pins[f'seed{seed}.blend']
 out=ROOT/'build/source-seam-v1'/f'seed{seed}.blend';assert not out.exists()
 bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);apply_policy(bpy.context.scene)
 bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)

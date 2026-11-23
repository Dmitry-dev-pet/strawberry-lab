from pathlib import Path
import bpy,hashlib
ROOT=Path(__file__).resolve().parents[2];source=ROOT.parent/'strawberry-nonlinear-exact/build/nonlinear-exact-v1/shouldered.blend'
# Pin the verified PR38 input using its committed download receipt.
import json
expected=json.loads((ROOT/'experiments/nonlinear-exact-v1/readback.json').read_text())['full_sha256_readback']['shouldered.blend']
assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
out=ROOT/'build/live-profile-v1/live-profile.blend';assert not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
for mat in bpy.data.materials:
 if not mat.node_tree:continue
 for combine in mat.node_tree.nodes:
  if combine.label!='Analytic nonlinear inverse: physical -> original PR29 rest':continue
  z=combine.inputs['Z'].links[0].from_node;z.name='LIVE inverse height'
  scale=combine.inputs['X'].links[0].from_node.inputs[1].links[0].from_node
  terms=scale.inputs[1].links[0].from_node
  terms.inputs[0].links[0].from_node.name='LIVE inverse shoulder'
  terms.inputs[1].links[0].from_node.name='LIVE inverse waist'
text=bpy.data.texts['TISSUE_ZONES__RUN.py'];code=text.as_string()
old='CURVES = (("V3 | 28-sag0.25 | CARRIERS", 28), ("V4 | hook0.85 | BRANCHES", 539))'
assert code.count(old)==1;code=code.replace(old,'CURVES = (("ARTIST | 28 trunks + 264 seed-linked terminals", 292),)')
anchor='    current = bpy.app.driver_namespace.get(RUNTIME)';assert code.count(anchor)==1
code=code.replace(anchor,"    if 'profile_cleanup' in globals():profile_cleanup()\n"+anchor)
text.clear();text.write(code+'\n'+(Path(__file__).parent/'profile_runtime.py').read_text());text.use_module=False
bpy.context.scene['Live profile status']='Opt-in panel Apply Profile; Exact defaults to ARTIST 28+264 source. Old 28+539 diagnostics retained.'
bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)

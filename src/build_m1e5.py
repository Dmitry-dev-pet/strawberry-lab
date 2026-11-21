#!/usr/bin/env python3
"""Build a safe self-contained M1e5 .blend from M1e4 Beauty pose15.

Default on file reopen: original Fast Geometry Nodes is live and visible.
To activate auto-updating local Exact, run the embedded script once or install
m1e5_live_exact.py as a Blender addon. Scripts are NOT autorun on file open.
"""
import bpy,sys, argparse
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--out',type=Path,required=True)
p.add_argument('--addon',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
scene=bpy.context.scene
body=bpy.data.objects['M1c | SDF cutter + rest-space tissue']
snapshot=bpy.data.objects['M1e4 | local CutSurface SNAPSHOT frame 15']
knife=bpy.data.objects['M1e | independently moving knife (cube half space)']
original=body.modifiers[0].node_group
assert 'M1e3' in original.name,original.name
# Separate live lowpoly SDF source: NO globally subdivided skin.
helper=bpy.data.objects.new('M1e5 | live SDF source for localized mesh',body.data.copy())
body.users_collection[0].objects.link(helper)
g=original.copy();g.name='M1e5 | source-only pre-subdivision volume mesh'
sub=g.nodes['M1e3 | true cut-surface mesh refinement']
upstream=sub.inputs['Mesh'].links[0].from_socket
out=next(n for n in g.nodes if n.bl_idname=='NodeGroupOutput' and n.is_active_output)
for link in list(out.inputs['Geometry'].links):g.links.remove(link)
g.links.new(upstream,out.inputs['Geometry'])
helper.modifiers.new('LIVE low-poly SDF body - cavity - knife','NODES').node_group=g
helper.hide_render=True;helper.hide_set(True)
helper.display_type='BOUNDS'
snapshot.name='M1e5 | EXACT live-local CutSurface'
snapshot['dynamic']='ON after manual enable or installation of M1e5 Blender add-on'
snapshot['m1e5_helper']=helper.name
# Source-only remains hidden; original GN is the safe live Fast default.
body.hide_render=False;body.hide_set(False)
snapshot.hide_render=True;snapshot.hide_set(True)
knife.hide_render=True;knife.hide_set(False);knife.display_type='WIRE'
# Exactly one known script can be explicitly executed from the Blender Text Editor.
t=bpy.data.texts.get('M1e5 - Enable Live Exact.py') or bpy.data.texts.new('M1e5 - Enable Live Exact.py')
t.clear();t.write(a.addon.read_text(encoding='utf8'))
# Deliberately no autoload flag / no hidden code execution.
t.use_module=False
scene['m1e5_scene']=True
scene['m1e5_mode']='FAST_GN_ALWAYS_LIVE'
scene['m1e5_instruction']='Text Editor > M1e5 - Enable Live Exact.py > Run Script; or enable addon'
scene['m1e5_warning']='Exact adaptive mesh requires opt-in Python handler. Without it GN Fast always live.'
scene['m1e5_source']='Independent Strawberry Lab source: M1e2 live SDF + M1e4 local BMesh.'
scene.frame_set(15)
bpy.context.view_layer.update()
a.out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()))
print('M1E5_BUILT_SAFE',str(a.out.resolve()),'objects',len(bpy.data.objects),flush=True)

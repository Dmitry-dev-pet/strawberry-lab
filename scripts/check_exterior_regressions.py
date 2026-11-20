"""Blender-only regression probes for the independent exterior review findings.

Open an exterior .blend with Blender, then run this script. Scene edits are
in-memory only, restored immediately; output fixtures use temporary directories.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import json
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from build_strawberry_exterior import build
from validate_strawberry_exterior import validate

body, = (o for o in bpy.context.scene.objects if o.get('role') == 'receptacle')
original = body.location.copy()
try:
    body.location.x += 4
    bpy.context.view_layer.update()
    try:
        validate()
    except AssertionError as error:
        assert 'transform differs' in str(error), str(error)
    else:
        raise AssertionError('Moved body falsely passed validation')
finally:
    body.location = original
    bpy.context.view_layer.update()

with TemporaryDirectory(prefix='exterior-regression-') as temp:
    out = Path(temp)
    preview = out / 'strawberry-exterior.png'
    sentinel = b'old-render-must-survive'
    preview.write_bytes(sentinel)
    args = SimpleNamespace(out=out, samples=28, resolution=900, seed=10, no_render=True)
    try:
        build(args)
    except FileExistsError:
        pass
    else:
        raise AssertionError('Build reused an evidence directory')
    assert preview.read_bytes() == sentinel
    assert not (out / 'stats.json').exists()
    preview.unlink()
    args.resolution = 999999
    try:
        build(args)
    except ValueError as error:
        assert 'Resolution' in str(error), str(error)
    else:
        raise AssertionError('Unsupported resolution accepted')

print(json.dumps({'status':'PASS','moved_body_rejected':True,
                  'previous_evidence_preserved':True,'resolution_limit_enforced':True}))

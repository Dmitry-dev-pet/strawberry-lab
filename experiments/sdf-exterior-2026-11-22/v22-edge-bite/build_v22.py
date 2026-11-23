"""Original Strawberry Lab v22A: reposition the existing SDF bite onto lower edge.
Only cutter transform changes; all source tissue, skin, seeds and materials retained.
ARTIST geometry, not copied Frucht implementation. Blender 5.2.4 LTS.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy

SOURCE_SHA = '92e7e288f7851ec8c5e68897d5f7f19b5b5f73310a6d7d9084836f854c258a13'
CUTTER = 'SDF cutter | spherical bite (move or scale)'

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    assert bpy.app.version[:3]==(5,2,4),bpy.app.version_string
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    src=a.source.resolve(strict=True)
    dst=a.out.expanduser().resolve()
    assert digest(src)==SOURCE_SHA,'Not the verified original v21B scene'
    assert not dst.exists(),'Never replace an existing .blend'
    dst.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False,use_scripts=False)
    cutter=bpy.data.objects[CUTTER]
    assert cutter.type=='MESH' and len(cutter.data.vertices)==6050
    assert abs(cutter.scale.x-12)<1e-6 and abs(cutter.location.z-26.3802318573)<1e-4
    cutter.location=(1.,-9.,6.5)
    cutter.scale=(23.,22.,21.5)
    scene=bpy.context.scene
    scene.frame_set(40)
    scene['v22_source_v21_sha256']=SOURCE_SHA
    scene['v22_hypothesis']='ARTIST edge-intersecting bite; no material changes'
    scene['v22_reference']='Private Frucht film 18-20s qualitative silhouette, not code'
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(dst),compress=True)
    print('V22_BUILD_OK',json.dumps({'source_sha256':SOURCE_SHA,'output':dst.name,'sha256':digest(dst),
       'scene_bytes':dst.stat().st_size,'cut_location':list(cutter.location),'cut_scale':list(cutter.scale)}),flush=True)

if __name__=='__main__':
    main()

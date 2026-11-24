"""One independent optical intervention: exclude only the juice object from
Cycles shadow rays. No reference nodes, source, assets or parameter presets.
The camera/refraction material, mesh and all Geometry Nodes are unchanged.
"""
from pathlib import Path
import bpy,sys,hashlib,json
PIN='2fcc5a8e65273d3ac0f633f887e4f5522da9642c375f5d4499e891bc2889d394'
JUICE='SL Juice | independent pool surface'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
if __name__=='__main__':
    src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)==PIN;assert not out.exists()
    bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),use_scripts=False)
    j=bpy.data.objects[JUICE];assert j.visible_shadow and j.visible_camera and j.visible_transmission
    j.visible_shadow=False
    assert not j.visible_shadow and j.visible_camera and j.visible_transmission
    bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()))
    print(json.dumps({'source_sha256':PIN,'output_sha256':sha(out),'change':'juice object.visible_shadow True -> False'}),flush=True)

"""Independent material-only saved scene regression; compare actual evaluated geometry."""
import bpy, sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from qa_crown import state,snapshots,snap,sha
from build_color import PIN
from qa_flesh import tree_inventory

def record():
    out=snapshots();out['crown']={o.name:snap(o.name,['sl_rest_position','sepal_vein']) for o in bpy.data.collections['SL Crown | sepals and pedicel'].objects};return out

def main():
    src,new,pose,out=sys.argv[sys.argv.index('--')+1:];assert sha(src)==PIN and not Path(out).exists();assert sha(new)==json.loads(Path(new).with_suffix('.json').read_text())['scene_sha']
    state(src,pose);a=record();state(new,pose);b=record();assert a==b
    Path(out).write_text(json.dumps({'pose':pose,'source_sha':sha(src),'scene_sha':sha(new),'evaluated_geometry_and_named_attributes_equal':True,'objects':sorted(b['crown']), 'snapshots':b},indent=2)+'\n');print('PASS',pose,flush=True)
if __name__=='__main__':main()

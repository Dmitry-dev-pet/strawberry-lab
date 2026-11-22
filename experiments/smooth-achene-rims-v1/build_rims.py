"""Two bounded shoulder-refinement alternatives; original PR34 code unchanged."""
from pathlib import Path
import sys,argparse,inspect,hashlib
import bpy
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'experiments/geometric-achene-pits-v1'))
import build_pits as base
from validate_pits import immutable_snapshot
p=argparse.ArgumentParser();p.add_argument('alternative',type=int,choices=(1,2));p.add_argument('pr34',type=Path);p.add_argument('pr33',type=Path);p.add_argument('out',type=Path)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
assert hashlib.sha256(a.pr34.read_bytes()).hexdigest()=='24a3f7a2b9b157aac3b5a8aa30aa1b84d2404be64df67f74705665de3dbf74b4'
bpy.ops.wm.open_mainfile(filepath=str(a.pr34.resolve()),use_scripts=False);snapshot=immutable_snapshot(bpy.context.scene)
bpy.ops.wm.open_mainfile(filepath=str(a.pr33.resolve()),use_scripts=False)
assert immutable_snapshot(bpy.context.scene)==snapshot
# Reconstruct on the exact original pre-pit hull of this same canonical object.
# Saved264anchor/normal/ID/rotation/scale, materials, network and runtime agree above.
base.EDGE_MM=.28;base.REFINE_PASSES=3 if a.alternative==1 else 1
source=inspect.getsource(base.local_refine)
source=source.replace('radius = max(s.anchor.pit_length_radius_mm for s in seats) / mm','radius = 1.25 * max(s.anchor.pit_length_radius_mm for s in seats) / mm')
source=source.replace('.length_squared <= 1:', '.length_squared <= 1.25**2:')
if a.alternative==2:source=source.replace('cuts=1,','cuts=2,')
exec(compile(source,'padded_shoulder_refinement','exec'),base.__dict__)
sys.argv=[sys.argv[0],'--',str(a.pr33),str(a.out)]
base.main()

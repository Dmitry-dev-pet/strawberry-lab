"""Bounded nonlinear CPU-field adapter; physical cap attribute feeds inverse shader once."""
from pathlib import Path
import sys,hashlib,json
import bpy
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments/geometric-achene-pits-v1')]
from validate_pits import activate_runtime
from build_tissue_zones import runtime_source,replace
HELPER='''
import json, math
def nonlinear_key():
    c=json.loads(bpy.context.scene['Nonlinear parameters'])
    return (float(c['a']),float(c['b']),float(c['h']))
def nonlinear_rest(p):
    a,b,h=nonlinear_key()
    z=p.z/h
    scale=1+a*math.exp(-((z-.5)/.36)**2)+b*math.exp(-((z+.3)/.4)**2)
    if h<=0 or scale<=0:raise ValueError('Invalid nonlinear inverse')
    return Vector((p.x/scale,p.y/scale,z))
'''
def adapted_source():
 s=runtime_source()
 s=replace(s,'            rest = Vector(vertex[rest_layer])','            rest = nonlinear_rest(Vector(vertex[rest_layer]))')
 s=replace(s,'transform @ Vector(point.co[:3]), depth * point.radius','nonlinear_rest(transform @ Vector(point.co[:3])), depth * point.radius')
 s=replace(s,'strand_key = (self.source_revision, scale,','strand_key = (self.source_revision, scale, nonlinear_key(),')
 return HELPER+'\n'+s
for v,sha in [('shouldered','6410bcf7ef70b28621e7c2c5bc260dd05739623246b55aae5c53cc82c5a63ea4'),('waisted','9f46663641c9ccfe65f80e6970f7e83b2af3757434a2d90d15fd8180ecbc989e')]:
 source=ROOT.parent/'strawberry-nonlinear-cut/build/nonlinear-final'/f'{v}.blend';assert hashlib.sha256(source.read_bytes()).hexdigest()==sha
 target=ROOT/'build/nonlinear-exact-v1'/f'{v}.blend';assert not target.exists()
 bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
 text=bpy.data.texts['TISSUE_ZONES__RUN.py'];text.clear();text.write(adapted_source());text.use_module=False
 bpy.context.scene['Nonlinear Exact status']='Opt-in inverse-F CPU tissue/old strands; cap attribute PHYSICAL -> existing shader inverse exactly once'
 bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)

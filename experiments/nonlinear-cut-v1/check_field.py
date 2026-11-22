"""Evaluate the actual saved inverse shader subgraphs at physical rest probes."""
from pathlib import Path
import sys,json,math,hashlib
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'experiments/profile-vascular-v1'))
from profile_probe import forward,inverse
p=Path(sys.argv[sys.argv.index('--')+1]);out=Path(sys.argv[sys.argv.index('--')+2]);bpy.ops.wm.open_mainfile(filepath=str(p.resolve()),use_scripts=False);s=bpy.context.scene;cfg=json.loads(s['Nonlinear parameters']);params=cfg['a'],cfg['b'],cfg['h']
def evaluate(socket,physical):
 n=socket.node
 def inp(i):return evaluate(n.inputs[i].links[0].from_socket,physical) if n.inputs[i].is_linked else n.inputs[i].default_value
 if n.type=='TEX_COORD':return physical
 if n.type=='SEPXYZ':return inp(0)[['X','Y','Z'].index(socket.name)]
 if n.type=='COMBXYZ':return [inp(0),inp(1),inp(2)]
 a=inp(0);op=n.operation
 if op=='EXPONENT':return math.exp(a)
 b=inp(1)
 return {'ADD':lambda:a+b,'SUBTRACT':lambda:a-b,'MULTIPLY':lambda:a*b,'DIVIDE':lambda:a/b}[op]()
errors=[];graphs=[]
for mat in bpy.data.materials:
 if not mat.node_tree:continue
 for n in mat.node_tree.nodes:
  if n.label!='Analytic nonlinear inverse: physical -> original PR29 rest':continue
  graphs.append(mat.name)
  for p0 in [(0,0,.2),(.2,.1,-.3),(.5,-.2,.7),(-.3,.4,-.7)]:
   physical=forward(p0,params);errors.append(float(np.linalg.norm(np.array(evaluate(n.outputs[0],physical))-p0)))
assert graphs and max(errors)<1e-6
curve_errors=[]
for o in s.objects:
 if o.type!='CURVE' or 'nonlinear_source_points' not in o:continue
 source=json.loads(o['nonlinear_source_points']);actual=[pt.co[:3] for sp in o.data.splines for pt in sp.points]
 assert len(source)==len(actual)
 curve_errors.extend(float(np.linalg.norm(forward(a,params)-b)) for a,b in zip(source,actual))
assert max(curve_errors)<1e-6
out.write_text(json.dumps({'status':'PASS','actual_shader_subgraphs':graphs,'inverse_shader_error':max(errors),'all_curve_forward_error':max(curve_errors),'probes_per_material':4,'limitation':'Evaluates saved math graph; not a GPU RGB-emission swatch comparison. Curve radii unwarped.'},indent=2)+'\n')

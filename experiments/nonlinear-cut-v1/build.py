"""Real nonlinear geometry + analytic inverse shader. FAST ONLY: Exact explicitly disabled."""
from pathlib import Path
import sys,json,hashlib,math
import bpy
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'experiments/profile-vascular-v1'))
from profile_probe import forward,inverse,PROFILES
source=ROOT.parent/'strawberry-profile-vascular/build/profile-vascular-final/round.blend'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='e2b93d3d393fd0bc5614932ea09c9b031ede9c263533e7be7cfc18724f8f6d8a'
out=ROOT/'build/nonlinear-final'
for name,params in PROFILES.items():
 path=out/(name+'.blend');assert not path.exists()
 bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);s=bpy.context.scene;root=s.objects['Strawberry | PR29 rest space'];root.animation_data_clear();root.scale=(1,1,1)
 digest={}
 for o in s.objects:
  if o.type not in {'MESH','CURVE'} or o.parent!=root or o.name.startswith('Knife') or o.get('role')=='knife':continue
  if o.type=='MESH' and o.get('role') not in {'receptacle','achene','sepal','pedicel'} and '539' not in o.name:continue
  o.data=o.data.copy()
  mat=o.matrix_local.copy()
  if o.type=='MESH':
   points=[mat@v.co for v in o.data.vertices];digest[o.name]=hashlib.sha256(repr([tuple(p) for p in points]).encode()).hexdigest()
   attr=o.data.attributes.new('nonlinear_source_rest','FLOAT_VECTOR','POINT')
   for v,a,p in zip(o.data.vertices,attr.data,points):a.vector=p;v.co=forward(p,params)
   o.matrix_basis=Matrix.Identity(4);o.data.update()
   if o.get('role')=='achene':
    o['nonlinear_original_anchor']=list(o['hull_anchor_rest']);o['hull_anchor_rest']=list(forward(o['hull_anchor_rest'],params))
  else:
   points=[mat@Vector(p.co[:3]) for sp in o.data.splines for p in sp.points];digest[o.name]=hashlib.sha256(repr([tuple(p) for p in points]).encode()).hexdigest();i=0
   for sp in o.data.splines:
    for pt in sp.points:pt.co=(*forward(points[i],params),1);i+=1
   o['nonlinear_source_points']=json.dumps([list(p) for p in points]);o.matrix_basis=Matrix.Identity(4)
 # Build the SAME analytic inverse in native shader math: z=Z/h, x=X/s(z), y=Y/s(z).
 for material in bpy.data.materials:
  if not material.node_tree:continue
  nt=material.node_tree;coords=[n for n in nt.nodes if n.type=='TEX_COORD' and n.object==root]
  for coord in coords:
   old=list(coord.outputs['Object'].links)
   def mathnode(op,a,b=None):
    n=nt.nodes.new('ShaderNodeMath');n.operation=op
    for i,v in enumerate([a,b] if b is not None else [a]):
     if isinstance(v,(int,float)):n.inputs[i].default_value=v
     else:nt.links.new(v,n.inputs[i])
    return n.outputs[0]
   sep=nt.nodes.new('ShaderNodeSeparateXYZ');nt.links.new(coord.outputs['Object'],sep.inputs[0]);z=mathnode('DIVIDE',sep.outputs['Z'],params[2]);terms=[]
   for amp,center,width in [(params[0],.5,.36),(params[1],-.3,.4)]:
    delta=mathnode('DIVIDE',mathnode('SUBTRACT',z,center),width);square=mathnode('MULTIPLY',delta,delta);terms.append(mathnode('MULTIPLY',amp,mathnode('EXPONENT',mathnode('MULTIPLY',square,-1))))
   scale=mathnode('ADD',1,mathnode('ADD',*terms));combine=nt.nodes.new('ShaderNodeCombineXYZ')
   for axis in ['X','Y']:nt.links.new(mathnode('DIVIDE',sep.outputs[axis],scale),combine.inputs[axis])
   nt.links.new(z,combine.inputs['Z'])
   for link in old:nt.links.new(combine.outputs[0],link.to_socket)
   combine.label='Analytic nonlinear inverse: physical -> original PR29 rest'
 # Prevent old matrix-only Exact from silently rendering an unrelated cap.
 for text in bpy.data.texts:
  if text.name.endswith('.py') and ('EXACT' in text.name or 'TISSUE_ZONES' in text.name):text.clear();text.write("raise RuntimeError('Exact disabled: nonlinear inverse cap adapter not implemented; use native Fast')\n")
 graph=s.objects['ARTIST | 28 trunks + 264 seed-linked terminals'];nodes=json.loads(graph['graph_manifest'])
 for n in nodes:n['points']=[list(forward(p,params)) for p in n['points']]
 graph['graph_manifest']=json.dumps(nodes)
 s['Nonlinear parameters']=json.dumps({'name':name,'a':params[0],'b':params[1],'h':params[2],'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'status':'FAST_ONLY; EXACT_DISABLED'})
 s['Nonlinear source digests']=json.dumps(digest);s['Nonlinear limitation']='Original curve source points retained; physical paths warped. Tube radii unchanged artist approximation. Exact intentionally disabled.'
 bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)

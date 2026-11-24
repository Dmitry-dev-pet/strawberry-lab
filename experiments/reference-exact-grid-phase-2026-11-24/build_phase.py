"""Independent grid-origin experiment: translate BOTH inputs equally, subtract, undo.
Zero isovalue and world-space cutter are unchanged. No local geometric cleanup.
"""
import bpy,sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'deps'))
from build_exact import EXACT,sha
from build_split import ROOT
PIN='36f9ff4a5de1f1d222548d3c827a87df209624d55949643d9ff61449a1460cd6'
def main():
 src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)==PIN and not out.exists();bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False)
 o=bpy.data.objects[EXACT];g=o.modifiers[1].node_group;N=g.nodes;L=g.links
 def one(label):return next(n for n in N if n.label==label)
 def vec(op,a,b):
  n=N.new('ShaderNodeVectorMath');n.operation=op
  for x,s in [(a,n.inputs[0]),(b,n.inputs['Scale'] if op=='SCALE' else n.inputs[1])]:
   if isinstance(x,bpy.types.NodeSocket):L.new(x,s)
   else:s.default_value=x
  return n.outputs['Vector']
 def transform(a,t,label):
  n=N.new('GeometryNodeTransform');n.label=label;L.new(a,n.inputs['Geometry']);L.new(t,n.inputs['Translation']);return n
 vox=one('exact_voxel_mm').outputs[0];off=vec('SCALE',(.5,.5,.5),vox);neg=vec('SCALE',off,-1.0)
 bo=one('Common source difference');body,cutter=(bo.inputs[s].links[0].from_node for s in ('Grid 1','Grid 2'))
 for n,label in [(body,'Body in shifted computational frame'),(cutter,'Cutter in same shifted computational frame')]:
  link=n.inputs['Mesh'].links[0];srcsock=link.from_socket;L.remove(link);t=transform(srcsock,off,label);L.new(t.outputs['Geometry'],n.inputs['Mesh'])
 for n,label in [(one('One common skin and cap mesh'),'Physical common body'),(one('Uncut reference from same body grid'),'Physical uncut reference')]:
  assert n.inputs['Threshold'].default_value==0
  output=n.outputs['Mesh'];targets=[l.to_socket for l in output.links];t=transform(output,neg,label)
  for dest in targets:L.new(t.outputs['Geometry'],dest)
 # All field evaluations downstream use physical positions; sample signed operands in grid frame.
 pos=one('Final physical surface').outputs[0];p=vec('ADD',pos,off)
 for label in ['Body signed operand','Cutter signed operand']:L.new(p,one(label).inputs['Position'])
 for i,n in enumerate(N):n.location=((i//7)*220,-(i%7)*180)
 bpy.context.scene['scope']='Research: zero-isovalue Exact with shared half-cell computational frame; Fast unmodified';bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()),compress=True)
 r={'source_sha':PIN,'scene_sha':sha(out),'grid_phase_in_voxels':[.5,.5,.5],'isovalue_mm':0.,'node_count':len(N),'world_cutter_unchanged':True};out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print(r,flush=True)
if __name__=='__main__':main()

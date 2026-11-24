"""Read-only investigation of zero-isovalue extraction artifacts."""
import bpy, sys, json, numpy as np, hashlib
from pathlib import Path
from collections import Counter,defaultdict
from mathutils.bvhtree import BVHTree
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent/'deps'))
from qa_split import setup, mesh_eval, co, polys, top, sdf, ROOT, SKIN, CUTTER, SPHERE
from build_exact import EXACT,sha

def examine(m,mode):
 v=co(m);fs=polys(m);n=len(v);par=list(range(n))
 def find(i):
  while par[i]!=i:par[i]=par[par[i]];i=par[i]
  return i
 for f in fs:
  p=find(f[0])
  for j in f[1:]:
   q=find(j)
   if q!=p:par[q]=p
 ids=np.array([find(i) for i in range(n)]);cts=Counter(ids);m.calc_loop_triangles();tri=np.array([tuple(t.vertices) for t in m.loop_triangles]);areas=np.array([float(t.area) for t in m.loop_triangles]);degen=np.flatnonzero(areas<1e-9);rows=[]
 for root,k in cts.most_common():
  if k>32:continue
  ix=np.flatnonzero(ids==root);vv=v[ix];tt=tri[ids[tri[:,0]]==root];pts=v[tt].astype(float)-vv.mean(axis=0);vol=float(np.einsum('ij,ij->i',pts[:,0],np.cross(pts[:,1],pts[:,2])).sum()/6)
  rows.append({'vertices':int(k),'triangles':len(tt),'bounds_mm':[vv.min(axis=0).tolist(),vv.max(axis=0).tolist()],'centroid_mm':vv.mean(axis=0).tolist(),'analytic_cutter_distances_mm':sdf(vv,mode).tolist(),'signed_volume_mm3':vol,'areas_mm2':areas[ids[tri[:,0]]==root].tolist()})
 result={'vertices':n,'faces':len(fs),'components':sorted(cts.values(),reverse=True),'small_components':rows,'degenerate':[{'vertices':tri[i].tolist(),'coords':v[tri[i]].tolist(),'area_mm2':float(areas[i]),'component_size':int(cts[ids[tri[i,0]]])} for i in degen]}
 return result

def main():
 src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)=='36f9ff4a5de1f1d222548d3c827a87df209624d55949643d9ff61449a1460cd6';bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False);mode=setup('bite',.32);root=bpy.data.objects[ROOT];root['exact_mode']=1;root['exact_voxel_mm']=.2;root.update_tag();bpy.context.view_layer.update();o=bpy.data.objects[EXACT];g=o.modifiers[1].node_group;outnode=next(n for n in g.nodes if n.type=='GROUP_OUTPUT');final=outnode.inputs[0].links[0].from_socket;gm=next(n for n in g.nodes if n.label=='One common skin and cap mesh');ref=next(n for n in g.nodes if n.label=='Uncut reference from same body grid');bo=next(n for n in g.nodes if n.label=='Common source difference');cg=bo.inputs['Grid 2'].links[0].from_socket
 r={'source_sha':sha(src),'build_hash':bpy.app.build_hash.decode(),'cutter_origin':list(bpy.data.objects[SPHERE].location),'voxel_mm':.2}
 for label,sock in [('final',final),('raw_difference',gm.outputs['Mesh']),('uncut_body',ref.outputs['Mesh'])]:
  g.links.new(sock,outnode.inputs[0]);bpy.context.view_layer.update();e,m=mesh_eval(EXACT);r[label]=examine(m,mode);e.to_mesh_clear();print(label,r[label],flush=True)
 cutter_mesh=g.nodes.new('GeometryNodeGridToMesh');cutter_mesh.inputs['Threshold'].default_value=0.;g.links.new(cg,cutter_mesh.inputs['Grid']);g.links.new(cutter_mesh.outputs['Mesh'],outnode.inputs[0]);bpy.context.view_layer.update();e,m=mesh_eval(EXACT);r['cutter_zero_surface']=examine(m,mode);e.to_mesh_clear();print('cutter',r['cutter_zero_surface'],flush=True)
 out.write_text(json.dumps(r,indent=2)+'\n')
if __name__=='__main__':main()

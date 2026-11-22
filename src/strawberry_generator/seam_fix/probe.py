"""Float64 native-source and evaluated-Boolean diagnostic, without altering source coordinates."""
from pathlib import Path
import sys,json,hashlib
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments/geometric-achene-pits-v1')]
from validate_pits import activate,body_mesh,pose_knife,KNIFE,topology

def metrics(mesh):
 p=np.array([tuple(v.co) for v in mesh.vertices],dtype=np.float64);edges=np.array([e.vertices[:] for e in mesh.edges]);lengths=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1);cap=set();skin=set()
 for f in mesh.polygons:
  ids=list(f.vertices);(cap if f.material_index==1 else skin).update(tuple(sorted(e)) for e in zip(ids,ids[1:]+ids[:1]))
 seam=cap&skin;zero=[e for e in seam if np.array_equal(p[e[0]],p[e[1]])];mesh.calc_loop_triangles();bad=[]
 triangles=list(mesh.loop_triangles);ids=np.array([t.vertices[:] for t in triangles]);q=p[ids];areas=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);zero_ids=np.flatnonzero(np.einsum('ij,ij->i',areas,areas)==0)
 for i in zero_ids:
  t=triangles[int(i)];bad.append({'ids':list(t.vertices),'points':q[i].tolist(),'material':t.material_index})
 groups={}
 for f in mesh.polygons:groups.setdefault(len(f.vertices),[]).append(f.vertices[:])
 polys=0
 for n,indices in groups.items():
  q=p[np.array(indices)];area=np.zeros((len(indices),3))
  for i in range(1,n-1):area+=np.cross(q[:,i]-q[:,0],q[:,i+1]-q[:,0])
  polys+=int(sum(np.einsum('ij,ij->i',area,area)==0))
 try:volume=topology(mesh);closed=True
 except AssertionError:volume=None;closed=False
 return {'zero_edges_all':int(sum(lengths==0)),'min_edge_model_units':float(min(lengths)),'zero_seam_edges':len(zero),'zero_polygon_faces':polys,'zero_render_triangles':len(bad),'closed_connected_positive':closed,'volume':volume,'zero_seam_points':[p[e[0]].tolist() for e in zero],'bad_triangles':bad}

def run():
 result={}
 for seed in [101,202]:
  source=ROOT.parent/'strawberry-generator/build/generator-v1-final'/f'seed{seed}/strawberry.blend';bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);s=bpy.context.scene;activate(s,'matched');body=s.objects['Receptacle | canonical PR29 hull'];raw=metrics(body.data);p=np.array([tuple(v.co) for v in body.data.vertices]);raw['vertices_exactly_on_center_plane']=int(sum(p[:,1]==0));raw['vertices_within_1e_7_center_plane']=int(sum(abs(p[:,1])<1e-7));rows=[]
  for solver in ['MANIFOLD','EXACT']:
   body.modifiers[0].solver=solver
   for pose in [(0,0,0),(.08,29,32),(-.26,0,0)]:
    pose_knife(s.objects[KNIFE],pose);bpy.context.view_layer.update();m=metrics(body_mesh(body));rows.append({'solver':solver,'pose':pose,**m})
  affected=next(r for r in rows if r['solver']=='MANIFOLD' and r['pose']==(0,0,0))['zero_seam_points'];near=[]
  for point in affected:
   distances=np.linalg.norm(p-np.array(point),axis=1);ids=np.argsort(distances)[:8];near.append([{'id':int(i),'point':p[i].tolist(),'distance':float(distances[i]),'signed_center_plane_y':float(p[i,1]),'pit_mask':body.data.attributes['achene_pit'].data[int(i)].value} for i in ids])
  result[str(seed)]={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'raw':raw,'near_collapsed_seam':near,'solver_cases':rows}
 (ROOT/'build/source-seam-v1/probe.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':run()

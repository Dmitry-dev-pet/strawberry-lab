"""Check material occupancy along source protrusion interiors in the closed cavity on the bite pose."""
import bpy,sys,json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent));sys.path.insert(0,str(Path(__file__).resolve().parent/'deps'))
from build_lumen import EXACT,ROOT,LUMEN,PROTRUSIONS,WALL,sha
from qa_split import setup,mesh_eval,co
src,out=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()),use_scripts=False);setup('bite',.32);r=bpy.data.objects[ROOT];r['exact_mode']=1;r['tissue_gain']=0.
cav=bpy.data.objects[LUMEN].data;ct=BVHTree.FromPolygons([v.co for v in cav.vertices],[list(p.vertices) for p in cav.polygons]);pro=bpy.data.objects[PROTRUSIONS].data;positions=co(pro).reshape(18,16,12,3);centres=positions.mean(axis=2)
def signed(tree,p):
 q,n,_,_=tree.find_nearest(Vector(p));return float((q-Vector(p)).dot(n))
# Probe source ring centres (exclude the very last ring, which is exactly on the source tip end cap).
checks=[]
for vox in (.32,.20):
 r['exact_voxel_mm']=vox;r.update_tag();bpy.context.view_layer.update();e,m=mesh_eval(EXACT);m.calc_loop_triangles();idx=[q.name if q else '' for q in m.materials].index(WALL);tree=BVHTree.FromPolygons([v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles if t.material_index==idx],all_triangles=True);rows=[]
 for i,pts in enumerate(centres):
  # Must be at least 0.20mm into original cavity and not lie at the capped end.
  samples=[(k,signed(ct,p),signed(tree,p)) for k,p in enumerate(pts[:-1]) if signed(ct,p)>.20]
  rows.append({'site':i,'samples':len(samples),'retained_samples':sum(s[2]>0 for s in samples),'max_inside_material_mm':max([s[2] for s in samples],default=None),'points':[list(x) for x in samples]})
 checks.append({'voxel_mm':vox,'sites_with_interior_sample_in_material':sum(row['retained_samples']>0 for row in rows),'sites':len(rows),'samples':sum(row['samples'] for row in rows),'retained_samples':sum(row['retained_samples'] for row in rows),'rows':rows});e.to_mesh_clear()
Path(out).write_text(json.dumps({'scene_sha':sha(src),'scope':'sampled occupancy only, not full continuous protrusion geometry','checks':checks},indent=2)+'\n');print([(x['voxel_mm'],x['sites_with_interior_sample_in_material'],x['samples'],x['retained_samples']) for x in checks],flush=True)

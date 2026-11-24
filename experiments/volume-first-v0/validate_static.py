import bpy,bmesh,json,sys,math
from pathlib import Path
root=Path(__file__).resolve().parent/'outputs'
meshes=[o for o in bpy.data.objects if o.name.startswith('CUT_')]
rows=[]
for ob in meshes:
 bm=bmesh.new();bm.from_mesh(ob.data)
 bad=sum(not e.is_manifold for e in bm.edges)
 zero=sum(f.calc_area()<1e-10 for f in bm.faces)
 unseen=set(bm.verts);comps=[]
 while unseen:
  q=[unseen.pop()];n=0
  while q:
   v=q.pop();n+=1
   for e in v.link_edges:
    w=e.other_vert(v)
    if w in unseen:unseen.remove(w);q.append(w)
  comps.append(n)
 bm.free()
 attrs=[a.name for a in ob.data.attributes]
 row={'name':ob.name,'verts':len(ob.data.vertices),'faces':len(ob.data.polygons),'nonmanifold_edges':bad,'components':len(comps),'min_component_vertices':min(comps),'degenerate_faces':zero,'3D_tissue_colors':('tissue_color' in attrs and 'tissue_fiber' in attrs and 'tissue_pith' in attrs)}
 rows.append(row)
 print('SLICED_MESH',json.dumps(row),flush=True)
report={'status':'PASS' if all(r['nonmanifold_edges']==0 and r['components']==1 and r['degenerate_faces']==0 and r['3D_tissue_colors'] for r in rows) else 'FAILED_TOPOLOGY','blender':bpy.app.version_string,'geometry':rows,'contract':'Three physical watertight sectional meshes, each samples same 3D substrate','limit':'Meshes are constructed as center-plane halves; this does not prove a real-time arbitrary Boolean cut or Frucht parity.'}
(root/'validation.json').write_text(json.dumps(report,indent=2))
print('VALIDATION_STATUS',report['status'],flush=True)
if report['status']!='PASS':sys.exit(3)

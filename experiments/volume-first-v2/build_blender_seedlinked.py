#!/usr/bin/env python3
"""Overlay independent seed-anchored V2 curves onto a verified V1 inspection scene.
Original V1 objects remain in the .blend but are hidden from V2 renders.
No external copyrighted Frucht code/scene is included.
"""
import bpy, numpy as np, json, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
f=np.load(ROOT/'v2-seed-anchored-vascular-network.npz')
lengths=f['lengths']; points=f['points']; radii=f['radius']; kind=f['kind']
anchors=f['achene_positions'];endpoints=f['branch_endpoints'];source_idx=f['achene_idx']
assert len(anchors)==539 and len(lengths)==567 and (kind==0).sum()==28
scenes=[s for s in bpy.data.scenes if s.name.startswith(('01 |','02 |','03 |'))]
assert len(scenes)==3
for ob in bpy.data.objects:
 if ob.name.startswith('FIBERS | original') or ob.name.startswith('FIBERS | additional'):
  ob.hide_render=True
  # hide_set applies only to active View Layer, while old paths span 3 scenes
  if ob.name.endswith(".001"):ob.hide_set(True)
for sc in scenes:
 sc['SOURCE']='V2 seed-anchored. Centers extracted from own M1a seeds, remapped to own Volume First hull'
 sc['SCOPE']='Structure-only diagnostic: original fruit cut mesh unchanged, not real anatomy'
# Clean low-cost shaders and mesh.
def mat(name,color,rough=.39,sss=.12,emission=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
 bs=m.node_tree.nodes.get('Principled BSDF')
 bs.inputs['Base Color'].default_value=(*color,1)
 bs.inputs['Roughness'].default_value=rough
 bs.inputs['Subsurface Weight'].default_value=sss
 if emission:
  bs.inputs['Emission Color'].default_value=(*color,1)
  bs.inputs['Emission Strength'].default_value=emission
 return m
cream=mat('V2 | core 28 true spatial carriers',(.88,.77,.66),.38,.16)
pink=mat('V2 | 539 anchored vascular branches',(.79,.60,.53),.40,.10)
orange=mat('V2 | 539 actual seed anchor markers',(.84,.28,.045),.33,.04,.03)

def create_curves(name,desired_type,material):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=2;cu.bevel_depth=.010;cu.bevel_resolution=2;cu.use_fill_caps=True
 j=0;count=0;vcount=0
 for i,n in enumerate(lengths):
  pts=points[j:j+n];r=radii[j:j+n];j+=n
  if int(kind[i])!=desired_type:continue
  spline=cu.splines.new('POLY');spline.points.add(int(n)-1)
  for q,p,rr in zip(spline.points,pts,r):
   q.co=(float(p[0]),float(p[1]),float(p[2]),1.0)
   q.radius=float(rr/.010)
  count+=1;vcount+=n
 cu.materials.append(material)
 ob=bpy.data.objects.new(name,cu)
 for sc in scenes:sc.collection.objects.link(ob)
 ob['source']='v2-seed-anchored-vascular-network.npz'
 ob['part']='central' if desired_type==0 else 'per-achene'
 ob['curves']=count
 return ob,count,vcount
main,c1,p1=create_curves('V2 | 28 core carriers',0,cream)
branches,c2,p2=create_curves('V2 | 539 branches ending at achenes',1,pink)
# Octahedral markers: 1 object for all 539 achenes; each marker is the exact
# surface anchor from the same stored 3D data, not painted in the camera plane.
verts=[];faces=[]
for anchor in anchors:
 x,y,z=map(float,anchor)
 n=Vector((x,y,0)).normalized()
 u=Vector((-n.y,n.x,0))
 v=Vector((0,0,1))
 c=Vector((x,y,z))
 small=.021
 start=len(verts)
 pts=[c+n*small*.9,c-n*small*.65,c+u*small,c-u*small,c+v*small*1.35,c-v*small*1.35]
 verts.extend([tuple(p) for p in pts]); a0,b0,p0,q0,t0,d0=range(start,start+6)
 faces.extend([(a0,p0,t0),(a0,t0,q0),(a0,q0,d0),(a0,d0,p0),
               (b0,t0,p0),(b0,q0,t0),(b0,d0,q0),(b0,p0,d0)])
me=bpy.data.meshes.new('V2 | procedural per-achene endpoint markers mesh');me.from_pydata(verts,[],faces);me.update();me.materials.append(orange)
seed_obj=bpy.data.objects.new('V2 | 539 seed positions and branch endpoints',me)
for sc in scenes:sc.collection.objects.link(seed_obj)
seed_obj['count']=len(anchors)
seed_obj['marker_compatible']='per-achene positions imported from existing M1a seed mesh, then projected to current v1 fruit hull'
# Note that endpoints are 0.019 BU beneath their marker surface location.
d=np.linalg.norm(endpoints-anchors,axis=1)
assert np.max(np.abs(d-.019))<1e-5
# Control scene provenance and switch active to fiber-only so opening feels useful.
for i,sc in enumerate(scenes):sc['V2_VIEW_MODE']=['seed-linked only','with translucent fruit body','with unchanged original cut'][i]
scene=scenes[0]
bpy.context.window.scene=scene if bpy.context.window else bpy.context.scene
bpy.context.scene['V2_ATLAS']='not generated; this diagnostic is direct 3D geometry only'
path=ROOT/'v2-seed-linked-539-diagnostic.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path))
report={'source':'actual 539 centers from owned M1a seed mesh and 539 original end-matched curves',
        'remap':'radial/height projection onto independent V1 Volume First fruit hull',
        'central_carriers':c1,'anchored_branches':c2,'markers':len(anchors),'source_points':int(len(points)),
        'endpoints_per_seed':1,'endpoints_exact_subsurface':True,'marker_to_endpoint_distance_min':float(d.min()),
        'marker_to_endpoint_distance_max':float(d.max()),'v1_previous_494_curves_retained':True,
        'scenes':[s.name for s in scenes],'output':str(path),
        'important':'Frucht GPL/python implementation NOT imported; no direct vertex connection to commercial geometry; 3D preview only, no cut relief regenerated'}
(ROOT/'build-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print('V2_SEED_LINKED_BUILD_PASS',json.dumps(report),flush=True)

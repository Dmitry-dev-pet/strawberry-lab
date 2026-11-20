#!/usr/bin/env python3
"""Independently check saved M2c Blender 3D cell meshes and true sections."""
import sys,argparse,json,math
from pathlib import Path
import bpy
import bmesh

p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--out',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
records=json.load(open(a.plan,encoding='utf-8'))
assert records['schema']=='fruitengine.m2c.cells.1'
assert 'NO_MEASURED_POROSITY' in records['warnings']
assert all(b['taxon']=='Actinidia chinensis var. chinensis' for b in records['blocks'])
B={(b['cultivar'],b['region']):b for b in records['blocks']}
group=bpy.data.node_groups['FE M2c | VolumetricCellSolids | shared']
assert any(o.name.startswith('M2b vascular DIAGNOSTIC') for o in bpy.data.objects)
arch=bpy.data.texts['M2c source-calibrated 3D cell solids, ARTIST packing.json']
assert json.loads(arch.as_string())==records
report={'schema':'fruitengine.m2c.saved_scene.v1','version':bpy.app.version_string,
  'source_scope':'JEON2024 TABLE5 diameter ONLY','warnings':records['warnings'],
  'volume_evaluations':[],'section_evaluations':[]}
base=bpy.data.scenes['06 | M2c | 3D CELL SOLIDS / source diameters']
macro=bpy.data.scenes['08 | M2c | mixed outer pericarp 3D macro']
sec=bpy.data.scenes['07 | M2c | exact TWO ORTHOGONAL SECTIONS']
for sc in (base,macro,sec):
 assert sc.unit_settings.system=='METRIC'
 assert abs(sc.unit_settings.scale_length-.001)<1e-8
objs=[o for o in base.objects if o.name.startswith('M2c volume')]
macro_objs=[o for o in macro.objects if o.name.startswith('M2c MACRO')]
assert (len(objs),len(macro_objs))==(8,4)
for obj in objs+macro_objs:
 cultivar=obj['fe_m2c_cultivar'];region=obj['fe_m2c_region']
 row=B[(cultivar,region if region in ('core','inner_pericarp') else 'outer_pericarp_MIXED_ARTIST')]
 source=[c for c in row['cells'] if c['region']==region]
 assert len(source)==len(obj.data.vertices)==obj['fe_m2c_cell_count']
 assert obj.modifiers[0].node_group==group
 assert obj.get('fe_m2c_cell_positions_and_ellipsoid_aspect')=='ARTIST'
 attr=obj.data.attributes['fe_m2c_half_axes_mm'];ids=obj.data.attributes['fe_m2c_cell_id']
 for i,(v,c) in enumerate(zip(obj.data.vertices,source)):
  assert ids.data[i].value==c['id']
  assert all(abs(v.co[k]-c['center_mm'][k])<3e-6 for k in range(3))
  assert all(abs(attr.data[i].vector[k]-c['half_axes_mm'][k])<3e-6 for k in range(3))
 bpy.context.window.scene=base if obj in objs else macro
 deps=bpy.context.evaluated_depsgraph_get()
 deps.update()
 evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh()
 assert len(mesh.vertices)>40*len(source), (obj.name,len(mesh.vertices),len(source))
 assert len(mesh.polygons)>40*len(source)
 bm=bmesh.new();bm.from_mesh(mesh)
 nonmanifold=sum(1 for edge in bm.edges if not edge.is_manifold)
 bm.free()
 assert nonmanifold==0,(obj.name,nonmanifold)
 report['volume_evaluations'].append({'name':obj.name,'cultivar':cultivar,'region':region,
   'source_row':source[0]['source_row'],'mean_equivalent_diameter_mm':source[0]['mean_diameter_mm'],
   '3d_cell_solids_ARTIST':len(source),'evaluated_mesh_vertices':len(mesh.vertices),
   'evaluated_mesh_faces':len(mesh.polygons),'nonmanifold_edges':nonmanifold})
 evaluated.to_mesh_clear()
sections=[o for o in sec.objects if o.name.startswith('M2c SECTION')]
assert len(sections)==4
for obj in sections:
 cultivar=obj['fe_m2c_cultivar'];axis=int(obj['fe_m2c_normal_axis'])
 row=B[(cultivar,'outer_pericarp_MIXED_ARTIST')]
 cdict={c['id']:c for c in row['cells']}
 expected={c['id'] for c in row['cells'] if 1-(c['center_mm'][axis]/c['half_axes_mm'][axis])**2>1e-12}
 assert len(obj.data.polygons)==len(expected)
 assert obj.get('fe_m2c_projection')=='TO_XZ_DISPLAY_PANEL_FROM_ORIGINAL_COORDINATE_PLANE'
 ids=obj.data.attributes['fe_m2c_cell_id'];ox=obj['fe_m2c_panel_origin_x'];oz=obj['fe_m2c_panel_origin_z']
 seen=set();maxerr=0.
 for i,poly in enumerate(obj.data.polygons):
  cid=int(ids.data[i].value);seen.add(cid);c=cdict[cid]
  axes=[j for j in range(3) if j!=axis];q=1-(c['center_mm'][axis]/c['half_axes_mm'][axis])**2
  rr=[c['half_axes_mm'][j]*math.sqrt(q) for j in axes]
  assert len(poly.vertices)==32
  for vi in poly.vertices:
   v=obj.data.vertices[vi].co
   e=abs(((v.x-ox-c['center_mm'][axes[0]])/rr[0])**2 + ((v.z-oz-c['center_mm'][axes[1]])/rr[1])**2-1)
   maxerr=max(maxerr,e)
   assert e<8e-4,(obj.name,cid,e)
 assert seen==expected
 report['section_evaluations'].append({'name':obj.name,'axis':axis,'cultivar':cultivar,
  'matching_3d_cell_intersections':len(expected),'max_ellipse_equation_error':maxerr})
report['summary']={'volume_examples':len(objs),'macro_examples':len(macro_objs),
 'physical_3d_cell_solids':sum(len(x['cells']) for x in records['blocks']),
 'source_exact_sections':len(sections),
 'total_cell_intersection_faces':sum(r['matching_3d_cell_intersections'] for r in report['section_evaluations'])}
Path(a.out).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('M2C_BLENDER_VALIDATION_PASS',json.dumps(report['summary']))
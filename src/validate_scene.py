#!/usr/bin/env python3
"""Source-backed verification of an M1a scene already loaded by Blender."""
import bpy, json
sc=bpy.context.scene
mode=sc.get('visible_mode')
assert mode in ('whole','longitudinal','transverse','anatomy'),f'Unknown mode {mode!r}'
groups=[o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='NODES' for m in o.modifiers)]
assert len(groups)==1,f'Need one live Geometry Nodes seed instance carrier; got {len(groups)}'
name=groups[0].name
assert 'achenes' in name.lower(),name
cap=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Exposed tissue')]
assert len(cap)==(0 if mode in ('whole','anatomy') else 1),'Cap object count mismatch'
if cap:
    assert cap[0].data.color_attributes.get('tissue_color') is not None,'Missing 3D tissue color data'
    assert len(cap[0].data.polygons)>1000
ring=[o for o in bpy.data.objects if o.name.startswith('Vascular core')]
branch=[o for o in bpy.data.objects if o.name.startswith('Vascular network')]
assert len(ring)==len(branch)==1,'Missing central vascular ring/branch objects'
assert branch[0].type=='CURVE' and len(branch[0].data.splines)>450,'No full connected branch geometry'
assert sc.get('not_scientifically_calibrated'),'Missing calibration disclosure'
print('SCENE_VALIDATED',json.dumps({'mode':mode,'live_geometry_nodes':len(groups),'cap_triangles':len(cap[0].data.polygons) if cap else 0,'vascular_branches':len(branch[0].data.splines)}),flush=True)
#!/usr/bin/env python3
"""Independent readback validator for actual saved Fruit Engine .blend.

Requires -b path.blend --python this_script -- --out validation.json
"""
import sys,json,math,collections
from pathlib import Path
import bpy

def check(condition,msg):
    if not condition:raise AssertionError(msg)

def main():
    output=None
    if '--' in sys.argv:
        args=sys.argv[sys.argv.index('--')+1:]
        for i,x in enumerate(args):
            if x=='--out':output=Path(args[i+1])
    scenes=list(bpy.data.scenes)
    check(len(scenes)==2,f'Expected 2 scenes, got {len(scenes)}')
    check(all(abs(s.unit_settings.scale_length-.001)<1e-7 for s in scenes),'Physical unit not mm')
    groups=[g for g in bpy.data.node_groups if g.bl_idname=='GeometryNodeTree']
    check(len(groups)==2,f'Expected 2 GN groups: {len(groups)}')
    region=next(g for g in groups if 'TissueRegionMaterials' in g.name)
    scatter=next(g for g in groups if 'ScatterSurfaceAttachment' in g.name)
    check(any(n.bl_idname=='GeometryNodeSetMaterialIndex' for n in region.nodes),'Shared field/material mapping not genuine')
    check(any(n.bl_idname=='GeometryNodeInstanceOnPoints' for n in scatter.nodes),'Shared scatter group not genuine')
    specimens={}
    for cultivar,radius,bounds in [('Sweet Gold',21.3,(3.6,14.0,21.3)),('Jecy Gold',20.7,(3.0,11.6,20.7))]:
        obj=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(f'Kiwi {cultivar}'))
        gn=[m for m in obj.modifiers if m.type=='NODES']
        check(len(gn)==1 and gn[0].node_group is region,f'Region group not reused for {cultivar}')
        check(len(obj.data.materials)==3,f'Wrong regional material slots for {cultivar}')
        check(all(f in range(3) for f in (a.value for a in obj.data.attributes['fe_region_id'].data)), 'invalid tissue group ID')
        centerx=-58 if cultivar=='Sweet Gold' else 0
        xs=[math.hypot(v.co.x-centerx,v.co.z) for v in obj.data.vertices]
        unique=sorted(set(round(x,3) for x in xs if x>0.05))
        check(all(any(abs(t-u)<.001 for u in unique) for t in bounds), f'Kiwi radial bounds wrong {cultivar}, {unique[:10]}')
        check(abs(max(xs)-radius)<.001, f'Wrong absolute radius {cultivar}')
        deps=bpy.context.evaluated_depsgraph_get()
        ob_eval=obj.evaluated_get(deps);mesh=ob_eval.to_mesh()
        hist=collections.Counter(poly.material_index for poly in mesh.polygons)
        ob_eval.to_mesh_clear()
        check(all(hist.get(i)>0 for i in range(3)),f'GN did not assign all tissue material indices {cultivar}')
        specimens[cultivar]={"radius_mm":radius,"measured_boundaries_mm":bounds,"material_face_counts":dict(hist)}

    obj=next(o for o in bpy.data.objects if o.name.startswith('Camarosa | measured H W'))
    check([m.node_group for m in obj.modifiers if m.type=='NODES']==[region], 'Strawberry not using same shared region group')
    verts=[v.co for v in obj.data.vertices]
    z=[x.z for x in verts];width=max(math.hypot(v.x-59,v.y) for v in verts)*2
    check(abs(max(z)-24)<1e-6 and abs(min(z)+24)<1e-6,'Camarosa height not 48mm')
    check(abs(width-32.5)<.015,'Camarosa measured width mismatch')
    anchors=next(o for o in bpy.data.objects if o.name.startswith('Camarosa | mean rounded anchors'))
    check(len(anchors.data.vertices)==326,'Expected rounded 325.6=326 anchors')
    check([m.node_group for m in anchors.modifiers if m.type=='NODES']==[scatter], 'Surface attachment GN not shared')
    deps=bpy.context.evaluated_depsgraph_get()
    evaluated=anchors.evaluated_get(deps);m=evaluated.to_mesh()
    marker_vertices=len(m.vertices);evaluated.to_mesh_clear()
    check(marker_vertices>=326*12,'GN achene marker geometry not instantiated')
    specimens['Camarosa']={"measured_length_mm":48.,"measured_width_mm":32.5,
                           "mean_achene_count":325.6,"schematic_marker_count":326,
                           "evaluated_marker_vertices":marker_vertices}

    micro=[s for s in scenes if s.name.startswith('02 |')][0]
    circles=[o for o in micro.objects if o.type=='MESH' and 'fe_diameter_mm' in o]
    check(len(circles)==8,f'Expected 8 physical cell-diameter proxies, got {len(circles)}')
    diameters=sorted(round(o['fe_diameter_mm'],4) for o in circles)
    expected=sorted([.0473,.0959,.0514,.1646,.0474,.0855,.0653,.1815])
    check(diameters==expected,f'Cell measurement mismatch: {diameters}')
    for obj in circles:
        pts=[(v.co.x,v.co.z) for v in obj.data.vertices]
        xcenter=sum(x for x,z in pts[1:])/len(pts[1:]);zcenter=sum(z for x,z in pts[1:])/len(pts[1:])
        diameter=max(2*math.hypot(x-xcenter,z-zcenter) for x,z in pts[1:])
        check(abs(diameter-float(obj['fe_diameter_mm']))<1e-6,f'Cell size geometry mismatch {obj.name}')
    result={"status":"PASS","blender_version":bpy.app.version_string,"scene_count":len(scenes),
      "shared_gn_groups":[g.name for g in groups],"shared_material_group_instances":3,
      "mm_per_BU":1.0,"specimens":specimens,
      "micro_diameters_mm":diameters,"micro_proxies_are_not_histology":True,
      "unmeasured_values_remain_unset":True}
    if output:
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(result,indent=2,ensure_ascii=False))
    print('FRUIT_ENGINE_VALIDATION_PASS',json.dumps(result,ensure_ascii=False))

if __name__=='__main__': main()
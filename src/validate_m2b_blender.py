#!/usr/bin/env python3
"""Independently validate saved M2b Blender module geometry, not just JSON metadata.

Usage: blender -b fruit-platform-m2b.blend --python src/validate_m2b_blender.py --
       --out outputs/validation-m2b.json
"""
from __future__ import annotations
import argparse,json,math,sys
from pathlib import Path
from collections import Counter
import bpy


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True)
    a=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
    scenes={s.name:s for s in bpy.data.scenes}
    main_scene=scenes['01 | Fruit Platform | 4 independent contexts']
    cell_scene=scenes['04 | M2b | 3D cell diameter proxies NOT histology']
    vessel_scene=scenes['05 | M2b | vascular graph QUALITATIVE']
    assert math.isclose(main_scene.unit_settings.scale_length,.001,abs_tol=1e-9)
    expected={
        'cam-a':{'measured':False,'regions':{0:7800}},
        'cam-b':{'measured':False,'regions':{0:7800}},
        'sweet':{'measured':True,'regions':{0:180,1:180,2:180}},
        'jecy':{'measured':True,'regions':{0:180,1:180,2:180}},
    }
    groups={g.name:g for g in bpy.data.node_groups if g.bl_idname=='GeometryNodeTree'}
    assert len(groups)==5,groups.keys()   # M2a two + M2b three
    gn_tissue=next(g for g in groups.values() if g.get('fe_category')=='ANATOMY_TISSUE_REGION')
    gn_cells=next(g for g in groups.values() if g.get('fe_category')=='ANATOMY_CELL_POPULATION')
    gn_veins=next(g for g in groups.values() if g.get('fe_category')=='ANATOMY_VASCULAR_GRAPH')
    report={'schema':'fruit_platform.m2b.validate','status':'PASS','Blender':bpy.app.version_string,
            'scene_units_mm_per_BU':main_scene['fe_mm_per_BLENDER_UNIT'],
            'shared_node_groups':{g.name:len(g.nodes) for g in groups.values()},
            'tissue_regions':{},'cell_populations':{},'vessels':{},
            'warning':'Measured diameters only, artist packing/shape, vessel routes qualitative'}
    bpy.context.window.scene=main_scene
    main_scene.frame_set(1)
    dg=bpy.context.evaluated_depsgraph_get()
    bodies=[o for o in main_scene.objects if o.get('fe_m2b_tissue_evidence')]
    assert len(bodies)==4
    for ob in bodies:
        p=expected[ob['fe_instance_id']]
        mod=[x for x in ob.modifiers if x.type=='NODES' and x.node_group==gn_tissue]
        assert len(mod)==1
        old=ob.data.attributes.get('fe_region_id')
        assert old is not None
        for key in ('fe_m2b_center_x_mm','fe_m2b_core_mm','fe_m2b_inner_mm','fe_m2b_has_radial'):
            assert ob.data.attributes.get(key) is not None
        assert bool(ob.data.attributes['fe_m2b_has_radial'].data[0].value) == p['measured']
        assert ('MEASURED' in ob['fe_m2b_tissue_evidence']) == p['measured'] or not p['measured']
        eva=ob.evaluated_get(dg);mesh=eva.to_mesh()
        attr=mesh.attributes.get('fe_m2b_tissue_region')
        assert attr is not None and attr.domain=='FACE'
        counts=dict(Counter(int(v.value) for v in attr.data))
        assert counts==p['regions'],(ob.name,counts,p)
        if p['measured']:
            orig=[int(v.value) for v in old.data]
            got=[int(v.value) for v in attr.data]
            assert got==orig,(ob.name,'measured face mapping mismatch')
        eva.to_mesh_clear()
        report['tissue_regions'][ob['fe_instance_id']]={
            'faces_by_id':counts,'evidence':ob['fe_m2b_tissue_evidence'],
            'source':ob['fe_m2b_source_rows']}
    bpy.context.window.scene=cell_scene
    cell_scene.frame_set(1);dg=bpy.context.evaluated_depsgraph_get()
    samples=[o for o in cell_scene.objects if o.get('fe_m2b_module')=='CellPopulation3D']
    assert len(samples)==8
    diameters={'sweet':{'core':.0473,'inner_pericarp':.0959,'outer_pericarp_small':.0514,'outer_pericarp_large':.1646},
               'jecy':{'core':.0474,'inner_pericarp':.0855,'outer_pericarp_small':.0653,'outer_pericarp_large':.1815}}
    source_groups=set()
    for ob in samples:
        instance=ob['fe_m2b_instance_id'];region=ob['fe_m2b_region']
        assert instance in diameters
        d=diameters[instance][region]
        assert math.isclose(d,float(ob['fe_m2b_mean_diameter_mm']),abs_tol=1e-8)
        assert len([m for m in ob.modifiers if m.type=='NODES' and m.node_group==gn_cells])==1
        input_attr=ob.data.attributes.get('fe_m2b_cell_diameter_mm')
        assert input_attr is not None and input_attr.domain=='POINT'
        assert all(math.isclose(v.value,d,abs_tol=1e-8) for v in input_attr.data)
        count=len(ob.data.vertices)
        assert count==ob['fe_m2b_sample_point_count']
        e=ob.evaluated_get(dg);mesh=e.to_mesh()
        assert len(mesh.vertices)==86*count,(ob.name,len(mesh.vertices),count)
        span=max(v.co.x for v in mesh.vertices)-min(v.co.x for v in mesh.vertices)
        expected_span=float(ob['fe_m2b_sample_span_mm'])
        assert math.isclose(span,expected_span,abs_tol=2.5e-6),(ob.name,span,expected_span)
        assert ob['fe_m2b_evidence_status']=='ILLUSTRATIVE_3D_LATTICE_NOT_HISTOLOGY'
        assert ob['fe_m2b_source_ids'].startswith('R')
        report['cell_populations'][instance+':'+region]={
            'mean_diameter_mm':d,'sampled_3d_proxy_count':count,
            'evaluated_mesh_vertices':len(mesh.vertices),
            'physical_span_mm':span,'expected_span_mm':expected_span,
            'source_row':ob['fe_m2b_source_ids'],
            'kind':'ILLUSTRATIVE_DIAGNOSTIC_NOT_CELL_PACKING'}
        e.to_mesh_clear();source_groups.add(ob.modifiers[0].node_group.name)
    assert source_groups=={gn_cells.name}
    assert not any(o.get('fe_m2b_instance_id','').startswith('cam') for o in samples)
    bpy.context.window.scene=vessel_scene
    vessel_scene.frame_set(1);dg=bpy.context.evaluated_depsgraph_get()
    routes=[o for o in vessel_scene.objects if o.get('fe_m2b_module')=='VascularGraph']
    assert len(routes)==2
    assert set(o['fe_m2b_instance_id'] for o in routes)=={'cam-a','cam-b'}
    for ob in routes:
        assert ob['fe_m2b_source_ids']=='S02'
        assert ob['fe_m2b_source_taxon']=='Fragaria × ananassa'
        assert not ob['fe_m2b_radii_measured']
        assert len([m for m in ob.modifiers if m.node_group==gn_veins])==1
        graph=json.loads(ob['fe_m2b_typed_edges'])
        assert any(e[2]=='branches_to' for e in graph)
        assert ob['fe_m2b_evidence_status']=='QUALITATIVE_TOPOLOGY_ONLY_ARTIST_PATHS'
        evaluated=ob.evaluated_get(dg);me=evaluated.to_mesh()
        assert len(me.vertices)>100 and len(me.polygons)>50
        report['vessels'][ob['fe_m2b_instance_id']]={
             'source':'S02','display_radius_is_artist':True,
             'typed_topology_edges':len(graph),'diagnostic_splines':len(ob.data.splines),
             'evaluated_mesh_vertices':len(me.vertices)}
        evaluated.to_mesh_clear()
    assert not any('Actinidia' in ob.get('fe_m2b_source_taxon','') for ob in routes)
    assert len(report['tissue_regions'])==4
    assert len(report['cell_populations'])==8
    assert len(report['vessels'])==2
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('M2B_SAVED_BLEND_VALIDATION_OK',json.dumps({'tissues':4,'cell_populations':8,
        'vascular_diagrams':2,'groups_total':len(groups),'evaluated_cell_diameters_measured':8}))

if __name__=='__main__':main()
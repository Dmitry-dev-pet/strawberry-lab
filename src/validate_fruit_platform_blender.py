#!/usr/bin/env python3
"""Read back a saved M2a Blender scene and validate actual evaluated GN."""
import sys
import argparse
import json
from pathlib import Path
import math
import bpy


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True)
    args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
    scene=bpy.data.scenes['01 | Fruit Platform | 4 independent contexts']
    micro=bpy.data.scenes['02 | Cell size calibration, not histology']
    assert math.isclose(scene.unit_settings.scale_length,.001,rel_tol=1e-6)
    assert scene['fe_mm_per_BLENDER_UNIT']==1.0
    assert scene['fe_independent_instance_count']==4
    groups={g.name:g for g in bpy.data.node_groups if g.bl_idname=='GeometryNodeTree'}
    tissue=next(g for name,g in groups.items() if name.startswith('FE | TissueRegionMaterials'))
    scatter=next(g for name,g in groups.items() if name.startswith('FE | ScatterSurfaceAttachmentMarkers'))
    assert len(groups)==2, sorted(groups)
    bodies=[o for o in scene.objects if o.type=='MESH' and o.get('fe_organ_id') in ('receptacle','pericarp_tissue_zones')]
    anchors=[o for o in scene.objects if o.type=='MESH' and o.get('fe_organ_id')=='surface_achenes']
    gauges=[o for o in micro.objects if o.type=='MESH' and o.get('fe_organ_id')=='cell_size_gauges']
    assert len(bodies)==4 and len(anchors)==2 and len(gauges)==8
    assert set(o['fe_instance_id'] for o in bodies)=={'cam-a','cam-b','sweet','jecy'}
    assert all(any(m.type=='NODES' and m.node_group==tissue for m in o.modifiers) for o in bodies)
    assert all(any(m.type=='NODES' and m.node_group==scatter for m in o.modifiers) for o in anchors)
    assert len([c for c in scene.collection.children if c.name.startswith('Fruit | ')])==4
    assert not any('Cutter' in g.name for g in groups.values())
    expected={
        'cam-a':{'height':48.0,'width':32.5,'source':'ARIZA2011'},
        'cam-b':{'height':48.0,'width':32.5,'source':'ARIZA2011'},
        'sweet':{'bounds':[3.6,14.0,21.3],'source':'JEON2024'},
        'jecy':{'bounds':[3.0,11.6,20.7],'source':'JEON2024'},
    }
    report={'status':'PASS','scene':scene.name,'scene_units':scene.unit_settings.scale_length,
            'node_groups':{g.name:len(g.nodes) for g in groups.values()},'contexts':{},
            'gauges':[], 'marker_instance_counts':{}}
    for ob in bodies:
        p=expected[ob['fe_instance_id']]
        assert ob['fe_source_rows'] and len(ob['fe_plan_sha256'])==64
        if ob['fe_organ_id']=='receptacle':
            v=[ob.matrix_world@v.co for v in ob.data.vertices]
            width=max(x.x for x in v)-min(x.x for x in v)
            height=max(x.z for x in v)-min(x.z for x in v)
            assert math.isclose(height,p['height'],abs_tol=1e-5),height
            assert math.isclose(width,p['width'],abs_tol=.02),width
            report['contexts'][ob['fe_instance_id']]={'height_mm':height,'width_mm':width}
        else:
            bounds=list(ob['fe_radial_boundaries_mm'])
            assert all(math.isclose(b,r,abs_tol=1e-8) for b,r in zip(bounds,p['bounds']))
            a=ob.data.attributes['fe_region_id']
            counts={i:sum(1 for v in a.data if v.value==i) for i in range(3)}
            assert counts=={0:180,1:180,2:180},counts
            report['contexts'][ob['fe_instance_id']]={'bounds_mm':bounds,'region_polygons':counts}
    bpy.context.window.scene=scene
    scene.frame_set(1);dg=bpy.context.evaluated_depsgraph_get()
    for ob in anchors:
        assert len(ob.data.vertices)==326
        evaluated=ob.evaluated_get(dg)
        emesh=evaluated.to_mesh()
        count=len(emesh.vertices)
        evaluated.to_mesh_clear()
        assert count==326*12,(ob.name,count)
        report['marker_instance_counts'][ob['fe_instance_id']]=count//12
    ag={o['fe_instance_id']:o for o in anchors}
    assert tuple(v.co for v in ag['cam-a'].data.vertices)!=tuple(v.co for v in ag['cam-b'].data.vertices)
    for o in gauges:
        vertices=[o.matrix_world@v.co for v in o.data.vertices]
        span=max(v.x for v in vertices)-min(v.x for v in vertices)
        expected_d=float(o['fe_gauge_diameter_mm'])
        assert math.isclose(span,expected_d,abs_tol=2e-7),(o.name,span,expected_d)
        report['gauges'].append({'name':o.name,'measured_diameter_mm':span,'source':o['fe_source_rows']})
    assert set(g['source'] for g in report['gauges'])
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print('FRUIT_PLATFORM_SAVED_BLEND_VALIDATION_OK')
    print(json.dumps({'bodies':len(bodies),'marker_objects':len(anchors),
                      'gauges':len(gauges),'shared_GN_groups':len(groups)},ensure_ascii=False))


if __name__=='__main__': main()
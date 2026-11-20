#!/usr/bin/env python3
"""M2b shared, source-scope-aware Geometry Nodes from an M2a editable .blend.

THREE functional GN groups are independently created:
  1) Tissue region sampling on all four fruit bodies;
  2) source-mean cell-diameter proxy spheres in illustrative 3D samples (kiwi only);
  3) typed-graph-inspired vascular route curve rendering (strawberry ONLY,
     shape/path/radius explicitly ARTIST and never a scientific diameter).

This is NOT real histology. Does not import Frucht source/tree. Maintains M2a.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import math
import sys

import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fruit_platform import make_context, standard_registry, FruitPlan, plans_digest
from fruit_morphometry import load_catalog
from fruit_biocomponents import (tissue_contract, measured_cell_populations,
                                  vascular_contract, anatomical_components)
from build_fruit_engine_blender import mat, font_object, camera_and_light, tube
from fe_geometry import strawberry_shape_radius

SCALES=('core','inner_pericarp','outer_pericarp_small','outer_pericarp_large')


def ng_socket(group,name,kind='NodeSocketFloat',direction='INPUT',default=None):
    s=group.interface.new_socket(name=name,in_out=direction,socket_type=kind)
    if default is not None:s.default_value=default
    return s


def mod_socket(mod,group,name,value):
    sockets=[s for s in group.interface.items_tree
             if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name==name]
    if len(sockets)!=1:raise RuntimeError('Cannot resolve GN socket '+name)
    mod[sockets[0].identifier]=value


def face_attr(mesh, name, value):
    a=mesh.attributes.get(name) or mesh.attributes.new(name=name,type='FLOAT',domain='FACE')
    for item in a.data:item.value=float(value)
    return a


def group_region_field():
    """Reusable region operator; all per-fruit parameters are FACE named attrs."""
    ng=bpy.data.node_groups.new('FE M2b | TissueRegionField | shared','GeometryNodeTree')
    ng_socket(ng,'Geometry','NodeSocketGeometry')
    ng_socket(ng,'Geometry','NodeSocketGeometry','OUTPUT')
    n=ng.nodes;L=ng.links
    gi=n.new('NodeGroupInput');gi.location=(-1000,160)
    go=n.new('NodeGroupOutput');go.location=(750,120)
    position=n.new('GeometryNodeInputPosition');position.location=(-990,-190)
    values={}
    for z,key in enumerate(('fe_m2b_center_x_mm','fe_m2b_core_mm','fe_m2b_inner_mm','fe_m2b_has_radial')):
        nd=n.new('GeometryNodeInputNamedAttribute');nd.data_type='FLOAT'
        nd.inputs['Name'].default_value=key;nd.location=(-1040,-420-z*150)
        values[key]=nd.outputs['Attribute']
    origin=n.new('ShaderNodeCombineXYZ');origin.location=(-750,-340)
    L.new(values['fe_m2b_center_x_mm'],origin.inputs['X'])
    dist=n.new('ShaderNodeVectorMath');dist.operation='DISTANCE';dist.location=(-600,-100)
    L.new(position.outputs['Position'],dist.inputs[0]);L.new(origin.outputs['Vector'],dist.inputs[1])
    checks=[]
    for i,key in enumerate(('fe_m2b_core_mm','fe_m2b_inner_mm')):
        comp=n.new('FunctionNodeCompare');comp.data_type='FLOAT';comp.operation='GREATER_THAN'
        comp.location=(-350,-120-i*170)
        L.new(dist.outputs['Value'],comp.inputs['A'])
        L.new(values[key],comp.inputs['B']);checks.append(comp)
    add=n.new('ShaderNodeMath');add.operation='ADD';add.location=(-100,-180)
    L.new(checks[0].outputs['Result'],add.inputs[0]);L.new(checks[1].outputs['Result'],add.inputs[1])
    enable=n.new('FunctionNodeCompare');enable.data_type='FLOAT';enable.operation='GREATER_THAN';enable.location=(-320,-450)
    L.new(values['fe_m2b_has_radial'],enable.inputs['A']);enable.inputs['B'].default_value=.5
    sw=n.new('GeometryNodeSwitch');sw.input_type='INT';sw.location=(100,-120)
    sw.inputs['False'].default_value=0  # unknown fruit => do not infer nested tissue widths
    L.new(enable.outputs['Result'],sw.inputs['Switch'])
    L.new(add.outputs['Value'],sw.inputs['True'])
    store=n.new('GeometryNodeStoreNamedAttribute');store.data_type='INT';store.domain='FACE';store.location=(390,80)
    store.inputs['Name'].default_value='fe_m2b_tissue_region'
    L.new(gi.outputs['Geometry'],store.inputs['Geometry']);L.new(sw.outputs['Output'],store.inputs['Value'])
    L.new(store.outputs['Geometry'],go.inputs['Geometry'])
    ng['fe_category']='ANATOMY_TISSUE_REGION'
    ng['fe_evidence_scope']='Measured only A. chinensis radial transect. Unknown Fragaria subregions'
    ng['fe_input_contract']='fe_m2b_has_radial/center_x/core/inner FACE named attributes'
    return ng


def group_cell_populations():
    """Shared GN instancing: source mean diameter via per-POINT named attribute.

    Input point POSITIONS are ARTIST lattice generated upstream in independent
    Python primitive. GN constructs and sizes individual real 3D proxy spheres.
    """
    ng=bpy.data.node_groups.new('FE M2b | CellPopulation3D | shared DIAGNOSTIC','GeometryNodeTree')
    ng_socket(ng,'Geometry','NodeSocketGeometry')
    ng_socket(ng,'Geometry','NodeSocketGeometry','OUTPUT')
    n=ng.nodes;L=ng.links
    inp=n.new('NodeGroupInput');inp.location=(-480,120)
    out=n.new('NodeGroupOutput');out.location=(730,110)
    attr=n.new('GeometryNodeInputNamedAttribute');attr.data_type='FLOAT';attr.location=(-470,-170)
    attr.inputs['Name'].default_value='fe_m2b_cell_diameter_mm'
    xyz=n.new('ShaderNodeCombineXYZ');xyz.location=(-210,-120)
    for axis in 'XYZ':L.new(attr.outputs['Attribute'],xyz.inputs[axis])
    sphere=n.new('GeometryNodeMeshUVSphere');sphere.location=(-210,-300)
    sphere.inputs['Segments'].default_value=12;sphere.inputs['Rings'].default_value=8
    sphere.inputs['Radius'].default_value=.5 # diameter exactly = attribute mm
    inst=n.new('GeometryNodeInstanceOnPoints');inst.location=(80,100)
    L.new(inp.outputs['Geometry'],inst.inputs['Points'])
    L.new(sphere.outputs['Mesh'],inst.inputs['Instance'])
    L.new(xyz.outputs['Vector'],inst.inputs['Scale'])
    real=n.new('GeometryNodeRealizeInstances');real.location=(320,100)
    L.new(inst.outputs['Instances'],real.inputs['Geometry'])
    visible_mat=mat('M2b SHARED | 3D proxy cell color (not histology)',(.37,.57,.18),roughness=.42)
    setmat=n.new('GeometryNodeSetMaterial');setmat.location=(520,100)
    setmat.inputs['Material'].default_value=visible_mat
    L.new(real.outputs['Geometry'],setmat.inputs['Geometry'])
    L.new(setmat.outputs['Geometry'],out.inputs['Geometry'])
    ng['fe_category']='ANATOMY_CELL_POPULATION'
    ng['fe_measure']='Cell mean diameter from Jeon et al. 2024 Table 5'
    ng['fe_not_measure']='Sphere shape, point positions, 3-D packing and count are ARTIST proxy'
    ng['fe_input_contract']='Geometry POINTS and fe_m2b_cell_diameter_mm POINT float attribute'
    return ng


def group_vascular_graph():
    """Shared curve-to-mesh emitter. Artist thickness explicitly not biological."""
    ng=bpy.data.node_groups.new('FE M2b | VascularGraph | shared QUALITATIVE','GeometryNodeTree')
    ng_socket(ng,'Geometry','NodeSocketGeometry')
    ng_socket(ng,'Geometry','NodeSocketGeometry','OUTPUT')
    n=ng.nodes;L=ng.links
    inp=n.new('NodeGroupInput');inp.location=(-330,30)
    out=n.new('NodeGroupOutput');out.location=(340,30)
    circle=n.new('GeometryNodeCurvePrimitiveCircle');circle.location=(-170,-160)
    circle.inputs['Resolution'].default_value=8
    circle.inputs['Radius'].default_value=.16  # artist diagnostic radius, no data source
    cm=n.new('GeometryNodeCurveToMesh');cm.location=(80,60)
    L.new(inp.outputs['Geometry'],cm.inputs['Curve'])
    L.new(circle.outputs['Curve'],cm.inputs['Profile Curve'])
    cm.inputs['Fill Caps'].default_value=True
    L.new(cm.outputs['Mesh'],out.inputs['Geometry'])
    ng['fe_category']='ANATOMY_VASCULAR_GRAPH'
    ng['fe_not_measured']='ALL path points and display radii are artist diagrams, not vessel histometrics'
    return ng


def tag(ob,instance,kind,evidence,source):
    ob['fe_m2b_instance_id']=instance
    ob['fe_m2b_module']=kind
    ob['fe_m2b_evidence_status']=evidence
    ob['fe_m2b_source_ids']=source
    return ob


def create_cells_scene(plans,group):
    scene=bpy.data.scenes.new('04 | M2b | 3D cell diameter proxies NOT histology')
    camera_and_light(scene,'M2b cells',ortho=8.9,res=(1820,920))
    scene.cycles.samples=12
    scene['fe_m2b_cell_scope']='MEASURED_DIAMETER_ARTIST_PACKING_NOT_HISTOLOGY'
    ink=bpy.data.materials.get('FE M2a | ink and labels')
    palettes=[(.91,.68,.22),(.52,.78,.38),(.65,.71,.28),(.93,.48,.23)]
    mats=[mat('M2b cell diameter proxy '+str(i),col,roughness=.49) for i,col in enumerate(palettes)]
    xs=(-2.98,-.99,.99,2.98)
    rows=[p for p in plans if 'Actinidia' in p.context.specimen.taxon]
    all_cells=[]
    font_object(scene,'3D CELL POPULATIONS   |   SOURCE-MEASURED DIAMETER',0,2.02,.19,ink)
    font_object(scene,'Shape and packing: ARTIST diagnostic. 1 Blender unit = 1 mm.',0,1.78,.11,ink)
    for ri,plan in enumerate(rows):
        records=measured_cell_populations(plan)
        z=.83-ri*2.04
        font_object(scene,plan.context.specimen.cultivar+' / '+plan.context.specimen.taxon,0,z+.61,.13,ink)
        for k,c in enumerate(records):
            # Geometry is ARTIST lattice; measured diameter is explicit point attr.
            nx,ny,nz=c.sample_count_xyz
            step=c.mean_diameter_mm*c.artist_spacing_factor
            verts=[((ix-(nx-1)/2)*step,(iy-(ny-1)/2)*step,(iz-(nz-1)/2)*step)
                   for iz in range(nz) for iy in range(ny) for ix in range(nx)]
            mesh=bpy.data.meshes.new('M2b proxy lattice points');mesh.from_pydata(verts,[],[])
            attr=mesh.attributes.new(name='fe_m2b_cell_diameter_mm',type='FLOAT',domain='POINT')
            for point in attr.data:point.value=c.mean_diameter_mm
            ob=bpy.data.objects.new('M2b | '+plan.context.instance_id+' | '+c.region,mesh)
            scene.collection.objects.link(ob);ob.location=(xs[k],0,z)
            mesh.materials.append(mats[k])
            m=ob.modifiers.new('FE shared 3D cell population','NODES');m.node_group=group
            tag(ob,plan.context.instance_id,'CellPopulation3D',c.arrangement_status,c.source_row)
            ob['fe_m2b_region']=c.region
            ob['fe_m2b_mean_diameter_mm']=c.mean_diameter_mm
            ob['fe_m2b_sample_point_count']=c.points_count
            ob['fe_m2b_sample_span_mm']=c.occupied_span_mm
            ob['fe_m2b_artist_spacing']=c.artist_spacing_factor
            all_cells.append(ob)
            label=c.region.replace('outer_pericarp_','outer-').replace('_',' ').upper()
            font_object(scene,label,xs[k],z-.49,.115,ink)
            font_object(scene,f'{c.mean_diameter_mm*1000:.1f} um | {nx}x{ny}x{nz}',xs[k],z-.66,.115,ink)
    # physical 0.5 mm scale bar at bottom
    # Individual source diameters are printed below each proxy sample; no fake density scale.
    return scene,all_cells


def make_multi_spline_curve(scene,name,poly_points):
    cu=bpy.data.curves.new(name,'CURVE')
    cu.dimensions='3D';cu.resolution_u=1
    for coords in poly_points:
        spl=cu.splines.new('POLY');spl.points.add(len(coords)-1)
        for v,co in zip(spl.points,coords):v.co=(*co,1)
    ob=bpy.data.objects.new(name,cu)
    scene.collection.objects.link(ob)
    return ob


def make_vascular_scene(plans,group):
    scene=bpy.data.scenes.new('05 | M2b | vascular graph QUALITATIVE')
    camera_and_light(scene,'M2b vascular',ortho=142,res=(1500,740))
    scene.cycles.samples=10
    ink=bpy.data.materials.get('FE M2a | ink and labels')
    yellow=mat('M2b artist-only vessel lines',(.95,.72,.16),.43)
    scene['fe_vascular_scope']='QUALITATIVE_PATHS_DIAGRAM; ALL DIAMETERS UNKNOWN'
    font_object(scene,'VASCULAR GRAPH   |   S02 topology, paths and widths ARTIST',0,31,2.3,ink)
    result=[]
    positions=[-42,0]
    for i,plan in enumerate(plans):
        if plan.context.specimen.taxon!='Fragaria × ananassa':continue
        v=vascular_contract(plan)
        assert v.evidence_status=='QUALITATIVE_TOPOLOGY_ONLY'
        x=positions[i]
        # Draw illustrative silhouette, not measured shape beyond size extents.
        h=plan.context.specimen.fruit_height.mm
        R=plan.context.specimen.fruit_width.mm/2
        outline=[]
        for j in range(125):
            t=.004+.992*j/124
            rad=strawberry_shape_radius(t,rmax_mm=R)
            outline.append((x-rad,-.9,h*(t-.5)))
        for j in range(125):
            t=.996-.992*j/124
            rad=strawberry_shape_radius(t,rmax_mm=R)
            outline.append((x+rad,-.9,h*(t-.5)))
        outline.append(outline[0]);tube(scene,'M2b silhouette '+plan.context.instance_id,outline,ink,.08)
        # Pedicel -> central bundle hub, multiple routes with tips selected from
        # schematic surface. NO real vessel positions/diameters in Darrow figures.
        splines=[[(x,0,h/2+2),(x,0,h/2-2)],[(x,0,h/2-1),(x,0,-h/2+6)]]
        for j in range(12):
            t=.10+.79*(j+.5)/12
            z=h*(t-.5)
            side=-1 if j%2 else 1
            rr=strawberry_shape_radius(t,rmax_mm=R)
            splines.append([(x+side*.7,-.6,z+3),
                            (x+side*(rr*.47),-.6,z+.8),
                            (x+side*(rr*.93),-.6,z)])
        ob=make_multi_spline_curve(scene,'M2b vascular DIAGNOSTIC '+plan.context.instance_id,splines)
        ob.data.materials.append(yellow)
        m=ob.modifiers.new('FE generic branch curve primitive','NODES');m.node_group=group
        # Shared group radius .16 mm = ARTIST display convention, not measurement
        tag(ob,plan.context.instance_id,'VascularGraph','QUALITATIVE_TOPOLOGY_ONLY_ARTIST_PATHS',v.source_id)
        ob['fe_m2b_source_taxon']=v.source_taxon
        ob['fe_m2b_radii_measured']=False
        ob['fe_m2b_typed_edges']=json.dumps(v.typed_edges)
        ob['fe_m2b_artist_paths']=len(splines)
        result.append(ob)
        font_object(scene,'CAMAROSA / '+plan.context.instance_id,x,28,2,ink)
        font_object(scene,'Darrow S02 qualitative topology',x,-29,1.2,ink)
    # The two yellow kiwi profiles lack matching vascular topology: render NONE.
    for plan in plans:
        if 'Actinidia' in plan.context.specimen.taxon:
            v=vascular_contract(plan)
            assert not v.typed_edges and v.evidence_status=='CROSS_TAXON_REF_DO_NOT_GENERATE'
    font_object(scene,'KIWI / Sweet Gold & Jecy Gold',45,13,2.0,ink)
    font_object(scene,'No verified yellow-kiwi vessel paths',45,7,1.5,ink)
    font_object(scene,'A. deliciosa reference is NOT specimen data',45,3,1.25,ink)
    font_object(scene,'Display thickness UNMEASURED | artery-like routes are schematic',0,-31,1.4,ink)
    return scene,result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base',required=True)
    ap.add_argument('--catalog',required=True)
    ap.add_argument('--out',required=True)
    opts=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
    out=Path(opts.out).resolve();out.mkdir(parents=True,exist_ok=True)
    catalog=load_catalog(opts.catalog)
    reg=standard_registry()
    contexts=(make_context(catalog,'Camarosa','cam-a',seed=13),
              make_context(catalog,'Camarosa','cam-b',seed=107),
              make_context(catalog,'Sweet Gold','sweet',seed=13),
              make_context(catalog,'Jecy Gold','jecy',seed=107))
    plans=tuple(reg.plan(c) for c in contexts)
    bpy.ops.wm.open_mainfile(filepath=str(Path(opts.base).resolve()))
    scene=bpy.data.scenes['01 | Fruit Platform | 4 independent contexts']
    scene['fe_schema']='fruit_platform.m2b'
    scene['fe_m2b_warning']='M2b diagnostic GN: measured region widths/diameters; artist cell packing and vessel geometry'
    tissue=group_region_field()
    cells=group_cell_populations()
    vessel=group_vascular_graph()
    annotated=[]
    for ob in scene.objects:
        if ob.type!='MESH' or ob.get('fe_organ_id') not in ('receptacle','pericarp_tissue_zones'):
            continue
        plan=next(p for p in plans if p.context.instance_id==ob['fe_instance_id'])
        ev=tissue_contract(plan)
        m=ob.modifiers.new('FE shared tissue domain analytical field','NODES');m.node_group=tissue
        cx=(max(v.co.x for v in ob.data.vertices)+min(v.co.x for v in ob.data.vertices))/2
        vals={'fe_m2b_has_radial':1.0 if ev.boundaries_mm else 0.0,
              'fe_m2b_center_x_mm':cx,
              'fe_m2b_core_mm':ev.boundaries_mm[0] if ev.boundaries_mm else 0.0,
              'fe_m2b_inner_mm':ev.boundaries_mm[1] if ev.boundaries_mm else 0.0}
        for name,val in vals.items():face_attr(ob.data,name,val)
        ob['fe_m2b_tissue_evidence']=ev.status
        ob['fe_m2b_source_rows']=','.join(ev.source_rows)
        ob['fe_m2b_tissue_order']=','.join(ev.tissue_labels)
        annotated.append(ob.name)
    cell_scene,cell_objs=create_cells_scene(plans,cells)
    vascular_scene,vessel_objs=make_vascular_scene(plans,vessel)
    summary={
        'schema':'fruit_platform.m2b',
        'base_m2a':str(opts.base),
        'base_digest':plans_digest(plans),
        'shared_node_groups':[tissue.name,cells.name,vessel.name],
        'tissue_bodies':annotated,
        'cell_objects':[o.name for o in cell_objs],
        'vascular_objects':[o.name for o in vessel_objs],
        'component_plans':[anatomical_components(p) for p in plans],
        'critical_caveats':[
            'Cell spatial packing is synthetic lattice, not histological anatomy',
            'No ripe Camarosa cell sizes from matching primary table',
            'Vascular route positions and display radii ALL ARTIST - topology qualitative only',
            'No yellow A. chinensis vascular geometry (available study is A. deliciosa)',
            'Kiwi regional circular symmetry schematic; only radial mean widths measured',
            'Cut remains separate universal operation, not a biological module'],
    }
    f=out/'fruit-platform-m2b.blend'
    bpy.context.window.scene=scene
    bpy.ops.wm.save_as_mainfile(filepath=str(f))
    (out/'component-plans-m2b.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
    print('M2B_BUILD_OK',json.dumps({'groups':len(summary['shared_node_groups']),
        'tissue_bodies':len(annotated),'cell_objects':len(cell_objs),
        'vascular_objects':len(vessel_objs),'path':str(f)}))

if __name__=='__main__':main()
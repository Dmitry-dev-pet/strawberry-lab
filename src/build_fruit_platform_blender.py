#!/usr/bin/env python3
"""M2a Fruit Platform proof: two taxon adapters, one explicit GN runtime.

Four isolated fruit contexts coexist in a single editable .blend:
  2 Camarosa receptacle+schematic achene markers, distinct artist seeds;
  Sweet Gold and Jecy Gold exact radial tissue widths (only schematic discs).

The emitter dispatch is by typed organ recipe, NOT a process-global fruit name.
Measurements come from primary rows and are never silently inferred.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass
import json
import math
import hashlib
from pathlib import Path
import sys

import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fruit_platform import (FruitContext, FruitPlan, standard_registry,
                            make_context, plans_digest, PlatformError)
from fruit_morphometry import load_catalog
from fe_geometry import strawberry_surface_mesh, kiwi_region_rings, achene_anchor_positions
from build_fruit_engine_blender import (mat, add_mesh, make_material_group,
                                        make_achene_group, assign_group,
                                        font_object, tube, camera_and_light,
                                        add_marker_disk)


@dataclass(frozen=True)
class VisualResources:
    tissue_group: bpy.types.NodeTree
    achene_group: bpy.types.NodeTree
    ink: bpy.types.Material
    red: bpy.types.Material
    ochre: bpy.types.Material
    kiwi_core: bpy.types.Material
    kiwi_inner: bpy.types.Material
    kiwi_outer: bpy.types.Material
    small: bpy.types.Material
    large: bpy.types.Material

    @property
    def kiwi_materials(self):
        return (self.kiwi_core,self.kiwi_inner,self.kiwi_outer)


def create_resources():
    return VisualResources(
        make_material_group(), make_achene_group(),
        mat('FE M2a | ink and labels',(.022,.065,.092)),
        mat('FE M2a | receptacle schematic red',(.66,.028,.062),.37),
        mat('FE M2a | achenes schematic ochre',(.92,.59,.13),.49),
        mat('FE M2a | kiwi core',(.96,.83,.44)),
        mat('FE M2a | kiwi inner pericarp',(.75,.54,.16)),
        mat('FE M2a | kiwi outer pericarp',(.43,.59,.16)),
        mat('FE M2a | kiwi small cells',(.36,.67,.32)),
        mat('FE M2a | kiwi large cells',(.93,.66,.16))
    )


def place_in_collection(ob, scene, collection):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    collection.objects.link(ob)
    assert collection.objects.get(ob.name) is ob


def tag(ob, recipe, plan):
    ob['fe_instance_id'] = plan.context.instance_id
    ob['fe_cultivar'] = plan.context.specimen.cultivar
    ob['fe_taxon'] = plan.context.specimen.taxon
    ob['fe_adapter'] = plan.adapter_id
    ob['fe_organ_id'] = recipe.organ_id
    ob['fe_evidence'] = recipe.evidence
    ob['fe_source_rows'] = ','.join(recipe.evidence_rows)
    ob['fe_plan_sha256'] = plan.digest()
    ob['fe_seed'] = plan.context.seed
    ob['fe_biology_complete'] = False
    return ob


def emit_receptacle(scene,collection,plan,recipe,res,x):
    p=recipe.parameters()
    verts,faces=strawberry_surface_mesh(height_mm=p['height_mm'],width_mm=p['width_mm'],rings=78,sectors=100)
    verts=[(vx+x,vy,vz) for vx,vy,vz in verts]
    ob=add_mesh(scene,f"{plan.context.instance_id} | Receptacle | measured extent",verts,faces,[0]*len(faces))
    assign_group(ob,res.tissue_group,(res.red,res.red,res.red))
    ob['fe_measured_height_mm']=p['height_mm']
    ob['fe_measured_width_mm']=p['width_mm']
    ob['fe_shape']='ILLUSTRATIVE_NOT_MEASURED'
    place_in_collection(tag(ob,recipe,plan),scene,collection)
    return [ob]


def emit_achenes(scene,collection,plan,recipe,res,x):
    sp=plan.context.specimen
    p=recipe.parameters()
    pts=achene_anchor_positions(height_mm=sp.fruit_height.mm,width_mm=sp.fruit_width.mm,
                                count=p['marker_count'])
    # Author-independent artist arrangement with instance-specific phase.
    phase=(plan.context.seed%1009)/1009*2*math.pi
    angle=math.cos(phase);sine=math.sin(phase)
    positions=[(vx*angle-vy*sine+x, vx*sine+vy*angle-.2, vz) for vx,vy,vz in pts]
    ob=add_mesh(scene,f"{plan.context.instance_id} | SurfaceAcheneMarkers",positions,[])
    ob.data.materials.append(res.ochre)
    mod=ob.modifiers.new('FE marker instancing shared','NODES')
    mod.node_group=res.achene_group
    ob['fe_anchor_count']=p['marker_count']
    ob['fe_mean_not_single_fruit_exact_count']=True
    ob['fe_arrangement']='ARTIST_SEEDED_ROTATION_NOT_MEASURED'
    place_in_collection(tag(ob,recipe,plan),scene,collection)
    return [ob]


def emit_kiwi_region(scene,collection,plan,recipe,res,x):
    p=recipe.parameters()
    boundaries=(p['core_boundary_mm'],p['inner_boundary_mm'],p['outer_boundary_mm'])
    verts,faces,face_regions=kiwi_region_rings(boundaries,sectors=180)
    ob=add_mesh(scene,f"{plan.context.instance_id} | Pericarp measured radial zones",
                [(vx+x,vy,vz) for vx,vy,vz in verts],faces,face_regions)
    assign_group(ob,res.tissue_group,res.kiwi_materials)
    ob['fe_radial_boundaries_mm']=list(boundaries)
    ob['fe_longitudinal_dimensions']='UNKNOWN_NOT_MODELED'
    ob['fe_locular_seed_positions']='UNKNOWN_NOT_MODELED'
    ob['fe_shape']='RADIAL_TRANSECT_SCHEMATIC'
    place_in_collection(tag(ob,recipe,plan),scene,collection)
    outline=[]
    for radius in boundaries:
        samples=[(x+radius*math.cos(math.tau*i/180),-.3,
                  radius*math.sin(math.tau*i/180)) for i in range(181)]
        ring=tube(scene,plan.context.instance_id+' | region boundary',samples,res.ink,.058)
        place_in_collection(ring,scene,collection)
        outline.append(ring)
    return [ob]+outline


MAIN_EMITTERS = {
  'schematic_receptacle_envelope': emit_receptacle,
  'schematic_surface_marker_scatter': emit_achenes,
  'schematic_radial_pericarp_section': emit_kiwi_region,
}


def make_micro_scene(plans,res):
    scene=bpy.data.scenes.new('02 | Cell size calibration, not histology')
    camera_and_light(scene,'M2a microscope scale',ortho=4.2,res=(1450,700))
    scene.cycles.samples=10
    scene['fe_note']='Gauges of MEAN cell diameters; not cell membrane shapes or packing'
    font_object(scene,'KIWI — measured mean cell diameters, scale accurate',0,.81,.115,res.ink)
    font_object(scene,'Schematic circles ONLY: original Jeon 2024 Table 5',0,.64,.075,res.ink)
    xs=(-1.32,-.45,.44,1.31)
    colors=(res.kiwi_core,res.kiwi_inner,res.small,res.large)
    labels=('CORE','INNER','OUTER SMALL','OUTER LARGE')
    for ri,plan in enumerate(plans):
        recipes=[r for r in plan.renderable_parts if r.emitter=='measured_cell_diameter_gauges']
        if not recipes:continue
        recipe=recipes[0]
        p=recipe.parameters()
        z=.36-ri*.65
        for j,key in enumerate(('core','inner_pericarp','outer_pericarp_small','outer_pericarp_large')):
            diam=p[key+'_diameter_mm']
            obj=add_marker_disk(scene,xs[j],z,diam,colors[j],f'{plan.context.instance_id} | {key} | diameter {diam}mm')
            tag(obj,recipe,plan)
            obj['fe_gauge_diameter_mm']=diam
            font_object(scene,labels[j],xs[j],z-.17,.085,res.ink)
            font_object(scene,f'{diam*1000:.1f} um',xs[j],z-.27,.105,res.ink)
        font_object(scene,plan.context.specimen.cultivar,0,z+.17,.12,res.ink)
    tube(scene,'Physical scale 0.2mm',[(-1.5,-.8,-.9),(-1.3,-.8,-.9)],res.ink,.004)
    font_object(scene,'0.2 mm',-1.4,-.85,.075,res.ink)
    return scene


def build_scene(plans, out_dir: Path, samples=10, render=True):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    res=create_resources()
    scene=bpy.context.scene
    scene.name='01 | Fruit Platform | 4 independent contexts'
    camera_and_light(scene,'M2a platform',ortho=250,res=(1850,850))
    scene.cycles.samples=samples
    scene['fe_schema']='fruit_platform.m2a'
    scene['fe_mm_per_BLENDER_UNIT']=1.0
    scene['fe_independent_instance_count']=len(plans)
    scene['fe_assembly_manifest_sha256']=plans_digest(plans)
    scene['fe_shared_runtime']='EXPLICIT_CONTEXT_NO_PROCESS_GLOBAL_SWITCH'
    scene['fe_no_frucht_tree_imported']='Only independent Strawberry Lab code'

    body_stats=[];x_positions=(-92,-31,31,92)
    fruit_paints=[]
    for plan,x in zip(plans,x_positions):
        inst=plan.context.instance_id
        collection=bpy.data.collections.new(f'Fruit | {inst} | {plan.context.specimen.cultivar}')
        scene.collection.children.link(collection)
        # No scene-global active fruit: every emitter receives its own context.
        emitted=[]
        for recipe in plan.renderable_parts:
            if recipe.emitter=='measured_cell_diameter_gauges':
                continue   # explicit secondary view, not anatomy object
            emitter=MAIN_EMITTERS.get(recipe.emitter)
            if emitter is None:raise PlatformError(f'No renderer for {recipe.emitter}')
            emitted.extend(emitter(scene,collection,plan,recipe,res,x))
        if not emitted:raise PlatformError(f'No renderer outputs for {inst}')
        fruit_paints.append(inst)
        label=('STRAWBERRY' if 'Fragaria' in plan.context.specimen.taxon else 'KIWI')+' / '+plan.context.specimen.cultivar
        if 'Fragaria' in plan.context.specimen.taxon:
            label2='48.0 x 32.5 mm | 326 achene marks'
            caption='silhouette + distribution SCHEMATIC'
        else:
            bands=plan.context.specimen.region_boundaries_mm
            label2=' / '.join(f'{v:.1f}' for v in bands)+' mm'
            caption='radial transect ONLY; seeds unmeasured'
        for text_line, zz, size in ((label,29.0,2.75),(label2,-30.5,1.8),(caption,-35.5,1.48)):
            label_ob=font_object(scene,text_line,x,zz,size,res.ink)
            place_in_collection(label_ob,scene,collection)
        body_stats.append({'instance':inst,'adapter':plan.adapter_id,'cultivar':plan.context.specimen.cultivar,
                           'plan_sha256':plan.digest(),'rendered_organ_ids':
                           [r.organ_id for r in plan.renderable_parts if r.emitter!='measured_cell_diameter_gauges'],
                           'source_id':plan.context.specimen.source_id})
    heading=font_object(scene,'FRUIT PLATFORM  |  organ adapters + shared Geometry Nodes',0,47.0,3.2,res.ink)
    footer=font_object(scene,'1 BU = 1 mm    |    anatomy incomplete    |    strict source & cultivar separation',0,-46.5,1.55,res.ink)

    secondary=make_micro_scene([p for p in plans if p.context.specimen.taxon.startswith('Actinidia')],res)
    scene['fe_profile_manifest']=json.dumps(body_stats,sort_keys=True,ensure_ascii=False)
    secondary['fe_profile_manifest_sha256']=plans_digest(plans)

    output=out_dir/'fruit-platform-m2a.blend'
    bpy.context.window.scene=scene
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    if render:
        scene.render.filepath=str(out_dir/'fruit-platform-m2a-overview.png')
        bpy.ops.render.render(scene=scene.name,write_still=True)
        secondary.render.filepath=str(out_dir/'fruit-platform-m2a-cell-gauges.png')
        bpy.ops.render.render(scene=secondary.name,write_still=True)
    return {'blend_path':str(output), 'schema':'fruit_platform.m2a',
            'instance_digest':plans_digest(plans),'instances':body_stats,
            'shared_GN_groups':[res.tissue_group.name,res.achene_group.name],
            'rendered':render}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--catalog',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--samples',type=int,default=10)
    ap.add_argument('--no-render',action='store_true')
    args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
    out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
    catalog=load_catalog(args.catalog)
    registry=standard_registry()
    contexts=[
        make_context(catalog,'Camarosa','cam-a',seed=13),
        make_context(catalog,'Camarosa','cam-b',seed=107),
        make_context(catalog,'Sweet Gold','sweet',seed=13),
        make_context(catalog,'Jecy Gold','jecy',seed=107),
    ]
    plans=tuple(registry.plan(c) for c in contexts)
    assert plans_digest(plans)==plans_digest(tuple(reversed(plans)))
    res=build_scene(plans,out,args.samples,not args.no_render)
    (out/'fruit-platform-m2a-plans.json').write_text(json.dumps({
        'schema':'fruit_platform.m2a',
        'notes':[
            'The platform shares algorithms, not one fruit biology or one giant GN graph.',
            'Missing yellow-kiwi seed/locule positions and vascular diameters are NOT generated.',
            'Strawberry achene positions are schematic, not original Ariza specimen morphology.',
            'Cut is an operation and is not executed in this demonstration.',
        ],
        'registry_taxa':list(registry.available_taxa()),
        'build':res,
        'plans':[p.as_dict() for p in plans],
    },ensure_ascii=False,indent=2),encoding='utf-8')
    print('FRUIT_PLATFORM_BUILD_OK',json.dumps({'instances':len(plans),
        'digest':plans_digest(plans),'two_camarosa_distinct_seeds':True}))


if __name__=='__main__': main()
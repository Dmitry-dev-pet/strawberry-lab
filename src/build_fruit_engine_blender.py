#!/usr/bin/env python3
"""Evidence-bound Blender overview of 3 fruit profiles, one reusable GN material group.

Run: blender -b -t 8 --python src/build_fruit_engine_blender.py -- \
       --catalog measurements-v1.json --out outputs --samples 18

The drawing visualizes measured dimensions, NOT sampled histology:
- Camarosa 48×32.5 mm, rounded mean 326 achene markers; silhouette, marker
  radius, and anchor phyllotaxis are explicitly schematic.
- Two yellow kiwis: radial annuli encode measured one-sided region widths.
  Longitudinal dimensions and seed placements are not provided in the tables
  and therefore are not fabricated. 3D section thickness is omitted.
- A separate micro-view displays circles of exact published MEAN cell
  diameters. Circles are size gauges, not cell-membrane reconstruction.
"""
from __future__ import annotations
import sys,argparse,json,math
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from fruit_morphometry import load_catalog
from fruit_engine import get_specimen,provenance_dict,MM_PER_BLENDER_UNIT
from fruit_engine_anatomy import strawberry_anatomy,kiwi_anatomy,export_anatomy
from fe_geometry import strawberry_surface_mesh,achene_anchor_positions,kiwi_region_rings


def mat(name,rgb,roughness=.62,metallic=0.):
    m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1.)
    m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*rgb,1.)
    bs.inputs['Roughness'].default_value=roughness
    bs.inputs['Metallic'].default_value=metallic
    return m

def add_mesh(scene,name,pts,faces,region_ids=None):
    mesh=bpy.data.meshes.new(name+' mesh');mesh.from_pydata(pts,[],faces)
    mesh.update(calc_edges=True)
    ob=bpy.data.objects.new(name,mesh);scene.collection.objects.link(ob)
    if region_ids is not None:
        a=mesh.attributes.new(name='fe_region_id',type='INT',domain='FACE')
        if len(region_ids)!=len(mesh.polygons):raise ValueError('region/face count mismatch')
        for i,v in enumerate(region_ids):a.data[i].value=int(v)
    return ob

def make_material_group():
    """Shared per-face region-ID -> material SLOT mapping for all fruits.

    The same GN group is reused. Slot 0/1/2 contents are local to the fruit,
    rather than group-global: no region pigments need to be shared.
    """
    ng=bpy.data.node_groups.new('FE | TissueRegionMaterials | shared','GeometryNodeTree')
    for direction,name in [('INPUT','Geometry'),('OUTPUT','Geometry')]:
        ng.interface.new_socket(name=name,in_out=direction,socket_type='NodeSocketGeometry')
    N=ng.nodes;L=ng.links
    entry=N.new('NodeGroupInput');entry.location=(-590,50)
    out=N.new('NodeGroupOutput');out.location=(550,50)
    attr=N.new('GeometryNodeInputNamedAttribute');attr.data_type='INT'
    attr.inputs['Name'].default_value='fe_region_id';attr.location=(-600,-170)
    current=entry.outputs['Geometry']
    for i in range(3):
        comp=N.new('FunctionNodeCompare');comp.data_type='INT';comp.operation='EQUAL'
        comp.inputs['B'].default_value=i;comp.location=(-300+i*250,-170)
        L.new(attr.outputs['Attribute'],comp.inputs['A'])
        setmat=N.new('GeometryNodeSetMaterialIndex');setmat.location=(-300+i*250,60)
        L.new(current,setmat.inputs['Geometry'])
        L.new(comp.outputs['Result'],setmat.inputs['Selection'])
        setmat.inputs['Material Index'].default_value=i
        current=setmat.outputs['Geometry']
    L.new(current,out.inputs['Geometry'])
    ng['fe_role']='face_region_to_object_local_material_slot'
    return ng

def make_achene_group():
    ng=bpy.data.node_groups.new('FE | ScatterSurfaceAttachmentMarkers | shared','GeometryNodeTree')
    for direction,name,kind in [('INPUT','Geometry','NodeSocketGeometry'),
         ('INPUT','Marker radius (schematic)','NodeSocketFloat'),
         ('OUTPUT','Geometry','NodeSocketGeometry')]:
        s=ng.interface.new_socket(name=name,in_out=direction,socket_type=kind)
        if name=='Marker radius (schematic)':s.default_value=.36;s.min_value=0.01
    N=ng.nodes;L=ng.links
    inp=N.new('NodeGroupInput');inp.location=(-450,0)
    out=N.new('NodeGroupOutput');out.location=(390,0)
    sph=N.new('GeometryNodeMeshIcoSphere');sph.location=(-450,-240)
    sph.inputs['Subdivisions'].default_value=1
    L.new(inp.outputs['Marker radius (schematic)'],sph.inputs['Radius'])
    inst=N.new('GeometryNodeInstanceOnPoints');inst.location=(0,0)
    L.new(inp.outputs['Geometry'],inst.inputs['Points'])
    L.new(sph.outputs['Mesh'],inst.inputs['Instance'])
    real=N.new('GeometryNodeRealizeInstances');real.location=(210,0)
    L.new(inst.outputs['Instances'],real.inputs['Geometry'])
    L.new(real.outputs['Geometry'],out.inputs['Geometry'])
    ng['fe_role']='surface_attachment_instancing'
    return ng

def assign_group(ob,group,materials):
    for material in materials:
        ob.data.materials.append(material)
    m=ob.modifiers.new('FE shared tissue region material mapping','NODES')
    m.node_group=group
    return m

def font_object(scene,content,x,z,size,material,name=None):
    cu=bpy.data.curves.new('font','FONT');cu.body=content;cu.size=size;cu.align_x='CENTER'
    ob=bpy.data.objects.new(name or ('Label '+content[:12]),cu)
    ob.location=(x,-0.8,z);ob.rotation_euler=(math.pi/2,0,0)
    scene.collection.objects.link(ob);cu.materials.append(material)
    return ob

def tube(scene,name,coords,material,width=.12):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=2
    spline=cu.splines.new('POLY');spline.points.add(len(coords)-1)
    for p,co in zip(spline.points,coords):p.co=(*co,1)
    cu.bevel_depth=width;cu.bevel_resolution=2
    ob=bpy.data.objects.new(name,cu);scene.collection.objects.link(ob)
    cu.materials.append(material)
    return ob

def camera_and_light(scene,name,x=0,y=-170,z=0,ortho=180,res=(1760,850)):
    cm=bpy.data.cameras.new(name+' camera');cam=bpy.data.objects.new(name+' camera',cm)
    scene.collection.objects.link(cam);cam.location=(x,y,z)
    direction=Vector((x,0,z))-cam.location
    cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
    cm.type='ORTHO';cm.ortho_scale=ortho;scene.camera=cam
    scn_w=bpy.data.worlds.get('FE Soft white')
    if scn_w is None:
        scn_w=bpy.data.worlds.new('FE Soft white');scn_w.use_nodes=True
        background=scn_w.node_tree.nodes.get('Background')
        background.inputs['Color'].default_value=(0.88,.93,.94,1)
        background.inputs['Strength'].default_value=.7
    scene.world=scn_w
    for i,loc in enumerate([(-40,-60,60),(60,-30,48)]):
        ld=bpy.data.lights.new(f'{name} Area{i}','AREA');ld.energy=1900
        ld.shape='DISK';ld.size=90
        lo=bpy.data.objects.new(f'{name} Area{i}',ld);scene.collection.objects.link(lo)
        lo.location=loc if ortho>50 else (x-1,-3,z+1)
        lo.rotation_euler=(Vector((x,0,z))-lo.location).to_track_quat('-Z','Y').to_euler()
    scene.render.engine='CYCLES';scene.cycles.samples=18
    scene.render.resolution_x=res[0];scene.render.resolution_y=res[1]
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.view_settings.view_transform='AgX'
    scene.unit_settings.system='METRIC'
    scene.unit_settings.scale_length=.001
    scene.unit_settings.length_unit='MILLIMETERS'
    scene.render.film_transparent=False


def add_kiwi(scene, p, x, region_group, mats, ink):
    verts,faces,ids=kiwi_region_rings(p.region_boundaries_mm,192)
    verts=[(vx+x,vy,vz) for vx,vy,vz in verts]
    ob=add_mesh(scene,f'Kiwi {p.cultivar} | actual measured radial width',verts,faces,ids)
    ob['fe_cultivar']=p.cultivar
    ob['fe_source_id']=p.source_id
    ob['fe_origin']=p.developmental_origin
    ob['fe_measured_outer_radius_mm']=p.physical_radius
    ob['fe_schematic_angular_symmetry']=True
    assign_group(ob,region_group,mats)
    for rad in p.region_boundaries_mm:
        samples=[(x+rad*math.cos(2*math.pi*j/180),-.8,rad*math.sin(2*math.pi*j/180))
                 for j in range(181)]
        tube(scene,p.cultivar+' measured radius boundary',samples,ink,.075)
    font_object(scene,f'KIWI  |  {p.cultivar}',x,29,3.0,ink)
    font_object(scene,f'r = {p.physical_radius:.1f} mm  |  {p.source_id}',x,-27.4,1.75,ink)
    font_object(scene, 'core / inner / outer radial zones',x,-32.5,1.55,ink)
    font_object(scene,f"{p.radial_region_widths['core'].mm:.1f} / {p.radial_region_widths['inner_pericarp'].mm:.1f} / {p.radial_region_widths['outer_pericarp'].mm:.1f} mm",x,-36.5,1.58,ink)
    return ob

def add_strawberry(scene,p,x,region_group,scatter_group,mats,ink):
    verts,faces=strawberry_surface_mesh(height_mm=p.fruit_height.mm,
                         width_mm=p.fruit_width.mm,rings=100,sectors=120)
    meshverts=[(vx+x,vy,vz) for vx,vy,vz in verts]
    obj=add_mesh(scene,'Camarosa | measured H W | illustrative silhouette',meshverts,faces,[0]*len(faces))
    obj['fe_measured_height_mm']=p.fruit_height.mm
    obj['fe_measured_width_mm']=p.fruit_width.mm
    obj['fe_achene_source_mean']=p.achene_mean
    obj['fe_cultivar']=p.cultivar
    obj['fe_origin']=p.developmental_origin
    obj['fe_silhouette_beyond_extent']='ARTIST_NOT_MEASURED'
    assign_group(obj,region_group,[mats[0],mats[0],mats[0]])
    pts=achene_anchor_positions(height_mm=p.fruit_height.mm,
            width_mm=p.fruit_width.mm,count=p.display_achene_count)
    anchors=add_mesh(scene,'Camarosa | mean rounded anchors | schematic layout',[(vx+x,vy-.32,vz) for vx,vy,vz in pts],[])
    anchors.data.materials.append(mats[1])
    anchors['fe_anchor_count']=len(pts)
    anchors['fe_achene_mean_row']=p.achene_mean_id
    anchors['fe_anchor_distribution']='ARTIST_QUASI_UNIFORM_NOT_MEASURED'
    seedmod=anchors.modifiers.new('FE SurfaceAttachmentMarkers','NODES');seedmod.node_group=scatter_group
    font_object(scene,'STRAWBERRY  |  Camarosa',x,29.3,2.9,ink)
    font_object(scene,'48.0 x 32.5 mm  |  ARIZA2011',x,-27.5,1.8,ink)
    font_object(scene,'326 markers = rounded mean 325.6',x,-32.5,1.65,ink)
    font_object(scene,'shape / marker size: schematic',x,-36.5,1.46,ink)
    return obj,anchors

def add_marker_disk(scene,x,z,diam,material,name):
    n=64;pts=[(x,0.,z)]
    for j in range(n):
        a=2*math.pi*j/n;pts.append((x+diam/2*math.cos(a),0.,z+diam/2*math.sin(a)))
    faces=[(0,1+j,1+(j+1)%n) for j in range(n)]
    obj=add_mesh(scene,name,pts,faces)
    obj.data.materials.append(material);obj['fe_diameter_mm']=diam
    return obj

def make_micro_scene(specimens,ink,mats):
    micro=bpy.data.scenes.new('02 | Measured cell diameters only')
    camera_and_light(micro,'Micro',ortho=3.6,res=(1600,800))
    font_object(micro,'KIWI  |  reported mean cell diameters in micrometres',0,.76,.115,ink)
    font_object(micro,'Scaled physical circles, NOT real cell shapes or packing',0,.60,.088,ink)
    xx=(-1.30,-.42,.46,1.31)
    keys=('core','inner_pericarp','outer_pericarp_small','outer_pericarp_large')
    colors=(mats['core'],mats['inner'],mats['small'],mats['large'])
    for row,p in enumerate(specimens):
        z=.27-row*.61
        for j,key in enumerate(keys):
            m=p.cell_diameters[key]
            add_marker_disk(micro,xx[j],z,m.mm,colors[j],f'{p.cultivar}:{key}:{m.mm}mm')
            tag={'core':'CORE','inner_pericarp':'INNER','outer_pericarp_small':'OUTER SMALL','outer_pericarp_large':'OUTER LARGE'}[key]
            font_object(micro,tag,xx[j],z-.18,.095,ink)
            font_object(micro,f'{m.value_original:.1f} um',xx[j],z-.305,.11,ink)
        font_object(micro,p.cultivar,0,z+.17,.11,ink)
    tube(micro,'Micro scale 0.2 mm',[(-1.5,-.8,-.93),(-1.3,-.8,-.93)],ink,.004)
    font_object(micro,'0.2 mm',-1.40,-.88,.07,ink)
    micro['fe_unit']='1 Blender Unit = 1 mm'
    micro['fe_not_a_histology_reconstruction']=True
    return micro

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--catalog',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--samples',type=int,default=18);args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
    db=load_catalog(args.catalog)
    specs={n:get_specimen(db,n) for n in ('Camarosa','Sweet Gold','Jecy Gold')}
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene;scene.name='01 | Measured fruit organs overview'
    camera_and_light(scene,'Overview',ortho=193,res=(1760,850))
    scene.cycles.samples=args.samples
    ink=mat('FE Ink | labels',(.025,.075,.095))
    strawberry=mat('FE strawberry illustrative pigment',(.66,.042,.08),roughness=.33)
    ochre=mat('FE ochre schematic achene marker',(.88,.60,.20),roughness=.5)
    tissue_colors={
      'core':mat('FE kiwi core schematic pale gold',(.95,.75,.26)),
      'inner':mat('FE kiwi inner pericarp schematic gold',(.84,.64,.18)),
      'outer':mat('FE kiwi outer pericarp schematic green',(.40,.62,.22)),
      'small':mat('FE small-cell proxy (schematic)',(.52,.67,.29)),
      'large':mat('FE large-cell proxy (schematic)',(.84,.67,.21)),
    }
    tissue_group=make_material_group();attachments=make_achene_group()
    add_kiwi(scene,specs['Sweet Gold'],-58,tissue_group,
             [tissue_colors['core'],tissue_colors['inner'],tissue_colors['outer']],ink)
    add_kiwi(scene,specs['Jecy Gold'],0,tissue_group,
             [tissue_colors['core'],tissue_colors['inner'],tissue_colors['outer']],ink)
    add_strawberry(scene,specs['Camarosa'],59,tissue_group,attachments,[strawberry,ochre],ink)
    font_object(scene,'FRUIT ENGINE / M1f  |  1 Blender Unit = 1 mm',0,42,3.2,ink)
    font_object(scene,'Measured extents & tissue widths  |  remaining shapes and colors explicitly schematic',0,36.7,1.45,ink)
    font_object(scene,'Core and inner/outer region widths from JEON2024 Table 3  |  Camarosa dimensions from ARIZA2011 Table 2',0,-43.5,1.30,ink)
    tube(scene,'Measured scale 20 mm',[(-81,-.7,-37.9),(-61,-.7,-37.9)],ink,.15)
    font_object(scene,'20 mm',-71,-41.3,1.35,ink)
    scene['fe_source_catalog']='fruit_morphometry.1'
    scene['fe_unmeasured_missing_in_kiwi']='longitudinal_height,seed_positions,vascular_diameters'
    scene['fe_unit']='1 BU = 1 mm | scale_length=0.001'
    scene['fe_result_status']='source_calibrated_extents__schematic_geometry'
    micro=make_micro_scene([specs['Sweet Gold'],specs['Jecy Gold']],ink,tissue_colors)
    micro.cycles.samples=args.samples
    result={"schema":"fruit_engine.m1f","blender":"5.2.4", "BU_per_mm":1,
      "geometry_groups":sorted([t.name for t in bpy.data.node_groups if t.bl_idname=='GeometryNodeTree']),
      "profiles":{n:provenance_dict(p) for n,p in specs.items()},
      "qualitative_reference_anatomies_not_assumed_identical":{
          "Fragaria × ananassa":export_anatomy(strawberry_anatomy()),
          "Actinidia deliciosa (DIFFERENT taxon from measured A. chinensis)":export_anatomy(kiwi_anatomy())},
      "not_calibrated":["strawberry_silhouette","achene_3d_sizes_and_positions","kiwi_seed_coordinates",
                        "vascular_bundle_diameter","kiwi_longitudinal_height","tissue_cell_packings"],
      "note":"Cross-sectional radial rings are schematic; measured radii and mean cell diameter markers are in 1 BU=1mm physical scale; reproduction topology differs by fruit."}
    (out/'fruit-engine-calibration.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'fruit-engine-m1f.blend'),compress=True)
    scene.render.filepath=str(out/'fruit-engine-specimens.png')
    bpy.ops.render.render(scene=scene.name,write_still=True)
    micro.render.filepath=str(out/'fruit-engine-cells-scale.png')
    bpy.ops.render.render(scene=micro.name,write_still=True)
    print('FE_RESULT_OK',json.dumps({"profiles":list(specs),"groups":result['geometry_groups'],
                                    "outputs":['fruit-engine-m1f.blend','fruit-engine-specimens.png','fruit-engine-cells-scale.png']},ensure_ascii=False))

if __name__=='__main__':main()
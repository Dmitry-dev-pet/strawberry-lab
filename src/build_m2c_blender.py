#!/usr/bin/env python3
"""M2c Blender: REAL 3-D ellipsoid cell solids, exact 2-plane sections.

We preserve (append to) the validated M2b .blend, which already holds
source-scoped tissue regions and qualitative vessels. M2c adds a new
source-diameter-scaled small tissue volume and independent sections in
2 axes using the *same cell centres and radii*, not 2-D textures.

Cell positions, spacing, 3-D ellipsoid anisotropy, gap fraction and large/small
population ratio are ARTIST. Do not call this histological reconstruction.
"""
from __future__ import annotations
import json,math,argparse,sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from fruit_morphometry import load_catalog
from fruit_platform import standard_registry,make_context
from fruit_cell_volumes import build_volume,plan_json,section_records,REGIONS

COLORS={
 'core':(.57,.80,.62,1),
 'inner_pericarp':(.91,.72,.30,1),
 'outer_pericarp_small':(.50,.78,.69,1),
 'outer_pericarp_large':(.97,.52,.31,1),
 'background':(.14,.22,.23,1),
 'frame':(.51,.63,.65,1),
 'font':(.88,.95,.94,1),
 'outline':(.08,.18,.19,1),
}


def material(name,color,*,rough=.55,alpha=1):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(*color[:3],alpha);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=color
    bs.inputs['Roughness'].default_value=rough
    bs.inputs['Metallic'].default_value=0.
    if alpha<1:
        bs.inputs['Alpha'].default_value=alpha
        try:m.surface_render_method='DITHERED'
        except Exception:pass
    return m


def box(scene,name,center,dx,dz,mat):
    x,y,z=center
    mesh=bpy.data.meshes.new(name+' mesh')
    verts=[(x-dx/2,0,z-dz/2),(x+dx/2,0,z-dz/2),(x+dx/2,0,z+dz/2),(x-dx/2,0,z+dz/2)]
    mesh.from_pydata(verts,[],[(0,1,2,3)])
    ob=bpy.data.objects.new(name,mesh);scene.collection.objects.link(ob)
    mesh.materials.append(mat)
    return ob


def text(scene,s,x,z,size,mat):
    cu=bpy.data.curves.new('FE text','FONT');cu.body=s;cu.size=size
    cu.align_x='CENTER';cu.extrude=.0004
    ob=bpy.data.objects.new('Label '+s[:36],cu)
    ob.location=(x,-.26,z);ob.rotation_euler=(math.pi/2,0,0)
    cu.materials.append(mat);scene.collection.objects.link(ob)
    return ob


def polyline(scene,name,points,mat,width=.004,closed=False):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D'
    cu.resolution_u=1;cu.bevel_depth=width;cu.bevel_resolution=1
    s=cu.splines.new('POLY');s.points.add(len(points)-1)
    for el,p in zip(s.points,points):el.co=(*p,1)
    s.use_cyclic_u=closed
    ob=bpy.data.objects.new(name,cu);scene.collection.objects.link(ob);cu.materials.append(mat)
    return ob


def wire_cube(scene,side,center,mat):
    x,y,z=center;h=side/2
    for k,(a,b) in enumerate([
        ((-1,-1,-1),(1,-1,-1)),((-1,1,-1),(1,1,-1)),
        ((-1,-1,1),(1,-1,1)),((-1,1,1),(1,1,1)),
        ((-1,-1,-1),(-1,1,-1)),((1,-1,-1),(1,1,-1)),
        ((-1,-1,1),(-1,1,1)),((1,-1,1),(1,1,1)),
        ((-1,-1,-1),(-1,-1,1)),((1,-1,-1),(1,-1,1)),
        ((-1,1,-1),(-1,1,1)),((1,1,-1),(1,1,1)),
    ]):
        pa=tuple(center[i]+a[i]*h for i in range(3))
        pb=tuple(center[i]+b[i]*h for i in range(3))
        polyline(scene,'sample frame '+str(k),[pa,pb],mat,.0023)


def lighting(scene,camdist,scale,res,tilt=False):
    scene.render.engine='CYCLES';scene.cycles.samples=14
    scene.cycles.use_denoising=True
    scene.render.resolution_x=res[0];scene.render.resolution_y=res[1]
    scene.render.resolution_percentage=100
    camdata=bpy.data.cameras.new('M2c macro orthographic')
    cam=bpy.data.objects.new('M2c macro orthographic',camdata)
    scene.collection.objects.link(cam)
    cam.location=(0,-camdist,4.0 if tilt else 0)
    direction=Vector((0,0,0))-cam.location
    cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
    camdata.type='ORTHO';camdata.ortho_scale=scale
    scene.camera=cam
    world=bpy.data.worlds.get('M2c microscope neutral')
    if world is None:
        world=bpy.data.worlds.new('M2c microscope neutral');world.use_nodes=True
        world.node_tree.nodes['Background'].inputs['Color'].default_value=(.11,.16,.16,1)
        world.node_tree.nodes['Background'].inputs['Strength'].default_value=.65
    scene.world=world
    for i,loc in enumerate([(-3.5,-4,5.5),(4.3,-3,3.7)]):
        d=bpy.data.lights.new('M2c softbox','AREA');d.energy=480 if i==0 else 280;d.shape='DISK';d.size=7
        ob=bpy.data.objects.new('M2c softbox',d);scene.collection.objects.link(ob);ob.location=loc
        ob.rotation_euler=(Vector((0,0,0))-ob.location).to_track_quat('-Z','Y').to_euler()
    scene.view_settings.view_transform='AgX'


def make_shared_cell_group():
    ng=bpy.data.node_groups.get('FE M2c | VolumetricCellSolids | shared')
    if ng:return ng
    ng=bpy.data.node_groups.new('FE M2c | VolumetricCellSolids | shared','GeometryNodeTree')
    for direction in ('INPUT','OUTPUT'):
        ng.interface.new_socket(name='Geometry',in_out=direction,socket_type='NodeSocketGeometry')
    n=ng.nodes;L=ng.links
    gi=n.new('NodeGroupInput');gi.location=(-520,150)
    go=n.new('NodeGroupOutput');go.location=(490,130)
    attr=n.new('GeometryNodeInputNamedAttribute');attr.data_type='FLOAT_VECTOR'
    attr.inputs['Name'].default_value='fe_m2c_half_axes_mm';attr.location=(-500,-140)
    proto=n.new('GeometryNodeMeshUVSphere');proto.inputs['Radius'].default_value=1.
    proto.inputs['Segments'].default_value=12;proto.inputs['Rings'].default_value=8;proto.location=(-440,-330)
    inst=n.new('GeometryNodeInstanceOnPoints');inst.location=(-140,140)
    L.new(gi.outputs['Geometry'],inst.inputs['Points'])
    L.new(proto.outputs['Mesh'],inst.inputs['Instance'])
    L.new(attr.outputs['Attribute'],inst.inputs['Scale'])
    real=n.new('GeometryNodeRealizeInstances');real.location=(130,135)
    L.new(inst.outputs['Instances'],real.inputs['Geometry'])
    smooth=n.new('GeometryNodeSetShadeSmooth');smooth.location=(310,135)
    smooth.inputs['Shade Smooth'].default_value=True
    L.new(real.outputs['Geometry'],smooth.inputs['Geometry'])
    shared=material('M2c | cell volume OBJECT COLOR | shared',(.66,.81,.73,1),rough=.49)
    nt=shared.node_tree
    objinfo=nt.nodes.new('ShaderNodeObjectInfo')
    bs=nt.nodes.get('Principled BSDF')
    nt.links.new(objinfo.outputs['Color'],bs.inputs['Base Color'])
    setmat=n.new('GeometryNodeSetMaterial');setmat.location=(470,125)
    setmat.inputs['Material'].default_value=shared
    L.new(smooth.outputs['Geometry'],setmat.inputs['Geometry'])
    L.new(setmat.outputs['Geometry'],go.inputs['Geometry'])
    ng['fe_role']='actual_3d_cell_solid_mesh_from_source_equivalent_diameter'
    ng['fe_source']='Jeon2024 Table5 numeric diameter ONLY'
    ng['fe_artist']='ellipsoid axes, centers, number and packing, porosity'
    return ng


def point_object(scene, name, cells, group, material_,loc,block):
    mesh=bpy.data.meshes.new('M2c cell center points '+name)
    mesh.from_pydata([c.center_mm for c in cells],[],[])
    r=mesh.attributes.new('fe_m2c_half_axes_mm','FLOAT_VECTOR','POINT')
    ids=mesh.attributes.new('fe_m2c_cell_id','INT','POINT')
    for i,c in enumerate(cells):r.data[i].vector=c.half_axes_mm;ids.data[i].value=c.cell_id
    ob=bpy.data.objects.new(name,mesh);scene.collection.objects.link(ob)
    ob.location=loc;ob.color=tuple(COLORS[cells[0].region]);mesh.materials.append(material_)
    mod=ob.modifiers.new('Shared source-sized 3D cell ellipsoids','NODES');mod.node_group=group
    ob['fe_m2c_module']='TRUE_3D_CELL_SOLIDS_DIAMETER_CALIBRATED_ARTIST_PACKING'
    ob['fe_m2c_cell_count']=len(cells)
    ob['fe_m2c_cultivar']=block.cultivar
    ob['fe_m2c_region']=cells[0].region
    ob['fe_m2c_instance_id']=block.instance_id
    ob['fe_m2c_block_side_mm']=block.side_mm
    ob['fe_m2c_source_row']=cells[0].source_row
    ob['fe_m2c_mean_diameter_mm']=cells[0].mean_diameter_mm
    ob['fe_m2c_cell_positions_and_ellipsoid_aspect']='ARTIST'
    return ob


def volume_display_scene(blocks,group):
    scene=bpy.data.scenes.new('06 | M2c | 3D CELL SOLIDS / source diameters')
    lighting(scene,14,7.7,(1600,950),tilt=True)
    scene['fe_m2c_status']='TRUE_3D_SOLIDS; SOURCE_DIAMETERS_ONLY; PACKING_ARTIST'
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.001
    ink=material('M2c | pale ink',COLORS['font'])
    frame=material('M2c | sample frame',COLORS['frame'])
    for k,color in COLORS.items():
        if k not in ('font','frame','background','outline'):material('M2c | '+k,color)
    # Row labels identify source specimen; no clipped decorative header.
    labels=['CORE','INNER PERICARP','OUTER PERICARP: LARGE + SMALL TOGETHER']
    positions=[-2.35,0,2.35]
    objs=[]
    for row,blocks3 in enumerate(blocks):
        z=1.12-row*2.10
        cultivar=blocks3[0].cultivar
        text(scene,cultivar.upper()+'   /   '+blocks3[0].taxon,0,z+.80,.145,ink)
        for col,block in enumerate(blocks3):
            x=positions[col]
            wire_cube(scene,block.side_mm,(x,0,z),frame)
            for region in REGIONS:
                these=block.by_region(region)
                if not these:continue
                # Source mean diameter matches actual mesh size; artist arrangement.
                alpha=.98 if region=='outer_pericarp_large' else .83
                m=material('M2c | '+region,COLORS[region],rough=.50,alpha=alpha)
                ob=point_object(scene,f'M2c volume {cultivar} {region}',these,group,m,(x,0,z),block)
                objs.append(ob)
            text(scene,labels[col],x,z-.67,.11,ink)
            text(scene,str(len(block.cells))+' synthetic cell solids / block',x,z-.86,.115,ink)
    # 1 BU=1mm via unit_settings; each population records scientific limits.
    return scene,objs


def make_section_mesh(scene,block,normal_axis,display_origin,material_map,outline_mat):
    """Analytic intersection surface from same 3D ellipsoids, then flattened for display."""
    x0,y0,z0=display_origin
    cells=section_records(block,normal_axis)
    verts=[];faces=[];matids=[];ids=[];regionids=[];edge_lines=[]
    for c,_ in cells:
        face=[];line=[]
        for j in range(32):
            p=c.section_point(normal_axis,2*math.pi*j/32)
            # section view rotation: physical XY or XZ mapped to XZ display panel
            a=tuple(i for i in range(3) if i!=normal_axis)
            v=(x0+p[a[0]], -.015, z0+p[a[1]])
            face.append(len(verts));verts.append(v);line.append((v[0],v[1]-.006,v[2]))
        faces.append(face);matids.append(REGIONS.index(c.region));ids.append(c.cell_id)
        regionids.append(REGIONS.index(c.region));edge_lines.append(line)
    mesh=bpy.data.meshes.new('M2c exact ellipsoid sections '+block.cultivar+str(normal_axis))
    mesh.from_pydata(verts,[],faces);mesh.update()
    for region in REGIONS:mesh.materials.append(material_map[region])
    a=mesh.attributes.new('fe_m2c_cell_id','INT','FACE')
    b=mesh.attributes.new('fe_m2c_class_index','INT','FACE')
    for i,pol in enumerate(mesh.polygons):
        pol.material_index=matids[i];a.data[i].value=ids[i];b.data[i].value=regionids[i]
    ob=bpy.data.objects.new('M2c SECTION '+block.cultivar+' '+('XY' if normal_axis==2 else 'XZ'),mesh)
    scene.collection.objects.link(ob)
    ob['fe_m2c_module']='EXACT_ANALYTICAL_INTERSECTION_OF_SAME_3D_CELL_SOLIDS'
    ob['fe_m2c_cultivar']=block.cultivar
    ob['fe_m2c_instance_id']=block.instance_id
    ob['fe_m2c_normal_axis']=normal_axis
    ob['fe_m2c_section_mm']=0.0
    ob['fe_m2c_intersection_count']=len(cells)
    ob['fe_m2c_source_regions']='outer_pericarp_small+outer_pericarp_large'
    ob['fe_m2c_projection']='TO_XZ_DISPLAY_PANEL_FROM_ORIGINAL_COORDINATE_PLANE'
    ob['fe_m2c_panel_origin_x']=x0
    ob['fe_m2c_panel_origin_z']=z0
    # A limited number of explicit border contours; avoid opaque clutter
    border=bpy.data.curves.new('M2c cell boundary curves','CURVE')
    border.dimensions='3D';border.resolution_u=1;border.bevel_depth=.0015;border.bevel_resolution=1
    for points in edge_lines:
        s=border.splines.new('POLY');s.points.add(len(points)-1)
        for pp,co in zip(s.points,points):pp.co=(*co,1)
        s.use_cyclic_u=True
    lines=bpy.data.objects.new('M2c boundaries '+block.cultivar+str(normal_axis),border)
    scene.collection.objects.link(lines);border.materials.append(outline_mat)
    return ob


def macro_scene(blocks,group):
    """Two mixed 3D outer-pericarp samples enlarged without changing dimensions."""
    scene=bpy.data.scenes.new('08 | M2c | mixed outer pericarp 3D macro')
    lighting(scene,12,3.9,(1550,850),tilt=True)
    scene['fe_m2c_status']='EXACT_DIAMETERS_3D_MIXED_CELLS_ARTIST_PACKING'
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.001
    ink=material('M2c | pale ink',COLORS['font'])
    frame=material('M2c | sample frame',COLORS['frame'])
    text(scene,'MIXED OUTER PERICARP  |  REAL 3D CELL SOLIDS',0,1.02,.135,ink)
    text(scene,'Big + small cells together; source size calibrated, 3D placement synthetic',0,.85,.10,ink)
    allobjects=[]
    for r,row in enumerate(blocks):
        block=row[2]
        x=-.9+1.8*r
        wire_cube(scene,block.side_mm,(x,0,0),frame)
        for region in ('outer_pericarp_large','outer_pericarp_small'):
            these=block.by_region(region)
            m=material('M2c | '+region,COLORS[region])
            ob=point_object(scene,'M2c MACRO '+block.cultivar+' '+region,
                       these,group,m,(x,0,0),block)
            allobjects.append(ob)
        text(scene,block.cultivar.upper(),x,-.62,.14,ink)
        text(scene,str(len(block.cells))+' 3D proxy solids',x,-.78,.102,ink)
    # Scientific warnings are in the source plan JSON and instance metadata.
    return scene,allobjects


def sections_scene(blocks):
    sc=bpy.data.scenes.new('07 | M2c | exact TWO ORTHOGONAL SECTIONS')
    lighting(sc,13,4.9,(1550,980),tilt=False)
    sc['fe_m2c_status']='two perpendicular planes cut SAME 3D cell centers, dimensions and source rows'
    sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=.001
    ink=material('M2c | pale ink',COLORS['font']);outline=material('M2c | outline',COLORS['outline'])
    bg=material('M2c | section background',COLORS['background'])
    region_mats={region:material('M2c | section '+region,COLORS[region]) for region in REGIONS}
    text(sc,'ORTHOGONAL CUTS  |  SAME ORIGINAL 3D OUTER-PERICARP VOLUME',0,2.12,.17,ink)
    text(sc,'One set of ellipsoid cell solids: analytical intersections with planes Z = 0 and Y = 0',0,1.90,.11,ink)
    actual=[]
    for r,block3 in enumerate(blocks):
        block=block3[2];zc=.69-r*1.58
        cultivar=block.cultivar
        for ci,axis in enumerate((2,1)):
            xc=-1.15+2.30*ci
            box(sc,'section BG '+cultivar+str(axis),(xc,.05,zc),block.side_mm,block.side_mm,bg)
            actual.append(make_section_mesh(sc,block,axis,(xc,0,zc),region_mats,outline))
            text(sc,cultivar.upper()+'  |  '+('XY (Z=0)' if axis==2 else 'XZ (Y=0)'),xc,zc+.55,.13,ink)
            count=len(section_records(block,axis))
            text(sc,f'{count} cell intersections | plane normal axis={axis}',xc,zc-.55,.11,ink)
    text(sc,'Diameters from Jeon et al. 2024 Table 5; 3D placement, anisotropy, air gaps = ARTIST hypotheses.',0,-1.78,.114,ink)
    return sc,actual


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--base',required=True,help='M2b Blender .blend')
    p.add_argument('--catalog',required=True,help='Primary numeric data JSON')
    p.add_argument('--out',required=True)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
    out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
    cat=load_catalog(a.catalog);reg=standard_registry()
    plans=[reg.plan(make_context(cat,c,id_,seed=1729)) for c,id_ in
           [('Sweet Gold','sweet'),('Jecy Gold','jecy')]]
    blocks=[build_volume(plan) for plan in plans]
    planfile=out/'m2c-tissue-volumes.json';planfile.write_text(json.dumps(plan_json(blocks),ensure_ascii=False,indent=2))
    bpy.ops.wm.open_mainfile(filepath=str(Path(a.base).resolve()))
    gn=make_shared_cell_group()
    vol,objects=volume_display_scene(blocks,gn)
    sections,secobs=sections_scene(blocks)
    macro,macroobjs=macro_scene(blocks,gn)
    archive=bpy.data.texts.new('M2c source-calibrated 3D cell solids, ARTIST packing.json')
    archive.write(planfile.read_text(encoding='utf-8'))
    base=bpy.data.scenes['01 | Fruit Platform | 4 independent contexts']
    base['fe_m2c_source_scope']='Jeon2024 Table5 diameters, NO physiological 3D packing inference'
    base['fe_m2c_number_of_valid_new_3d_samples']=len(blocks)*3
    bpy.context.window.scene=vol
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'fruit-platform-m2c.blend'))
    print('M2C_VOLUME_BUILD_OK',json.dumps({'volume_objects':len(objects),'macro_objects':len(macroobjs),'cuts':len(secobs),
         'cells':sum(len(b.cells) for row in blocks for b in row),'gn':gn.name,'blend':str(out/'fruit-platform-m2c.blend')}))

if __name__=='__main__':main()
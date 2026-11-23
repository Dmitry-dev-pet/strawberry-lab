"""Own v20 core/halo surface-relief A/B; run in Blender 5.2.4 with autoexec off.

This experiment reuses owned Strawberry Lab v19 fields and v8 sampling nodes.
It contains no Frucht code, node templates, meshes, shaders or numerical presets.
The sole A/B variable is the cell-suppression input: narrow core versus broad halo.
"""
from __future__ import annotations
import argparse, hashlib, json, sys, time
from pathlib import Path
import bpy
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
from fields import WIDTH_FACTOR, wider_graph, unpack_atlas_channel, pack_core_halo, sha_array, suppression

SOURCE_SHA='d89dd750f6f97bd7e85bce55eae0fb58af7d2a1dee9d07dc503932258a8b8110'
GRAPH_R_SHA='ffe30f3ac3dd75824afb69ca37aa500ab028b0730a40138b9df65af5e95d2eaf'
RIDGE_GAIN_MM=0.18  # ARTIST: maximum scalar coefficient, actual height=R*gain*cap/rim.

def math_node(g,op,name,a,b):
    n=g.nodes.new('ShaderNodeMath');n.operation=op;n.name=name;n.label=name
    for i,v in enumerate((a,b)):
        if isinstance(v,(int,float)):n.inputs[i].default_value=v
        else:g.links.new(v,n.inputs[i])
    return n.outputs[0]

def add_attribute(g,geometry,name,value,kind='FLOAT'):
    n=g.nodes.new('GeometryNodeStoreNamedAttribute');n.data_type=kind;n.domain='POINT'
    n.name='V20 | store '+name;n.label=name;n.inputs['Name'].default_value=name
    g.links.new(geometry,n.inputs['Geometry']);g.links.new(value,n.inputs['Value'])
    return n.outputs['Geometry']

def pack_hash(image):
    assert image.packed_file is not None
    return hashlib.sha256(bytes(image.packed_file.data)).hexdigest()

def main():
    a=argparse.ArgumentParser();a.add_argument('--source',required=True);a.add_argument('--v19-code',required=True);a.add_argument('--out',required=True)
    args=a.parse_args(sys.argv[sys.argv.index('--')+1:])
    source=Path(args.source).resolve();out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_SHA
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    assert bpy.app.version[:2]==(5,2)
    t=time.perf_counter();bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    for filename in ['strawberry-v20a-core-suppression.blend','strawberry-v20b-halo-suppression.blend']:
        assert not (out/filename).exists(),f'Refusing overwrite: {filename}'
    sys.path.insert(0,str(Path(args.v19_code).resolve()))
    from v19_graph import make_graph,validate_graph,rasterize_graph
    seeds=bpy.data.objects['SDF visible seeds | planar'];attr=seeds.data.attributes['achene_center']
    stride=len(seeds.data.vertices)//264
    anchors=np.array([attr.data[i*stride].vector[:] for i in range(264)],np.float32)
    graph=make_graph(anchors);graph_check=validate_graph(graph,anchors)
    raw_r,raw_r_info=rasterize_graph(graph)
    assert raw_r_info['field_sha256']==GRAPH_R_SHA,'Owned graph must reproduce before widening'
    raw_h,raw_h_info=rasterize_graph(wider_graph(graph))
    original=bpy.data.images['V19 | rooted 264-seed graph 192^3 rest R (ARTIST)']
    original_pack=pack_hash(original)
    pixels=np.empty((2304,3072,4),np.float32);original.pixels.foreach_get(pixels.ravel())
    core=unpack_atlas_channel(pixels,0)
    halo=np.maximum(raw_h,core).astype(np.float32)
    packed=pack_core_halo(core,halo)
    del raw_h,raw_r
    geom=bpy.data.images.new('V20 | core R and broad halo G, separate from pith (ARTIST)',width=3072,height=2304,alpha=True,float_buffer=True)
    geom.colorspace_settings.name='Non-Color'
    geom.pixels.foreach_set(packed.ravel());geom.update();geom.pack()
    geom['channel_contract']='R=existing owned graph core; G=same graph with sigma*1.8, max existing R; B=unused; A=1'
    geom['source_scene_sha256']=SOURCE_SHA
    geom['not_in_material']='Original material G=mottling, B=pith remains unchanged'
    geometry_pack=pack_hash(geom)
    # Clone only our existing trilinear sampler. This is independent project code.
    sampler=bpy.data.node_groups['V8 | original rest-space vascular field (192^3)'].copy()
    sampler.name='V20 | owned 192cubed core and halo sampler'
    sampler.interface.items_tree['vascular_intensity'].name='core'
    sampler.interface.new_socket(name='halo',in_out='OUTPUT',socket_type='NodeSocketFloat')
    for n in sampler.nodes:
        if n.bl_idname=='GeometryNodeImageTexture':n.inputs['Image'].default_value=geom
    low=math_node(sampler,'MULTIPLY','V20 | low halo slice',sampler.nodes['Separate Color'].outputs['Green'],sampler.nodes['Math.029'].outputs[0])
    high=math_node(sampler,'MULTIPLY','V20 | high halo slice',sampler.nodes['Separate Color.001'].outputs['Green'],sampler.nodes['Math.010'].outputs[0])
    h=math_node(sampler,'ADD','V20 | trilinear halo',low,high)
    sampler.links.new(h,sampler.nodes['Group Output'].inputs['halo'])
    sampler['provenance']='Copied owned v8 sampler; separate green interpolation added independently. No third-party nodes.'
    group_records={}
    for tag in ('planar','bite'):
        g=bpy.data.node_groups['SDF cutter + rest-space | '+tag];N,L=g.nodes,g.links
        assert N['V19_SCAFFOLD_SOLID_GAIN'].outputs[0].default_value==0.
        # Restore the owned original native SDF path in BOTH variants.
        # Disconnected v18 resampling/solid-tube nodes are removed, not hidden.
        L.new(N['Grid to Mesh'].outputs['Mesh'],N['Set Shade Smooth'].inputs['Geometry' if 'Geometry' in N['Set Shade Smooth'].inputs else 'Mesh'])
        to_remove=[n for n in N if n.name.startswith(('V18','V19')) or n.label.startswith(('V18','V19'))]
        for n in to_remove:N.remove(n)
        sample=N.new('GeometryNodeGroup');sample.node_tree=sampler;sample.name='V20 | geometry core halo from fixed rest coordinates'
        L.new(N['Named Attribute'].outputs['Attribute'],sample.inputs['rest_xyz'])
        core_socket=N['V8 | vessel sample from SAME 192cubed atlas'].outputs['vascular_intensity']
        halo_socket=sample.outputs['halo']
        toggle=N.new('FunctionNodeInputBool');toggle.name='V20_USE_BROAD_HALO';toggle.label='Cell smoothing: core / broad halo';toggle.boolean=False
        choose=N.new('GeometryNodeSwitch');choose.input_type='FLOAT';choose.name='V20 | select cell suppression field'
        L.new(toggle.outputs['Boolean'],choose.inputs['Switch']);L.new(core_socket,choose.inputs['False']);L.new(halo_socket,choose.inputs['True'])
        L.new(choose.outputs['Output'],N['Map Range.001'].inputs['Value'])
        assert N['V8_CELL_STRENGTH'].outputs[0].default_value==1.
        gain=N.new('ShaderNodeValue');gain.name='V20_RIDGE_GAIN_MM';gain.label='Common surface ridge coefficient, ARTIST mm';gain.outputs[0].default_value=RIDGE_GAIN_MM
        ridge0=math_node(g,'MULTIPLY','V20 | narrow core ridge',core_socket,gain.outputs[0])
        ridge=math_node(g,'MULTIPLY','V20 | ridge respects cut and skin rim',ridge0,N['Math.003'].outputs[0])
        total=math_node(g,'ADD','V20 | cell plus independent ridge',N['Math.006'].outputs[0],ridge)
        L.new(total,N['Vector Math.003'].inputs['Scale'])
        geometry=N['Store Named Attribute.002'].outputs['Geometry']
        for name,value,kind in [
            ('v20_halo',halo_socket,'FLOAT'),
            ('v20_cell_suppression',N['Map Range.001'].outputs['Result'],'FLOAT'),
            ('v20_ridge_height_mm',ridge,'FLOAT'),
            ('v20_total_height_mm',total,'FLOAT'),
            ('v20_cap_rim',N['Math.003'].outputs[0],'FLOAT'),
            ('v20_rest_normal',N['Normal'].outputs['Normal'],'FLOAT_VECTOR')]:
            geometry=add_attribute(g,geometry,name,value,kind)
        L.new(geometry,N['V8 | actual cut cell pillows'].inputs['Geometry'])
        g['v20_scope']='Continuous cut surface; core ridge independent of cell suppression. No solid tube union.'
        group_records[tag]={'nodes':len(N),'links':len(L),'cell_strength':1.,'ridge_gain_mm':RIDGE_GAIN_MM,'inherited_cap_tolerance_mm':N['Compare'].inputs[1].default_value,'inherited_voxel_size_mm':N['Mesh to SDF Grid'].inputs['Voxel Size'].default_value,'removed_unused_v18_v19_nodes':len(to_remove)}
    assert pack_hash(original)==original_pack
    rec={'hypothesis':'Only change A/B cell-suppression input from existing narrow core to broader same-graph halo.',
         'source_sha256':SOURCE_SHA,'blender':bpy.app.version_string,'graph':graph_check,'raw_original_core_reproduction':raw_r_info,
         'halo_raster':raw_h_info,'halo_sigma_factor_ARTIST':WIDTH_FACTOR,'ridge_coefficient_mm_ARTIST':RIDGE_GAIN_MM,
         'original_material_atlas_packed_sha256':original_pack,'original_material_pixels_sha256':sha_array(pixels),
         'original_material_R_sha256':sha_array(pixels[:,:,0]),'original_material_GBA_sha256':sha_array(pixels[:,:,1:]),
         'geometry_atlas_packed_sha256':geometry_pack,'geometry_core_zyx_sha256':sha_array(core),'geometry_halo_zyx_sha256':sha_array(halo),
         'halo_not_below_core':bool(np.all(halo>=core)),
         'grid_fraction_halo_above_core_by_0_05':float(np.mean(halo-core>.05)),
         'mean_cell_suppression_core':float(suppression(core).mean()),'mean_cell_suppression_halo':float(suppression(halo).mean()),
         'pith_policy':'Unchanged original material B. Ring-relative coordinate and geometric liquid are outside this single-factor experiment.',
         'groups':group_records,'variants':{}}
    np.savez_compressed(out/'core_halo_fields.npz',core=core,halo=halo)
    scene=bpy.context.scene
    scene['v20_source_sha256']=SOURCE_SHA;scene['v20_original_material_atlas_sha256']=original_pack
    scene['v20_hypothesis']=rec['hypothesis'];scene['v20_sigma_factor_ARTIST']=WIDTH_FACTOR
    scene['v20_ridge_coefficient_mm_ARTIST']=RIDGE_GAIN_MM
    bpy.context.preferences.filepaths.save_version=0
    for variant,enabled,name in [('a',False,'core'),('b',True,'halo')]:
        for tag in ('planar','bite'):
            bpy.data.node_groups['SDF cutter + rest-space | '+tag].nodes['V20_USE_BROAD_HALO'].boolean=enabled
        scene['v20_variant']=variant;scene.frame_set(20)
        path=out/f'strawberry-v20{variant}-{name}-suppression.blend'
        bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
        rec['variants'][variant]={'file':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'broad_halo':enabled}
        print('V20_SAVED',json.dumps(rec['variants'][variant]),flush=True)
    rec['build_seconds']=time.perf_counter()-t
    (out/'build_evidence.json').write_text(json.dumps(rec,indent=2)+'\n')
    print('V20_BUILD_COMPLETE',rec['build_seconds'],flush=True)

if __name__=='__main__':main()

"""Integration proof for the OWN original v19/v20 vascular core & halo algorithms.

A new field is re-rasterized from *this* seed101 264-achemes anchor coordinates;
never reuse the unrelated old v20b atlas. Retain source PR48 hull and 150^3
material atlas. Reuse ONLY our own saved v20B trilinear sampler group, with
correctly adjusted normalization for the new grid bounding box.

Original Frucht GPL/commercial nodes, objects, presets and footage: NONE.
"""
from pathlib import Path
import bpy,hashlib,sys,json,time,argparse
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v19_graph import BBOX as HISTORICAL_BBOX,make_graph,validate_graph,rasterize_graph
import v19_graph
from fields import pack_core_halo,wider_graph,sha_array
from sampler import make_sampler

PIN_PR48='bfecf691df67cafff020971368f1afc877f4bac1165e851520bdcc1773f85ce1'
BODY='Receptacle | canonical PR29 hull'
ORIGINAL_ATLAS='LIVE | ORIGINAL V0 native RGB volume atlas (150^3)'
BOUNDS=((-25.,25.),(-25.,25.),(-2.,52.))
Z_OFFSET_MM=27.
ARTIST_RIDGE_MM=.18
ARTIST_CELL_MM=.045


def node(g,bl_idname,name):
 n=g.nodes.new(bl_idname);n.name=n.label=name;return n

def wire(g,a,b):g.links.new(a,b)

def mathn(g,operation,name,a,b=None):
 n=node(g,'ShaderNodeMath',name);n.operation=operation
 for i,value in enumerate((a,b)):
  if value is None:continue
  if isinstance(value,(int,float)):n.inputs[i].default_value=value
  else:wire(g,value,n.inputs[i])
 return n.outputs[0]

def slider(g,body,key):
 n=node(g,'ShaderNodeValue','V20 bridge: live '+key)
 n.outputs[0].default_value=body[key]
 d=n.outputs[0].driver_add('default_value').driver
 v=d.variables.new();v.name='value';v.targets[0].id=body;v.targets[0].data_path=f'["{key}"]';d.expression='value'
 return n.outputs[0]

def save_attr(g,geometry,key,value):
 n=node(g,'GeometryNodeStoreNamedAttribute','V20 bridge: '+key)
 n.domain='POINT';n.data_type='FLOAT';n.inputs['Name'].default_value=key
 wire(g,geometry,n.inputs['Geometry']);wire(g,value,n.inputs['Value']);return n.outputs['Geometry']

def build(args):
 source=Path(args.source).resolve();out=Path(args.output).resolve()
 assert source.is_file() and not out.exists()
 assert hashlib.sha256(source.read_bytes()).hexdigest()==PIN_PR48
 assert bpy.app.version[:2]==(5,2)
 start=time.monotonic()
 bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
 assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
 s=bpy.context.scene;body=s.objects[BODY];mm=s.unit_settings.scale_length*1000
 assert abs(mm-22.22222276)<1e-5
 main_atlas=bpy.data.images[ORIGINAL_ATLAS]
 original_pack=hashlib.sha256(bytes(main_atlas.packed_file.data)).hexdigest()
 seeds=sorted((o for o in s.objects if o.get('role')=='achene'),key=lambda o:o.name)
 assert len(seeds)==264
 anchors=np.asarray([list(o['nonlinear_original_anchor']) for o in seeds],dtype=np.float32)
 physical=anchors*mm+np.array([0.,0.,Z_OFFSET_MM],dtype=np.float32)
 assert (physical.min(axis=0)>np.array([b[0] for b in BOUNDS])).all() and (physical.max(axis=0)<np.array([b[1] for b in BOUNDS])).all()
 # Instead of copying v20b field from a DIFFERENT seed set, rebuild *our own*
 # original connected graph exactly on the PR40 source-rest positions.
 v19_graph.BBOX=BOUNDS
 graph=make_graph(physical);graph_check=validate_graph(graph,physical)
 core,core_info=rasterize_graph(graph,192)
 raw,halo_info=rasterize_graph(wider_graph(graph),192)
 halo=np.maximum(raw,core).astype(np.float32);del raw
 assert (halo>=core).all() and halo_info['raster_dabs_clipped']==core_info['raster_dabs_clipped']==0
 pixels=pack_core_halo(core,halo)
 img=bpy.data.images.new('V20 bridge | seed101 core R halo G 192^3 ARTIST',width=3072,height=2304,alpha=True,float_buffer=True)
 img.colorspace_settings.name='Non-Color'
 img.pixels.foreach_set(pixels.ravel());img.update();img.pack()
 img['producer']='Own v19/v20 fields rebuilt for source PR48 seed101 anchors; not v20 original population'
 img['bbox_xyz_mm']=json.dumps(BOUNDS)
 img['source_sha256']=PIN_PR48
 img['channel_contract']='R=owned narrow graph core; G=same graph x1.8 Gaussian halo >= R; B=unused; A=1'
 img_pack=hashlib.sha256(bytes(img.packed_file.data)).hexdigest()
 # Independent, deterministic recreation of the *owned* V8/V20 16x12 tiled
 # trilinear sampler (sampler.py). No previous private Blender library needed.
 sampler=make_sampler(img,BOUNDS)
 assert len(sampler.nodes)>35 and len(sampler.nodes)<60
 assert [s.name for s in sampler.interface.items_tree if s.item_type=='SOCKET' and s.in_out=='OUTPUT']==['core','halo']
 sampler['field_source_sha256']=PIN_PR48
 # With rest-space mask drawn from same source 3D for ANY plane or sphere pose.
 g=body.modifiers[0].node_group
 body['sdf_use_broad_halo']=1.;body['sdf_tissue_gain']=1.
 cut=next(n for n in g.nodes if n.bl_idname=='GeometryNodeSetMaterial' and 'Cut material' in n.name)
 smooth=next(n for n in g.nodes if n.bl_idname=='GeometryNodeSetShadeSmooth')
 links=[l for l in g.links if l.from_node==cut and l.to_node==smooth]
 assert len(links)==1
 for l in links:g.links.remove(l)
 rest=node(g,'GeometryNodeInputNamedAttribute','V20 bridge: true original rest xyz')
 rest.data_type='FLOAT_VECTOR';rest.inputs['Name'].default_value='sdf_rest_position'
 rest_to_mm=node(g,'ShaderNodeVectorMath','V20 bridge: rest -> mm with canonical seed101 shift')
 rest_to_mm.operation='MULTIPLY_ADD';rest_to_mm.inputs[1].default_value=(mm,mm,mm);rest_to_mm.inputs[2].default_value=(0,0,Z_OFFSET_MM)
 wire(g,rest.outputs['Attribute'],rest_to_mm.inputs[0])
 sample=node(g,'GeometryNodeGroup','V20 bridge: core and halo from same source 3D')
 sample.node_tree=sampler;wire(g,rest_to_mm.outputs['Vector'],sample.inputs['rest_xyz_mm'])
 core_out=sample.outputs['core'];halo_out=sample.outputs['halo']
 geometry=cut.outputs['Geometry']
 geometry=save_attr(g,geometry,'sdf_v20_core',core_out)
 geometry=save_attr(g,geometry,'sdf_v20_halo',halo_out)
 # One-variable A/B of the original verified v20 core vs broad-halo cell
 # suppression; the raised narrow vascular ridge is identical in A and B.
 sel=node(g,'GeometryNodeSwitch','V20 bridge: choose suppression source core / halo')
 sel.input_type='FLOAT';wire(g,mathn(g,'GREATER_THAN','V20 bridge: use broad halo',slider(g,body,'sdf_use_broad_halo'),.5),sel.inputs['Switch'])
 wire(g,core_out,sel.inputs['False']);wire(g,halo_out,sel.inputs['True'])
 sup=node(g,'ShaderNodeMapRange','V20 bridge: owned original cell suppression curve')
 sup.clamp=True;sup.interpolation_type='SMOOTHSTEP';sup.inputs['From Min'].default_value=.04;sup.inputs['From Max'].default_value=.48;sup.inputs['To Min'].default_value=1.;sup.inputs['To Max'].default_value=.12
 wire(g,sel.outputs['Output'],sup.inputs['Value'])
 geometry=save_attr(g,geometry,'sdf_v20_cell_suppression',sup.outputs['Result'])
 # V20's original cell mechanism was actual CutFace Voronoi relief; keep
 # independent rest XYZ (not regenerated per knife, not camera UVs).
 vor=node(g,'ShaderNodeTexVoronoi','V20 bridge: own 3D source tissue cell field')
 vor.voronoi_dimensions='3D';vor.feature='DISTANCE_TO_EDGE';vor.inputs['Scale'].default_value=32.
 wire(g,rest.outputs['Attribute'],vor.inputs['Vector'])
 cell=node(g,'ShaderNodeMapRange','V20 bridge: bounded cell domes')
 cell.clamp=True;cell.interpolation_type='SMOOTHERSTEP'
 cell.inputs['From Min'].default_value=0.006;cell.inputs['From Max'].default_value=.07
 cell.inputs['To Min'].default_value=-.65;cell.inputs['To Max'].default_value=.35
 wire(g,vor.outputs['Distance'],cell.inputs['Value'])
 # Use existing SAME cut assignment field and gently fade toward cutter distance.
 selected=cut.inputs['Selection'].links[0].from_socket
 prox=next(n for n in g.nodes if n.bl_idname=='GeometryNodeProximity')
 voxel=mathn(g,'DIVIDE','V20 bridge: live voxel size in scene BU',slider(g,body,'sdf_voxel_mm'),mm)
 norm=mathn(g,'DIVIDE','V20 bridge: normalized cutter distance',prox.outputs['Distance'],voxel)
 fade=node(g,'ShaderNodeMapRange','V20 bridge: original cutter-local fade')
 fade.clamp=True;fade.interpolation_type='SMOOTHERSTEP';fade.inputs['From Min'].default_value=0.05;fade.inputs['From Max'].default_value=1.8;fade.inputs['To Min'].default_value=1.;fade.inputs['To Max'].default_value=0.
 wire(g,norm,fade.inputs['Value'])
 active=mathn(g,'GREATER_THAN','V20 bridge: mode active',slider(g,body,'sdf_mode'),.5)
 mask=mathn(g,'MULTIPLY','V20 bridge: cap face assignment × cutter',selected,fade.outputs['Result'])
 mask=mathn(g,'MULTIPLY','V20 bridge: active cut only',mask,active)
 cells=mathn(g,'MULTIPLY','V20 bridge: same source suppresses cell relief',cell.outputs['Result'],sup.outputs['Result'])
 cells=mathn(g,'MULTIPLY','V20 bridge: cell ARTIST mm',cells,ARTIST_CELL_MM)
 ridge=mathn(g,'MULTIPLY','V20 bridge: narrow vascular ridge ARTIST mm',core_out,ARTIST_RIDGE_MM)
 surface=mathn(g,'ADD','V20 bridge: cell+ridge shared displacement mm',cells,ridge)
 surface=mathn(g,'MULTIPLY','V20 bridge: only genuine cut surface',surface,mask)
 surface=mathn(g,'MULTIPLY','V20 bridge: live tissue gain',surface,slider(g,body,'sdf_tissue_gain'))
 geometry=save_attr(g,geometry,'sdf_v20_height_mm',surface)
 position=node(g,'GeometryNodeSetPosition','V20 bridge: connected native SDF cap surface relief')
 wire(g,geometry,position.inputs['Geometry'])
 normal=node(g,'GeometryNodeInputNormal','V20 bridge: actual cut mesh normal')
 scale=node(g,'ShaderNodeVectorMath','V20 bridge: height mm to normal offset')
 scale.operation='SCALE';wire(g,normal.outputs['Normal'],scale.inputs[0]);wire(g,mathn(g,'DIVIDE','V20 bridge: displacement to BU',surface,mm),scale.inputs[3])
 wire(g,scale.outputs['Vector'],position.inputs['Offset'])
 wire(g,position.outputs['Geometry'],smooth.inputs['Geometry'])
 body['sdf_use_broad_halo']=1.;body.id_properties_ui('sdf_use_broad_halo').update(min=0,max=1,description='v20 suppression from core(0) or broad halo(1), shared vascular ridge')
 body['sdf_tissue_gain']=1.;body.id_properties_ui('sdf_tissue_gain').update(min=0,max=1,description='0 original exact PR48 body, 1 v20 own core+halo relief on cut only')
 s['SDF V20 bridge']='Own v19/20 re-raster field to 264 current PR40 seed101 rest anchors, R core G halo, no Frucht nodes; v21 not integrated.'
 s['SDF V20 details']=json.dumps({'source_sha256':PIN_PR48,'sampler_provenance':'Portable own V8/V20 trilinear rebuilt by sampler.py','grid_bbox_mm_xyz':BOUNDS,'offset_z_mm':Z_OFFSET_MM,'grid_N':192,'cell_mm_ARTIST':ARTIST_CELL_MM,'ridge_mm_ARTIST':ARTIST_RIDGE_MM})
 # The source skin/material atlas must remain identical.
 assert hashlib.sha256(bytes(main_atlas.packed_file.data)).hexdigest()==original_pack
 assert all(o.get('role')!='achene' or o.modifiers[0].node_group.name.startswith('SDF | live seed vertex') for o in seeds)
 for mode in [0,1,2]:
  body['sdf_mode']=mode;body['sdf_voxel_mm']=.32
  body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
  ob=body.evaluated_get(dg);mesh=ob.to_mesh();print('V20_BRIDGE_EVAL',mode,len(mesh.vertices),'attrs',[(x.name) for x in mesh.attributes if x.name.startswith('sdf_v20')],flush=True);assert len(mesh.vertices)>1000;ob.to_mesh_clear()
 body['sdf_mode']=0;body['sdf_voxel_mm']=.20;body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update()
 out.parent.mkdir(parents=True,exist_ok=True)
 bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
 summary={'source_sha256':PIN_PR48,'sampler':'portable own V8/V20 trilinear','generated_scene_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'graph':graph_check,'raster_core':core_info,'raster_wide_halo':halo_info,'halo_not_below_core':bool((halo>=core).all()),'core_sha':sha_array(core),'halo_sha':sha_array(halo),'packed_image_sha256':img_pack,'original_material_atlas_sha256':original_pack,'new_controls':['sdf_use_broad_halo','sdf_tissue_gain'],'build_seconds':time.monotonic()-start,'status':'SCENE_BUILT_QA_PENDING','caveat':'Source PR48 seed101 .blend is pinned, only the first seed recipe is tested; no prior v20 private Blender dependency.'}
 out.with_suffix('.build.json').write_text(json.dumps(summary,indent=2)+'\n')
 print('V20_BRIDGE_CREATED',json.dumps({'scene':str(out),'sha':summary['generated_scene_sha256'],'seconds':round(summary['build_seconds'],2)}),flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--output',required=True)
 build(ap.parse_args(sys.argv[sys.argv.index('--')+1:]))

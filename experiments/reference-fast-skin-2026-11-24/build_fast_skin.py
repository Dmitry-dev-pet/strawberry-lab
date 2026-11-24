"""Independent face deletion on owned split stock; no reference graph/assets/presets."""
import bpy,sys,json,hashlib
from pathlib import Path
PIN='4cee7f472d5ebe8a9ee48b39f760ee87a5d16f3c1e2db0ee5aaffe4fcdcd0ff3'
HELPER='1fd07748a0bc668b81715d037e3ee5db8b6cad20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def gitsha(p):
 b=Path(p).read_bytes();return hashlib.sha1(('blob %d\0'%len(b)).encode()+b).hexdigest()
def main():
 src,helper,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)==PIN and gitsha(helper)==HELPER and not out.exists();sys.path.insert(0,str(helper.parent))
 from build_split import Graph,ROOT,SKIN,CUTTER,FLESH
 bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),use_scripts=False);r=bpy.data.objects[ROOT];skin=bpy.data.objects[SKIN];old=skin.modifiers[-1];assert old.node_group.name=='SL Split | preserve original skin'
 # Shared cutter mesh, voxel driver and raster settings; no shared persistent grid asserted.
 tissue=bpy.data.objects[FLESH].modifiers[0].node_group
 raster=next(n for n in tissue.nodes if n.bl_idname=='GeometryNodeMeshToSDFGrid');sample0=next(n for n in tissue.nodes if n.bl_idname=='GeometryNodeSampleGrid')
 assert raster.inputs['Band Width'].default_value==3
 g=Graph('SL Fast Skin | signed face deletion',r)
 pos=g.node('GeometryNodeInputPosition','Source face-domain position');grid=g.sdf(g.info(bpy.data.objects[CUTTER]).outputs['Geometry'],g.driven('flesh_voxel_mm'));sample=g.node('GeometryNodeSampleGrid','Signed cutter distance at face position');sample.data_type='FLOAT';sample.inputs['Interpolation'].default_value=sample0.inputs['Interpolation'].default_value;g.w(grid,sample.inputs['Grid']);g.w(pos.outputs[0],sample.inputs['Position'])
 index=g.node('GeometryNodeInputIndex','Stable source face index');geo=g.store(g.input,'sl_fast_source_face','INT','FACE',index.outputs[0]);geo=g.store(geo,'sl_fast_face_signed_mm','FLOAT','FACE',sample.outputs[0]);d=g.math('LESS_THAN',g.attr('sl_fast_face_signed_mm','FLOAT'),0.);deleted=g.delete(geo,d,'FACE');deleted.node.label='Remove negative source faces; no position edits'
 g.finish(skin,g.switch(g.math('GREATER_THAN',g.driven('split_mode'),.5),g.input,deleted));skin.modifiers.remove(old)
 bpy.context.scene['scope']='Independent Fast skin face deletion vs exact-clip control; same cutter/raster settings, unchanged flesh and seed paths; research only'
 bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()),compress=True)
 report={'source_sha':PIN,'scene_sha':sha(out),'helper_git_sha':HELPER,'node_count':len(g.g.nodes),'face_threshold_mm':0.,'band_width':3,'sample_interpolation':sample.inputs['Interpolation'].default_value,'skin_voxel_source':'flesh_voxel_mm (isolated matched-grid experiment; author uses separately configurable resolution)','skin_position_nodes':sum(n.type=='SET_POSITION' for n in g.g.nodes),'flesh_groups_unchanged':True,'anchor_digest':r['anchor_digest'],'stock_key':r['neutral_stock_key']};out.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print('BUILT',json.dumps(report),flush=True)
if __name__=='__main__':main()

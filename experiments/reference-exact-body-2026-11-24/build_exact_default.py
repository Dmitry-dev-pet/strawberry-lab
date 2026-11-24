"""Independent common-body Exact research; no author assets, code or presets.
Fast remains unchanged; Exact is an alternative native SDF path, not a weld.
"""
import bpy,sys,json,hashlib
from pathlib import Path
PIN='4cee7f472d5ebe8a9ee48b39f760ee87a5d16f3c1e2db0ee5aaffe4fcdcd0ff3'
HELPER='1fd07748a0bc668b81715d037e3ee5db8b6cad20'
EXACT='SL Exact | common labelled body'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def gitsha(p):
 b=Path(p).read_bytes();return hashlib.sha1(('blob %d\0'%len(b)).encode()+b).hexdigest()
def main():
 src,helper,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)==PIN and gitsha(helper)==HELPER and not out.exists();sys.path.insert(0,str(helper.parent))
 from build_split import Graph,ROOT,SKIN,SEEDS,FLESH,CUTTER,CAP
 bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),use_scripts=False);s=bpy.context.scene;root=bpy.data.objects[ROOT];skin=bpy.data.objects[SKIN];flesh=bpy.data.objects[FLESH]
 for key,val,lo,hi in [('exact_mode',0,0,1),('exact_voxel_mm',.20,.20,.40)]:root[key]=val;root.id_properties_ui(key).update(min=lo,max=hi)
 # Common source stock and shape group; do not consume either Fast display mesh.
 obj=skin.copy();obj.data=skin.data;obj.name=EXACT;s.collection.objects.link(obj)
 for m in list(obj.modifiers)[1:]:obj.modifiers.remove(m)
 obj['role']='Exact common body';obj.hide_set(False);obj.hide_render=False
 def active(g):return g.math('MULTIPLY',g.math('GREATER_THAN',g.driven('exact_mode'),.5),g.math('GREATER_THAN',g.driven('split_mode'),.5))
 g=Graph('SL Exact | native single body',root);vox=g.driven('exact_voxel_mm');bg=g.sdf(g.input,vox);cg=g.sdf(g.info(bpy.data.objects[CUTTER]).outputs['Geometry'],vox);bo=g.node('GeometryNodeSDFGridBoolean','Common source difference');bo.operation='DIFFERENCE';g.w(bg,bo.inputs['Grid 1']);g.w(cg,bo.inputs['Grid 2']);gm=g.node('GeometryNodeGridToMesh','One common skin and cap mesh');g.w(bo.outputs['Grid'],gm.inputs['Grid']);geo=gm.outputs['Mesh'];pos=g.node('GeometryNodeInputPosition','Final physical surface').outputs[0]
 def sample(grid,label):
  n=g.node('GeometryNodeSampleGrid',label);n.data_type='FLOAT';g.w(grid,n.inputs['Grid']);g.w(pos,n.inputs['Position']);return n.outputs[0]
 # Difference field = max(body, -cutter). Classify by dominant operand at face centres.
 bv=sample(bg,'Body signed operand');cv=sample(cg,'Cutter signed operand');geo=g.store(geo,'sl_exact_body_signed_mm','FLOAT','FACE',bv);geo=g.store(geo,'sl_exact_cutter_signed_mm','FLOAT','FACE',cv)
 cut=g.math('GREATER_THAN',g.math('MULTIPLY',g.attr('sl_exact_cutter_signed_mm','FLOAT'),-1),g.attr('sl_exact_body_signed_mm','FLOAT'));geo=g.store(geo,'sl_cut_face','BOOLEAN','FACE',cut);geo=g.material(geo,skin.data.materials[0]);geo=g.material(geo,bpy.data.materials[CAP],g.attr('sl_cut_face','BOOLEAN'))
 # Sample the original pitted skin attribute; for cap interior this is just a nearest-surface diagnostic, not skin provenance.
 near=g.node('GeometryNodeSampleNearestSurface','Transfer original pit mask');near.data_type='FLOAT';g.w(g.input,near.inputs['Mesh']);g.w(g.attr('achene_pit','FLOAT'),near.inputs['Value']);g.w(pos,near.inputs['Sample Position']);geo=g.store(geo,'achene_pit','FLOAT','POINT',near.outputs[0])
 ref=g.node('GeometryNodeGridToMesh','Uncut reference from same body grid');g.w(bg,ref.inputs['Grid']);d=g.prox(ref.outputs['Mesh']);geo=g.store(geo,'sl_edge_distance_mm','FLOAT','POINT',d.outputs['Distance']);sm=g.node('GeometryNodeSetShadeSmooth','Smooth common mesh');sm.domain='FACE';g.w(geo,sm.inputs['Geometry']);n=g.finish(obj,g.switch(active(g),g.node('GeometryNodeDeleteGeometry','Empty inactive branch').outputs[0],sm.outputs[0]))
 # Reuse previously validated native inverse/rest and pre-cell reference group exactly.
 mod=obj.modifiers.new('SL Exact | shared inverse coordinates','NODES');mod.node_group=flesh.modifiers[-1].node_group
 # Append routing only. Existing Fast algorithms and stock are not modified.
 for o in (skin,flesh):
  route=Graph('SL Quality | hide '+o.name+' in Exact',root);route.finish(o,route.switch(active(route),route.input,route.delete(route.input,True,'POINT')))
 s['scope']='Research: independent native Exact common SDF body; existing Fast; diagnostic only';root['exact_mode']=0;root['split_mode']=0;root.update_tag();bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()),compress=True)
 r={'source_sha':PIN,'scene_sha':sha(out),'helper_git_sha':HELPER,'exact_nodes':n,'fast_default':True,'default_exact_voxel_mm':.20,'body_operand':'max(body,-cutter) face-centre winner','anchor_digest':root['anchor_digest'],'stock_key':root['neutral_stock_key'],'shape_map':root['shape_map_version']};out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print('BUILT',json.dumps(r),flush=True)
if __name__=='__main__':main()

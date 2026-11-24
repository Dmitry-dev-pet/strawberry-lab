"""Independent source-informed ARTIST skin/achene materials on pinned Exact pigment.
Only shaders and immutable neutral local shading attributes on seeds are added.
No Frucht code, presets or meshes transferred."
"""
import bpy, numpy as np, sys, json, time, hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_pigment import Graph, ROOT, linear
PIN='267bdaa85d806f383e24875be46f8a056a2841574819776d734509784ffe0915'
STOCK_PIN='23beb6082f419148578ed556cc8dee0b83799b83f499df6453b161d9bb79bde6'
SKIN='Diagnostic clay | skin'; SEED='Diagnostic clay | achenes'; SEED_OBJ='SL Neutral Achenes'
FOUNDATION='SL Pigment | shared warm skin foundation v2'; GRADE='SL Pigment | fruit-wide colour grade'
PALETTE={'seed_dark':'805027','seed_gold':'B78B36','seed_cap':'E6CD86','seed_olive':'A5A05A','seed_grain':'5D401C'}
FIELDS=('sl_achene_local','sl_achene_variation','sl_achene_gradient')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def attr(mesh,k):
 a=mesh.attributes[k];vec=a.data_type=='FLOAT_VECTOR';v=np.empty(len(a.data)*(3 if vec else 1),np.float32 if vec or a.data_type=='FLOAT' else np.int32);a.data.foreach_get('vector' if vec else 'value',v);return v.reshape(-1,3) if vec else v

def seed_fields(root,stock):
 me=bpy.data.objects[SEED_OBJ].data;v=attr(me,'sl_rest_position');idx=attr(me,'sl_anchor_index');assert digest(v)==stock['objects'][SEED_OBJ]['rest_sha'] and root['anchor_digest']==stock['anchor_digest'] and root['neutral_stock_key']==stock['stock_key'];assert set(idx)==set(range(len(stock['anchor_rows'])))
 local=np.zeros_like(v);var=np.zeros(len(v),np.float32);grad=var.copy();rng=np.random.default_rng(418291);records=[]
 for row in stock['anchor_rows']:
  j=row['index'];a=row['anchor'];ids=np.flatnonzero(idx==j);assert len(ids)==row['seed_vertex_count'];assert ids[0]==row['seed_vertex_start'];n=np.asarray(a['normal']);center=np.asarray(row['seat_mm'])+.19*a['thickness_mm']*n;basis=np.array([a['side_axis'],a['long_axis'],n]);scale=np.array([a['width_mm'],a['length_mm'],a['thickness_mm']]);p=(v[ids].astype(float)-center)@basis.T/scale;assert abs(p[:,1].min()+.5)<2e-5 and abs(p[:,1].max()-.5)<2e-5
  local[ids]=p;variation=float(rng.uniform(.05,.95));var[ids]=variation;tilt=float(rng.uniform(-.34,.34));flip=-1 if rng.random()<.22 else 1;g=np.clip(.5+flip*p[:,1]+tilt*p[:,0],0,1);grad[ids]=g;records.append({'index':j,'variation':variation,'tilt':tilt,'flip':flip})
 for k,a in zip(FIELDS,(local,var,grad)):
  assert k not in me.attributes;vec=a.ndim==2;q=me.attributes.new(k,'FLOAT_VECTOR' if vec else 'FLOAT','POINT');q.data.foreach_set('vector' if vec else 'value',a.ravel())
 me.update();return {'seeds':len(records),'vertices':len(v),'attribute_sha':{k:digest(attr(me,k)) for k in FIELDS},'longitudinal_range':[float(local[:,1].min()),float(local[:,1].max())],'variation_range':[float(var.min()),float(var.max())],'gradient_range':[float(grad.min()),float(grad.max())]}

def install(root):
 root['exterior_material_mode']=0;root.id_properties_ui('exterior_material_mode').update(min=0,max=1,description='0 diagnostic exterior; 1 shared skin pigment and golden achenes (both Fast and Exact)')
 skin=bpy.data.materials[SKIN];seed=bpy.data.materials[SEED]
 def select(q,bs):
  out=next(n for n in q.N if n.type=='OUTPUT_MATERIAL' and n.is_active_output);old=out.inputs['Surface'].links[0].from_socket;assert old.node.bl_idname=='ShaderNodeBsdfPrincipled';flag=q.m('GREATER_THAN',q.drive(root,'exterior_material_mode'),.5,'exterior enabled');mix=q.n('ShaderNodeMixShader','old or exterior');q.w(flag,mix.inputs[0]);q.w(old,mix.inputs[1]);q.w(bs.outputs[0],mix.inputs[2]);q.w(mix.outputs[0],out.inputs['Surface']);q.layout()
 q=Graph(skin.node_tree,'Exterior | ');rest=q.attr('sl_rest_position',True);pit=q.attr('achene_pit');base=q.grp(bpy.data.node_groups[FOUNDATION],'same pigment as flesh rim',{'Rest':rest});col=q.grp(bpy.data.node_groups[GRADE],'fruit-wide grade',{'Color':base});shadow=q.remap(pit,.03,.85,1.,.61,'darken pit interiors');col=q.mix(1.,col,shadow,'pit pigment attenuation','MULTIPLY');
 grain=q.noise(rest,5.5,'fine organic pores');wrinkles=q.noise(q.vec('MULTIPLY',rest,(1.8,1.8,.32),'elongated skin detail'),1.7,'longitudinal fine wrinkles');detail=q.m('ADD',q.m('MULTIPLY',grain,.68,'pore contribution'),q.m('MULTIPLY',wrinkles,.32,'wrinkle contribution'),'skin microstructure');bump=q.n('ShaderNodeBump','micropores and fine folds');bump.inputs['Strength'].default_value=.23;bump.inputs['Distance'].default_value=.018;q.w(detail,bump.inputs['Height']);
 rough=q.m('MINIMUM',q.m('ADD',q.remap(grain,.16,.84,.24,.38,'variable wax gloss'),q.remap(pit,.08,.85,0.,.32,'reduce pit gloss'),'combine roughness'),.70,'bounded roughness');bs=q.n('ShaderNodeBsdfPrincipled','wax skin ARTIST');q.w(col,bs.inputs['Base Color']);q.w(rough,bs.inputs['Roughness']);q.w(bump.outputs['Normal'],bs.inputs['Normal']);bs.inputs['IOR'].default_value=1.43;bs.inputs['Subsurface Weight'].default_value=.28;bs.inputs['Subsurface Scale'].default_value=.24;bs.inputs['Subsurface Radius'].default_value=(1.,.43,.24);q.w(q.remap(pit,.05,.8,.22,.025,'less wax in pits'),bs.inputs['Coat Weight']);bs.inputs['Coat Roughness'].default_value=.24;select(q,bs)
 q=Graph(seed.node_tree,'Exterior | ');local=q.attr(FIELDS[0],True);var=q.attr(FIELDS[1]);grad=q.attr(FIELDS[2]);C=lambda k:linear(PALETTE[k]);mid=q.mix(var,C('seed_gold'),C('seed_olive'),'individual gold to olive variation');col=q.mix(q.remap(grad,.10,.70,0.,1.,'dark bottom to warm shell'),C('seed_dark'),mid,'longitudinal colour');col=q.mix(q.remap(grad,.69,.98,0.,.82,'light seed cap'),col,C('seed_cap'),'light tip');grain=q.noise(local,13.,'local dark grain');islands=q.noise(local,3.2,'small colour islands');col=q.mix(q.remap(grain,.66,.90,0.,.36,'dark fine grains'),col,C('seed_grain'),'grain tint');col=q.mix(1.,col,q.remap(islands,.08,.92,.83,1.12,'seed local brightness'),'small islands','MULTIPLY');bump=q.n('ShaderNodeBump','fine shell relief');bump.inputs['Strength'].default_value=.24;bump.inputs['Distance'].default_value=.012;q.w(grain,bump.inputs['Height']);bs=q.n('ShaderNodeBsdfPrincipled','gold translucent seed ARTIST');q.w(col,bs.inputs['Base Color']);q.w(q.remap(grain,.1,.9,.30,.46,'seed shell roughness'),bs.inputs['Roughness']);q.w(bump.outputs['Normal'],bs.inputs['Normal']);bs.inputs['IOR'].default_value=1.46;bs.inputs['Subsurface Weight'].default_value=.32;bs.inputs['Subsurface Scale'].default_value=.08;bs.inputs['Subsurface Radius'].default_value=(1.,.55,.30);bs.inputs['Transmission Weight'].default_value=.06;bs.inputs['Coat Weight'].default_value=.14;select(q,bs)
 return {m.name:sum(n.name.startswith('Exterior | ') for n in m.node_tree.nodes) for m in (skin,seed)}

def main():
 src,stockpath,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)==PIN and sha(stockpath)==STOCK_PIN and not out.exists();t=time.perf_counter();bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),use_scripts=False);root=bpy.data.objects[ROOT];r=seed_fields(root,json.loads(stockpath.read_text()));nodes=install(root);root.update_tag();bpy.context.view_layer.update();bpy.context.scene['scope']='ARTIST exterior skin and achene materials; shared skin/flesh foundation; geometry frozen; no calyx';bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()),compress=True);r.update(source_sha=PIN,scene_sha=sha(out),stock_receipt_sha=STOCK_PIN,shader_nodes=nodes,seed_palette_srgb_ARTIST=PALETTE,default_exterior_mode=0,scope='Exterior shaders and seed shading attributes only; same skin pigment and grade as revised cap; seed grade independent; no calyx',elapsed_seconds=time.perf_counter()-t);out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print('BUILT',json.dumps(r),flush=True)
if __name__=='__main__':main()

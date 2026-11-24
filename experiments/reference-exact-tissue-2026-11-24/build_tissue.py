"""Independent ring field on neutral stock and cut-interior relief. ARTIST only.
Reuse owned ring and sampler algorithms; no Frucht source or assets transferred.
"""
import sys,hashlib,json,math,time
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'deps'))
from build_split import Graph,ROOT,SKIN,SEEDS
from ring_field import N,BOUNDS,SEED,make_graph,validate_graph,raster,ring_relative,sha as array_sha
from sampler import make_sampler
PIN='2e31a68dba83e689b55b5599a7f2a13a34a9f3fb08dd09b4eff055c31c108224'
EXACT='SL Exact | common labelled body'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def gitsha(p):
 b=Path(p).read_bytes();return hashlib.sha1(('blob %d\0'%len(b)).encode()+b).hexdigest()
def coords(m):
 a=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',a);return a.reshape(-1,3)
def attr(m,name):
 x=m.attributes[name];vec=x.data_type=='FLOAT_VECTOR';a=np.empty(len(x.data)*(3 if vec else 1),np.float32 if vec or x.data_type=='FLOAT' else np.bool_ if x.data_type=='BOOLEAN' else np.int32);x.data.foreach_get('vector' if vec else 'value',a);return a.reshape(-1,3) if vec else a

def make_field(root,stock,field,graph):
 anchors=bpy.data.objects['SL Anchor Set'].data;seats=bpy.data.objects['SL Pit Seats'].data;seeds=bpy.data.objects[SEEDS].data;hull=bpy.data.objects[SKIN].data
 assert root['anchor_digest']==stock['anchor_digest'] and root['neutral_stock_key']==stock['stock_key']
 for name in ('SL Anchor Set','SL Pit Seats',SEEDS,SKIN):assert array_sha(coords(bpy.data.objects[name].data))==stock['objects'][name]['rest_sha']
 count=root['count'];idx=attr(seeds,'sl_anchor_index');assert set(idx)==set(range(count));assert np.array_equal(attr(anchors,'sl_anchor_index'),np.arange(count));assert np.array_equal(attr(seats,'sl_anchor_index'),np.arange(count))
 # Neutral seed centres from actual saved seating transforms; meshes are realised, not instances.
 rows=stock['anchor_rows'];assert all(r['index']==i for i,r in enumerate(rows))
 a=np.asarray([r['seat_mm'] for r in rows])+np.asarray([r['anchor']['normal'] for r in rows])*(.19*np.array([r['anchor']['thickness_mm'] for r in rows]))[:,None]
 sv=coords(seeds);centroid=np.stack([sv[idx==i].mean(axis=0) for i in range(count)]);assert np.max(np.linalg.norm(centroid-a,axis=1))<1.
 segs=make_graph(a);report=validate_graph(segs,a);segs2=make_graph(a);assert all(np.array_equal(x['points'],y['points']) and np.array_equal(x['sigma'],y['sigma']) for x,y in zip(segs,segs2))
 hull.calc_loop_triangles();tree=BVHTree.FromPolygons(coords(hull).tolist(),[tuple(t.vertices) for t in hull.loop_triangles],all_triangles=True);points=np.concatenate([s['points'] for s in segs]);margin=[]
 for p in points:
  hit,no,_,_=tree.find_nearest(Vector(p));margin.append(float((hit-Vector(p)).dot(no)))
 report.update(sampled_points=len(points),min_sampled_inside_margin_mm=min(margin),outside_samples=int(sum(x<-.02 for x in margin)),max_seed_centroid_offset_mm=float(np.linalg.norm(centroid-a,axis=1).max()));print('GRAPH',json.dumps(report),flush=True);assert min(margin)>0,report
 R,cr=raster(segs,1.);H,hr=raster(segs,1.8);H=np.maximum(H,R);B=ring_relative(a);assert np.isfinite(R).all() and np.isfinite(H).all() and np.isfinite(B).all() and not cr['clipped'] and not hr['clipped']
 key=hashlib.sha256(json.dumps({'anchor_digest':root['anchor_digest'],'neutral_stock_key':root['neutral_stock_key'],'centres_sha':array_sha(a),'algorithm_git_sha':gitsha(HERE/'deps/ring_field.py'),'bounds':BOUNDS.tolist(),'n':N,'seed':SEED,'halo_factor':1.8,'coordinate_map':root['shape_map_version']},sort_keys=True,separators=(',',':')).encode()).hexdigest()
 np.savez_compressed(field,core=R,halo=H,ring_relative=B,seed_centres=a,anchor_ids=np.array([r['id'] for r in rows]),bounds=BOUNDS)
 graph.write_text(json.dumps({'dependency_key':key,'anchor_digest':root['anchor_digest'],'segments':[{**s,'points':s['points'].tolist(),'sigma':s['sigma'].tolist(),'anchor_id':rows[s['seed_id']]['id'] if s['seed_id'] is not None else None} for s in segs]},separators=(',',':'))+'\n')
 pix=np.zeros((2304,3072,4),np.float32);pix[:,:,3]=1.
 for z in range(N):
  y,x=divmod(z,16);pix[y*N:(y+1)*N,x*N:(x+1)*N,:3]=np.stack([R[z],H[z],B[z]],axis=-1)
 img=bpy.data.images.new('SL Exact | new neutral vascular R H B',width=3072,height=2304,alpha=True,float_buffer=True);img.colorspace_settings.name='Non-Color';img.pixels.foreach_set(pix.ravel());img.update();img.pack();root['sl_vascular_dependency_key']=key;img['dependency_key']=key;img['anchor_digest']=root['anchor_digest']
 report.update(dependency_key=key,anchor_digest=root['anchor_digest'],stock_key=root['neutral_stock_key'],seed_centres_sha=array_sha(a),core_sha=array_sha(R),halo_sha=array_sha(H),ring_sha=array_sha(B),raster_core=cr,raster_halo=hr,field_sha=sha(field),graph_sha=sha(graph),packed_image_sha=hashlib.sha256(bytes(img.packed_file.data)).hexdigest());return img,report

def install(root,obj,img):
 sampler=make_sampler(img,BOUNDS.tolist());sampler.name='SL Exact | rest-space R H B trilinear sampler';sampler.interface.new_socket(name='ring_relative',in_out='OUTPUT',socket_type='NodeSocketFloat');N0,L0=sampler.nodes,sampler.links;out=next(n for n in N0 if n.type=='GROUP_OUTPUT');splits=[n for n in N0 if n.bl_idname=='FunctionNodeSeparateColor'];assert len(splits)==2
 add=out.inputs['core'].links[0].from_node;mults=[s.links[0].from_node for s in add.inputs[:2]];vals=[]
 for mul in mults:
  links=[l for s in mul.inputs[:2] for l in s.links];split=next(l.from_node for l in links if l.from_node in splits);weight=next(l.from_socket for l in links if l.from_node not in splits);m=N0.new('ShaderNodeMath');m.operation='MULTIPLY';L0.new(split.outputs['Blue'],m.inputs[0]);L0.new(weight,m.inputs[1]);vals.append(m.outputs[0])
 addb=N0.new('ShaderNodeMath');addb.operation='ADD';L0.new(vals[0],addb.inputs[0]);L0.new(vals[1],addb.inputs[1]);L0.new(addb.outputs[0],out.inputs['ring_relative'])
 root['tissue_gain']=0.;root.id_properties_ui('tissue_gain').update(min=0.,max=1.,description='Research: 0 field diagnostics, 1 cell/vascular relief on Exact cut interior')
 g=Graph('SL Exact | shared vascular field and cell relief',root)
 def vec(op,a,b=None):
  n=g.node('ShaderNodeVectorMath',op);n.operation=op;g.w(a,n.inputs[0]);
  if b is not None:g.w(b,n.inputs['Scale'] if op=='SCALE' else n.inputs[1])
  return n.outputs['Value' if op in ('LENGTH','DISTANCE','DOT_PRODUCT') else 'Vector']
 def remap(x,lo,hi,a,b):
  n=g.node('ShaderNodeMapRange','Smooth transition');n.clamp=True;n.interpolation_type='SMOOTHERSTEP';g.w(x,n.inputs['Value']);g.w(lo,n.inputs['From Min']);g.w(hi,n.inputs['From Max']);g.w(a,n.inputs['To Min']);g.w(b,n.inputs['To Max']);return n.outputs['Result']
 rest=g.attr('sl_rest_position','FLOAT_VECTOR');sg=g.node('GeometryNodeGroup','One packed neutral vascular field');sg.node_tree=sampler;g.w(rest,sg.inputs['rest_xyz_mm']);geo=g.input
 for key in ('core','halo','ring_relative'):geo=g.store(geo,'sl_vascular_'+key,'FLOAT','POINT',sg.outputs[key])
 # Explicit face float -> point average. Only points incident exclusively to cap faces may move.
 geo=g.store(geo,'sl_cap_face_weight','FLOAT','FACE',g.attr('sl_cut_face','BOOLEAN'));interior=g.math('GREATER_THAN',g.attr('sl_cap_face_weight','FLOAT'),.999999);geo=g.store(geo,'sl_cell_interior','BOOLEAN','POINT',interior)
 # Prior owned smooth-centre field adapted to mm. No additional subdivision in this gate.
 r=vec('LENGTH',vec('MULTIPLY',rest,(1.,1.,0.)));inner=g.math('POWER',math.e,g.math('MULTIPLY',g.math('MULTIPLY',r,r),-1/(.38*22.22222276)**2));local=g.math('ADD',1.,g.math('MULTIPLY',inner,.55))
 noise=g.node('ShaderNodeTexNoise','Neutral coordinate warp');noise.noise_dimensions='3D';g.w(rest,noise.inputs['Vector']);noise.inputs['Scale'].default_value=4.3/22.22222276;noise.inputs['Detail'].default_value=2.
 warp=vec('SCALE',vec('SUBTRACT',noise.outputs['Color'],(.5,.5,.5)),.022*22.22222276);co=vec('SCALE',vec('MULTIPLY',vec('ADD',rest,warp),(1.,1.,.87)),local)
 vor=g.node('ShaderNodeTexVoronoi','Smooth nearest centre');vor.voronoi_dimensions='3D';vor.feature='SMOOTH_F1';g.w(co,vor.inputs['Vector']);vor.inputs['Scale'].default_value=29./22.22222276;vor.inputs['Smoothness'].default_value=.34
 dome=remap(vor.outputs['Distance'],.18,.81,1.,0.);fade=remap(g.attr('sl_edge_distance_mm','FLOAT'),.04,1.05,0.,1.);supp=remap(g.attr('sl_vascular_halo','FLOAT'),.04,.48,1.,.12)
 ridge=g.math('ADD',g.math('MULTIPLY',g.attr('sl_vascular_core','FLOAT'),.12),g.math('MULTIPLY',g.attr('sl_vascular_halo','FLOAT'),.045))
 for key,value in [('sl_cell_dome',dome),('sl_cell_edge_fade',fade),('sl_vascular_cell_multiplier',supp),('sl_vascular_ridge_mm',ridge)]:geo=g.store(geo,key,'FLOAT','POINT',value)
 height=g.math('MULTIPLY',g.math('MULTIPLY',g.math('ADD',g.math('MULTIPLY',g.math('MULTIPLY',g.attr('sl_cell_dome','FLOAT'),.145),g.attr('sl_vascular_cell_multiplier','FLOAT')),g.attr('sl_vascular_ridge_mm','FLOAT')),g.attr('sl_cell_edge_fade','FLOAT')),g.math('MULTIPLY',g.driven('tissue_gain'),g.attr('sl_cell_interior','BOOLEAN')))
 geo=g.store(geo,'sl_cell_height_mm','FLOAT','POINT',height);move=g.node('GeometryNodeSetPosition','Cut interior only');g.w(geo,move.inputs['Geometry']);g.w(g.attr('sl_cell_interior','BOOLEAN'),move.inputs['Selection']);g.w(vec('SCALE',vec('NORMALIZE',g.attr('sl_reference_normal','FLOAT_VECTOR')),g.attr('sl_cell_height_mm','FLOAT')),move.inputs['Offset']);nodes=g.finish(obj,move.outputs[0]);return nodes,len(sampler.nodes)

def main():
 src,stock,out=map(Path,sys.argv[sys.argv.index('--')+1:]);assert sha(src)==PIN and not out.exists();assert gitsha(HERE/'deps/ring_field.py')=='14af1776a31c7afe393866e625391f17598e399d';assert gitsha(HERE/'deps/sampler.py')=='6d691d6bf1a95679b947d6eaa4bcd25406049c3a';assert gitsha(HERE/'deps/build_split.py')=='1fd07748a0bc668b81715d037e3ee5db8b6cad20';assert sha(stock)=='23beb6082f419148578ed556cc8dee0b83799b83f499df6453b161d9bb79bde6';t=time.perf_counter();bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),use_scripts=False);root=bpy.data.objects[ROOT];obj=bpy.data.objects[EXACT];assert abs(bpy.context.scene.unit_settings.scale_length-.001)<1e-8
 field=out.with_name('vascular-field.npz');graph=out.with_name('vascular-graph.json');img,r=make_field(root,json.loads(stock.read_text()),field,graph);r['tissue_nodes'],r['sampler_nodes']=install(root,obj,img);bpy.context.scene['scope']='Exact tissue research: rebuilt neutral-stock vascular field, optional cap-interior cell relief; no final materials';bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()),compress=True);r.update(scene_sha=sha(out),source_sha=PIN,elapsed_seconds=time.perf_counter()-t,tissue_gain_default=0.);out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print('BUILT',json.dumps(r),flush=True)
if __name__=='__main__':main()

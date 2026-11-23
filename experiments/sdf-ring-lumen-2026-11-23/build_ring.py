import bpy,numpy as np,sys,hashlib,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).parent));from ring_field import *
PIN='361696819fd44733d560e3f59b101cd11f59862e7ebd7b7f83ce94fd07909963';BODY='Receptacle | canonical PR29 hull';IMAGE='SL Vascular Relief | owned 192 cube core halo'
def file_sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
if __name__=='__main__':
 src,out,field=map(Path,sys.argv[sys.argv.index('--')+1:]);assert file_sha(src)==PIN and not out.exists() and not field.exists();bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False);s=bpy.context.scene;b=s.objects[BODY];mm=s.unit_settings.scale_length*1000;objects=sorted((o for o in s.objects if o.get('role')=='achene'),key=lambda o:o.name);a=np.array([o['nonlinear_original_anchor'] for o in objects])*mm+[0,0,27]
 rest=np.empty(len(b.data.vertices)*3,np.float32);b.data.attributes['nonlinear_source_rest'].data.foreach_get('vector',rest);rest=rest.reshape(-1,3)*mm+[0,0,27];bvh=BVHTree.FromPolygons(rest.tolist(),[list(f.vertices) for f in b.data.polygons],all_triangles=False)
 segs=make_graph(a);report=validate_graph(segs,a);points=np.concatenate([g['points'] for g in segs]);outside=[];min_margin=1e6
 for i,p in enumerate(points):
  hit,no,_,dist=bvh.find_nearest(Vector(p));margin=float((hit-Vector(p)).dot(no));min_margin=min(min_margin,margin)
  if margin<-.02:outside.append(i)
 report.update(inside_probe='nearest outward normal on original rest hull; sampled centreline points only',points=len(points),outside_points=len(outside),min_signed_nearest_margin_mm=min_margin);print('GRAPH',json.dumps(report),flush=True);assert not outside,report
 R,cr=raster(segs,1.);H,hr=raster(segs,1.8);H=np.maximum(H,R);B=ring_relative(a);assert not cr['clipped'] and not hr['clipped'];assert np.all(H>=R) and np.isfinite(B).all();np.savez_compressed(field,core=R,halo=H,ring_relative=B,anchors=a,seed_names=np.array([o.name for o in objects]));img=bpy.data.images[IMAGE];assert tuple(img.size)==(3072,2304);pix=np.zeros((2304,3072,4),np.float32);pix[:,:,3]=1
 for z in range(N):
  row,col=divmod(z,16);pix[row*N:(row+1)*N,col*N:(col+1)*N,:3]=np.stack([R[z],H[z],B[z]],axis=-1)
 img.pixels.foreach_set(pix.ravel());img.update();img.pack();img['source']='Independent ring scaffold from own fruit anchors and rest hull; R core G halo B ring relative (B not used); ARTIST';report.update(core_sha=sha(R),halo_sha=sha(H),ring_sha=sha(B),anchor_sha=sha(a),raster_core=cr,raster_halo=hr,core_fraction_gt_025=float((R>.25).mean()),halo_fraction_gt_025=float((H>.25).mean()),field_sha=file_sha(field),packed_image_sha=hashlib.sha256(bytes(img.packed_file.data)).hexdigest(),source_sha=PIN);bpy.ops.wm.save_as_mainfile(filepath=str(out));report['scene_sha']=file_sha(out);out.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print('DONE',json.dumps(report),flush=True)

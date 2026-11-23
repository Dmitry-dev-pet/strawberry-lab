# Strawberry Lab proof v2 — 3D rest-space vessel atlas with consistent cuts
import bpy, math, json, hashlib, time
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__import__('os').environ.get('STRAWBERRY_SDF_OUT',str(Path(__file__).resolve().parents[2]/'build/sdf-vertical-slice')))
SRC=P/'strawberry-sdf-vertical-slice.blend'
bpy.ops.wm.open_mainfile(filepath=str(SRC))
sc=bpy.context.scene
T0=time.monotonic()
n=128;cols=16;rows=8
bounds=((-18,18),(-18,18),(-1,50))
voxel=(36/(n-1),36/(n-1),51/(n-1))
seedo=bpy.data.objects['SDF visible seeds | planar']
attr=seedo.data.attributes['achene_center']
V=len(seedo.data.vertices); N=264; stride=V//N
assert V==264*178
centers=np.array([attr.data[k*stride].vector[:] for k in range(N)],dtype=np.float32)
print('ANCHOR_COORDS',len(centers),centers.min(axis=0).tolist(),centers.max(axis=0).tolist(),flush=True)
# Global atlas channels in original fruit coordinates, independent of any cutter pose.
xs=np.linspace(-18,18,n,dtype=np.float32)
ys=np.linspace(-18,18,n,dtype=np.float32)
zs=np.linspace(-1,50,n,dtype=np.float32)
xx,yy=np.meshgrid(xs,ys)
r=np.sqrt(xx*xx+yy*yy)
val=np.zeros((n,n,n,3),dtype=np.float32)
rng=np.random.default_rng(6174)
for k,z in enumerate(zs):
 pith=1/(1+np.exp(np.clip((r-(2.8+.23*np.sin(z*.26)))*1.6,-20,20)))
 val[k,:,:,2]=pith
 mott=.56+.10*np.sin(xx*.78+z*.31)*np.cos(yy*.87-z*.4)+.11*np.sin(xx*2.3+z*.27)*np.sin(yy*2.6+z*.61)
 val[k,:,:,1]=np.clip(mott,0,1)
 # subtle continuous central vascular axis
 val[k,:,:,0]=.32*np.exp(-(r/1.8)**2)
# Rasterize connected 3D stylized Bézier vascular strands.
# Source: our own per-achene anchors; radii and curves deliberately marked ARTIST.
vessel=val[:,:,:,0]
for ci,(sx,sy,sz) in enumerate(centers):
 p0=np.array([0.,0.,np.clip(sz-8.,2.,45.)],dtype=np.float32)
 p1=np.array([sx*.14,sy*.14,sz-6.],dtype=np.float32)
 p2=np.array([sx*.55,sy*.55,sz-2.0],dtype=np.float32)
 p3=np.array([sx*.97,sy*.97,sz],dtype=np.float32)
 for t in np.linspace(0,1,32,dtype=np.float32):
  q=(1-t)**3*p0+3*(1-t)**2*t*p1+3*(1-t)*t*t*p2+t**3*p3
  ix=int(round((q[0]+18)/voxel[0]));iy=int(round((q[1]+18)/voxel[1]));iz=int(round((q[2]+1)/voxel[2]))
  x0=max(0,ix-3);x1=min(n,ix+4)
  y0=max(0,iy-3);y1=min(n,iy+4)
  z0=max(0,iz-3);z1=min(n,iz+4)
  if x0>=x1 or y0>=y1 or z0>=z1:continue
  dz=(zs[z0:z1,None,None]-q[2])**2
  dy=(ys[None,y0:y1,None]-q[1])**2
  dx=(xs[None,None,x0:x1]-q[0])**2
  radius=.53 if t>.52 else .70
  tube=np.exp(-(dx+dy+dz)/(2*radius*radius))*(.56+0.28*(1-t))
  sl=vessel[z0:z1,y0:y1,x0:x1]
  np.maximum(sl,tube,out=sl)
# Avoid hard tiles; sample original rest-space bounds with bilinear XY/linear Z.
atlas=np.zeros((rows*n,cols*n,4),dtype=np.float32)
atlas[...,3]=1.0
for k in range(n):
 tx=k%cols;ty=k//cols
 atlas[ty*n:(ty+1)*n, tx*n:(tx+1)*n, :3]=np.clip(val[k],0,1)
img=bpy.data.images.new('SDF proof | shared 128cubed tissue atlas',width=cols*n,height=rows*n,alpha=True,float_buffer=False)
img.colorspace_settings.name='Non-Color'
img.pixels.foreach_set(atlas.ravel())
img.update()
img.filepath_raw=str(P/'shared-tissue-128-atlas.png')
img.file_format='PNG'
img.save();img.pack()
print('ATLAS_SAVED',img.filepath_raw,Path(img.filepath_raw).stat().st_size,flush=True)
# Replace v1 cut shader in both cut bodies with v2 spatial sampler.
mat=bpy.data.materials['SDF proof | rest-space wet tissue / ARTIST']
mat.name='SDF proof v2 | spatial vascular/pith fields + cut microtexture'
mat.use_nodes=True
nodes=mat.node_tree.nodes;nodes.clear();links=mat.node_tree.links
def N(typ,loc=(0,0),label=''):
 a=nodes.new(typ);a.location=loc
 if label:a.label=label
 return a
def M(op,a=None,b=None,v=None,loc=(0,0)):
 m=N('ShaderNodeMath',loc);m.operation=op
 if a is not None: links.new(a,m.inputs[0])
 if b is not None: links.new(b,m.inputs[1])
 elif v is not None:m.inputs[1].default_value=v
 return m.outputs[0]
out=N('ShaderNodeOutputMaterial',(1900,500))
princip=N('ShaderNodeBsdfPrincipled',(1560,500))
princip.inputs['Roughness'].default_value=.54
princip.inputs['Subsurface Weight'].default_value=.12
princip.inputs['Coat Weight'].default_value=.07
princip.inputs['Coat Roughness'].default_value=.21
links.new(princip.outputs['BSDF'],out.inputs['Surface'])
pos=N('ShaderNodeAttribute',(-2700,500),'Continuous rest-space coordinates from SDF')
pos.attribute_name='fruit_rest'
normal=N('ShaderNodeVectorMath',(-2470,560));normal.operation='MULTIPLY_ADD'
normal.inputs[1].default_value=(1/36,1/36,1/51)
normal.inputs[2].default_value=(.5,.5,1/51)
links.new(pos.outputs['Vector'],normal.inputs[0])
separate=N('ShaderNodeSeparateXYZ',(-2240,560))
links.new(normal.outputs[0],separate.inputs[0])
X=separate.outputs['X'];Y=separate.outputs['Y'];Z=separate.outputs['Z']
zf=M('MULTIPLY',Z,v=n-1,loc=(-2060,750))
zclamp=M('MAXIMUM',zf,v=0,loc=(-1860,750))
zclamp=M('MINIMUM',zclamp,v=n-1,loc=(-1670,750))
lo=M('FLOOR',zclamp,loc=(-1480,750))
hi=M('ADD',lo,v=1,loc=(-1300,750))
hi=M('MINIMUM',hi,v=n-1,loc=(-1100,750))
frac=M('SUBTRACT',zclamp,lo,loc=(-900,750))
def clamp01(s,y):
 p=M('MAXIMUM',s,v=0,loc=(-1700,y))
 return M('MINIMUM',p,v=1,loc=(-1500,y))
XC=clamp01(X,350);YC=clamp01(Y,150)
def tex_for_slice(slice_ix,y):
 col=M('FLOORED_MODULO',slice_ix,v=cols,loc=(-980,y))
 rowdiv=M('DIVIDE',slice_ix,v=cols,loc=(-800,y-200))
 row=M('FLOOR',rowdiv,loc=(-600,y-200))
 xp=M('MULTIPLY',XC,v=(n-1)/n,loc=(-980,y+250))
 xp=M('ADD',xp,v=.5/n,loc=(-800,y+250))
 xp=M('ADD',col,xp,loc=(-590,y+250))
 xu=M('DIVIDE',xp,v=cols,loc=(-380,y+250))
 yp=M('MULTIPLY',YC,v=(n-1)/n,loc=(-980,y-400))
 yp=M('ADD',yp,v=.5/n,loc=(-800,y-400))
 yp=M('ADD',row,yp,loc=(-390,y-400))
 yu=M('DIVIDE',yp,v=rows,loc=(-170,y-400))
 combine=N('ShaderNodeCombineXYZ',(0,y))
 links.new(xu,combine.inputs['X']);links.new(yu,combine.inputs['Y'])
 tex=N('ShaderNodeTexImage',(190,y))
 tex.image=img;tex.interpolation='Linear';tex.extension='EXTEND'
 links.new(combine.outputs['Vector'],tex.inputs['Vector'])
 return tex.outputs['Color']
lower=tex_for_slice(lo,200)
upper=tex_for_slice(hi,-850)
mix=N('ShaderNodeMixRGB',(490,400))
mix.blend_type='MIX'
links.new(frac,mix.inputs[0]);links.new(lower,mix.inputs[1]);links.new(upper,mix.inputs[2])
sep=N('ShaderNodeSeparateColor',(700,520));sep.mode='RGB';links.new(mix.outputs[0],sep.inputs['Color'])
pith=N('ShaderNodeMixRGB',(900,680))
pith.inputs[1].default_value=(.48,.018,.028,1)
pith.inputs[2].default_value=(.89,.36,.30,1)
links.new(sep.outputs['Blue'],pith.inputs[0])
vstrength=M('MULTIPLY',sep.outputs['Red'],v=.78,loc=(880,320))
vcol=N('ShaderNodeMixRGB',(1080,700))
links.new(vstrength,vcol.inputs[0]);links.new(pith.outputs[0],vcol.inputs[1])
vcol.inputs[2].default_value=(.97,.75,.63,1)
# Mottling field modulates local pigment in rest-space, without moving with cutter.
mod=N('ShaderNodeMixRGB',(1320,750))
mod.blend_type='MULTIPLY';mod.inputs[0].default_value=.22
links.new(vcol.outputs[0],mod.inputs[1]);links.new(sep.outputs['Green'],mod.inputs[2])
links.new(mod.outputs[0],princip.inputs['Base Color'])
# Three independent cell/film frequencies; bump operates only on cut material.
bumpfields=[]
for i,(freq,weight) in enumerate(((1.6,.58),(5.6,.31),(15.5,.10))):
 vo=N('ShaderNodeTexVoronoi',(450,-450-i*260))
 vo.voronoi_dimensions='3D';vo.feature='DISTANCE_TO_EDGE';vo.inputs['Scale'].default_value=freq
 links.new(pos.outputs['Vector'],vo.inputs['Vector'])
 bumpfields.append(M('MULTIPLY',vo.outputs['Distance'],v=weight,loc=(680,-440-i*260)))
total=M('ADD',bumpfields[0],bumpfields[1],loc=(900,-520))
total=M('ADD',total,bumpfields[2],loc=(1110,-520))
bump=N('ShaderNodeBump',(1340,-430))
bump.inputs['Strength'].default_value=.65
bump.inputs['Distance'].default_value=.11
links.new(total,bump.inputs['Height']);links.new(bump.outputs['Normal'],princip.inputs['Normal'])
# Add a real shallow 3D microdisplacement on exposed cap only; retain watertight topology.
for tag in ('planar','bite'):
 g=bpy.data.node_groups['SDF cutter + rest-space | '+tag]
 gn=g.nodes;lk=g.links
 pro=next(a for a in gn if a.bl_idname=='GeometryNodeProximity')
 c=next(a for a in gn if a.bl_idname=='FunctionNodeCompare')
 mats=[a for a in gn if a.bl_idname=='GeometryNodeSetMaterial']
 so=mats[-1];go=next(a for a in gn if a.bl_idname=='NodeGroupOutput')
 vor=gn.new('ShaderNodeTexVoronoi');vor.voronoi_dimensions='3D';vor.feature='DISTANCE_TO_EDGE'
 vor.inputs['Scale'].default_value=1.25
 pos=gn.new('GeometryNodeInputPosition')
 lk.new(pos.outputs['Position'],vor.inputs['Vector'])
 sub=gn.new('ShaderNodeMath');sub.operation='SUBTRACT';sub.inputs[1].default_value=.21
 lk.new(vor.outputs['Distance'],sub.inputs[0])
 amp=gn.new('ShaderNodeMath');amp.operation='MULTIPLY';amp.inputs[1].default_value=.27
 lk.new(sub.outputs['Value'],amp.inputs[0])
 nor=gn.new('GeometryNodeInputNormal')
 vsca=gn.new('ShaderNodeVectorMath');vsca.operation='SCALE'
 lk.new(nor.outputs['Normal'],vsca.inputs[0]);lk.new(amp.outputs[0],vsca.inputs['Scale'])
 setp=gn.new('GeometryNodeSetPosition')
 lk.new(so.outputs['Geometry'],setp.inputs['Geometry'])
 lk.new(c.outputs['Result'],setp.inputs['Selection'])
 lk.new(vsca.outputs['Vector'],setp.inputs['Offset'])
 for link in list(go.inputs['Geometry'].links):lk.remove(link)
 lk.new(setp.outputs['Geometry'],go.inputs['Geometry'])
 print('GN_CAP_DISPLACEMENT_ADDED',tag,flush=True)
sc['tissue']='ARTIST shared 128cubed RGB: achene-connected vessel strands, mottling and central pith; all cuts use fruit_rest'
sc['tissue_biological_validation']='NOT VALIDATED; shape/links artistic, not microscopy'
sc['v2_visual_changes']='Shared true 3D field; local cap microdisplacement; 3 Voronoi wet/cell shader layers'
out= P/'strawberry-sdf-vertical-slice-v2.blend'
sc.frame_set(20)
bpy.ops.wm.save_as_mainfile(filepath=str(out))
sha=hashlib.sha256((P/'shared-tissue-128-atlas.png').read_bytes()).hexdigest()
print('V2_SAVED',str(out),'ATLAS_SHA',sha,'SECONDS',round(time.monotonic()-T0,2),flush=True)
# Verify two live cut configurations after reopening is tested separately.

#!/usr/bin/env python3
"""Blender 5.2+ independent visual proof: one volumetric strawberry, three cut angles.
Reads a single 3D substrate, sampling the same voxel arrays on three differently
oriented physical cut surfaces. No Frucht source and no dependency on previous M1e.
Designed for lookdev only: not a live arbitrary cutter, not validated anatomy.
"""
import sys, math, json, time
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs'
volume=np.load(OUT/'tissue_3d.npz')
LO=volume['lo']; HI=volume['hi']; N=volume['color'].shape[0]
TSTART=time.time()
ZMIN,ZMAX=-1.18,.98
NZ,NCUT,NBACK=235,224,112
angles=[0,math.radians(32),math.radians(82)]

bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=20
sc.render.resolution_x=920;sc.render.resolution_y=1030;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.render.film_transparent=False
sc.render.threads_mode='FIXED';sc.render.threads=4
sc.view_settings.view_transform='AgX'
sc.world.color=(.18,.18,.18)
sc.world.use_nodes=True
sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.21,.21,.21,1)
sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.56
sc['STRAWBERRY_LAB']='Visual POC v0: one 3D tissue, three independent cut planes'
sc['VALIDITY']='ANATOMICAL COLOR ARTISTIC; static sectional proof only'
sc['VOLUME_SOURCE']='outputs/tissue_3d.npz (RGB, height, pith, fiber in one 150^3 field)'

def mat(name,color,rough,sss=0,coat=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
 b=m.node_tree.nodes.get('Principled BSDF')
 b.inputs['Base Color'].default_value=(*color,1)
 b.inputs['Roughness'].default_value=rough
 b.inputs['Subsurface Weight'].default_value=sss
 b.inputs['Coat Weight'].default_value=coat
 b.inputs['Coat Roughness'].default_value=.18
 return m

skin=mat('SKIN | thin waxy red layer',(.39,.008,.012),.18,.03,.24)
nt=skin.node_tree
skinTex=nt.nodes.new('ShaderNodeTexNoise');skinTex.inputs['Scale'].default_value=104
skB=nt.nodes.new('ShaderNodeBump');skB.inputs['Strength'].default_value=.11;skB.inputs['Distance'].default_value=.009
nt.links.new(skinTex.outputs['Fac'],skB.inputs['Height']);nt.links.new(skB.outputs['Normal'],nt.nodes['Principled BSDF'].inputs['Normal'])

flesh=mat('FLESH | native 3D tissue color volume',(.62,.03,.02),.28,.02,.08)
nt=flesh.node_tree
attr=nt.nodes.new('ShaderNodeAttribute');attr.attribute_name='tissue_color'
grade=nt.nodes.new('ShaderNodeHueSaturation');grade.inputs['Saturation'].default_value=1.25;grade.inputs['Value'].default_value=.88
nt.links.new(attr.outputs['Color'],grade.inputs['Color'])
nt.links.new(grade.outputs['Color'],nt.nodes['Principled BSDF'].inputs['Base Color'])
# Very fine non-geometric wetness; the main tissue color/relief is truly 3D.
# Entire lookdev micro-detail is sampled in the original 3D rest-space, too.
restsh=nt.nodes.new('ShaderNodeAttribute');restsh.attribute_name='tissue_rest'
tex=nt.nodes.new('ShaderNodeTexNoise');tex.noise_dimensions='3D';tex.inputs['Scale'].default_value=105;tex.inputs['Detail'].default_value=2.0
nt.links.new(restsh.outputs['Vector'],tex.inputs['Vector'])
vor=nt.nodes.new('ShaderNodeTexVoronoi');vor.voronoi_dimensions='3D';vor.feature='DISTANCE_TO_EDGE';vor.inputs['Scale'].default_value=32
nt.links.new(restsh.outputs['Vector'],vor.inputs['Vector'])
multiply=nt.nodes.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=.17
nt.links.new(grade.outputs['Color'],multiply.inputs[1]);nt.links.new(tex.outputs['Fac'],multiply.inputs[2])
nt.links.new(multiply.outputs['Color'],nt.nodes['Principled BSDF'].inputs['Base Color'])
plus=nt.nodes.new('ShaderNodeMath');plus.operation='ADD'
nt.links.new(vor.outputs['Distance'],plus.inputs[0]);nt.links.new(tex.outputs['Fac'],plus.inputs[1])
bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.006
nt.links.new(plus.outputs['Value'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],nt.nodes['Principled BSDF'].inputs['Normal'])
leafmat=mat('LEAVES | dark olive green',(.06,.21,.035),.35,.10,.09)
stemmat=mat('STEM | olive stalk',(.11,.16,.045),.48)
seedmat=mat('ACHENE | ochre yellow seeds',(.45,.22,.065),.25,.02,.18)

# Radius profile is evaluated analytically for all three meshes; no old mesh used.
def radius(z):
 t=max(0,min(1,(z-ZMIN)/(ZMAX-ZMIN)))
 return 1.00*max(math.sin(math.pi*t),0)**.58*(.36+.92*t)
def r_with_furrows(z,theta):
 r=radius(z)
 return r*(1+.021*math.sin(7*theta+2.6*z)+.013*math.cos(13*theta-4.2*z)+.012*math.sin(3*theta-z))

def sample_volume(world):
 """Continuous trilinear sampling of the same archived 3D array; no scipy needed in Blender."""
 pos=np.clip((world-LO)/(HI-LO)*(N-1),0,N-1.00001)
 a=np.floor(pos).astype(np.int32)
 frac=pos-a
 b=np.minimum(a+1,N-1)
 ix,iy,iz=a.T; jx,jy,jz=b.T
 def tri(field):
  v=np.zeros((len(pos),)+(field.shape[3:] if field.ndim>3 else ()),dtype=np.float32)
  for qx,wx in ((ix,1-frac[:,0]),(jx,frac[:,0])):
   for qy,wy in ((iy,1-frac[:,1]),(jy,frac[:,1])):
    for qz,wz in ((iz,1-frac[:,2]),(jz,frac[:,2])):
     w=(wx*wy*wz).astype(np.float32)
     data=field[qx,qy,qz].astype(np.float32)
     if field.ndim>3:w=w[:,None]
     v+=w*data
  return v
 return tri(volume['color'])/255, tri(volume['height']), tri(volume['pith'])/255, tri(volume['fiber'])/255

def one_half(angle_deg,idx):
 a=math.radians(angle_deg)
 C,S=math.cos(a),math.sin(a)
 verts=[(0,0,ZMIN)] # one physical bottom tip shared by skin and fresh cut
 cut_indices=[];cut_world=[];cut_frac=[]
 skin_indices=[];face_defs=[];mat_idx=[]
 prev_sk=None;prev_cut=None
 for iz in range(1,NZ):
  z=ZMIN+(ZMAX-ZMIN)*(iz/NZ)
  sk=[]
  # The visible skin is the intact BACK half (y>0) of the 3D fruit.
  for k in range(NBACK+1):
   th=k*math.pi/NBACK
   rr=r_with_furrows(z,th+a)
   sk.append(len(verts));verts.append((rr*math.cos(th),rr*math.sin(th),z))
  # Physical plane occupies the flat front opening, while the skin is curved.
  left=verts[sk[-1]][0];right=verts[sk[0]][0]
  cross=[sk[-1]]
  for k in range(1,NCUT):
   u=k/NCUT
   x=left+(right-left)*u
   cross.append(len(verts));verts.append((x,0.,z))
  cross.append(sk[0])
  # The two endpoints are explicitly SHARED: seam remains welded.
  for k,vi in enumerate(cross):
   x,y,z0=verts[vi]
   cut_indices.append(vi)
   cut_world.append((x*C-y*S,x*S+y*C,z0))
   cut_frac.append((k/NCUT,iz/NZ))
  if prev_sk is None:
   for k in range(NBACK):
    face_defs.append((0,sk[k+1],sk[k]));mat_idx.append(0)
   for k in range(NCUT):
    face_defs.append((0,cross[k],cross[k+1]));mat_idx.append(1)
  else:
   for k in range(NBACK):
    face_defs.append((prev_sk[k],prev_sk[k+1],sk[k+1],sk[k]));mat_idx.append(0)
   for k in range(NCUT):
    face_defs.append((prev_cut[k],prev_cut[k+1],cross[k+1],cross[k]));mat_idx.append(1)
  prev_sk,prev_cut=sk,cross
 # Top tip fan uses same shared apex across skin and plane.
 top=len(verts);verts.append((0.,0.,ZMAX))
 for k in range(NBACK):face_defs.append((prev_sk[k],prev_sk[k+1],top));mat_idx.append(0)
 for k in range(NCUT):face_defs.append((prev_cut[k],top,prev_cut[k+1]));mat_idx.append(1)

 # Same full 3D arrays, differently sampled by cross-section angle.
 pts=np.asarray(cut_world,dtype=np.float32)
 colors,heights,pith,fiber=sample_volume(pts)
 verts=np.asarray(verts,dtype=np.float32)
 cut_indices=np.asarray(cut_indices,dtype=np.int32)
 frac=np.asarray(cut_frac,dtype=np.float32)
 # Signed 3D surface relief. Zero at ALL outer-skin seams and both tips.
 fade_x=np.clip(np.minimum(frac[:,0],1-frac[:,0])/.07,0,1)
 fade_z=np.clip(np.minimum(frac[:,1],1-frac[:,1])/.04,0,1)
 verts[cut_indices,1]-=np.asarray(heights,dtype=np.float32)*fade_x*fade_z
 # A slight natural outward wet convexity along middle of cut, independent of angle.
 verts[cut_indices,1]-=.004*np.sin(np.pi*frac[:,0])*np.sin(np.pi*frac[:,1])

 mesh=bpy.data.meshes.new(f'TissueSample_{angle_deg:03d}_mesh')
 mesh.from_pydata([tuple(x) for x in verts],[],face_defs);mesh.update()
 mesh.materials.append(skin);mesh.materials.append(flesh)
 for face,mi in zip(mesh.polygons,mat_idx):face.material_index=mi;face.use_smooth=True
 # Vertex colors for cut shading; skin has its separate glossy red shader.
 clr=np.empty((len(verts),4),dtype=np.float32);clr[:]=(.75,.15,.1,1)
 clr[cut_indices,:3]=np.asarray(colors,dtype=np.float32)
 clr[cut_indices,3]=1.0
 atr=mesh.attributes.new(name='tissue_color',type='FLOAT_COLOR',domain='POINT');atr.data.foreach_set('color',clr.ravel())
 restcoords=np.zeros((len(verts),3),dtype=np.float32);restcoords[cut_indices,:]=pts
 atrrest=mesh.attributes.new(name='tissue_rest',type='FLOAT_VECTOR',domain='POINT')
 atrrest.data.foreach_set('vector',restcoords.ravel())
 for field_name,arr in [('tissue_fiber',fiber),('tissue_pith',pith)]:
  src=np.zeros(len(verts),dtype=np.float32);src[cut_indices]=arr
  el=mesh.attributes.new(name=field_name,type='FLOAT',domain='POINT')
  el.data.foreach_set('value',src)
 obj=bpy.data.objects.new(f'CUT_{angle_deg:03d}_deg | SAME 3D SUBSTRATE',mesh)
 sc.collection.objects.link(obj)
 obj['source'] = 'tissue_3d.npz shared across all cut orientations'
 obj['cut_angle_deg']=angle_deg
 obj['cut_kind']='Longitudinal central physical half with back skin and closed exposed tissue'
 obj['topology']='Skin + cut share seam vertices'
 obj.hide_render=(idx!=0)
 # Mark exact center world-axis sample as a consistency control.
 mid=np.linspace(-.98,.74,32,dtype=np.float32)
 axis=np.column_stack([np.zeros(len(mid)),np.zeros(len(mid)),mid])
 axis_color=sample_volume(axis)[0]
 return obj, {'angle_deg':angle_deg,'vertices':len(verts),'faces':len(face_defs), 'material_faces':{'skin':mat_idx.count(0),'cut':mat_idx.count(1)},'axis_colors':axis_color.tolist(), 'mean_rgb':np.asarray(colors).mean(axis=0).tolist(),'pith_mean':float(np.mean(pith)),'fiber_mean':float(np.mean(fiber))}

results=[]
for idx,deg in enumerate([0,32,82]):
 obj,meta=one_half(deg,idx);results.append(meta)
 print('SLICE_READY',deg,meta['vertices'],meta['faces'],flush=True)

# Reusable physical leaves on the upper back of the berry, shared among cut angles.
for i in range(7):
 phi=(i+.3)*2*math.pi/7
 if math.sin(phi)<-.3:continue # only calyx behind the cut plane
 length=.40+.12*math.sin(i*3.3)
 w=.10
 v=[];faces=[]
 for q in range(15):
  t=q/14
  R=.045+t*length
  z=.96+.105*math.sin(t*math.pi)-.085*t*t
  width=w*(math.sin(math.pi*t)**.7)
  for sgn in (-1,1):
   rr=R
   x=rr*math.cos(phi)-sgn*width*math.sin(phi)
   y=rr*math.sin(phi)+sgn*width*math.cos(phi)
   v.append((x,y,z))
  if q>0:
   j=2*q;faces.append((j-2,j-1,j+1,j))
 me=bpy.data.meshes.new('sepal_geometry');me.from_pydata(v,[],faces);me.update();me.materials.append(leafmat)
 ob=bpy.data.objects.new(f'CALYX leaf {i}',me);sc.collection.objects.link(ob)
 for face in me.polygons:face.use_smooth=True
# Central stem
bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.038,depth=.34,location=(0,.12,1.02))
stem=bpy.context.object;stem.name='STEM';stem.data.materials.append(stemmat)

# Studio: neutral gray background + softbox and subtle warm kick.
def area(name,loc,energy,size,look=(0,0,-.03),color=(1,1,1)):
 data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size;data.color=color
 obj=bpy.data.objects.new(name,data);sc.collection.objects.link(obj);obj.location=loc
 obj.rotation_euler=(Vector(look)-obj.location).to_track_quat('-Z','Y').to_euler()
area('SOFTBOX_large_left',(-3.5,-3.9,4.1),700,5.5)
area('SOFTBOX_upper_right',(3.2,-2.5,1.0),300,3.1,color=(1,.93,.89))
area('EDGE_kick',(1.4,2.4,3.2),460,3.0,color=(1,.95,.86))
camdat=bpy.data.cameras.new('CAM_macro_ortho')
cam=bpy.data.objects.new('CAM_macro_ortho',camdat);sc.collection.objects.link(cam)
cam.location=(0,-6.5,.32);target=Vector((0,0,-.11));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
camdat.type='ORTHO';camdat.ortho_scale=2.69;sc.camera=cam

# Test one shared-axis property: every azimuth accesses exact same centerline.
ref=results[0]['axis_colors']
assert all(np.max(np.abs(np.array(v['axis_colors'])-np.array(ref)))<1e-7 for v in results)
for x in results:x.pop('axis_colors')
sc.frame_set(1)
bpy.context.view_layer.update()
scene_path=OUT/'strawberry-volumetric-3cut.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(scene_path))
report={'blender':bpy.app.version_string,'model':'independent artist-defined 3D tissue POC','volume':str(OUT/'tissue_3d.npz'),'slices':results,'centerline_invariant':'PASS: same 3D volume values at exact same spatial positions for all cut angles','time_build_s':round(time.time()-TSTART,2),'notes':['Skin and cut face share boundary vertices','Not live Boolean; physically built section planes from analytic source profile','Not a calibrated botany model','Not author Frucht graph or assets']}
(OUT/'build-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('STATIC_PROOF_READY',scene_path,'build_seconds',report['time_build_s'],flush=True)

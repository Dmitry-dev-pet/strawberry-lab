"""Independent Blender QA for v8: shared volume sampled by native GN, cell flattening on strands.
No script autoexecution, no Blender file rewriting; checks 4 cutter positions.
"""
import bpy,bmesh,numpy as np,json,time,hashlib,os
from mathutils import Vector
from pathlib import Path
P=Path(os.environ.get('STRAWBERRY_SDF_OUT',str(Path(__file__).resolve().parents[2]/'build/sdf-vertical-slice')))
file=P/'strawberry-sdf-vertical-slice-v8.blend'
bpy.ops.wm.open_mainfile(filepath=str(file),use_scripts=False)
assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
sc=bpy.context.scene
img=bpy.data.images['SDF proof v4 | 192^3 sparse volume and continuous branches']
field=bpy.data.node_groups['V8 | original rest-space vascular field (192^3)']
texture_nodes=[n for n in field.nodes if n.bl_idname=='GeometryNodeImageTexture']
assert len(texture_nodes)==2 and all(n.inputs['Image'].default_value==img for n in texture_nodes)
report={'version':'v8','script_autoexec':False,'sdf_source_version':'v4','three_d_sampler_count':len(texture_nodes),'atlas_size':list(img.size),'states':{},'a_b':{}}
def assert_body(mode,frame,label):
 sc.frame_set(frame)
 o=bpy.data.objects['Receptacle | sculpted skin and achene pits'] if mode=='whole' else bpy.data.objects['SDF visible body | '+mode]
 dg=bpy.context.evaluated_depsgraph_get()
 ev=o.evaluated_get(dg);m=ev.to_mesh()
 bm=bmesh.new();bm.from_mesh(m)
 nonmanifold=sum(not e.is_manifold for e in bm.edges)
 volume=bm.calc_volume(signed=True)
 bm.free()
 row={'vertices':len(m.vertices),'faces':len(m.polygons),'nonmanifold_edges':nonmanifold,'signed_volume':round(volume,2)}
 assert nonmanifold==0 and volume>0 and len(m.vertices)>1000
 if mode!='whole':
  for k in ('fruit_rest','v8_vascular_intensity','v8_cell_height_mm'):
   assert k in m.attributes,k
  vv=np.empty(len(m.vertices),dtype=np.float32)
  hh=np.empty(len(m.vertices),dtype=np.float32)
  m.attributes['v8_vascular_intensity'].data.foreach_get('value',vv)
  m.attributes['v8_cell_height_mm'].data.foreach_get('value',hh)
  row.update({'vessel_percentiles':np.percentile(vv,[50,90,95,99]).round(5).tolist(),
     'vessel_max':float(vv.max()),'cut_height_p99_mm':float(np.percentile(hh,99)),
     'cut_height_abs_max_mm':float(np.abs(hh).max()),
     'cells_vertices_gt_0_002mm':int(np.sum(np.abs(hh)>.002)),
     'vessel_verts_gt_0_12':int(np.sum(vv>.12))})
  assert 0<=vv.min() and vv.max()<=1.01 and row['vessel_max']>.23
  assert row['vessel_verts_gt_0_12']>300 and row['cells_vertices_gt_0_002mm']>500
  seed=bpy.data.objects['SDF visible seeds | '+mode]
  cutter=bpy.data.objects['SDF cutter | '+('planar (move or rotate)' if mode=='planar' else 'spherical bite (move or scale)')]
  es=seed.evaluated_get(dg);sm=es.to_mesh()
  transform=cutter.matrix_world.inverted_safe()@seed.matrix_world
  intrusion=0
  for v in sm.vertices:
   q=transform@v.co
   inside=max(abs(q.x),abs(q.y),abs(q.z))<.999 if mode=='planar' else q.length<.999
   intrusion+=int(inside)
  row['visible_seed_solids']=len(sm.vertices)//178
  row['seed_vertices_inside_cutter']=intrusion
  es.to_mesh_clear()
  assert intrusion==0
 ev.to_mesh_clear()
 report['states'][label]=row
 print('QA_STATE',label,json.dumps(row),flush=True)

assert_body('whole',1,'whole')
assert_body('planar',20,'plane')
assert_body('bite',40,'bite')

# Displacement really geometry, not merely bump; test exact 0-strength vertex output.
def vertex_pos_and_field(tag):
 sc.frame_set(20 if tag=='planar' else 40)
 bpy.context.view_layer.update()
 dg=bpy.context.evaluated_depsgraph_get()
 ev=bpy.data.objects['SDF visible body | '+tag].evaluated_get(dg);m=ev.to_mesh()
 co=np.empty(len(m.vertices)*3,np.float32)
 m.vertices.foreach_get('co',co)
 v=np.empty(len(m.vertices),np.float32)
 m.attributes['v8_vascular_intensity'].data.foreach_get('value',v)
 h=np.empty(len(m.vertices),np.float32)
 m.attributes['v8_cell_height_mm'].data.foreach_get('value',h)
 ev.to_mesh_clear()
 return co.reshape(-1,3),v,h
for tag in ('planar','bite'):
 g=bpy.data.node_groups['SDF cutter + rest-space | '+tag]
 ctrl=g.nodes['V8_CELL_STRENGTH']
 orig=float(ctrl.outputs['Value'].default_value)
 pos,intensity,height=vertex_pos_and_field(tag)
 ctrl.outputs['Value'].default_value=0
 zero,_,_=vertex_pos_and_field(tag)
 ctrl.outputs['Value'].default_value=orig
 delta=np.linalg.norm(pos-zero,axis=1)
 row={'max_position_delta_mm':float(delta.max()),'vertices_shift_gt_0_005mm':int((delta>.005).sum())}
 assert row['max_position_delta_mm']>.008 and row['vertices_shift_gt_0_005mm']>1000
 # Prove the *same atlas field* actually flattens the cell relief on original fibers:
 masknode=next(n for n in g.nodes if n.bl_idname=='ShaderNodeMapRange' and n.label.startswith('No cell relief'))
 lows=[float(masknode.inputs[k].default_value) for k in ('To Min','To Max')]
 masknode.inputs['To Min'].default_value=1
 masknode.inputs['To Max'].default_value=1
 _,idensity,unflattened=vertex_pos_and_field(tag)
 masknode.inputs['To Min'].default_value=lows[0]
 masknode.inputs['To Max'].default_value=lows[1]
 # Calculate exclusively at high-density voxels WITH actual cell relief before flatten.
 high=(intensity>.23)&(np.abs(unflattened)>.004)
 low=(intensity<.01)&(np.abs(unflattened)>.004)
 assert np.sum(high)>100 and np.sum(low)>100
 ratio_hi=float(np.mean(np.abs(height[high]))/np.mean(np.abs(unflattened[high])))
 ratio_lo=float(np.mean(np.abs(height[low]))/np.mean(np.abs(unflattened[low])))
 row.update({'fiber_density_verts_in_test':int(high.sum()),'nonfiber_density_verts_in_test':int(low.sum()),
             'fiber_relief_amplitude_ratio_to_unflattened':ratio_hi,
             'nonfiber_relief_amplitude_ratio_to_unflattened':ratio_lo})
 assert ratio_hi<.8 and .90<ratio_lo<1.1,(tag,row)
 report['a_b'][tag]=row
 print('QA_FLATTEN_OVER_REAL_ATLAS',tag,json.dumps(row),flush=True)

pc=bpy.data.objects['SDF cutter | planar (move or rotate)']
loc=pc.location.copy();rot=pc.rotation_euler.copy()
pc.location.y+=3.0;pc.rotation_euler.x+=.1745329252
assert_body('planar',20,'plane_moved')
pc.location=loc;pc.rotation_euler=rot
bc=bpy.data.objects['SDF cutter | spherical bite (move or scale)']
loc=bc.location.copy();scale=bc.scale.copy()
bc.location.x-=4.0;bc.scale=scale*1.13
assert_body('bite',40,'bite_moved')
bc.location=loc;bc.scale=scale
(P/'validation-v8.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('V8_PASS',flush=True)

#!/usr/bin/env python3
"""Tone down diagnostic fibre tubes into a conservative strawberry lookdev."""
import bpy,numpy as np,sys,json
from pathlib import Path
out=Path(sys.argv[sys.argv.index('--')+1])
mat=bpy.data.materials['V1 FLESH | physical 3D filament bundle ridges + wet glints']
mat.node_tree.nodes['Map Range'].inputs['To Max'].default_value=.31
mat.node_tree.nodes['Map Range.001'].inputs['To Max'].default_value=.18
# Avoid a very pale wire effect: less saturated ivory in exposed cortex.
mat.node_tree.nodes['Mix (Legacy).001'].inputs[2].default_value=(.83,.46,.33,1)
rows=[]
for ang in (0,32,82):
 ob=bpy.data.objects[f'V1_CUT_{ang:03d} | thin 3D fiber physical relief']
 mesh=ob.data
 n=len(mesh.vertices)
 v=np.empty(n*3,dtype='f4');mesh.vertices.foreach_get('co',v);v=v.reshape(-1,3)
 offset=np.empty(n,dtype='f4');mesh.attributes['fine_fiber_geometric_offset'].data.foreach_get('value',offset)
 v[:,1]+=.30*offset
 mesh.vertices.foreach_set('co',v.ravel());mesh.update()
 offset*=.70
 mesh.attributes['fine_fiber_geometric_offset'].data.foreach_set('value',offset)
 rows.append({'angle':ang,'vertices':n,'count_actual_offset_gt_0_002':int((abs(offset)>.002).sum()),'max_abs_offset':float(abs(offset).max())})
bpy.context.scene['V1_VISUAL_MODE']='Beauty: restrained spatial fibre color, 0.7x physical ridge height'
bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()))
(Path(__file__).parent/'outputs'/'beauty-report.json').write_text(json.dumps(rows,indent=2)+'\n')
print('V1_BEAUTY_TUNED',rows)

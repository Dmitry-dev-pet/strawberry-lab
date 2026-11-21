#!/usr/bin/env python3
"""CPU evaluation samples, entire current frame_set->depsgraph->mesh path, not FPS."""
import bpy,sys,time,json
from pathlib import Path
s=bpy.context.scene;body=bpy.data.objects['M1c | SDF cutter + rest-space tissue']
rows=[]
for f in (1,15,21,30,21,15):
 t=time.perf_counter();s.frame_set(f);dg=bpy.context.evaluated_depsgraph_get();dg.update();e=body.evaluated_get(dg);m=e.to_mesh();v=len(m.vertices);e.to_mesh_clear()
 rows.append({'frame':f,'vertices':v,'seconds':round(time.perf_counter()-t,4)})
print('M1E6_BENCH',json.dumps(rows),flush=True)
out=Path(sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else '/mnt/data/strawberry-m1e6/benchmark.json');out.write_text(json.dumps({'status':'PASS','environment':'Blender 5.2.4 LTS, CPU headless, one machine','contract':'full frame_set + depsgraph evaluation + to_mesh; excludes viewport UI and Cycles render','samples':rows,'limitations':['No GPU or interactive FPS inference','Source shape/Cavity edits may create SDF micro-islands']},indent=2)+'\n')

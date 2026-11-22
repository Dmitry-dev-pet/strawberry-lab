import bpy,os,time
from pathlib import Path
P=Path(str(Path(__file__).resolve().parents[2]/'build/sdf-vertical-slice'))
bpy.ops.wm.open_mainfile(filepath=str(P/'strawberry-sdf-vertical-slice-v10-ragged-bite.blend'),use_scripts=False)
sc=bpy.context.scene
sc.frame_set(40)
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=36
sc.render.resolution_x=860;sc.render.resolution_y=860;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'
sc.render.filepath=str(P/'sdf-v10-bite.png')
start=time.monotonic()
bpy.ops.render.render(write_still=True)
print('V10_BITE_CYCLES_DONE',round(time.monotonic()-start,2),os.path.getsize(sc.render.filepath),flush=True)

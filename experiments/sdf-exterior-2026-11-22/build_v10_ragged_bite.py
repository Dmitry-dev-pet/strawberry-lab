"""Video-grounded v10: ragged/scalloped bite cutter surface, no changes to SDF/seed logic.
Author source frames 18-19 s show irregular scalloped bites, not a perfect sphere.
This changes ONLY the editable sphere-cutter mesh, preserving same native SDF
and linked live seed mask. Proportions/teeth marks are ARTIST estimates.
"""
import bpy,bmesh,math,hashlib,json,time,os
from pathlib import Path
P=Path(os.environ.get('STRAWBERRY_SDF_OUT',str(Path(__file__).resolve().parents[2]/'build/sdf-vertical-slice')))
src=P/'strawberry-sdf-vertical-slice-v8.blend';out=P/'strawberry-sdf-vertical-slice-v10-ragged-bite.blend'
assert src.is_file() and not out.exists(), 'No source or refusing overwrite'
start=time.monotonic()
bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False)
cutter=bpy.data.objects['SDF cutter | spherical bite (move or scale)']
old_mesh=cutter.data
old_count=len(old_mesh.vertices)
bpy.ops.mesh.primitive_uv_sphere_add(segments=96,ring_count=64,radius=1)
temp=bpy.context.object
mesh=temp.data.copy()
mesh.name='V10 / deterministic jagged edible bite cutter'
bpy.data.objects.remove(temp,do_unlink=True)
deltas=[]
for v in mesh.vertices:
    x,y,z=v.co
    phi=math.atan2(y,x)
    rho=max(1e-9,v.co.length)
    theta=math.acos(max(-1.,min(1.,z/rho)))
    latitude=max(0.,math.sin(theta))**1.2
    # Seven broad scallop/teeth intervals + short ragged torn sections.
    major=.064*math.sin(9*phi+1.4*math.sin(2.8*theta))*latitude
    fine=.021*math.sin(21*phi-6.0*theta)*latitude
    rough=.013*math.sin(13*x+11*y+17*z)*math.cos(7*x-13*y+8*z)
    factor=1.0+major+fine+rough
    deltas.append(factor-1.0)
    v.co*=factor
mesh.update()
bm=bmesh.new();bm.from_mesh(mesh)
bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
closed=sum(not e.is_manifold for e in bm.edges)
volume=bm.calc_volume(signed=True)
bm.to_mesh(mesh);bm.free();mesh.update()
assert closed==0 and volume>0,(closed,volume)
cutter.data=mesh
# Keep original object transforms, naming and hide_render, so body & achene
# point mask continue referencing the exact same cutter object.
cutter['v10_cutter_shape']='9 broad angular scallops + fine cuts, amplitude 0.064 unit radius; ARTIST'
cutter['v10_source_video']='Owner-provided Frucht MP4 frames 18.2s/19s'
bpy.context.scene['v10_hypothesis']='Ragged cutter geometry (not another SDF engine) addresses physically circular cavity mismatch in owner video 18.2s.'
bpy.context.scene['v10_source']='v8, all voxel tissues/skin/materials unchanged.'
bpy.context.scene['v10_status']='Experimental qualitative lookdev, ARTIST tooth contours; not anatomical bite reconstruction.'
bpy.context.scene.frame_set(40)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out))
r={'version':'v10','source':'v8','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
   'blend_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
   'old_cutter_vertices':old_count,'new_cutter_vertices':len(mesh.vertices),
   'cutter_nonmanifold_edges':closed,'cutter_signed_volume_local':volume,
   'radius_delta_min':min(deltas),'radius_delta_max':max(deltas),'face_scales':list(cutter.scale),
   'owner_video_reference':['18.2 sec','19.0 sec'],
   'time_s':round(time.monotonic()-start,2),'ARTIST':True}
(P/'v10-build.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print('V10_SCALLOPED_CUTTER_BUILT',json.dumps(r),flush=True)

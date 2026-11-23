from pathlib import Path
import bpy,json,hashlib,argparse,sys
from mathutils import Vector
parser=argparse.ArgumentParser();parser.add_argument('--scene',required=True,type=Path);parser.add_argument('--out',required=True,type=Path);args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);scene=args.scene.resolve();out=args.out.resolve();assert scene.is_file() and not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(scene),use_scripts=False)
s=bpy.context.scene;body=s.objects['Receptacle | canonical PR29 hull'];seeds=[o for o in s.objects if o.get('role')=='achene'];assert len(seeds)==264
plane=s.objects['SDF | editable plane halfspace'];sphere=s.objects['SDF | editable sphere bite']
rows=[]
for name,mode,oblique,edge in [('whole',0,False,False),('plane',1,False,False),('oblique',1,True,False),('bite-edge',2,False,True)]:
 body['sdf_mode']=mode;body['sdf_voxel_mm']=.32
 plane.location=(0,.08 if oblique else 0,0);plane.rotation_euler=(.506145483 if oblique else 0,0,.558505360 if oblique else 0)
 sphere.location=(.82,-.70,-.42) if edge else (.60,-.70,.42)
 sphere.scale=(1.04,)*3 if edge else (.65,)*3
 body.update_tag();s.frame_set(s.frame_current);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
 visible=0;intruding=0;expected=0
 for seed in seeds:
  if mode==0:inside=False
  elif mode==1:
   xf=plane.matrix_world.inverted()@seed.matrix_world;inside=any((xf@v.co).y<0 for v in seed.data.vertices)
  else:
   xf=sphere.matrix_world.inverted()@seed.matrix_world;inside=any((xf@v.co).length<1 for v in seed.data.vertices)
  if not inside:expected+=1
  evaluated=seed.evaluated_get(dg);m=evaluated.to_mesh();is_visible=len(m.vertices)>0
  if is_visible:
   visible+=1
   if mode:
    cut=plane if mode==1 else sphere
    xf=cut.matrix_world.inverted()@seed.matrix_world
    intruding+=sum(((xf@v.co).y<-.0001 if mode==1 else (xf@v.co).length<.9999) for v in m.vertices)
  evaluated.to_mesh_clear()
 assert visible==expected and intruding==0,(name,visible,expected,intruding)
 rows.append({'pose':name,'visible_achenes':visible,'expected':expected,'intruding_retained_seed_vertices':intruding})
 print('SEED_GUARD_QA',name,visible,'intruding=',intruding,flush=True)
out.write_text(json.dumps({'status':'PASS_SAME_PR48_VERTEX_GUARD','scene_sha256':hashlib.sha256(scene.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'rows':rows},indent=2))

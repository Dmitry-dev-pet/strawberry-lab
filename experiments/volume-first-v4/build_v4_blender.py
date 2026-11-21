"""Add owned terminal-tangent V4 variants to the verified V3 .blend."""
from pathlib import Path
import bpy,numpy as np,json,sys
ROOT=Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
out=Path(args[0]).resolve() if args else ROOT/'v4-terminal-hooks.blend'
scenes=[s for s in bpy.data.scenes if s.name.startswith(('01 |','02 |','03 |'))]
assert len(scenes)==3
base=np.load(ROOT/'input-v3-network.npz');bpoints=base['points']; lens=base['lengths'];nmain=int((base['kind']==0).sum());assert nmain==28
original=bpy.data.objects['V3 | 28-sag0.25 | BRANCHES'];material=original.data.materials[0]
for ob in bpy.data.objects:
 if ob.name.startswith(('V2 | 28 core carriers','V2 | 539 branches ending','V3 |')):ob.hide_render=True
names=['0.35','0.85','1.5'];created=[]
for label in names:
 d=np.load(ROOT/f'v4-hook{label}.npz')
 assert np.array_equal(d['achene_positions'],base['achene_positions'])
 assert np.array_equal(d['branch_endpoints'],base['branch_endpoints'])
 assert np.array_equal(d['points'][:lens[:nmain].sum()],bpoints[:lens[:nmain].sum()])
 cr=bpy.data.curves.new(f'V4 local approach {label}','CURVE');cr.dimensions='3D';cr.resolution_u=2;cr.bevel_depth=.010;cr.bevel_resolution=2;cr.use_fill_caps=True
 cr.materials.append(material)
 pos=np.r_[0,np.cumsum(d['lengths'][:-1])]
 for i in range(nmain,len(lens)):
  n=int(lens[i]);start=int(pos[i]);p=d['points'][start:start+n];r=d['radius'][start:start+n]
  s=cr.splines.new('POLY');s.points.add(n-1)
  for z,q,rr in zip(s.points,p,r):
   z.co=(float(q[0]),float(q[1]),float(q[2]),1.);z.radius=float(rr/.010)
 ob=bpy.data.objects.new(f'V4 | hook{label} | BRANCHES',cr)
 for scene in scenes:scene.collection.objects.link(ob)
 ob.hide_render=(label!='0.85')
 ob['original_v3_profile']='V3 28-sag0.25, 28 carriers unchanged'
 ob['preserved_achene_endpoints']=539
 ob['tip_strength']=float(label)
 ob['morphology']='terminal tangent variation, terminal lateral bend only; all early source points unchanged'
 created.append(ob.name)
# Shared carriers from exact same V3 source, do not create a new strand profile.
bpy.data.objects['V3 | 28-sag0.25 | CARRIERS'].hide_render=False
for s in scenes:
 s['V4_VARIANTS']='V3 sag0.25; V4 hook0.35 / hook0.85 / hook1.5'
 s['V4_STATUS']='controlled morphology-only; seed endings and central carriers unchanged'
 s['V4_SCOPE']='not anatomy, not a Frucht reconstruction, not re-generated tissue cut'
bpy.context.scene['V4_DEFAULT']='hook0.85'
out.parent.mkdir(exist_ok=True,parents=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out))
rep={'status':'PASS','blender':bpy.app.version_string,'parent':'V3 28-sag0.25','v4_splines':created,'v4_branch_count_each':539,'carriers_reused':28,'camera_from_parent':True,'materials_from_parent':True,'seed_ends_unchanged':True,'output':str(out)}
(ROOT/'build-report.json').write_text(json.dumps(rep,indent=2)+'\n',encoding='utf8')
print('V4_BUILD_PASS',json.dumps(rep),flush=True)

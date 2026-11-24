"""Integrate exact independently authored PR50 research components. No new ARTIST tuning."""
import bpy, sys, hashlib, json
from pathlib import Path
PIN='2d540447b36063408808995079295d2c6f3045835e4362216fbc48c6ca78b23d'
BODY='Receptacle | canonical PR29 hull'
CAP='SDF | inherited 150^3 tissue + own multiscale wetness'
sha=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
if __name__=='__main__':
 src,lumen_py,protrusions_py,out=map(Path,sys.argv[sys.argv.index('--')+1:]); assert sha(src)==PIN and not out.exists()
 # Verify exact previous author-owned source scripts, not Frucht source.
 def git_blob(p):
  d=p.read_bytes();return hashlib.sha1(f'blob {len(d)}\0'.encode()+d).hexdigest()
 assert git_blob(lumen_py)=='c083b79ee28665d3372117b398c3e6d9f598e461'
 assert git_blob(protrusions_py)=='7d6e24adabfaabf5d6e7fb47292e095e014d77b5'
 import importlib.util
 def load(p,name):
  spec=importlib.util.spec_from_file_location(name,p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
 bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),use_scripts=False);s=bpy.context.scene;b=s.objects[BODY];mm=s.unit_settings.scale_length*1000
 assert not s.objects.get('SL Lumen | editable enclosed cavity') and not s.objects['SL Juice | independent pool surface'].visible_shadow
 lumen=load(lumen_py,'own_lumen').install(b,mm)
 protrusions=load(protrusions_py,'own_protrusions').install()
 g=b.modifiers[0].node_group;dif=g.nodes['Lumen | subtract BEFORE editable cutter'];assert len(dif.inputs['Grid 2'].links)==1 and dif.inputs['Grid 2'].links[0].from_node.name.startswith('Lumen protrusions | remove tissue')
 # Color is a prior negative visual control, not an accepted default.
 mat=bpy.data.materials[CAP];gain=mat.node_tree.nodes['SL Ring Pigment | A/B gain'];gain.outputs[0].default_value=0.0
 # Whole mode and cut features off at opening; native scene can be edited.
 b['sdf_mode']=0;b['sdf_voxel_mm']=.32;b['cell_surface_gain']=1.;b['cell_surface_detail']=1;b['vascular_relief_gain']=1.;b['juice_surface_gain']=1.;b.update_tag()
 s['SL integrated research status']='PR50 integrated cell/ring/lumen/juice/shadow candidate; experimental ring pigment off by default, gain in cut material; no visual acceptance; no new artist tuning.'
 bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()))
 r={'status':'BUILT_QA_PENDING','source_sha':PIN,'scene_sha':sha(out),'lumen_script_git_blob':git_blob(lumen_py),'protrusion_script_git_blob':git_blob(protrusions_py),'lumen':lumen,'protrusions':protrusions,'pigment_gain_default':0.,'shadow_visibility':False}
 out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print('BUILT',r['scene_sha'],flush=True)

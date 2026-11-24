"""Reopen A and candidate and compare exact actual geometry for each shader mode."""
import bpy,sys,json,hashlib,time,numpy as np
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE/'deps')]
from build_optics import ROOT,JUICE,MAT,PIN,sha,REFERENCE_TINT,REF_MM,MAX_MM
from qa_juice import snapshot,load,update,juicecheck,attr,mesh_eval,snap

def main():
 src,new,pose,out=sys.argv[sys.argv.index('--')+1:];out=Path(out);assert sha(src)==PIN and sha(new)==json.loads(Path(new).with_suffix('.json').read_text())['scene_sha'] and not out.exists();t=time.perf_counter()
 r=load(src,pose,.32);update(r,juice_gain=1.);base=snapshot();jbase=juicecheck();assert jbase['faces']>0
 fields=['sl_juice_clearance_mm','sl_reference_position','sl_reference_normal','sl_rest_position','sl_juice_tissue_position','sl_juice_final_level_mm'];js=snap(JUICE,fields)
 r=load(new,pose,.32);update(r,juice_gain=1.);m=bpy.data.materials[MAT];N=m.node_tree.nodes;shadow=next(n for n in N if n.bl_idname=='ShaderNodeOutputMaterial' and n.is_active_output).inputs['Surface'].links[0].from_node;assert shadow.inputs[0].links[0].from_socket.name=='Is Shadow Ray' and shadow.inputs[2].links[0].from_node.bl_idname=='ShaderNodeBsdfTransparent'
 dielectric=N['Optics | refractive dielectric'];assert dielectric.inputs['Transmission Weight'].default_value==1. and abs(dielectric.inputs['IOR'].default_value-1.333)<1e-6;assert N['Optics | signed normal clearance in mm'].attribute_name=='sl_juice_clearance_mm'
 ctrl=N['Optics | mode 0 / 1 / 2'];rows=[]
 for mode in (0,1,2,0):
  update(r,juice_optics_mode=mode);assert snapshot()==base and snap(JUICE,fields)==js;assert juicecheck()==jbase
  evaluated=m.node_tree.evaluated_get(bpy.context.evaluated_depsgraph_get());val=evaluated.nodes[ctrl.name].outputs[0].default_value;assert abs(val-mode)<1e-6,(val,mode)
  rows.append({'mode':mode,'evaluated_driver':val,'body_seed_fast_equal':True,'juice_geometry_attributes_equal':True})
 e,mesh=mesh_eval(JUICE);gap=attr(mesh,'sl_juice_clearance_mm').astype(float);ex=np.clip(gap,0,MAX_MM)/REF_MM;rgb=np.power(np.asarray(REFERENCE_TINT)[None,:],ex[:,None]);assert np.isfinite(rgb).all() and np.all(rgb[gap<=0]==1) and rgb.min()<1; e.to_mesh_clear()
 # The numerical check independently evaluates the intended function, not the actual shader at every pixel.
 res={'source_sha':PIN,'scene_sha':sha(new),'pose':pose,'voxel_mm':.32,'modes':rows,'juice':jbase,'transparent_shadow_route':True,'intended_linear_rgb_ranges':[[float(x) for x in rgb.min(axis=0)],[float(x) for x in rgb.max(axis=0)]],'gap_model':'normal clearance proxy, not measured optical path; numerical equation not direct shader sampling','gate':True,'elapsed_seconds':time.perf_counter()-t};out.write_text(json.dumps(res,indent=2)+'\n');print('RESULT',json.dumps(res),flush=True)
if __name__=='__main__':main()

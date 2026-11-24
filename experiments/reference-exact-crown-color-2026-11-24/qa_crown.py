"""Independent saved-scene crown regression and attachment observations."""
import bpy,bmesh,sys,json,numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
H=Path(__file__).resolve().parent;sys.path[:0]=[str(H),str(H/'source'),str(H/'source'/'deps')]
from qa_juice import load,update,snapshot,snap,JUICE,mesh_eval,co,KEYS
from qa_split import sdf,top,ROOT,SKIN,SEEDS,PLANE,SPHERE
from qa_flesh import JKEYS,tree_inventory
from build_crown import PIN,sha
EXACT='SL Exact | common labelled body'

def state(p,pose):
    r=load(p,pose,.32);update(r,juice_gain=1.,juice_optics_mode=2,flesh_material_mode=2,pigment_revision=1,exterior_material_mode=1);return r

def snapshots():
    return {'core':snapshot(),'juice':snap(JUICE,JKEYS),'seed':snap(SEEDS,list(KEYS[SEEDS])+['sl_achene_local','sl_achene_variation','sl_achene_gradient'])}

def tree(me):return BVHTree.FromPolygons([v.co.copy() for v in me.vertices],[tuple(p.vertices) for p in me.polygons]) if len(me.polygons) else None

def main():
    old,new,pose,out=sys.argv[sys.argv.index('--')+1:];assert sha(old)==PIN and not Path(out).exists();r=state(old,pose);orig=snapshots();materials={m.name:tree_inventory(m) for m in bpy.data.materials if m.node_tree};print('BASELINE',pose,flush=True)
    r=state(new,pose);assert snapshots()==orig;assert all(tree_inventory(bpy.data.materials[k])==v for k,v in materials.items());mode=r['split_mode'];organ_rows={};trees={};components={}
    for o in bpy.data.collections['SL Crown | sepals and pedicel'].objects:
        e,me=mesh_eval(o.name);vs=co(me);q=top(me)[0];q['role']=o.get('role');q['common_shape_map']=o.modifiers[0].node_group.name;assert q['common_shape_map']=='SL | common shape map v1';q['min_cutter_margin_mm']=float(sdf(vs,mode).min()) if len(vs) and mode else None
        if len(vs):
            assert q['boundary_edges']==q['wire_or_over_two_face_edges']==q['inconsistent_edges']==q['degenerate_triangles']==0 and q['signed_volume_mm3']>0,(o.name,q)
            if mode:assert q['min_cutter_margin_mm']>=-.002,(o.name,q)
            bm=bmesh.new();bm.from_mesh(me);seen=set();count=0
            for v in bm.verts:
                if v in seen:continue
                count+=1;seen.add(v);stack=[v]
                while stack:
                    for edge in stack.pop().link_edges:
                        other=[w for w in edge.verts if w not in seen]
                        seen.update(other);stack.extend(other)
            bm.free();q['components']=count;trees[o.name]=tree(me)
        else:q['components']=0
        organ_rows[o.name]=q;e.to_mesh_clear()
    e,body=mesh_eval(EXACT if mode else SKIN);bt=tree(body);e.to_mesh_clear()
    connected={'fruit'};links={n:[] for n in trees}
    for n,t in trees.items():
        if bt and t.overlap(bt):links[n].append('fruit')
        for k,u in trees.items():
            if n!=k and t.overlap(u):links[n].append(k)
    for _ in range(len(trees)+1):
        connected.update(n for n,l in links.items() if connected.intersection(l))
    unattached=sorted(set(trees)-connected)
    result={'pose':pose,'blender':bpy.app.version_string,'source_sha':sha(old),'scene_sha':sha(new),'unchanged_baseline_geometry_attributes_and_materials':True,'organs':organ_rows,'contact_graph':links,'unattached_organs':unattached,'attachment_gate':not unattached,'geometry_gate':True}
    Path(out).write_text(json.dumps(result,indent=2)+'\n');print('RESULT',json.dumps(result),flush=True)
if __name__=='__main__':main()

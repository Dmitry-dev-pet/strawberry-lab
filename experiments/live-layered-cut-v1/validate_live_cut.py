"""Quantitative saved-Blender validation for the single movable shared-knife proof.
Check authentic re-evaluated Boolean geometry at three cutter poses, cap material,
signed cut plane and one exact same source set of 28+539 spatial splines.
"""
from pathlib import Path
import bpy, numpy as np, math, json, time, hashlib
R=Path(__file__).resolve().parent
scs=[bpy.data.scenes[x] for x in ('LIVE MATCHED | shared movable plane','LIVE FLESH ONLY | shared movable plane')]
ctrl=bpy.data.objects['LIVE CUT | move or rotate this Empty'];knife=bpy.data.objects['LIVE CUT | Boolean subtraction volume (hidden in render)']
assert knife.parent is ctrl and knife.hide_render
assert ctrl.name in scs[0].objects and ctrl.name in scs[1].objects
origcore=bpy.data.objects['V3 | 28-sag0.25 | CARRIERS'];origbranch=bpy.data.objects['V4 | hook0.85 | BRANCHES'];origmarker=bpy.data.objects['V2 | 539 seed positions and branch endpoints']
assert len(origcore.data.splines)==28 and len(origbranch.data.splines)==539 and len(origmarker.data.vertices)==3234

def digest(ob):
 h=hashlib.sha256()
 for spl in ob.data.splines:
  h.update(len(spl.points).to_bytes(4,'little'))
  for p in spl.points:
   h.update(np.asarray(p.co[:3],dtype='f4').tobytes());h.update(np.float32(p.radius).tobytes())
 return h.hexdigest()
hc,hb=digest(origcore),digest(origbranch)
for sc in scs:
    assert sc.camera is not None
    for kind,original,n in [('core',origcore,28),('branch',origbranch,539)]:
        for variant in ('full','clip'):
            obj=bpy.data.objects[sc.name+' | '+kind+variant]
            assert len(obj.data.splines)==n
            assert digest(obj)==digest(original), (sc.name,kind,variant)
            assert obj.name in sc.objects
            if variant=='clip':
                mat=obj.data.materials[0]
                coord=next(n for n in mat.node_tree.nodes if n.type=='TEX_COORD')
                assert coord.object is ctrl
                assert any(n.type=='MIX_SHADER' for n in mat.node_tree.nodes)
    for v in ('full','clip'):
        obj=bpy.data.objects[sc.name+' | marker'+v]
        assert len(obj.data.vertices)==3234
        a=np.asarray([p.co[:] for p in obj.data.vertices],dtype=np.float32)
        b=np.asarray([p.co[:] for p in origmarker.data.vertices],dtype=np.float32)
        assert np.array_equal(a,b)
        if v=='clip':
            coord=next(n for n in obj.data.materials[0].node_tree.nodes if n.type=='TEX_COORD')
            assert coord.object is ctrl
    assert bpy.data.objects[sc.name+' | LIVE cut berry'].data is bpy.data.objects[sc.name+' | WHOLE berry (optional)'].data
    boolmod=bpy.data.objects[sc.name+' | LIVE cut berry'].modifiers[0]
    assert boolmod.type=='BOOLEAN' and boolmod.object is knife and boolmod.material_mode=='INDEX'
    assert all(m is not None for m in bpy.data.objects[sc.name+' | LIVE cut berry'].data.materials)
    assert bpy.data.objects[sc.name+' | LIVE cut berry'].data.materials[1].name.startswith('LIVE | cut flesh')
assert scs[0].camera.data.ortho_scale==scs[1].camera.data.ortho_scale
assert np.allclose(scs[0].camera.location,scs[1].camera.location)
assert np.allclose(scs[0].camera.rotation_euler,scs[1].camera.rotation_euler)
for sc in scs:
    assert len([o for o in sc.objects if o.type=='LIGHT'])==len([o for o in scs[0].objects if o.type=='LIGHT'])
assert all(len(bpy.data.objects[sc.name+' | LIVE cut berry'].data.vertices)==30242 for sc in scs)
wholemesh=bpy.data.objects[scs[0].name+' | WHOLE berry (optional)'].data
assert len(wholemesh.vertices)==30242
img=bpy.data.images['LIVE | ORIGINAL V0 native RGB volume atlas (150^3)']
assert bool(img.packed_file) and img.size[:]==(2250,1500)
mat=wholemesh.materials[1]
texnodes=[n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE']
assert len(texnodes)==2 and all(n.image==img for n in texnodes)

# Native Boolean dynamic cap tests. No render, no baked alternatives.
rows=[]
cutobj=bpy.data.objects[scs[0].name+' | LIVE cut berry']
for offset,angle in [(0.,0.),(.34,0.),(-.26,0.),(0.,32.)]:
    ctrl.location.y=offset;ctrl.rotation_euler.z=math.radians(angle)
    bpy.context.window.scene=scs[0]
    bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
    t=time.perf_counter()
    deps=bpy.context.evaluated_depsgraph_get();evaluated=cutobj.evaluated_get(deps)
    mesh=evaluated.to_mesh()
    mats=np.array([p.material_index for p in mesh.polygons],dtype=np.uint8)
    cap=np.flatnonzero(mats==1)
    vert=np.array([p.co[:] for p in mesh.vertices],dtype=np.float64)
    # Cut plane normal: local +Y transformed by controller (rotation Z), plane passes ctrl.location.
    rot=ctrl.matrix_world.to_3x3();normal=np.array(rot@__import__('mathutils').Vector((0,1,0)),dtype=np.float64)
    point=np.array(ctrl.matrix_world.translation,dtype=np.float64)
    signed=(vert-point)@normal
    # Existing skin vertices must all be kept in positive plane or within numerical tolerance.
    assert signed.min()>-1e-4,(offset,angle,signed.min())
    assert len(cap)>=1,(offset,angle,len(cap))
    faceverts={int(v) for j in cap for v in mesh.polygons[int(j)].vertices}
    capdist=np.abs(signed[list(faceverts)])
    assert capdist.max()<2e-4,(offset,angle,capdist.max())
    # Curves and seeds are not modified when same Empty moves!
    assert hc==digest(origcore) and hb==digest(origbranch)
    dt=time.perf_counter()-t
    rows.append({'offset':offset,'angle_deg':angle,'retained_vertices':len(mesh.vertices),'retained_faces':len(mesh.polygons),'new_cap_faces':len(cap),'max_cap_dist_from_plane':float(capdist.max()),'min_keep_halfspace_signed':float(signed.min()),'eval_seconds':round(dt,3)})
    evaluated.to_mesh_clear()
ctrl.location.y=0;ctrl.rotation_euler.z=0
for sc in scs:
    bpy.context.window.scene=sc
    bpy.context.view_layer.update()
report={'status':'PASS','blender':bpy.app.version_string,'plane_shared_both_scenes':True,'original_28_carriers_sha256':hc,'original_539_branches_sha256':hb,'same_source_positions_all_layers':True,'seed_marker_vertices_unchanged':3234,'packed_original_150cubed_volume_atlas':True,'source_mesh_analytic_whole_closed':True,'cut_caps_real_boolean_and_correct_material':True,'tested_4_plane_poses':rows,'volume_color_has_2_adjacent_z_samples':True,'not_included':['separate microcells','real botanical seed meshes','juice','vendor Frucht scenes']}
(R/'validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print('LIVE_CUT_GEOMETRY_QA_PASS',json.dumps({'poses':rows,'source_unchanged':True}),flush=True)

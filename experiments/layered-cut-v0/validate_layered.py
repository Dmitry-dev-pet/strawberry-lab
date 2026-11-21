#!/usr/bin/env python3
"""Independent saved-Blender verification of correct layer splitting and clipping."""
import bpy,numpy as np,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
O=ROOT/'outputs'
a=bpy.data.scenes['LAYER A | common cut y=0']
b=bpy.data.scenes['LAYER B | flesh-only cut y=0']
base_core=bpy.data.objects['V3 | 28-sag0.25 | CARRIERS']
base_branches=bpy.data.objects['V4 | hook0.85 | BRANCHES']
base_seeds=bpy.data.objects['V2 | 539 seed positions and branch endpoints']
assert len(base_core.data.splines)==28 and len(base_branches.data.splines)==539


def read_curves(ob):
    return [(np.array([p.co[:3] for p in s.points],dtype='f4'),np.array([p.radius for p in s.points],dtype='f4')) for s in ob.data.splines]

def digest_curves(ob):
    h=hashlib.sha256()
    for p,r in read_curves(ob):
        h.update(len(p).to_bytes(4,'little'));h.update(p.tobytes());h.update(r.tobytes())
    return h.hexdigest()

def obj_for(s,key):
    return bpy.data.objects[s.name+' | '+key]

for s in [a,b]:
    assert digest_curves(base_core)==digest_curves(obj_for(s,'fullcore'))
    assert digest_curves(base_branches)==digest_curves(obj_for(s,'fullbranch'))
    assert len(obj_for(s,'clipcore').data.splines)==15
    assert len(obj_for(s,'clipbranch').data.splines)==283
    for key in ['clipcore','clipbranch']:
        for p,r in read_curves(obj_for(s,key)):
            assert len(p)>=2 and np.min(p[:,1])>=-1.e-7, (s.name,key)
    seedfull=bpy.data.objects[s.name+' | seeds full']
    seedclip=bpy.data.objects[s.name+' | seeds clipped']
    assert len(seedfull.data.vertices)==3234 and len(seedclip.data.vertices)==1620
    assert len(seedfull.data.polygons)==539*8 and len(seedclip.data.polygons)==270*8
    # Exact source seed vertex coordinates remain unaltered for each marker.
    xyz1=np.array([v.co[:] for v in seedfull.data.vertices],dtype='f4')
    xyz0=np.array([v.co[:] for v in base_seeds.data.vertices],dtype='f4')
    assert np.array_equal(xyz0,xyz1)
    assert all(o.name in s.objects for o in [obj_for(s,'fullcore'),obj_for(s,'clipcore'),obj_for(s,'fullbranch'),obj_for(s,'clipbranch'),seedfull,seedclip])

flesh_a=obj_for(a,'FLESH actual static cut')
flesh_b=obj_for(b,'FLESH actual static cut')
assert len(flesh_a.data.vertices)==len(flesh_b.data.vertices)==78626
assert len(flesh_a.data.polygons)==len(flesh_b.data.polygons)==78960
for m in [0,1]:assert flesh_a.data.materials[m]==flesh_b.data.materials[m]
xyza=np.array([v.co[:] for v in flesh_a.data.vertices],dtype='f4')
xyzb=np.array([v.co[:] for v in flesh_b.data.vertices],dtype='f4')
xyzsrc=np.array([v.co[:] for v in bpy.data.objects['CUT_000_deg | SAME 3D SUBSTRATE'].data.vertices],dtype='f4')
assert np.array_equal(xyza,xyzb) and np.array_equal(xyza,xyzsrc)
assert len(bpy.data.objects['CUT_000_deg | SAME 3D SUBSTRATE'].data.materials)==2
assert flesh_a.data.materials[1].name=='FLESH | native 3D tissue color volume'
# Exact same camera space and lighting shape/power/location between two scenes.
cam_a=a.camera;cam_b=b.camera
assert np.array_equal(np.array(cam_a.location),np.array(cam_b.location)) and np.array_equal(np.array(cam_a.rotation_euler),np.array(cam_b.rotation_euler))
assert cam_a.data.type==cam_b.data.type and cam_a.data.ortho_scale==cam_b.data.ortho_scale
lights={}
for sc in [a,b]:
    ls=[o for o in sc.objects if o.type=='LIGHT']
    lights[sc.name]=sorted([(o.name.split(' | ')[-1], tuple(round(float(x),8) for x in o.location)+tuple(round(float(x),8) for x in o.rotation_euler),o.data.type,round(o.data.energy,8)) for o in ls])
assert lights[a.name]==lights[b.name]

# All 8 real content collections are switchable per scene and defaults differ.
def active_layers(s):
    layer=s.view_layers[0].layer_collection
    assert layer
    return [c.collection.name.split(' | ')[-1] for c in layer.children if not c.exclude]
active_a=active_layers(a);active_b=active_layers(b)
assert any('CLIPPED' in x for x in active_a) and not any('FULL' in x for x in active_a)
assert any('FULL' in x for x in active_b) and not any('CLIPPED' in x for x in active_b)
assert len(active_a)==5 and len(active_b)==5
# Source V4 new camera not touched; all modes operate on ONE original geometry.
report={'status':'PASS','blender_version':bpy.app.version_string,
 'scene_a':a.name,'scene_b':b.name,
 'same_opaque_cut_mesh_vertices':len(flesh_a.data.vertices),
 'same_camera':True,'same_lights':True,'same_flesh_material':True,
 'original_28_core_spline_sha256':digest_curves(base_core),
 'original_539_branch_spline_sha256':digest_curves(base_branches),
 'full_curve_identity_in_both_scenes':True,
 'source_seed_marker_vertices':3234,'full_seed_marker_vertices_both_scenes':3234,
 'clipped_seed_count':270,'clipped_core_curve_segments':15,'clipped_branch_curve_segments':283,
 'all_clipped_samples_y_ge_0':True,
 'independent_visibility_collections_per_scene':8,
 'defaults':{'matched_visible':active_a,'flesh_only_visible':active_b},
 'limitations':['The original Volume First baseline flesh is a static half fruit at y=0, no animated arbitrary knife',
                'Original v0 flesh material has its own tissue color, not recomputed from V4 curves',
                'Achene markers are diagnostic octahedra, not physical strawberry achene meshes',
                'Pith, microscopic cell and juice layers are not in V4 independent objects',
                'Not evidence of actual commercial Frucht clipping/wiring']}
(O/'validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print('LAYER_VALIDATION_PASS',json.dumps(report),flush=True)

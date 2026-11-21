#!/usr/bin/env python3
"""Build editable Blender scene comparing V2 spokes with independently authored
V3 PCHIP-inspired variable-center carriers + cubic Bezier branches.

The V2 scene provides camera, lights and 539 *existing* seed markers; every
V3 source is anchored to exactly those coordinates. No Frucht source copied.
"""
from pathlib import Path
import sys,json,time
import numpy as np
import bpy

ROOT=Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
out=Path(args[0]).resolve() if args else ROOT/'v3-carriers-bezier-variants.blend'
variants=['28-sag0.25','28-sag1.0','28-sag1.8','14-sag1.0','40-sag1.0']
scenes=[s for s in bpy.data.scenes if s.name.startswith(('01 |','02 |','03 |'))]
assert len(scenes)==3, [s.name for s in bpy.data.scenes]
oldmain=bpy.data.objects['V2 | 28 core carriers'];oldbranch=bpy.data.objects['V2 | 539 branches ending at achenes']
oldmain.hide_render=True;oldbranch.hide_render=True
assert bpy.data.objects['V2 | 539 seed positions and branch endpoints'].data.vertices

# Reuse known fixed assets from actual V2, including the same camera and lights.
mainmat=oldmain.data.materials[0]
branchmat=oldbranch.data.materials[0]
report={}
for name in variants:
    d=np.load(ROOT/f'v3-profile{name}.npz')
    count=int((d['kind']==0).sum())
    assert count in (14,28,40) and len(d['achene_positions'])==539
    assert np.array_equal(d['achene_positions'], np.load(ROOT/'input-v2-network.npz')['achene_positions'])
    assert np.array_equal(d['branch_endpoints'], np.load(ROOT/'input-v2-network.npz')['branch_endpoints'])
    lens=d['lengths'];p=d['points'];radius=d['radius'];kinds=d['kind']
    starts=np.r_[0,np.cumsum(lens[:-1])]
    for kind,objtype,material in [(0,'CARRIERS',mainmat),(1,'BRANCHES',branchmat)]:
        cu=bpy.data.curves.new(f'V3 {name} {objtype} curve data','CURVE')
        cu.dimensions='3D';cu.resolution_u=2;cu.bevel_depth=.010;cu.bevel_resolution=2;cu.use_fill_caps=True
        n_splines=0
        for j,(start,L) in enumerate(zip(starts,lens)):
            if kinds[j]!=kind:continue
            sl=cu.splines.new('POLY');sl.points.add(int(L)-1)
            for item,xyz,rr in zip(sl.points,p[start:start+L],radius[start:start+L]):
                item.co=(float(xyz[0]),float(xyz[1]),float(xyz[2]),1.)
                item.radius=float(rr/.010)
            n_splines+=1
        cu.materials.append(material)
        ob=bpy.data.objects.new(f'V3 | {name} | {objtype}',cu)
        for s in scenes:s.collection.objects.link(ob)
        ob.hide_render=not name=='28-sag1.0'
        ob['source_npz']=f'v3-profile{name}.npz'
        ob['part']=objtype
        ob['parameter_variant']=name
        ob['shared_achene_anchors']=539
        assert n_splines==(count if kind==0 else 539)
        report[ob.name]=n_splines
for s in scenes:
    s['V3_STATUS']='INDEPENDENT 3D DIAGNOSTIC, not Frucht/parity or true cut geometry'
    s['V3_VARIANTS']='V2; 28-sag0.25; 28-sag1.0; 28-sag1.8; 14-sag1.0; 40-sag1.0'
    s['V3_SEED_COUNT']=539
    s['V3_DEFAULT']='28-sag1.0'
    s['V3_CAMERA']='Same as original V2 for scientific A/B'

bpy.context.scene['V3_BRANCHING']='11 original profile control points + noncentered axis + cubic 3D Bezier paths'
out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out))
(ROOT/'blender-build-report.json').write_text(json.dumps({'status':'PASS','source_scene':'input-v2-scene.blend','main_objects':report,'scenes':[s.name for s in scenes],'out':str(out)},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('V3_EDITABLE_SCENE_SAVED',out,'objects',len(report),flush=True)

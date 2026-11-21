#!/usr/bin/env python3
"""Strawberry Lab M1e5 — opt-in Blender 5.2+ live adaptive CutSurface.

This small Blender add-on refreshes the exact locally refined mesh automatically
on frame changes AND when the knife is moved in Object Mode. It is intentionally
not called 'GN-only': BMesh rebuilds the cut face at each new knife pose. The
underlying M1e3 Geometry Nodes SDF cutter remains live as a safe Fast fallback.

Install as Blender addon, or open embedded Text block 'M1e5 - Enable Live Exact.py'
and click Run Script once per Blender session (Blender's automatic script execution
need not be enabled). No network, no external model or commercial source.
"""
bl_info = {"name":"Strawberry Lab — Live Exact CutSurface", "author":"Strawberry Lab", "version":(0,1,0),"blender":(5,2,0),"category":"Object", "description":"Auto-refresh seam-safe localized exact cut on knife moves; editable volume baseline"}
import bpy
import bmesh
import time
import math
from mathutils import Vector
from mathutils.kdtree import KDTree
from bpy.app.handlers import persistent

BODY = 'M1c | SDF cutter + rest-space tissue'
KNIFE = 'M1e | independently moving knife (cube half space)'
HELPER = 'M1e5 | live SDF source for localized mesh'
SNAP = 'M1e5 | EXACT live-local CutSurface'
NETWORK = 'M1e4 | persistent 3D curved fibers (source)'
CUT_MAT = 'M1c | rest-space pith/cortex + wet Voronoi surface'
CAV_MAT = 'M1e | shadowy wet cavity walls'
TEXT_NAME='M1e5 - Enable Live Exact.py'
_STATE={'busy':False,'key':None,'refresh_count':0,'last_seconds':None,'last_result':None,'last_error':None,'kd':None,'kd_fingerprint':None,'installed':False}
_HANDLER_KEY = 'strawberry_lab.m1e5.registered_handlers.v1'

def ready(scene=None):
    return (BODY in bpy.data.objects and KNIFE in bpy.data.objects and HELPER in bpy.data.objects and
            SNAP in bpy.data.objects and NETWORK in bpy.data.objects and
            (scene is None or bool(scene.get('m1e5_scene'))))

def _show(obj, yes):
    obj.hide_render = not yes
    obj.hide_set(not yes)

def signature(scene):
    obj=bpy.data.objects[KNIFE]
    # Frame is deliberately NOT part of the signature: when the knife occupies
    # the same pose, exact rest-space fields should not unnecessarily regenerate.
    return tuple(round(obj.matrix_world[row][col], 8) for row in range(4) for col in range(4))

def _kd_points():
    src=bpy.data.objects[NETWORK]
    splines=src.data.splines
    fingerprint=(len(splines),tuple(len(s.points) for s in splines),tuple(tuple(round(v,7) for v in p.co[:3]) for s in splines for p in s.points))
    if _STATE['kd'] is not None and _STATE['kd_fingerprint']==fingerprint:
        return _STATE['kd']
    pts=[Vector(p.co[:3]) for s in splines for p in s.points]
    kd=KDTree(len(pts))
    for i,p in enumerate(pts):kd.insert(p,i)
    kd.balance()
    _STATE['kd']=kd
    _STATE['kd_fingerprint']=fingerprint
    return kd

def _make_mesh(scene):
    """Evaluate live low-poly SDF, refine cut edges, preserve whole shell seam."""
    helper=bpy.data.objects[HELPER]
    knife=bpy.data.objects[KNIFE]
    dg=bpy.context.evaluated_depsgraph_get()
    dg.update()
    evaluated=helper.evaluated_get(dg)
    base=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=dg)
    try:
        mats={m.name:i for i,m in enumerate(base.materials) if m is not None}
        ic,iv=mats[CUT_MAT],mats[CAV_MAT]
        isk=next(i for i,m in enumerate(base.materials) if m and m.name.startswith('Strawberry M1a'))
        pt=knife.matrix_world @ Vector((0,1,0))
        nv=(knife.matrix_world.to_3x3() @ Vector((0,1,0))).normalized()
        bm=bmesh.new()
        try:
            bm.from_mesh(base)
            for f in bm.faces:f.normal_update()
            selected=[f for f in bm.faces if f.material_index==ic or
                      (f.material_index==iv and abs((f.calc_center_median()-pt).dot(nv))<.54)]
            edges=set(edge for face in selected for edge in face.edges)
            if edges:
                bmesh.ops.subdivide_edges(bm,edges=list(edges),cuts=2,use_grid_fill=True,smooth=0)
            nm=sum(not e.is_manifold for e in bm.edges)
            if nm:raise RuntimeError(f'BMesh topology has {nm} nonmanifold edges')
            # Preserve our real 3-D source fields from M1e4, not a 2D paint on the cut.
            rest=bm.verts.layers.float_vector.get('fruit_rest')
            if rest is None:raise RuntimeError('fruit_rest attribute missing')
            fld=bm.verts.layers.float.get('m1e4_fiber') or bm.verts.layers.float.new('m1e4_fiber')
            kd=_kd_points()
            positive=0
            for vert in bm.verts:
                typ={f.material_index for f in vert.link_faces}
                if isk in typ or (ic not in typ and iv not in typ):
                    vert[fld]=0.0
                    continue
                dist=kd.find(Vector(vert[rest]))[2]
                if ic in typ:
                    x=max(0.,min(1.,(.082-dist)/.062));v=.53*x*x*(3.-2.*x)
                else:
                    x=max(0.,min(1.,(.040-dist)/.029));v=.09*x*x*(3.-2.*x)
                vert[fld]=v
                if v>.11:positive+=1
            new=bpy.data.meshes.new(f'M1e5 | exact mesh pose {scene.frame_current}')
            for mat in base.materials:new.materials.append(mat)
            bm.to_mesh(new)
            new.update()
            return new,{'frame':scene.frame_current,'vertices':len(new.vertices),'faces':len(new.polygons),
                        'input_faces':len(base.polygons),'selected_faces':len(selected),
                        'subdivided_edges':len(edges),'nonmanifold_edges':nm,'fiber_vertices':positive}
        finally:
            bm.free()
    finally:
        if base.users==0:bpy.data.meshes.remove(base)

def refresh(scene=None, force=False):
    """Synchronous exact reconstruction on current knife pose, safe to re-enter."""
    scene=scene or bpy.context.scene
    if not ready(scene):return None
    if _STATE['busy']:return None
    key=signature(scene)
    if not force and key==_STATE['key']:return None
    _STATE['busy']=True
    t0=time.perf_counter()
    try:
        mesh,stats=_make_mesh(scene)
        target=bpy.data.objects[SNAP]
        old=target.data
        target.data=mesh
        target['m1e5_last_frame']=scene.frame_current
        target['m1e5_last_knife_pose']=','.join(f'{n:.7f}' for n in key)
        if old.users==0:bpy.data.meshes.remove(old)
        stats['seconds']=round(time.perf_counter()-t0,4)
        _STATE['key']=key
        _STATE['refresh_count']+=1
        _STATE['last_seconds']=stats['seconds']
        _STATE['last_result']=stats
        _STATE['last_error']=None
        print('M1E5_LIVE_EXACT_REFRESH',stats,flush=True)
        return stats
    except Exception as exc:
        _STATE['last_error']=repr(exc)
        print('M1E5_LIVE_EXACT_ERROR',repr(exc),flush=True)
        # Crucial safety: fail open to the up-to-date GN preview (no stale snapshot).
        _show(bpy.data.objects[SNAP],False)
        _show(bpy.data.objects[BODY],True)
        scene['m1e5_mode']='FAST_FALLBACK_ERROR'
        raise
    finally:
        _STATE['busy']=False

def enable(scene=None):
    scene=scene or bpy.context.scene
    if not ready(scene):return False
    # Make fresh exact geometry BEFORE hiding the always-live GN model.
    refresh(scene,force=True)
    _show(bpy.data.objects[BODY],False)
    _show(bpy.data.objects[SNAP],True)
    scene['m1e5_mode']='EXACT_SCRIPT_ENABLED'
    return True

def disable(scene=None):
    scene=scene or bpy.context.scene
    if not ready(scene):return False
    _show(bpy.data.objects[SNAP],False)
    _show(bpy.data.objects[BODY],True)
    scene['m1e5_mode']='FAST_GN_ALWAYS_LIVE'
    return True

@persistent
def _on_frame(scene,*_args):
    if not ready(scene) or scene.get('m1e5_mode')!='EXACT_SCRIPT_ENABLED' or _STATE['busy']:
        return
    refresh(scene)

@persistent
def _on_depsgraph(scene,depsgraph):
    if not ready(scene) or scene.get('m1e5_mode')!='EXACT_SCRIPT_ENABLED' or _STATE['busy']:
        return
    if signature(scene)==_STATE['key']:return
    # Ignore mesh-change-induced dependency updates to avoid feedback loops;
    # only a changed knife pose is relevant to exact rebuild.
    refresh(scene)

@persistent
def _on_load(_dummy):
    _STATE['key']=None
    _STATE['kd']=None
    _STATE['kd_fingerprint']=None
    if ready(bpy.context.scene):
        enable(bpy.context.scene)

class STRAWBERRY_OT_m1e5_enable(bpy.types.Operator):
    bl_idname='strawberry_lab.m1e5_enable'
    bl_label='Live Exact: enable'
    bl_description='Enable automatic locally refined cut-surface rebuilds when knife moves'
    def execute(self,context):
        try:
            if not enable(context.scene):return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'},str(e));return {'CANCELLED'}
        return {'FINISHED'}

class STRAWBERRY_OT_m1e5_fast(bpy.types.Operator):
    bl_idname='strawberry_lab.m1e5_fast'
    bl_label='Fast: GN preview'
    bl_description='Switch to always-live Blender Geometry Nodes (no Python mesh rebuild)'
    def execute(self,context):
        disable(context.scene)
        return {'FINISHED'}

class STRAWBERRY_OT_m1e5_refresh(bpy.types.Operator):
    bl_idname='strawberry_lab.m1e5_refresh'
    bl_label='Force Refresh'
    bl_description='Force regeneration after editing source meshes, cavity or filament curves'
    def execute(self,context):
        _STATE['kd']=None
        _STATE['kd_fingerprint']=None
        try:
            result=refresh(context.scene,force=True)
            if not result:return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'},str(e));return {'CANCELLED'}
        return {'FINISHED'}

class STRAWBERRY_PT_m1e5(bpy.types.Panel):
    bl_label='Strawberry Lab — Live Exact'
    bl_idname='STRAWBERRY_PT_m1e5'
    bl_space_type='VIEW_3D'
    bl_region_type='UI'
    bl_category='Strawberry'
    @classmethod
    def poll(cls,context):return ready(context.scene)
    def draw(self,context):
        layout=self.layout
        if context.scene.get('m1e5_mode')=='EXACT_SCRIPT_ENABLED':
            layout.label(text='Exact: live script-assisted detail',icon='CHECKMARK')
        else:layout.label(text='Fast: geometry nodes preview',icon='MOD_SUBSURF')
        row=layout.row(align=True)
        row.operator('strawberry_lab.m1e5_enable',text='Exact')
        row.operator('strawberry_lab.m1e5_fast',text='Fast')
        layout.operator('strawberry_lab.m1e5_refresh',text='Force Refresh',icon='FILE_REFRESH')
        if _STATE['last_seconds'] is not None:
            layout.label(text='Last update: {:.2f} s'.format(_STATE['last_seconds']))
        layout.label(text='Move CTRL knife or scrub timeline')
        layout.label(text='Not GN-only; needs addon or Run Script')

_CLASSES=(STRAWBERRY_OT_m1e5_enable,STRAWBERRY_OT_m1e5_fast,STRAWBERRY_OT_m1e5_refresh,STRAWBERRY_PT_m1e5)

def register():
    # Re-running a Text datablock creates new Python function objects; remove
    # callbacks from the previous invocation to prevent duplicate updates.
    previous=bpy.app.driver_namespace.get(_HANDLER_KEY)
    if previous:
        for callback_list,fn in previous.get('handlers',[]):
            while fn in callback_list:callback_list.remove(fn)
        for cls in reversed(previous.get('classes',())):
            try:bpy.utils.unregister_class(cls)
            except RuntimeError:pass
    for cls in _CLASSES:bpy.utils.register_class(cls)
    if _on_frame not in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.append(_on_frame)
    if _on_depsgraph not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph)
    if _on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_on_load)
    bpy.app.driver_namespace[_HANDLER_KEY]={'handlers':[
        (bpy.app.handlers.frame_change_post,_on_frame),
        (bpy.app.handlers.depsgraph_update_post,_on_depsgraph),
        (bpy.app.handlers.load_post,_on_load)],'classes':_CLASSES}
    _STATE['installed']=True
    if ready(bpy.context.scene):enable(bpy.context.scene)
    print('M1E5_LIVE_EXACT_REGISTERED',flush=True)

def unregister():
    for hs,fn in [(bpy.app.handlers.frame_change_post,_on_frame),
                  (bpy.app.handlers.depsgraph_update_post,_on_depsgraph),
                  (bpy.app.handlers.load_post,_on_load)]:
        while fn in hs: hs.remove(fn)
    if ready(bpy.context.scene):disable(bpy.context.scene)
    for cls in reversed(_CLASSES):
        try:bpy.utils.unregister_class(cls)
        except RuntimeError:pass
    if bpy.app.driver_namespace.get(_HANDLER_KEY,{}).get('classes') is _CLASSES:
        bpy.app.driver_namespace.pop(_HANDLER_KEY,None)
    _STATE['key']=None
    _STATE['installed']=False
    print('M1E5_LIVE_EXACT_UNREGISTERED',flush=True)

if __name__=='__main__':
    register()

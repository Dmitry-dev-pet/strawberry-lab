"""Self-contained Blender 5.2 N sidebar for Strawberry Lab's real shared-plane cut.
The Empty LIVE CUT | move or rotate this Empty controls BOTH scene states in real time.
The full-fruit Boolean and clipped curves/seed shaders automatically evaluate its pose.
No external plugin install needed; run this Text block once after opening the .blend.
"""
import bpy,math
from bpy.props import EnumProperty,FloatProperty,BoolProperty
PLANE='LIVE CUT | move or rotate this Empty'
PREFIX='LIVE '
KEYS={
 'body_cut':'10 | FLESH cut','body_full':'11 | FLESH whole',
 'core_full':'20 | 28 CORE','core_clip':'21 | 28 CORE',
 'branch_full':'30 | 539 BRANCHES','branch_clip':'31 | 539 BRANCHES',
 'marker_full':'40 | 539 MARKERS','marker_clip':'41 | 539 MARKERS',
 'ghost':'50 | WHOLE OUTLINE'
}

def find_layer(sc,pattern):
    def scan(node):
        if pattern in node.collection.name:return node
        for ch in node.children:
            v=scan(ch)
            if v:return v
    return scan(sc.view_layers[0].layer_collection)

def toggle(sc,key,value):
    x=find_layer(sc,KEYS[key])
    if x is None:raise KeyError((sc.name,key))
    x.exclude=not value

def apply(sc):
    if not sc.name.startswith(PREFIX):return
    fb=sc.scl_body
    toggle(sc,'body_cut',fb=='CUT');toggle(sc,'body_full',fb=='FULL')
    for part in ('core','branch','marker'):
        v=getattr(sc,'scl_'+part)
        toggle(sc,part+'_full',v=='FULL')
        toggle(sc,part+'_clip',v=='CLIP')
    toggle(sc,'ghost',sc.scl_ghost)

def change(sc,ctx):apply(sc)

def get_offset(sc):return float(bpy.data.objects[PLANE].location.y)
def set_offset(sc,value):bpy.data.objects[PLANE].location.y=float(value)
def get_angle(sc):return math.degrees(float(bpy.data.objects[PLANE].rotation_euler.z))
def set_angle(sc,value):bpy.data.objects[PLANE].rotation_euler.z=math.radians(float(value))

class SCL_PT_main(bpy.types.Panel):
    bl_label='Strawberry Live Layers'
    bl_idname='SCL_PT_main'
    bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='Strawberry Live'
    @classmethod
    def poll(cls,ctx):return ctx.scene is not None and ctx.scene.name.startswith(PREFIX)
    def draw(self,ctx):
        l=self.layout;sc=ctx.scene
        l.label(text='ONE shared live plane')
        l.prop(sc,'scl_offset',text='Plane Y offset')
        l.prop(sc,'scl_angle',text='Plane rotation Z (deg)')
        l.separator()
        l.label(text='Geometry shown in this scene')
        l.prop(sc,'scl_body',text='Flesh')
        l.prop(sc,'scl_core',text='28 core carriers')
        l.prop(sc,'scl_branch',text='539 branches')
        l.prop(sc,'scl_marker',text='539 seed markers')
        l.prop(sc,'scl_ghost',text='Translucent whole outline')
        l.separator()
        l.label(text='Compare LIVE MATCHED / LIVE FLESH ONLY')
        l.label(text='No micro-cell/juice geometry yet')

_registered=False

def register():
    global _registered
    old=bpy.types.Panel.bl_rna_get_subclass_py('SCL_PT_main',None)
    if old:
        try:bpy.utils.unregister_class(old)
        except RuntimeError:pass
    items=[('OFF','Off','Hidden'),('CLIP','Clipped','Only positive local Y halfspace'),('FULL','Full','Unclipped source')]
    defs=[
      ('scl_offset',FloatProperty(name='Cut offset',min=-.75,max=.80,get=get_offset,set=set_offset)),
      ('scl_angle',FloatProperty(name='Cut angle',min=-80,max=80,get=get_angle,set=set_angle)),
      ('scl_body',EnumProperty(name='Flesh',items=[('OFF','Off',''),('CUT','Cut','Live Boolean'),('FULL','Whole','')],default='CUT',update=change)),
      ('scl_core',EnumProperty(name='Core',items=items,default='FULL',update=change)),
      ('scl_branch',EnumProperty(name='Branches',items=items,default='FULL',update=change)),
      ('scl_marker',EnumProperty(name='Markers',items=items,default='FULL',update=change)),
      ('scl_ghost',BoolProperty(name='Ghost outline',default=False,update=change))]
    for name,p in defs:
        if hasattr(bpy.types.Scene,name):delattr(bpy.types.Scene,name)
        setattr(bpy.types.Scene,name,p)
    bpy.utils.register_class(SCL_PT_main)
    current=bpy.context.window.scene if bpy.context.window else None
    for sc in bpy.data.scenes:
        if not sc.name.startswith(PREFIX):continue
        if bpy.context.window:bpy.context.window.scene=sc
        mode='CLIP' if 'MATCHED' in sc.name else 'FULL'
        sc.scl_body='CUT';sc.scl_core=mode;sc.scl_branch=mode;sc.scl_marker=mode;sc.scl_ghost=False
        apply(sc)
    if current and bpy.context.window:bpy.context.window.scene=current
    _registered=True
    print('STRAWBERRY_LIVE_UI_READY: Viewport N -> Strawberry Live',flush=True)

if __name__=='__main__':register()

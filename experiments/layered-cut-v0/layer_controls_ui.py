"""Optional interactive Blender N-panel for Strawberry Layer Lab v0.

Open layered .blend, go to Scripting, open 'LAYER_LAB_UI__RUN_IN_BLENDER.py'
and click Run Script once. A 'Strawberry Layers' tab then appears in the 3D
viewport sidebar (N). No external plugin install or proprietary code needed.

All controls change *actual* Blender ViewLayer collection exclusion state.
They operate on the CURRENT active layered scene only, so A/B are independent.
"""
import bpy
from bpy.props import BoolProperty, EnumProperty

SCENE_PREFIX='LAYER '
KEYS={
 'flesh':['10 | FLESH'],
 'core_full':['20 | CORE CARRIERS'],
 'core_clip':['21 | CORE CARRIERS'],
 'branches_full':['30 | VASCULAR BRANCHES'],
 'branches_clip':['31 | VASCULAR BRANCHES'],
 'seeds_full':['40 | SEED END MARKERS'],
 'seeds_clip':['41 | SEED END MARKERS'],
 'ghost':['50 | OUTLINE'],
}

def get_by_suffix(scene,fragment):
    def scan(layer):
        if fragment in layer.collection.name:return layer
        for c in layer.children:
            r=scan(c)
            if r:return r
        return None
    return scan(scene.view_layers[0].layer_collection)

def set_layer(scene,fragment,enabled):
    node=get_by_suffix(scene,fragment)
    if node is None:raise ValueError('Missing Blender layer '+fragment)
    node.exclude=not enabled

def apply(scene):
    if not scene.name.startswith(SCENE_PREFIX):return
    set_layer(scene,KEYS['flesh'][0],scene.sll_show_flesh)
    for part,param in [('core','sll_core'),('branches','sll_branches'),('seeds','sll_seeds')]:
        value=getattr(scene,param)
        set_layer(scene,KEYS[part+'_full'][0],value=='FULL')
        set_layer(scene,KEYS[part+'_clip'][0],value=='CLIP')
    set_layer(scene,KEYS['ghost'][0],scene.sll_ghost)

def changed(scene,context):
    apply(scene)

class SLL_PT_layers(bpy.types.Panel):
    bl_label='Independent layers / Strawberry'
    bl_idname='SLL_PT_layers'
    bl_space_type='VIEW_3D'
    bl_region_type='UI'
    bl_category='Strawberry Layers'

    @classmethod
    def poll(cls,context):
        return bool(context.scene) and context.scene.name.startswith('LAYER ')

    def draw(self,context):
        layout=self.layout
        sc=context.scene
        layout.label(text='Fixed physical flesh cut: Y = 0')
        layout.prop(sc,'sll_show_flesh',text='Flesh / Skin')
        layout.prop(sc,'sll_core',text='28 core carriers')
        layout.prop(sc,'sll_branches',text='539 vascular branches')
        layout.prop(sc,'sll_seeds',text='Achene end markers')
        layout.prop(sc,'sll_ghost',text='Transparent whole body')
        layout.separator()
        layout.label(text='FULL / CLIP / OFF per layer')
        layout.label(text='Commercial Frucht UI not reproduced')

registered=False

def register():
    global registered
    if registered:return
    # Running a text block twice is supported: replace prior panel class first.
    old=bpy.types.Panel.bl_rna_get_subclass_py('SLL_PT_layers',None)
    if old:
        try:bpy.utils.unregister_class(old)
        except Exception:pass
    items=[('OFF','Off','Hide this layer'),('CLIP','Clipped','Keep only y >= 0'),('FULL','Full','Whole 3D source')]
    props=[
        ('sll_show_flesh',BoolProperty(name='Flesh',default=True,update=changed)),
        ('sll_core',EnumProperty(name='Core carriers',items=items,default='FULL',update=changed)),
        ('sll_branches',EnumProperty(name='Branches',items=items,default='FULL',update=changed)),
        ('sll_seeds',EnumProperty(name='Achenes',items=items,default='FULL',update=changed)),
        ('sll_ghost',BoolProperty(name='Transparent outer shape',default=False,update=changed))
    ]
    for name,p in props:
        if hasattr(bpy.types.Scene,name):
            delattr(bpy.types.Scene,name)
        setattr(bpy.types.Scene,name,p)
    bpy.utils.register_class(SLL_PT_layers)
    registered=True
    previous_scene=bpy.context.window.scene if bpy.context.window else None
    for sc in bpy.data.scenes:
        if sc.name.startswith('LAYER '):
            if bpy.context.window:bpy.context.window.scene=sc
            mode='CLIP' if 'LAYER A' in sc.name else 'FULL'
            sc.sll_show_flesh=True
            sc.sll_core=mode
            sc.sll_branches=mode
            sc.sll_seeds=mode
            sc.sll_ghost=False
            apply(sc)
    if previous_scene and bpy.context.window:bpy.context.window.scene=previous_scene
    print('LAYER_LAB_UI_READY: 3D viewport > N > Strawberry Layers',flush=True)

if __name__=='__main__':register()

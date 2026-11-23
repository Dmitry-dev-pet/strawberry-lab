# Embedded after the nonlinear Exact runtime. No external module dependency.
PROFILE_CLASSES = []
def profile_cleanup():
    for cls in reversed(PROFILE_CLASSES):
        if cls.is_registered:bpy.utils.unregister_class(cls)
    for key in ('live_profile_a','live_profile_b','live_profile_h'):
        if hasattr(bpy.types.Scene,key):delattr(bpy.types.Scene,key)

def profile_forward(point, values):
    a,b,h=values;x,y,z=point
    scale=1+a*math.exp(-((z-.5)/.36)**2)+b*math.exp(-((z+.3)/.4)**2)
    return Vector((scale*x,scale*y,h*z))

class STRAWBERRY_OT_apply_profile(bpy.types.Operator):
    bl_idname='strawberry.apply_profile'
    bl_label='Apply Profile'
    bl_description='Recompute the same fruit from canonical source buffers; preserve seed IDs'
    bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        scene=context.scene
        values=(scene.live_profile_a,scene.live_profile_b,scene.live_profile_h)
        if not (-.25<=values[0]<=.3 and -.25<=values[1]<=.3 and .85<=values[2]<=1.2):
            self.report({'ERROR'},'Profile outside supported artist bounds');return {'CANCELLED'}
        was=SESSION.enabled;SESSION.disable()
        try:
            for obj in scene.objects:
                if obj.type=='MESH' and 'nonlinear_source_rest' in obj.data.attributes:
                    source=obj.data.attributes['nonlinear_source_rest'].data
                    for vertex,rest in zip(obj.data.vertices,source,strict=True):vertex.co=profile_forward(rest.vector,values)
                    obj.data.update()
                    if 'nonlinear_original_anchor' in obj:obj['hull_anchor_rest']=list(profile_forward(obj['nonlinear_original_anchor'],values))
                elif obj.type=='CURVE' and 'nonlinear_source_points' in obj:
                    source=json.loads(obj['nonlinear_source_points']);points=[p for sp in obj.data.splines for p in sp.points]
                    if len(source)!=len(points):raise ValueError('Canonical curve topology changed: '+obj.name)
                    for point,rest in zip(points,source,strict=True):point.co=(*profile_forward(rest,values),1)
                    obj.data.update_tag()
            for mat in bpy.data.materials:
                if not mat.node_tree or mat.get(TAG):continue
                for key,value in zip(('LIVE inverse shoulder','LIVE inverse waist','LIVE inverse height'),values,strict=True):
                    node=mat.node_tree.nodes.get(key)
                    if node:node.inputs[1 if key.endswith('height') else 0].default_value=value
            config=json.loads(scene['Nonlinear parameters']);config.update(a=values[0],b=values[1],h=values[2],status='LIVE_PROFILE_NEW_SEED_GRAPH_EXACT')
            scene['Nonlinear parameters']=json.dumps(config)
            obj=scene.objects['ARTIST | 28 trunks + 264 seed-linked terminals'];manifest=json.loads(obj['graph_manifest'])
            for node,sp in zip(manifest,obj.data.splines,strict=True):node['points']=[list(p.co[:3]) for p in sp.points]
            obj['graph_manifest']=json.dumps(manifest)
            SESSION.key=SESSION.strand_key=SESSION.strands=None
            context.view_layer.update();SESSION.enabled=was
            if was:SESSION.refresh(scene)
            if SESSION.error:raise ValueError(SESSION.error)
        except Exception as error:
            SESSION.disable();self.report({'ERROR'},str(error));return {'CANCELLED'}
        return {'FINISHED'}

class STRAWBERRY_PT_live_profile(bpy.types.Panel):
    bl_label='Live nonlinear profile'
    bl_idname='STRAWBERRY_PT_live_profile'
    bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='Strawberry Cut'
    def draw(self,context):
        layout=self.layout
        for key in ('live_profile_a','live_profile_b','live_profile_h'):layout.prop(context.scene,key)
        layout.operator('strawberry.apply_profile')
        layout.label(text='ARTIST graph: 28 trunks + 264 terminals')

for name in ('STRAWBERRY_PT_live_profile','STRAWBERRY_OT_apply_profile'):
    old=getattr(bpy.types,name,None)
    if old and old.is_registered:bpy.utils.unregister_class(old)
config=json.loads(bpy.context.scene['Nonlinear parameters'])
for key,label,default,lo,hi in [('live_profile_a','Shoulder a',config['a'],-.25,.3),('live_profile_b','Waist b',config['b'],-.25,.3),('live_profile_h','Height h',config['h'],.85,1.2)]:
    setattr(bpy.types.Scene,key,bpy.props.FloatProperty(name=label,default=default,min=lo,max=hi,precision=3))
for cls in (STRAWBERRY_OT_apply_profile,STRAWBERRY_PT_live_profile):
    bpy.utils.register_class(cls);PROFILE_CLASSES.append(cls)

"""Run this embedded Text to add N > Strawberry Layers to the 3D View."""

import bpy

SCENE = "Strawberry | live exterior and cut"
KNIFE = "LIVE CUT | move or rotate this Empty"
DIAGNOSTICS = "Diagnostics | original paths and 539 markers"
MARKERS = "Markers | 539 diagnostic anchors"
MODES = ("WHOLE", "MATCHED", "FLESH ONLY", "FIBERS ONLY")


class STRAWBERRY_OT_select_layer(bpy.types.Operator):
    bl_idname = "strawberry.select_layer"
    bl_label = "Select Strawberry View Layer"

    layer: bpy.props.EnumProperty(items=[(name, name, "") for name in MODES])

    @classmethod
    def poll(cls, context):
        return context.window is not None and context.scene.name == SCENE

    def execute(self, context):
        context.window.view_layer = context.scene.view_layers[self.layer]
        context.view_layer.update()
        return {"FINISHED"}


class STRAWBERRY_PT_layer_modes(bpy.types.Panel):
    bl_label = "Strawberry Layers"
    bl_idname = "STRAWBERRY_PT_layer_modes"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Strawberry Layers"

    @classmethod
    def poll(cls, context):
        return STRAWBERRY_OT_select_layer.poll(context)

    def draw(self, context):
        layout = self.layout
        layer = context.view_layer
        for name in MODES:
            control = layout.operator("strawberry.select_layer", text=name, depress=layer.name == name)
            control.layer = name
        knife = context.scene.objects[KNIFE]
        if layer.name in {"MATCHED", "FLESH ONLY"}:
            layout.prop(knife, "location", index=1, text="Knife Y")
            layout.prop(knife, "rotation_euler", index=0, text="Knife tilt")
            layout.prop(knife, "rotation_euler", index=2, text="Knife turn")
        if layer.name == "WHOLE":
            layout.label(text="Knife parked outside the fruit")
        else:
            markers = layer.layer_collection.children[DIAGNOSTICS].children[MARKERS]
            layout.prop(markers, "exclude", text="Hide diagnostic markers")
            layout.label(text="539 anchors ≠ 264 exterior achenes")


def register():
    classes = (STRAWBERRY_OT_select_layer, STRAWBERRY_PT_layer_modes)
    for cls in reversed(classes):
        base = cls.__bases__[0]
        old = getattr(bpy.types, cls.__name__, None)
        if old is None and base is bpy.types.Operator:
            old = base.bl_rna_get_subclass_py("STRAWBERRY_OT_select_layer", None)
        if old is not None:
            bpy.utils.unregister_class(old)
    for cls in classes:
        bpy.utils.register_class(cls)


if __name__ == "__main__":
    register()

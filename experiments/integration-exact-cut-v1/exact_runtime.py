"""Session controls for the derived Exact cap. Embedded after cap_geometry.py."""

import bpy

SCENE = "Strawberry | live exterior and cut"
BODY = "Receptacle | canonical PR29 hull"
REST = "Strawberry | PR29 rest space"
KNIFE = "LIVE CUT | move or rotate this Empty"
CUTTER = "LIVE CUT | Boolean subtraction volume (hidden in render)"
CURVES = (("V3 | 28-sag0.25 | CARRIERS", 28), ("V4 | hook0.85 | BRANCHES", 539))
PARK_KNIFE = "strawberry_park_knife"
CUT_LAYERS = {"MATCHED", "FLESH ONLY"}
HEIGHT = "strawberry_exact_height_mm"
INFLUENCE = "strawberry_exact_strand_influence"
HEIGHT_CONTROL = "strawberry_exact_height_control"
INFLUENCE_CONTROL = "strawberry_exact_influence_control"
TEXT = "EXACT_CUT__RUN.py"
RUNTIME = "strawberry.integration.exact_cut.v1"
TAG = "_strawberry_transient_exact"


def belongs(scene):
    return scene is not None and scene.name == SCENE and TEXT in bpy.data.texts


def remove_derived():
    """Remove tagged IDs, including transient data restored by Blender undo."""
    for body in bpy.data.objects:
        for modifier in list(body.modifiers):
            if modifier.type == "NODES" and modifier.node_group and modifier.node_group.get(TAG):
                park = modifier.node_group.interface.items_tree.get("Park knife")
                if park is not None:
                    getattr(modifier.properties.inputs, park.identifier).driver_remove("value")
                owned_animation = modifier.node_group.get("created_animation_data")
                body.modifiers.remove(modifier)
                animation = body.animation_data
                if owned_animation and animation and not (animation.action or animation.drivers or animation.nla_tracks):
                    body.animation_data_clear()
    for items in (bpy.data.node_groups, bpy.data.objects, bpy.data.meshes, bpy.data.materials):
        for item in list(items):
            if item.get(TAG):
                items.remove(item, do_unlink=True)


def cache_material(body):
    material = body.data.materials[CAP].copy()
    material[TAG] = True
    material.name = "Strawberry | Exact cap with undeformed atlas coordinates"
    tree = material.node_tree
    original = tree.nodes["PR29 rest coordinates"].outputs["Object"]
    attribute = tree.nodes.new("ShaderNodeAttribute")
    attribute.name = "Exact cap | undeformed PR29 atlas coordinates"
    attribute.attribute_name = REST_ATTRIBUTE
    attribute.location = original.node.location
    for link in list(original.links):
        tree.links.new(attribute.outputs["Vector"], link.to_socket)
    return material


def install_modifier(scene, body, mesh):
    """Route the derived mesh through the canonical object's render and layer visibility."""
    cache = bpy.data.objects.new("Strawberry | transient Exact mesh cache", mesh)
    cache[TAG] = True
    scene.collection.objects.link(cache)
    cache.hide_render = True
    cache.hide_select = True
    for layer in scene.view_layers:
        cache.hide_set(True, view_layer=layer)

    tree = bpy.data.node_groups.new("Strawberry | choose native or derived cut", "GeometryNodeTree")
    tree[TAG] = True
    tree.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    park = tree.interface.new_socket(name="Park knife", in_out="INPUT", socket_type="NodeSocketFloat")
    tree.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    inputs = tree.nodes.new("NodeGroupInput")
    obj = tree.nodes.new("GeometryNodeObjectInfo")
    obj.transform_space = "ORIGINAL"
    obj.inputs["Object"].default_value = cache
    switch = tree.nodes.new("GeometryNodeSwitch")
    switch.input_type = "GEOMETRY"
    output = tree.nodes.new("NodeGroupOutput")
    inputs.location, obj.location, switch.location, output.location = (
        (-400, 160), (-400, -60), (-100, 120), (160, 120))
    for source, target in (
        (inputs.outputs["Park knife"], switch.inputs["Switch"]),
        (inputs.outputs["Geometry"], switch.inputs["True"]),
        (obj.outputs["Geometry"], switch.inputs["False"]),
        (switch.outputs["Output"], output.inputs["Geometry"]),
    ):
        tree.links.new(source, target)
    modifier = body.modifiers.new("Cut quality | Exact (session only)", "NODES")
    modifier.node_group = tree
    tree["created_animation_data"] = body.animation_data is None
    driver = getattr(modifier.properties.inputs, park.identifier).driver_add("value").driver
    driver.type = "AVERAGE"
    var = driver.variables.new()
    var.name = "park"
    var.type = "CONTEXT_PROP"
    target = var.targets[0]
    target.context_property = "ACTIVE_VIEW_LAYER"
    target.data_path = f'["{PARK_KNIFE}"]'
    target.use_fallback_value = True
    target.fallback_value = 1
    return cache, modifier


def matrix_key(matrix):
    return tuple(round(value, 8) for row in matrix for value in row)


class ExactSession:
    def __init__(self):
        self.enabled = False
        self.busy = False
        self.key = None
        self.strand_key = None
        self.strands = None
        self.cache = None
        self.modifier = None
        self.material = None
        self.error = None
        self.last = None
        self.refresh_count = 0
        self.source_revision = 0

    def inputs(self, scene, graph):
        body, rest, knife, cutter = (scene.objects[name] for name in (BODY, REST, KNIFE, CUTTER))
        curves = [(scene.objects[name].evaluated_get(graph), count) for name, count in CURVES]
        world_to_rest = rest.evaluated_get(graph).matrix_world.inverted()
        model = body.evaluated_get(graph).matrix_world
        body_to_rest = world_to_rest @ model
        body_to_knife = knife.evaluated_get(graph).matrix_world.inverted() @ model
        knife_to_cutter = knife.evaluated_get(graph).matrix_world.inverted() @ cutter.evaluated_get(graph).matrix_world
        scale = scene.unit_settings.scale_length * 1000.0
        settings = (float(scene[HEIGHT]), float(scene[INFLUENCE]))
        if not (scale > 0 and 0 <= settings[0] <= 0.6 and 0 <= settings[1] <= 1):
            raise ValueError("Invalid scene scale or Exact relief settings")
        strand_key = (self.source_revision, scale, *(matrix_key(world_to_rest @ obj.matrix_world)
                                                      for obj, _ in curves))
        key = (matrix_key(body_to_knife), matrix_key(body_to_rest), matrix_key(knife_to_cutter),
               strand_key, settings)
        return key, body, body_to_knife, body_to_rest, world_to_rest, curves, scale, settings

    def clear_mesh(self):
        remove_derived()
        self.cache = self.modifier = self.material = None

    def disable(self):
        self.enabled = False
        if not self.busy and bpy.app.timers.is_registered(on_timer):
            bpy.app.timers.unregister(on_timer)
        self.clear_mesh()
        self.key = self.strand_key = self.strands = None

    def refresh(self, scene=None):
        scene = scene or bpy.context.scene
        layer = bpy.context.view_layer
        if not self.enabled or self.busy or not belongs(scene) or layer.name not in CUT_LAYERS:
            return
        self.busy = True
        started = perf_counter()
        try:
            layer.update()
            graph = bpy.context.evaluated_depsgraph_get()
            key, body, to_knife, to_rest, world_to_rest, curves, scale, settings = self.inputs(scene, graph)
            if key == self.key:
                return
            if body.mode != "OBJECT":
                raise ValueError("Return the canonical hull to Object Mode for Exact")
            # Disable only the transient output while sampling the live native Boolean.
            if self.modifier is not None:
                self.modifier.show_viewport = False
                layer.update()
            graph = bpy.context.evaluated_depsgraph_get()
            base = body.evaluated_get(graph).data
            if self.strand_key != key[3] and all(settings):
                self.strands = strand_segments(curves, world_to_rest, scale)
                self.strand_key = key[3]
            mesh, stats = make_mesh(base, to_knife, to_rest, scale, settings, self.strands)
            if mesh is None:
                self.clear_mesh()
            else:
                mesh[TAG] = True
                if self.material is None:
                    self.material = cache_material(body)
                mesh.materials[CAP] = self.material
                if self.cache is None:
                    self.cache, self.modifier = install_modifier(scene, body, mesh)
                else:
                    old = self.cache.data
                    self.cache.data = mesh
                    bpy.data.meshes.remove(old)
                self.modifier.show_viewport = True
            self.key = key
            layer.update()
            stats["refresh_seconds"] = perf_counter() - started
            self.last = stats
            self.refresh_count += 1
            self.error = None
            print("STRAWBERRY_EXACT", stats, flush=True)
            return stats
        except Exception as exc:
            self.fail(exc)
        finally:
            self.busy = False

    def fail(self, exc):
        self.error = str(exc)
        self.disable()
        print(f"STRAWBERRY_EXACT_FALLBACK {type(exc).__name__}: {exc}", flush=True)


SESSION = ExactSession()


def on_timer():
    SESSION.refresh()
    return None


def queue_refresh():
    if not bpy.app.timers.is_registered(on_timer):
        bpy.app.timers.register(on_timer, first_interval=0.12)


def on_setting(scene, _context):
    if SESSION.enabled and belongs(scene):
        queue_refresh()


def on_change(scene, graph):
    if (not SESSION.enabled or SESSION.busy or not belongs(scene)
            or graph.view_layer.name not in CUT_LAYERS or graph.mode != "VIEWPORT"):
        return
    try:
        names = (BODY, CUTTER, *(name for name, _ in CURVES))
        authored_data = {scene.objects[name].data for name in names}
        if any(update.id.original in authored_data for update in graph.updates):
            SESSION.source_revision += 1
        if SESSION.inputs(scene, graph)[0] != SESSION.key:
            queue_refresh()
    except Exception as exc:
        # Defer fallback too so the callback never changes the evaluating graph.
        print(f"STRAWBERRY_EXACT_REFRESH_PENDING {exc}", flush=True)
        queue_refresh()


def on_render(scene, *_args):
    if not belongs(scene) or not SESSION.enabled:
        return
    # A render can request MATCHED while the viewport is still in WHOLE.
    # Evaluate the unparked knife before any render layer consumes this cache.
    window = bpy.context.window
    if window is None or window.scene != scene:
        SESSION.fail(RuntimeError("No cut-layer evaluation context; Fast restored for render"))
        return
    previous = window.view_layer
    try:
        window.view_layer = scene.view_layers["MATCHED"]
        SESSION.refresh(scene)
    except Exception as exc:
        SESSION.fail(exc)
    finally:
        window.view_layer = previous
        previous.update()


def on_save(_filepath):
    SESSION.disable()


def on_load(_filepath):
    unregister()


def on_undo(_scene):
    SESSION.disable()


class STRAWBERRY_OT_exact_quality(bpy.types.Operator):
    bl_idname = "strawberry.exact_quality"
    bl_label = "Strawberry Cut Quality"

    exact: bpy.props.BoolProperty()

    @classmethod
    def poll(cls, context):
        return belongs(context.scene) and context.view_layer.name in CUT_LAYERS

    def execute(self, context):
        SESSION.error = None
        if self.exact:
            SESSION.enabled = True
            SESSION.refresh(context.scene)
            if SESSION.error:
                self.report({"WARNING"}, SESSION.error)
                return {"CANCELLED"}
        else:
            SESSION.disable()
            context.view_layer.update()
        return {"FINISHED"}


class STRAWBERRY_OT_exact_unload(bpy.types.Operator):
    bl_idname = "strawberry.exact_unload"
    bl_label = "Disable Exact Runtime"

    def execute(self, _context):
        # Unregister the active operator after Blender returns from its execution.
        SESSION.disable()
        if not bpy.app.timers.is_registered(unregister):
            bpy.app.timers.register(unregister)
        return {"FINISHED"}


class STRAWBERRY_PT_exact_cut(bpy.types.Panel):
    bl_label = "Strawberry Cut Quality"
    bl_idname = "STRAWBERRY_PT_exact_cut"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Strawberry Cut"

    @classmethod
    def poll(cls, context):
        return belongs(context.scene)

    def draw(self, context):
        layout = self.layout
        if context.view_layer.name in CUT_LAYERS:
            row = layout.row(align=True)
            row.operator("strawberry.exact_quality", text="Fast", depress=not SESSION.enabled).exact = False
            row.operator("strawberry.exact_quality", text="Exact", depress=SESSION.enabled).exact = True
            layout.prop(context.scene, HEIGHT_CONTROL)
            layout.prop(context.scene, INFLUENCE_CONTROL, slider=True)
            if SESSION.enabled and SESSION.last and SESSION.last["cap"]:
                layout.label(text=f'Last rebuild  {SESSION.last["refresh_seconds"]:.2f} s')
        if SESSION.error:
            layout.label(text="Fast restored. See console for detail.", icon="ERROR")
        layout.operator("strawberry.exact_unload")


CLASSES = (STRAWBERRY_OT_exact_quality, STRAWBERRY_OT_exact_unload, STRAWBERRY_PT_exact_cut)
HANDLERS = {
    "depsgraph_update_post": on_change,
    "render_pre": on_render,
    "save_pre": on_save,
    "load_pre": on_load,
    "undo_post": on_undo,
    "redo_post": on_undo,
}


def unregister():
    current = bpy.app.driver_namespace.get(RUNTIME)
    if current is not None and current["session"] is not SESSION:
        return
    SESSION.disable()
    for name, handler in HANDLERS.items():
        handlers = getattr(bpy.app.handlers, name)
        if handler in handlers:
            handlers.remove(handler)
    for cls in reversed(CLASSES):
        if cls.is_registered:
            bpy.utils.unregister_class(cls)
    for name in (HEIGHT_CONTROL, INFLUENCE_CONTROL):
        if hasattr(bpy.types.Scene, name):
            delattr(bpy.types.Scene, name)
    bpy.app.driver_namespace.pop(RUNTIME, None)


def register():
    if not belongs(bpy.context.scene):
        raise RuntimeError("Open the Strawberry Exact Cut scene first")
    old = bpy.app.driver_namespace.get(RUNTIME)
    if old:
        old["unregister"]()
    remove_derived()
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    setattr(bpy.types.Scene, HEIGHT_CONTROL, bpy.props.FloatProperty(
        name="Relief height (mm)", min=0.0, max=0.6, precision=3,
        get=lambda scene: scene[HEIGHT], set=lambda scene, value: scene.__setitem__(HEIGHT, value),
        update=on_setting))
    setattr(bpy.types.Scene, INFLUENCE_CONTROL, bpy.props.FloatProperty(
        name="Strand influence", min=0.0, max=1.0,
        get=lambda scene: scene[INFLUENCE], set=lambda scene, value: scene.__setitem__(INFLUENCE, value),
        update=on_setting))
    for name, handler in HANDLERS.items():
        getattr(bpy.app.handlers, name).append(handler)
    bpy.app.driver_namespace[RUNTIME] = {
        "session": SESSION, "unregister": unregister, "timer": on_timer, "handler": on_change,
    }


if __name__ == "__main__":
    register()

"""Independent triangle intersections and reviewer regression checks; no scene save."""
from pathlib import Path
import json
import sys
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_pits import BODY, immutable_snapshot, tree_for_mesh
from render_pits import sha

scene_path, baseline, renders, output = map(Path, sys.argv[sys.argv.index("--") + 1:])
assert not output.exists()
bpy.ops.wm.open_mainfile(filepath=str(scene_path.resolve()), use_scripts=False)
scene = bpy.context.scene
body = scene.objects[BODY].data
body.calc_loop_triangles()
body_tree = tree_for_mesh(body)

def intersections(obj):
    obj.data.calc_loop_triangles()
    points = [obj.matrix_local @ vertex.co for vertex in obj.data.vertices]
    faces = [triangle.vertices[:] for triangle in obj.data.loop_triangles]
    seed_tree = BVHTree.FromPolygons(points, faces, all_triangles=True)
    return len(seed_tree.overlap(body_tree))

seeds = sorted((o for o in scene.objects if o.get("role") == "achene"), key=lambda o:o.name)
assert len(seeds) == 264
counts = {seed.name: intersections(seed) for seed in seeds}
assert min(counts.values()) > 0
seed = seeds[0]
original = seed.location.copy()
seed.location += Vector(seed["hull_normal_rest"]) * .15
bpy.context.view_layer.update()
assert intersections(seed) == 0, "Detached seed was not detected"
seed.location = original
bpy.context.view_layer.update()
snapshot = immutable_snapshot(scene)
ramp = next(node for material in bpy.data.materials if material.node_tree
            for node in material.node_tree.nodes if node.type == "VALTORGB")
original_color = tuple(ramp.color_ramp.elements[0].color)
ramp.color_ramp.elements[0].color = (0, 1, 0, 1)
assert immutable_snapshot(scene) != snapshot, "ColorRamp mutation escaped the snapshot"
ramp.color_ramp.elements[0].color = original_color
assert immutable_snapshot(scene) == snapshot
report = {"status":"PASS", "scene_sha256":sha(scene_path),
          "all_264_actual_meshes_intersect_body":True, "triangle_pair_counts":counts,
          "detached_seed_rejected":True, "color_ramp_mutation_rejected":True}
output.write_text(json.dumps(report, indent=2) + "\n")
print("264 actual mesh contacts and two negative regressions PASS", flush=True)

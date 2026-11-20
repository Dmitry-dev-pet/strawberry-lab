"""Reopen the generated blend and validate its real geometry in Blender.

blender -b build/exterior-v1/strawberry-exterior.blend --python-exit-code 1 \
    --python src/validate_strawberry_exterior.py
"""

from array import array
import hashlib
import json
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exterior_shape import ExteriorParams, ExteriorShape


def closed_surface(mesh):
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        assert all(edge.is_manifold and edge.is_contiguous for edge in bm.edges), mesh.name
        assert bm.calc_volume(signed=True) > 0, mesh.name
        return BVHTree.FromBMesh(bm)
    finally:
        bm.free()


def validate():
    scene = bpy.context.scene
    assert scene.unit_settings.system == "METRIC"
    assert scene.unit_settings.length_unit == "MILLIMETERS"
    assert abs(scene.unit_settings.scale_length - 0.001) < 1e-9
    assert scene.render.engine == "CYCLES" and scene.camera is not None
    assert scene.render.image_settings.file_format == "PNG"
    assert not bpy.data.libraries
    assert not any(image.source in {"FILE", "SEQUENCE", "MOVIE", "TILED"}
                   and not image.packed_file for image in bpy.data.images)
    params = ExteriorParams(**json.loads(scene["exterior_params"]))
    anchors = ExteriorShape(params).anchors()
    body, = (obj for obj in scene.objects if obj.get("role") == "receptacle")
    # Ray tests below use the shared parent coordinate system. Reject a body
    # moved independently from its seeds instead of reporting false contact.
    from mathutils import Matrix
    assert all(abs(body.matrix_local[i][j] - Matrix.Identity(4)[i][j]) < 1e-7
               for i in range(4) for j in range(4)), "Receptacle transform differs from seed parent space"
    pedicel, = (obj for obj in scene.objects if obj.get("role") == "pedicel")
    sepals = [obj for obj in scene.objects if obj.get("role") == "sepal"]
    seeds = sorted((obj for obj in scene.objects if obj.get("role") == "achene"),
                   key=lambda obj: obj.name)
    assert len(sepals) == 8
    assert len(seeds) == len(anchors)
    assert all(obj.parent == body.parent for obj in [pedicel, *sepals, *seeds])
    assert len(body.data.vertices) < 200_000
    assert body.data.attributes["achene_pit"].domain == "POINT"
    assert body.data.materials[0].node_tree
    vertices = body.data.vertices
    bounds = [max(v.co[i] for v in vertices) - min(v.co[i] for v in vertices) for i in range(3)]
    assert abs(bounds[2] - params.height_mm) < 0.01
    assert abs(max(bounds[:2]) - params.width_mm) < 0.15

    body_bvh = closed_surface(body.data)
    closed_surface(pedicel.data)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in sepals:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            closed_surface(mesh)
        finally:
            evaluated.to_mesh_clear()

    prototype_heights = {}
    min_exposed = float("inf")
    min_embedded = float("inf")
    largest_pit_floor_error = 0.0
    digest = hashlib.sha256()
    coords = array("f", [0.0]) * (3 * len(body.data.vertices))
    body.data.vertices.foreach_get("co", coords)
    digest.update(coords.tobytes())
    for obj, anchor in zip(seeds, anchors):
        center = obj.location
        normal = obj.rotation_quaternion @ Vector((0, 0, 1))
        along = obj.rotation_quaternion @ Vector((0, 1, 0))
        assert (center - Vector(anchor.center)).length < 1e-5, obj.name
        assert (normal - Vector(anchor.normal)).length < 1e-5, obj.name
        assert (along - Vector(anchor.long_axis)).length < 1e-5, obj.name
        if obj.data.name not in prototype_heights:
            seed_bvh = closed_surface(obj.data)
            up = Vector((0, 0, 1))
            top, *_ = seed_bvh.ray_cast(up, -up)
            bottom, *_ = seed_bvh.ray_cast(-up, up)
            assert top is not None and bottom is not None
            prototype_heights[obj.data.name] = (top.z, bottom.z)

        floor, *_ = body_bvh.ray_cast(center + normal * 2, -normal, 3)
        assert floor is not None, obj.name
        offset = (floor - center).dot(normal)
        top, bottom = prototype_heights[obj.data.name]
        exposed = top * obj.scale.z - offset
        embedded = offset - bottom * obj.scale.z
        assert exposed > 0.02 and embedded > 0.02, obj.name
        min_exposed = min(min_exposed, exposed)
        min_embedded = min(min_embedded, embedded)
        pit_depth = (Vector(anchor.point) - floor).dot(normal)
        assert pit_depth > 0.15, obj.name
        largest_pit_floor_error = max(largest_pit_floor_error, abs(pit_depth - anchor.pit_depth_mm))
        digest.update(array("f", (*center, *obj.rotation_quaternion, *obj.scale)).tobytes())
    assert largest_pit_floor_error < 0.055

    report = {
        "status": "pass",
        "blend": bpy.data.filepath,
        "body_local_bbox_mm": bounds,
        "body_vertices": len(body.data.vertices),
        "closed_body": True,
        "achenes_with_surface_contact": len(seeds),
        "linked_achene_meshes": len(prototype_heights),
        "closed_sepals": len(sepals),
        "closed_pedicel": True,
        "min_achene_exposure_mm": min_exposed,
        "min_achene_embedding_mm": min_embedded,
        "max_pit_depth_error_mm": largest_pit_floor_error,
        "body_and_achene_transforms_sha256": digest.hexdigest(),
    }
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    validate()

"""Refine the evaluated Boolean cap while keeping its original skin and seam."""

from math import ceil, floor, sqrt
from time import perf_counter

import bmesh
import bpy
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
from mathutils.kdtree import KDTree
from mathutils.noise import noise, voronoi

REST_ATTRIBUTE = "strawberry_exact_rest"
CAP = 1
PLANE_EPS = 1e-4
STEP_MM = 0.27
SEAM_FADE_MM = 0.75
STRAND_FALLOFF_MM = 0.65
MAX_CAP_VERTICES = 60000


def smoothstep(value):
    t = min(1.0, max(0.0, value))
    return t * t * (3.0 - 2.0 * t)


class Segments:
    """Exact point-to-segment queries within a finite distance, via midpoint bounds."""

    def __init__(self, segments, max_length):
        self.pieces = []
        self.max_radius = 0.0
        for start, end, ra, rb in segments:
            delta = end - start
            count = max(1, ceil(delta.length / max_length))
            for i in range(count):
                a, b = i / count, (i + 1) / count
                step = delta / count
                self.pieces.append((start + a * delta, step, step.length_squared,
                                    ra + a * (rb - ra), (rb - ra) / count))
            self.max_radius = max(self.max_radius, ra, rb)
        self.half_length = max_length / 2
        self.tree = KDTree(len(self.pieces))
        for i, (start, delta, *_rest) in enumerate(self.pieces):
            self.tree.insert(start + delta / 2, i)
        self.tree.balance()

    def distance(self, point, limit):
        nearest = limit
        for _, i, _ in self.tree.find_range(point, limit + self.max_radius + self.half_length):
            start, delta, length_sq, radius, radius_delta = self.pieces[i]
            offset = point - start
            t = min(1.0, max(0.0, offset.dot(delta) / length_sq)) if length_sq else 0.0
            nearest = min(nearest, (offset - t * delta).length - radius - t * radius_delta)
        return nearest


def strand_segments(curves, world_to_rest, mm_per_unit):
    segments = []
    for obj, count in curves:
        if len(obj.data.splines) != count:
            raise ValueError(f"Expected {count} splines on {obj.name}")
        transform = world_to_rest @ obj.matrix_world
        scale = transform.to_scale()
        if max(scale) - min(scale) > 1e-5:
            raise ValueError(f"Expected uniform curve scale on {obj.name}")
        depth = obj.data.bevel_depth * abs(scale.x)
        for spline in obj.data.splines:
            if spline.type != "POLY":
                raise ValueError("Exact relief requires the original polygonal paths")
            points = [(transform @ Vector(point.co[:3]), depth * point.radius)
                      for point in spline.points]
            if spline.use_cyclic_u:
                points.append(points[0])
            segments.extend((a, b, ra, rb) for (a, ra), (b, rb) in zip(points, points[1:]))
    return Segments(segments, 0.45 / mm_per_unit)


def cap_patch(bm, body_to_knife, mm_per_unit):
    cap_faces = [face for face in bm.faces if face.material_index == CAP]
    if not cap_faces:
        return None

    # Work in knife X/Z. Counterclockwise triangles in this basis face knife -Y.
    plane = body_to_knife.inverted()
    outward = body_to_knife.to_3x3().transposed() @ Vector((0.0, -1.0, 0.0))
    outward.normalize()
    source_verts = sorted({vert for face in cap_faces for vert in face.verts},
                          key=lambda vert: vert.index)
    to_index = {vert: index for index, vert in enumerate(source_verts)}
    coords = []
    for vert in source_verts:
        v = body_to_knife @ vert.co
        if abs(v.y) > PLANE_EPS:
            raise ValueError("A Boolean cap face lies off the knife plane")
        coords.append(Vector((v.x, v.z)))
    faces = []
    seam = set()
    for face in cap_faces:
        if face.normal.dot(outward) < 0.99:
            raise ValueError("Unexpected Boolean cap winding")
        faces.append([to_index[vert] for vert in face.verts])
        seam.update(edge for edge in face.edges
                    if any(other.material_index != CAP for other in edge.link_faces))
    if not seam:
        raise ValueError("The Boolean cap has no shared skin seam")
    seam_edges = sorted(tuple(sorted(to_index[vert] for vert in edge.verts)) for edge in seam)
    seam_ids = {i for edge in seam_edges for i in edge}

    # Staggered interior samples let CDT refine a large ngon without touching skin edges.
    # The oriented original cap faces constrain the patch, including any holes.
    x0, x1 = min(v.x for v in coords), max(v.x for v in coords)
    z0, z1 = min(v.y for v in coords), max(v.y for v in coords)
    unit_x = plane.to_3x3().col[0].length
    unit_z = plane.to_3x3().col[2].length
    step_x = STEP_MM / mm_per_unit / unit_x
    step_z = STEP_MM * sqrt(3) / 2 / mm_per_unit / unit_z
    rows = range(floor(z0 / step_z), ceil(z1 / step_z) + 1)
    columns = range(floor(x0 / step_x), ceil(x1 / step_x) + 1)
    if len(rows) * len(columns) + len(coords) > MAX_CAP_VERTICES:
        raise ValueError("Exact cap exceeds its sampling budget")
    for row in rows:
        for column in columns:
            coords.append(Vector(((column + 0.5 * (row % 2)) * step_x, row * step_z)))

    points, _, triangles, origins, _, covering = delaunay_2d_cdt(coords, [], faces, 1, 1e-7)
    triangles = [tri for tri, source in zip(triangles, covering, strict=True) if source]
    used = sorted({index for tri in triangles for index in tri})
    if not triangles:
        raise ValueError("No refined triangles inside the Boolean cap")

    # Preserve all shared vertices and edges while removing the old cap interior.
    inner_edges = {edge for face in cap_faces for edge in face.edges} - seam
    bmesh.ops.delete(bm, geom=cap_faces, context="FACES_ONLY")
    for edge in inner_edges:
        bm.edges.remove(edge)
    for i, vertex in enumerate(source_verts):
        if i not in seam_ids and not vertex.link_edges:
            bm.verts.remove(vertex)
    refined = {}
    seen = set()
    for i in used:
        edge_ids = set(origins[i]) & seam_ids
        if edge_ids:
            if len(edge_ids) != 1:
                raise ValueError("The triangulator merged distinct seam vertices")
            original = edge_ids.pop()
            refined[i] = source_verts[original]
            seen.add(original)
        else:
            refined[i] = bm.verts.new(plane @ Vector((points[i].x, 0, points[i].y)))
    if seen != seam_ids:
        raise ValueError("The triangulator dropped a seam vertex")
    for triangle in triangles:
        face = bm.faces.new([refined[index] for index in triangle])
        face.material_index = CAP
        face.smooth = True
    if not all(edge.is_valid and edge.is_manifold for edge in seam):
        raise ValueError("A refined triangle split the skin seam")
    # Keep cap smoothing out of the skin's existing normal fan.
    for edge in seam:
        edge.smooth = False
    return outward, refined.values(), {source_verts[i] for i in seam_ids}, seam


def make_mesh(base, body_to_knife, body_to_rest, mm_per_unit, settings, strands):
    """Return a derived closed mesh, or None when the knife makes no cut."""
    started = perf_counter()
    bm = bmesh.new()
    mesh = None
    try:
        bm.from_mesh(base)
        rest_layer = bm.verts.layers.float_vector.new(REST_ATTRIBUTE)
        bm.verts.index_update()
        bm.normal_update()
        patch = cap_patch(bm, body_to_knife, mm_per_unit)
        if patch is None:
            return None, {"cap": False}
        outward, cap_vertices, seam_vertices, seam = patch
        mm = mm_per_unit
        fade = SEAM_FADE_MM / mm
        boundary = Segments(((a.co.copy(), b.co.copy(), 0.0, 0.0)
                             for a, b in (edge.verts for edge in seam)), fade)
        for vertex in bm.verts:
            vertex[rest_layer] = body_to_rest @ vertex.co
        height_mm, strand_influence = settings
        heights = []
        for vertex in cap_vertices:
            if vertex in seam_vertices:
                continue
            rest = Vector(vertex[rest_layer])
            # Coherent rest-space cellular ridges, softened by a broader irregular field.
            sample = rest * (mm / 0.96) + Vector((3.7, 8.2, 5.1))
            distances, _ = voronoi(sample)
            ridge = 1 - smoothstep((distances[1] - distances[0]) / 0.34)
            variation = 0.5 + 0.5 * noise(rest * (mm / 1.81))
            signal = 0.14 + 0.52 * ridge + 0.24 * variation
            if height_mm and strand_influence:
                reach = STRAND_FALLOFF_MM / mm
                signal += 0.46 * strand_influence * (1 - smoothstep(strands.distance(rest, reach) / reach))
            distance = boundary.distance(vertex.co, fade)
            height = min(height_mm / mm * signal, 0.45 * distance) * smoothstep(distance / fade)
            vertex.co += height * outward
            heights.append(height * mm)
        bm.normal_update()
        bad_edges = sum(not edge.is_manifold or not edge.is_contiguous for edge in bm.edges)
        volume = bm.calc_volume(signed=True)
        if bad_edges or volume <= 0:
            raise ValueError(f"Exact mesh has {bad_edges} open/misoriented edges and volume {volume}")
        mesh = bpy.data.meshes.new("Strawberry | transient Exact cut mesh")
        for material in base.materials:
            mesh.materials.append(material)
        bm.to_mesh(mesh)
        mesh.update()
        return mesh, {
            "cap": True, "fast_vertices": len(base.vertices), "vertices": len(mesh.vertices),
            "faces": len(mesh.polygons), "seam_vertices": len(seam_vertices),
            "cap_interior_vertices": len(heights),
            "mean_displacement_mm": sum(heights) / len(heights), "max_displacement_mm": max(heights),
            "nonmanifold_edges": bad_edges, "volume_model_units_cubed": volume,
            "refine_seconds": perf_counter() - started,
        }
    except Exception:
        if mesh is not None:
            bpy.data.meshes.remove(mesh)
        raise
    finally:
        bm.free()

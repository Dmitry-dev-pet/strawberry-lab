# M1e4 · Selection-refined cut surface + persistent 3D filament skeleton

**21 Nov 2026; experimental Blender 5.2.4 LTS implementation.** Written independently from the source M1e3 Fast scene; no Frucht GPL/private nodes copied. The goal is procedural geometry and the visible appearance of a cut, not scientific histology.

## Implementation

- The source is the saved **M1e3 Geometry Nodes** scene: full sealed strawberry, persistent 3D cavity and a knife that moves independently. The original GN body is retained in each resulting `.blend` but hidden for exact-snapshot rendering.
- `build_m1e4.py` evaluates the original pre-detail SDF-cut surface at an explicit knife pose, then selects *only* faces labelled `cut` plus the cavity faces **near the knife**. It uses `bmesh.ops.subdivide_edges` on all edges of these faces; adjacent faces are stitched by BMesh. The rest of the skin mesh is not globally subdivided.
- Cut/cavity relief is evaluated with the earlier **3D `fruit_rest` fields**, by reconnecting the original Geometry Nodes displacement stage to the **locally refined** mesh instead of the former whole-mesh `Subdivide Mesh` node.
- The existing M1a authored curve network has **539 spatial 17-point paths**. M1e4 deterministically takes every fourth spline (**135 curves, 2,295 source points**). A KDTree of these true 3D points gives a stable distance field, evaluated at locally refined mesh vertices from the original 3D coordinates. A narrow, smooth `m1e4_fiber` value colors the fresh cut and adds a small local geometry ridge.
- A separate editable **3D `Curve to Mesh` source** shows real tubular filament geometry. A live SDF mask samples the *same knife* at 60 resampled curve points, deletes the clipped portion and converts surviving curves to 3D tubes. This is a visualization/debug layer: the `beauty` mode hides it, while `diagnostic` shows it.
- Source polyline positions, counts, widths and warm colors are **artist decisions**. Curves are deliberately not called actual vascular anatomy or true strawberry tissue.

## Independent saved-scene validation

Each `.blend` was reopened in Blender 5.2.4. `validate_m1e4.py` checks actual evaluated geometry, 3D rest-space and filament attributes, source curve identity, a separately evaluated tube mesh and zero non-manifold edges.

| Knife frame | M1e2 original body verts | M1e4 local snapshot verts | Components | Non-manifold edges | Live 3D tube verts |
|---:|---:|---:|---:|---:|---:|
| 1 (closed void) | 44,474 | **44,474** | 2 | **0** | 20,520 |
| 15 (opened) | 31,482 | **83,806** | 1 | **0** | 15,628 |
| 30 (deep cut) | 20,894 | **78,650** | 1 | **0** | 7,798 |

A standalone M1e3 whole-mesh **Exact** version had **503,682 vertices** at frame 15. The local M1e4 version has ~**6.0× fewer** at the same pose. This is a geometry-memory win, **not** a proven end-to-end speedup. Local selected-edge split time on this CPU was ~0.12–0.16 s, while total per-pose source/field/scene build was ~2.1–2.4 s. None of these is a measured live knife update latency.

The original M1e3 live surface and the local snapshot use different triangulation/subdivision. A true nearest-*surface* sample over 2,500 skin-only vertices per frame gave max distances ~0.0024, 0.0023 and 0.0028 Blender units (median 0). These differences are **not zero**; we do not claim pixel-identity or exact original skin geometry.

The 3D tube vertex count decreases with knife travel (20,520 → 15,628 → 7,798), demonstrating that the visible tubes actually respond to the same 3D SDF cutter. This does not establish exact cap intersections: clipping happens on curve points.

## Controlled visual comparison

At frame 15, M1e3 Exact, M1e4 Beauty and M1e4 Diagnostic were rendered at the **same camera**, 720×720 and **16 CPU Cycles samples**. The `m1e4-ab-comparison.jpg` is only a montage of unchanged render pixels; a separate three-pose sequence uses 640 px for frames 1 and 30 and 720 px for frame 15.

- Beauty keeps subtle filament-dependent 3D cut color/relief without visible tubes in the open void. The smooth round cavity and simplistic skin continue to limit photorealism.
- Diagnostic reveals the actual spatial network and its weaknesses: geometric spokes and curves in the cavity can look decorative rather than natural. This was intentionally **not** baked into the beauty mode.
- We do not claim the model now matches the paid Frucht strawberry. No scientific measurement was added, and no author asset/code was imported.

## Known limits / future

1. Selective subdivision currently occurs in **BMesh per-pose snapshots**, not in a dynamic GN modifier; moving the knife requires running the builder again. Original GN body remains live, but hidden for the exact snapshot.
2. Splines clipped by point samples may have imperfect endpoints, and tubes are not perfectly clipped to the fruit's actual tissue volume; a proper per-curve SDF intersection/remesh remains an experiment.
3. The source volume and strands are true 3D procedures, but the dense mesh is generated only around the currently open cut. There is no whole-fruit cellular solid simulation.
4. Existing cut/cavity color, SSS, material roughness and seed contacts still look stylized. The previous grainy/porous M1e3 effect remains, and the cavity is smooth and nearly spherical.
5. Manifold edge tests are topological; they do not prove the absence of self-intersections, physical realism or botanical correspondence.
6. Future live LOD needs a tested adaptive Geometry Nodes topology algorithm or a bounded rebuild/bake workflow. Splitting source volume from knife alone is not a precomputed cache.

## Provenance and outputs

Independent Python source, technical report and verified asset SHA-256 manifest belong in a new GitHub PR stacked on #17; binary .blend and genuine Cycles PNG remain in a versioned, owner-private Google Drive folder. The previous M1e3 scene is retained unchanged. Reproduce from the included original M1e3 Fast .blend and Python scripts, without conversational history.

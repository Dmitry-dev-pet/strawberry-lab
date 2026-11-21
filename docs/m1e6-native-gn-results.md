# M1e6 engineering report — native GN localized cut topology and 3D fiber field

Date: 2026-11-21. Evaluated locally under Blender **5.2.4 LTS**, x86-64 Linux, CPU Cycles. This milestone is **not equivalent to the paid Frucht Strawberry**, and does not recreate Frucht's licensed node graphs.

## Why this path

M1e5 creates true live, locally subdivided mesh, but a Python/BMesh addon must be explicitly activated and rebuilds synchronously (reported ~0.37–0.68 seconds for the BMesh callback alone). In Blender 5.2 `Subdivide Mesh` exposes no per-face `Selection` input [official manual](https://docs.blender.org/manual/en/5.2/modeling/geometry_nodes/mesh/operations/subdivide_mesh.html). Blender **5.2 Mesh Bevel**, however, has a selected-edge input ([manual](https://docs.blender.org/manual/id/5.2/modeling/geometry_nodes/mesh/operations/mesh_bevel.html)). We built a native GN alternative to test **watertight, localized extra topology without a Python callback**.

## Implemented architecture (user-authored)

The existing M1e2 source SDF and dynamic knife stay unchanged. After material classification, the GN graph selects freshly exposed cut-face edges *away from* the outer skin and hollow cavity rims and uses a constrained three-segment `Mesh Bevel` width 0.008 BU, followed by original rest-space `Set Position` cut and cavity relief. This is **not** true selected face subdivision or a complete cell population. Global M1e3 `Subdivide Mesh` is absent from the final group.

A separate GN signal samples our existing 135 3D filaments by converting the **evaluated legacy CURVE mesh** to a point cloud (`Mesh to Points`); its `Geometry Proximity` field measures distance from each `fruit_rest` sample position to that network. The field is stored as `m1e4_fiber`, masked to cut faces, and its strength/reach can be tuned. A preliminary version incorrectly used `Curve to Points` on the evaluated, beveled legacy `CURVE` object: it returned zero points and the fiber field was a constant 0.53 across the cut. That error was discovered via attribute-value and source-transform tests, corrected, and is *not* present in the distributed scene.

Six user inputs are exposed on the existing GN modifier (no addon required), with values explicitly set using **Blender 5.2 `NodesModifier.properties.inputs.<socket>.value`** rather than removed `modifier[identifier]` ID-property access. Geometry Nodes reads fields and reconstructs on cutter moves; its source field remains unbaked.

## Verified geometry and field continuity

| Knife frame | M1e5 Fast original body verts | M1e6 native GN verts | Components | Open/non-manifold edges | Original skin samples maximum distance |
|---:|---:|---:|---:|---:|---:|
| 1, closed cavity | 177,884 | **44,474** | 2 (outer+void) | 0 | 0 (2500 samples) |
| 15, cavity opened | 125,922 | **56,739** | 1 | 0 | 0 (2500 samples) |
| 21, intermediate | 94,338 | **53,224** | 1 | 0 | 0 (2500 samples) |
| 30, deep cut | 83,570 | **49,404** | 1 | 0 | 0 (2500 samples) |

The standard poses, manual knife translation `+0.3 Y` at frame 21 (44,092 resulting vertices), manually rotated knife `+18°` (54,170 vertices) and full restoration all produced one connected, closed mesh, except for the intentionally closed cavity at frame 1. The original skin was compared against the **closest skin surface** rather than unreliable nearest-vertex indices. The 3D source filament network test changed the number of cut vertices with `m1e4_fiber > 0.11` from 1,432 to 1,655 when moved by `+0.5 X`: this is a true rest-space 3D field, not a constant shader.

**User controls tested**: `Cut edge segments` 3→1 changes geometry from 56,739→36,697 vertices without breaking topology, then restores; `Fiber intensity` 0.53→0 makes all field values zero and restores on return. New GN inputs are real modifier inputs, not decorative custom properties.

## Important failure case and non-default experiment

**Cavity geometry edit at frame 21**: translating source cavity `+0.18 X` created **7 connected components**, one large surface plus six 8-vertex floating closed SDF artifacts (53,947 total verts), even though **zero non-manifold edges**. This failure is recorded in the validator and prevents claiming arbitrary cavity edits work. Restoring the cavity returns to one component.

We prototyped a second Geometry Nodes modifier, using `Mesh Island` + `Accumulate Field` + `Delete Geometry` to delete islands smaller than 16 vertices. It removed all six tiny artifacts: changed cavity produced 53,899 vertices and **one** component, but original cavity movement increased update cost to ~1.9–2.2 s, and changing the GN Fiber intensity sometimes stalled Blender. An earlier inline version could also hang. **Both experimental island cleanup versions are excluded from the production .blend** until their performance and stability are established. Cleanup itself might remove legitimately tiny intended fragments. Avoid overclaiming robustness.

## Fair performance measurement

Full CPU evaluation includes `scene.frame_set()`, depsgraph update and evaluated `to_mesh`, not the render or interactive UI:

- Native M1e6: **1.48–1.59 seconds** (6 samples, standard poses).
- M1e5 GN Fast baseline: **1.38–1.63 seconds** under the same measurement method.

M1e6 uses fewer evaluated vertices but has **not** shown a meaningful end-to-end speedup; unbaked source SDF/volume recomputation likely dominates. These are single-machine samples, not per-frame viewport FPS. Native GN removes the **requirement to install and activate Python**, not the cost of evaluating the SDF.

## Controlled visual result

Real CPU Cycles frame 15 images use the same camera, lights, **720×720** pixels and **16 samples**:

- M1e5 Exact: sharper small cellular relief from selectively refined BMesh snapshots.
- M1e6 native GN Beauty: pink flesh and a lighter-weight GN-only edge-bevel approximation; **less high-frequency relief** than M1e5 Exact, not a visual upgrade.
- M1e6 GN Fiber diagnostic: uses live `m1e4_fiber` attribute on its independently authored cutter material and shows thinner, spatially localized pale streaks, not a pervasive white color.

M1e6 frame 21 also rendered successfully with no callbacks. The final controlled scene's frame 15 image is **pixel-identical** to the pre-controls M1e6 Beauty test, showing that exposed controls retained their intended default numeric values. Old and new renders have intentionally not been retouched in the comparisons.

## Next engineering gates

1. Profile **SourceVolume and SDF** by stage and determine whether bake/cache invalidation can reduce the ~1.5 s complete update. A source-level benchmark must be comparable to M1e5.
2. Develop genuinely local *face* subdivision (not edge bevel only) natively if possible, without introducing seam cracks, and compare image texture to the M1e5 BMesh Exact baseline.
3. Solve micro-islands under cavity changes with a robust algorithm not involving hangs, preserving intentionally detached small tissue fragments when requested.
4. Improve actual visual fidelity: heterogeneous tissue fields, complex void geometry, wet material/SSS, fibers coherently clipped within tissue, seed pits and calyx. No invented biological calibration.
5. Revisit multi-frame Cycles stability (a past sequential render within one process stalled); keep single-frame processes for reliable proof.

**Provenance:** all Blender scripts and GN structures are independently written for Strawberry Lab. No proprietary Frucht strawberry `.blend`, no vendor-node graph, and no GPL source code are distributed here. Full binary scenes/PNGs should live only in the owner-private Drive Strawberry Lab folder with SHA256; code/docs/manifest in public GitHub as a reviewable PR stacked atop M1e5.

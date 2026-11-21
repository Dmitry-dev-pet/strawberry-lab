# Stage B: Exact relief compatibility, not an implemented transfer

Stage A restores independent rendering modes. This assessment does **not** claim M1e5 micro-relief is integrated. No cavity, new cells or new vessel network is generated. No live Blender GUI state was changed.

## Actual sources inspected

- PR19 `294f683ee03d8ab3b5139790a28dd3d39ed53174`: `m1e5_live_exact.py`, `build_m1e5.py`, inherited `build_m1e4.py`. Authenticated saved `strawberry-m1e5-live-exact.blend`, SHA256 `2082a81c0d2607faabdefefe0403deed997c703f2c3a1dfe96ea0338e6c4efb2`, [private original](https://drive.google.com/file/d/1QXFQHVT3DM0PNpnLHOiHaWxcVXc_9YBX/view). Reopened with `use_scripts=False`, no callbacks registered. Its real frame15 PNG was downloaded from the owner-private M1e6 comparison folder and visually inspected; this is a reference image, not a controlled comparison to PR30.
- PR20 `4a97e3848f2d455ad94ac01f1912c3c98081707e`: native GN builder and result/reproduction documentation. Authenticated `m1e6-nativeGN-production.blend`, SHA256 `119dd13b7e7fa7ed130fba844e02c698095b7d601fea6227bb00d7fa7149d33f`, [private original](https://drive.google.com/file/d/19IKond0VGn7-BzeXYASpjuw3BwtbHEnH/view), reopened without autorun. Native selected-edge bevel is a different approximation, documented as worse visual detail than Exact, with known cavity-motion islands.
- PR30 `381a8c8d34823fc93a7b3ceacdfb077f8c5f1343`: verified corrected owned scene SHA256 `0b8af93c399d0077f51f864f7b9f55673b822a1755e2badcc626f5bfc6256bca`.

`probe_saved_sources.py` is a read-only local probe. `saved-source-inventory.json` records actual object, attribute and GN group inventories. It contains only our owned source facts, no third-party Blender graph/media.

## Why a direct transplant fails

1. M1e5 `ready()` checks named SDF body/helper/Exact cache, its scene flag and its own 135-spline `M1e4 | persistent 3D curved fibers (source)`. PR30 has one analytic-hull Boolean mesh and the separately preserved 28+539 diagnostic paths; renaming these to the old 135 network would be false provenance.
2. `_make_mesh()` evaluates the old SDF helper, selects old cut/cavity material indices and requires interpolated `fruit_rest`; `m1e4_fiber` is a derived proximity field created and filled by the routine when absent. The actual saved PR30 mesh has neither attribute. Old helper/cavity topology does not exist in it. The cavity material is looked up later in `_make_mesh()`, not in `ready()`.
3. The Exact snapshot has 83,806 stored vertices and a downstream 70-node localized CutSurface graph. PR30 has a 30,242-vertex raw canonical hull and no Geometry Nodes groups. Copying the old snapshot produces a different fruit, not an adapter.
4. Physical conventions differ: old source scene scale_length=1; current PR30 scale_length≈0.0222222 maps its 2.16 model-unit height to nominal 48mm. Old numerical radii/noise/relief values cannot be copied unchanged as millimetres.
5. M1e5's micro-relief includes inherited M1e3 geometry displacement and an additional 3D proximity attribute/material. Copying only its shader or the RGB image cannot reproduce this geometry. M1e6's bevel is not a drop-in replacement for local face subdivision, and its old cavity-proximity inputs also remain absent.

## Smallest subsequent adapter contract

Input: canonical PR30 rest-space hull and its evaluated Boolean result, the **same** knife matrix, cap material ID, explicit mm-per-native-unit, and preserved optional source curves. No additional fruit source, no transfer of old 135 curves and no new vascular model.

1. Record rest coordinates on the canonical source, then obtain the current evaluated cut mesh. Select true cap faces by material and verified knife plane, not world Z or a painted mask.
2. Subdivide only the cap interior with zero displacement on its shared outer seam. Preserve source outside coordinates, per-face materials and every source curve/radius/endpoint. Whole mode bypasses the derived Exact cache. Only one body result may be visible in any mode.
3. Provide a standalone cap-relief field in physical units with explicit artist parameters. Reuse independently owned local-refinement principles; remove dependencies on missing cavity/old SDF sockets. A proximity signal from the preserved 28+539 source requires an explicit new rest-space sampling adapter and must not imply 539↔264 seed mapping.
4. Bind an opt-in Exact callback to the existing knife matrix and field configuration. Use busy/reentry guard, source fingerprint, cached-pose key, idle no-op and a live Boolean fallback on error. Surface changes must not alter the independent diagnostic visibility state.
5. Gate on saved-scene reopen, whole + four existing knife poses, non-manifold edges/positive volume, unchanged skin seam, unchanged 28+539 source digests and all four layer modes. Same camera/light/samples Fast-vs-Exact macro renders must show a geometry-based improvement; report evaluation cost and boundaries, not viewport FPS.

This is a bounded implementation contract for a later independent step. No Exact adapter is enabled in the four-mode scene, and the old model/cavity is deliberately not appended to it.

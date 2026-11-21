# M1e5 — verified live Exact CutSurface bridge

**2026-11-21. Blender 5.2.4 LTS.** Success criterion: exact locally refined cut geometry must update when a knife is moved manually or by timeline animation, without manually rerunning a geometry-build script each time, while keeping the previous live Geometry Nodes mechanism as a safe fallback.

## Implementation

- From M1e4's own `.blend`, add **`M1e5 | live SDF source for localized mesh`**, a hidden Geometry Nodes helper that evaluates the original cutter at the current pose **before whole-mesh subdivision**. Retain source-volume and SDF cavity semantics unchanged.
- Rename the previous detailed body to **`M1e5 | EXACT live-local CutSurface`**, and provide its detailed Geometry Nodes material and displacement modifier with a newly rebuilt local mesh rather than a frozen per-pose one.
- `m1e5_live_exact.py` installs `frame_change_post`, `depsgraph_update_post` and `load_post` callbacks. Each new knife matrix triggers source SDF evaluation → selected BMesh edge subdivision of newly exposed cut and nearby cavity → 3D rest-space filament distance field → atomic mesh swap → existing downstream GN geometry displacement/shader. Reentrant-safe and no regeneration when the knife did not move.
- Explicit local Exact activation via embedded Blender Text **Run Script** or installed addon. `Fast` keeps original M1e3 live GN body without requiring addon. Blender N-panel offers Fast / Exact / Force Refresh.
- No invisible script execution on file open; the scene defaults to native Fast when not using the addon. A failed Exact refresh falls back to Fast rather than displaying a stale snapshot.

## Tests in a new Blender process

| Trigger | Live Exact body vertices | Connected surfaces | Non-manifold edges | Visible achene mesh vertices | Refresh CPU seconds |
|---|---:|---:|---:|---:|---:|
| Frame 1: sealed cavity | 44,474 | 2 | 0 | 90,552 | ~0.37 |
| Frame 15: cavity opened | 83,806 | 1 | 0 | 56,448 | ~0.55 |
| Frame 30: deep cut | 78,650 | 1 | 0 | 38,304 | ~0.51 |
| Frame 21 (non-keyframed) | 82,382 | 1 | 0 | 42,840 | ~0.56 |
| Frame 21 + manual Y 0.3 | **75,448** | 1 | 0 | **33,936** | ~0.54 |
| Frame 21 restored | 82,382 | 1 | 0 | 42,840 | ~0.52 |

Additional checks: repeated depsgraph evaluation without any knife motion causes **no rebuild**; an 18° manually rotated knife recalculates into an 81,564-vertex mesh; running the embedded Text twice does not duplicate handlers; the UI operators work; installed addon survives file reload and reenables the tagged Exact scene; without addon original GN Fast remains live.

### Controlled visual evidence

M1e4 Beauty frame 15 vs new M1e5 Exact frame 15, using **identical Cycles 720 × 720, 16 CPU samples, camera, lights and scene**: RGB pixel difference bounding box `None`, per-channel average absolute difference **0.0**. This establishes same visual output, not Frucht parity.

Authentic separate-session Cycles images were also rendered for frames 21 and 30 (frame 21 at 720 × 720/16 samples; frame 30 at 560 × 560/10 samples). The three-frame contact sheet labels these distinct resolution/sampling settings; it is not a per-pixel A/B.

### Limits and investigation items

- The native GN SDF stays live, but precise **local mesh refinement remains Python/BMesh** and is synchronous (~0.5 sec on this CPU): no 60fps or GN-only claim. The previous M1e4 required external manual script execution for each new pose; M1e5 removes that user requirement after addon activation.
- Automatic invalidation currently tracks the **knife matrix**. Changing source mesh, cavity or 3D fiber paths without moving the knife requires **Force Refresh**.
- Full mesh manifoldness has been tested; not all possible self-intersections or cut shapes have been exhaustively proven.
- Curves are still artist-designed and diagnostic tubes are only point-clipped; the original round cavity and film-like pulp still fall short visually of Frucht.
- A multi-frame rendering attempt in **one** Blender/Cycles process stalled on a subsequent frame; per-frame renders in fresh processes worked. Requires separate investigation before automated high-resolution animation is promised.
- No Frucht GPL code or vendor meshes imported.

## Next: entirely native GN adaptive mesh or cooperative interpolation

Investigate an actual **selected-edge subdivision** Geometry Nodes feature or a sparse dual-mesh/refit method, not just the current global `Subdivide Mesh` (Blender 5.2 `Subdivide Mesh` has only `Mesh` and `Level` inputs and no selection). If GN-only selective topology remains unavailable, measure cost of a debounced handler, active viewport responsiveness, collision with repeated frame renders and source-data invalidation before further material polish.

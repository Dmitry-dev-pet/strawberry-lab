# Engineering audit — Volume First v1, thin coherent 3D fibers

Date: 2026-11-21. Blender: 5.2.4 LTS CPU headless.

## Hypothesis

The v0 150³ voxel field blurred pale internal fibers. We tested a **continuous 3D filament source** with explicit tube-like curve geometry rather than merely raising sampling resolution or decorating each cut in 2D. The same 494 authored polylines supply the 0°, 32°, 82° cuts.

## What changed

- Retain the original 150³ coarse source tissue color, pith and macro relief and original 146 3D curves.
- Add 348 additional narrow spatial polylines to a single global 494-curve, 45,928-point source. The curve reference is also embedded as a hidden actual Blender 3D `CURVE` object.
- For every exposed cut vertex, use the **shortest 3D distance to a finite source segment** (not nearest 2D texture pixel and not 3D 150³ EDT interpolation). An analytic smooth field encodes an interior core and weaker halo. The material uses that attribute for fiber hue and roughness.
- The geometric cut vertex is displaced in the physical cut-normal direction, with an additional halo recession. The displacement is strictly zero at all skin-cut shared vertices. For fair comparison, all old objects remain unchanged and are included within the saved `.blend`.
- The final Beauty variant reduces the stronger diagnostic color to 31% mixing and the physical displacement to 70%. Both diagnostic and Beauty variants are preserved.

## Geometry and independent QA

| Angle | 3D signal vertices (>0.25) | Actual displaced vertices (>0.002 BU) | Physical height max | Watertight | Skin change |
|---|---:|---:|---:|---|---:|
| 0° | 7,370 | 5,418 | 0.007069 BU | PASS, 1 component | 0 |
| 32° | 6,846 | 4,723 | 0.007069 BU | PASS, 1 component | 0 |
| 82° | 6,991 | 4,940 | 0.007068 BU | PASS, 1 component | 0 |

Each enhanced cut is 78,626 vertices, 78,960 faces, zero non-manifold edges, zero degenerate faces. Vertex-wise comparison to the source v0 meshes confirms X and Z unchanged and that physical Y displacement equals the archived per-vertex metric. Shared skin/cut seams have exactly zero displacement.

A fresh rebuild after source-code clean-up produced **bitwise matching saved vertex coordinates, physical offsets and fiber signal attributes** for all 3 cuts. The regenerated scripts do not depend on the previous session output beyond explicitly included input-v0 files.

## Controlled visual examination

The v0 vs v1 full-frame renders at angles 0° and 82° share exactly the same Blender lighting, camera, 840×960 resolution and Cycles 20 samples. Static macro v0/v1 renders share an additional close camera at 520×520, 8 samples. A separate **uniform clay** comparison at 520×520, 10 samples removes fiber color and bump: thin lines still affect shading, verifying physical geometry. The denoiser and light transport remain unchanged per matched A/B.

**Judgment:** clear line continuity and nonzero physical relief were demonstrated for two substantially different azimuths, unlike the v0 diffuse 150³ signal. **Photorealism is not achieved.** The relatively long pale paths look somewhat like taut wires radiating through the fruit, the central pith is too smooth, the cut lacks fine heterogeneous tissue, and seeds/calyx lack Frucht-level geometry. Subtle glints alone cannot fix the wrong morphology.

## Failed / limited items

- An initial 840px/20-sample macro Cycles job stalled beyond the execution budget, like an earlier Strawberry Lab macro case. Lowered to 520px/8-sample per-frame macro renders, which completed. We do **not** infer macro animation stability.
- The 150³ substrate is still coarse in the broader cortex; continuous line geometry compensates for select filaments, not for missing vascular branching or packed cells.
- The static cut meshes are analytic half-fruits, **not real arbitrary 3D Boolean cuts**. Geometry is closed but the test cannot validate a live cutter or all possible topology.
- Source splines are synthetic artist geometry, **not biological measurements**; their ability to produce lines at multiple angles is not proof of real strawberry vascular anatomy.
- Editing source splines requires rerunning builder; no live stream from curves to cut-face geometry is implemented.

## Decision

Keep v1 as **successful engineering probe / visually insufficient prototype**. Do not yet merge it with M1e6 and do not implement full live knife. The next discriminating step should evaluate *short branching, spatially irregular vascular bundles + continuous non-fiber cellular tissue* at macro scale, rather than merely adding more bright radial lines. Publish only independent code, metrics and checksums in GitHub; leave binary `.blend`, NPZ and user-private reference out of the public repository.

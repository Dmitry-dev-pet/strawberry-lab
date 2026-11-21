# Morphology experiment — V3 independent carrier profile and Bézier network

## Tested hypothesis

After audit of the owner-supplied Frucht Free 0.4.3 sources, the geometric shortcomings of Volume First v2 are not explained by the number of seed endpoints: V2 has 28 central carriers and all 539 attached branches, but its carriers are almost constant-radius and its radial branch interpolation yields visibly spoke-like geometry.

This experiment changes only the **3D internal path geometry**, preserving precisely the same 539 remapped seed markers, branch end points, camera, color materials and lights. Its algorithm is independently written and uses principles common in geometric modeling: a user-chosen 11-point piecewise monotone cubic radial profile, a mild off-center axis, separate carrier tracks, and cubic Bézier branches with two explicit control handles. It does **not** copy the Frucht implementation or claim to reconstruct the paid `erdbeere.blend`.

## Actual test setup

- Blender 5.2.4 LTS, 3 original V2 preview scenes, all saved in one editable `.blend`.
- 28 carriers with 3 bend configurations (`sag=0.25`, `1.00`, `1.80`) while 539 branch targets are immutable.
- Fixed `sag=1.0` with 14, 28 and 40 carriers, same source endpoints.
- Real CPU Cycles 680×763 px, 11 samples, identical scene studio lighting and camera. All render frames are the actual stored curves, not generated imagery.
- Three views supported by scene: only; transparent hull; an *unchanged v1 cut* overlay (a high-cost render attempt of the cut did not complete).

## Numeric results

| Variant | Central trunks | Branches | Median path length/chord | Endpoint error |
|---|---:|---:|---:|---:|
| V2 spokes | 28 | 539 | 1.0197 | 0 |
| V3 sag 0.25 | 28 | 539 | 1.0332 | 0 |
| V3 sag 1.00 | 28 | 539 | 1.1095 | 0 |
| V3 sag 1.80 | 28 | 539 | 1.2233 | 0 |
| V3 strands 14, sag 1 | 14 | 539 | 1.1100 | 0 |
| V3 strands 40, sag 1 | 40 | 539 | 1.1095 | 0 |

The independent V3 radial profile spans **0.0193–0.3340 model units** in sampled carrier height; these are *our chosen values*, not verbatim author data. Each source file contains a complete 3D polyline coordinate list and per-point radii, not a 2D drawn texture.

## Visual findings

The source/target topology remains stable while increased sag visibly increases the arching of the curves; the central structure is now radially wider in the middle and narrower near ends. The fixed-camera V2/V3 comparison validates that changing carrier profile and cubic handles materially changes the geometry. However, **V3 does not reproduce the author Frucht look**. At sag ~1.8 many branches resemble drooping threads or a jellyfish canopy; at sag 0.25 they remain too uniformly directed. In Frucht's ~00:15 video the visual focus is much closer and some branches appear curled or hook-like, emerging from a different-looking central structure. We cannot infer an exact parameter match from the promotional still. Comparison including the author is restricted and clearly labeled *unequal camera/zoom and possible animation state*.

## Implications

The original user's observation was right: **correct endpoints do not determine correct internal morphology**. Simply increasing curve count or sag cannot solve the visual gap. An improved hypothesis would model varying terminal tangents and local hook geometry at seed bases, with density correlated to seed placement and central carrier cross-section; evaluate the core and branch field before cut/shaders. Defer tissue atlas and adaptive knife until morphology improves. Keep V3 as an experimental research branch, do not merge as production fruit geometry.

## Verification

Saved Blender scene has 5 V3 variants, retaining the V2 curve objects. Exact per-spline geometry matches each `.npz`. All variants preserve the complete set of 539 achene positions and 539 branch terminal positions **bit-for-bit at float32 precision**. A fresh generation with the same seed produced identical arrays. QA JSON, fixed-camera Cycles and log files retained. The unchanged v1 cut and ghost context are not a new cut-surface implementation.

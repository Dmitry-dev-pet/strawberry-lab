# Strawberry Lab v7 — conservative Frucht-inspired cut cells (22 Nov 2026)

**Status: VERIFIED ENGINEERING PROOF / VISUAL FRUCHT FIDELITY NOT ACCEPTED.**
This is a small independent procedural experiment, deliberately **rebased on v4 rather than v5/v6**.

## Why change course

The free Kiwi audit and public explanation of commercial Frucht describe *local fine cells on the visible cut surface*, with reduced relief over pale fiber strands, plus separate multi-frequency Voronoi wet highlights. They do NOT establish an array of individually manifold histological cell solids throughout strawberry flesh. V5 over-embossed and looked like caviar; V6 was less harsh but still unrelated to actual strand regions. V7 tests the author-described principle using **our own code/data**.

## Implementation

- Native **Mesh→SDF Grid, SDF difference, Grid→Mesh** stays exactly the old editable body cutter. Source 264 achene meshes, physical pits, calyx and both SDF cutter geometries are unchanged.
- One original-coordinate packed **192³ RGB field** (16×12 2D atlas; original v4 image preserved). v7 samples **the exact same atlas's red vascular channel in Geometry Nodes** using two `GeometryNodeImageTexture` nodes and XYZ trilinear interpolation, not an independently painted duplicate fiber mask.
- One `Subdivide Mesh` level followed by **small 3D warped Voronoi physical cell relief** only on the cut face. Original-skin distance and cutter proximity stop cells from damaging rind/edge. Vessel intensity from the same 3D field suppresses displacement over pale fibers. Moisture remains independently in the shader, with three Voronoi layers and reduced glossy coat.
- `V7_CELL_STRENGTH` provides instant in-Blender 0/1 geometric A/B; native modifiers work with Python autoexecution disabled.
- All cell, vascular and shader magnitudes are **ARTIST**; this is not a scientific 3D cellular packing model.

## Independent verification in Blender 5.2.2 (no autoexec)

| Evaluated state | Body vertices | Nonmanifold edges | Positive volume | Seeds remaining | Seed vertices intruding |
| --- | ---: | ---: | :---: | ---: | ---: |
| Whole | 157,250 | 0 | PASS | 264 | n/a |
| Plane | 194,354 | 0 | PASS | 93 | 0 |
| Plane moved/rotated | 154,762 | 0 | PASS | 66 | 0 |
| Bite | 344,634 | 0 | PASS | 227 | 0 |
| Bite moved/enlarged | 354,698 | 0 | PASS | 215 | 0 |

- Max measured additional physical displacement: **0.01854 mm**. Plane **56,199** and bite **41,514** vertices change by more than 0.005 mm when enabling cell relief relative to strength=0.
- **Vascular flattening A/B (strong strand points, density > 0.23):** mean absolute relief is **0.3269× planar** / **0.3219× bite** the value with flattening disabled, a **67–68% reduction**. On points outside strands (intensity < 0.01), ratio is **1.0×**. This proves that the same 3D data drives actual cell flattening.
- All four moved-cut tests retain closed positive-volume bodies and conservative seed collision clearance. Not a general proof for all possible object transforms, nor a benchmark against mesh Boolean/exact.

## Real Cycles images and visual conclusion

Three genuine Blender 860×860 Cycles 36-sample frames `sdf-v7-plane.png`, `sdf-v7-bite.png`, and `sdf-v7-macro.png` compared directly to equivalent v4 frames, same studio/camera, with original v4 left and v7 right in three PNGs `comparison-v4-v7-*.png`. No ImageGen used for Blender verification.

**Qualitative:** v7 is slightly more finely textured and has preserved visible pale vessels without v5's caviar. Still looks too uniformly smooth/fine and has overbright/stylized center in the bite. The improvement is smaller than the engineering change; **Frucht visual acceptance remains FAIL**. We did **not** obtain accessible original author video frames from the currently mounted Drive placeholders during this run, so do not claim a new calibrated frame-by-frame Frucht comparison. Existing author reference observations in `docs/visual-reference-frucht.md` supplied prior constraints.

## Reproduce

Using Blender 5.2+, start from authenticated source v4 `build/sdf-vertical-slice/strawberry-sdf-vertical-slice-v4.blend` and its already packed atlas:

```bash
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/build_v7.py
$B -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/validate_v7.py
$B -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/render_v7.py
$B -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/make_v7_comparison.py
```

Output under `build/sdf-vertical-slice/`; optional `STRAWBERRY_SDF_OUT` for alternate folder. V4, V5 and V6 are not modified or deleted.

## Decision

**Remain a draft experiment, do not merge to main.** Further work should compare equivalent frames with accessible author video, then address actual visible strand topology, ragged cut-edge and physically credible localized moisture. No more general-purpose new cutters or isolated 3D cell objects without visual evidence. The calyx still does not clip with a sufficiently extreme cutter, and source 3D fiber paths remain artist-designed.

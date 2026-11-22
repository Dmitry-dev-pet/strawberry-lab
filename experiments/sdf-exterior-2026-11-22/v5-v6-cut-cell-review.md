# Strawberry Lab — v5/v6 native cut-cell lookdev (22 Nov 2026)

**Engineering status: PASS for tested configurations. Visual Frucht-level acceptance: FAIL.**

## Objective

Make cellular detail **real geometry** on the freely movable SDF cut surfaces, not just bump-map shading, while preserving the original sculpted fruit, 264 real achene meshes, original 192³ tissue atlas, and SDF cutter architecture.

This is an independent artistic study. Blender 5.2.2 LTS, scripts-disabled reopen. All numerical cell size/shape/wetness parameters are ARTIST, **not measured strawberry histology**. It does not create isolated watertight biological cell solids.

## Versions and visual findings

| Variant | What changed | Actual geometric movement | Observed from genuine 860×860 Cycles |
| --- | --- | --- | --- |
| v4 baseline | 192³ rest-space strand texture and shader cell normals | Local cap noise, no true Voronoi cell sculpt | Relatively smooth flesh, tenuous white streaks and central bright patch on bite |
| v5 high-contrast diagnostic | One native GN mesh subdivision followed by 3D warped Voronoi *physical displacement* on cut, smoothly tapered near original skin | Max **0.131 mm**; >57k plane and >42k bite vertices moved by >0.03mm vs same topology with strength zero | **FAIL**: densely packed caviar/bubbly cut face overwhelms vascular details |
| v6 restrained | Same graph with physically real displacement strength 0.18, lower shader bump and restrained coat | Max **0.02374 mm**, >53k plane and >39k bite vertices moved by >0.008mm vs zero-strength | Better balance than v5, but visually flat/synthetic; white center in bite and faint vessel pattern remain |

All three variants have **genuine Blender Cycles** output at the same primary studio cameras and 860×860 pixels, 36 samples. Macro shots have the same separate close-up framing. Triptychs order: **v4 LEFT / v5 CENTER / v6 RIGHT**. Images are from Blender rendering only, no generative-image substitution or postprocessed artwork.

## Geometry / QA (v6 scene, evaluated, with Blender autoexec disabled)

| State | Vertices in body | Nonmanifold edges | Signed volume (mm³ approx.) | Visible achene solids | Remaining achene verts intruding into cutter |
| --- | ---: | ---: | ---: | ---: | ---: |
| Whole | 157,250 | 0 | 21,506.83 | Original 264 | Not cut |
| Plane base | 194,354 | 0 | 6,779.59 | 93 | 0 |
| Plane moved+rotated | 154,762 | 0 | 4,268.55 | 66 | 0 |
| Bite base | 344,634 | 0 | 18,926.18 | 227 | 0 |
| Bite moved+scaled | 354,698 | 0 | 16,879.13 | 215 | 0 |

- **Physical relief proof**: turn `V5_CELL_RELIEF_STRENGTH` to 0 inside the identical GN group and compare post-subdivision vertex positions without changing cutters. With v6's 0.18 strength, **53,614 plane** and **39,354 bite** vertices change by more than 0.008 mm; max displacement ≈0.0237 mm. This measures actual mesh positions, not shader normals.
- Full mesh is subdivided once (roughly 4× faces vs v4); cell displacement is damped by a native cutter proximity mask and source-skin proximity to keep cut boundaries intact.
- Both cut bodies still sample the **same 192³ packed spatial atlas using `fruit_rest`**, with no separate 2D texture fixed to the camera/knife.
- All evaluated geometries remain watertight in four tested poses with positive signed volume; this is **not** a proof for every arbitrary cutter orientation, no self-intersection sweep was attempted.
- Whole-anchored crown/calyx does **not** respond to cutter; entire achene solids disappear conservatively near cut rather than being exactly clipped.
- Visual quality and anatomical correctness must be judged independently.

## Reproduction (requires v4 proof file available locally)

```bash
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/build_v5.py
$B -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/validate_v5.py
$B -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/finalize_v6.py
$B -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/validate_v6.py
$B -b build/sdf-vertical-slice/strawberry-sdf-vertical-slice-v6.blend --disable-autoexec --python experiments/sdf-exterior-2026-11-22/render_v6.py
$B -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/make_v6_triptych.py
```

All source scripts use `STRAWBERRY_SDF_OUT` to point at a nondefault output folder. Source v4 is preserved and unmodified; v5 and v6 are distinct saved scenes. GN updates operate with script autoexecution disabled after opening the .blend.

## Decision

Do **not** merge this lookdev on the basis of numeric QA alone. The next meaningful visual goal is a **physically convincing localized cut face**, using visible but subtle tears, correctly organized strands and a demonstrably appropriate moist surface at comparable camera/light to the owner's Frucht reference. Start with reference-based A/B and region-specific masks, not another round of arbitrary microdetail knobs or new SDF cutter implementations.

Source code lives in GitHub draft PR #43. Blender, PNG and atlas artifacts should be kept privately on owner Drive with hashes; they are not inserted as binaries into GitHub main.

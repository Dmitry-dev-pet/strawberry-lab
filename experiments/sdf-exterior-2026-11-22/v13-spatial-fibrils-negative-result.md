# v13 — independent coherent 3D fibril field on SDF cut (22 Nov 2026)

**Result: ENGINEERING PASS / VISUAL FAIL (REGRESSION).** Research only; not accepted for product use, not a merge candidate. The owner's original Frucht footage remains private and was not copied into this repository.

## New hypothesis and exact delta

Starting from *unchanged* editable **v12** `strawberry-sdf-vertical-slice-v12-continuous-wet.blend` (SHA-256 `300a2bfeaa86831220657b74fe8b00d4d7ec0b42f4ffefca863d6410cbb405b7`), replace ONLY the red/vascular channel of the common packed 192³ rest-space tissue atlas. The original source seed-linked 3D curves remain, supplemented with 38 smoothly curving, *periodic radial sheets* and one fainter family. Unmeasured parameters are **ARTIST**. Preserve atlas G/B (mottling and pith) and preserve the v12 SDF cutter, 264 achene sources, material scaffold and exterior.

The new R-channel is bound to both Cycles material image lookup (**2 shader texture samplers**) and GN geometry lookup (**2 image texture samplers**). Newly added cap-only GN `V13 | native continuous exposed ridges` raises/lowers evaluated mesh vertices in proportion to the *same* 3D field, with a seam fade, within a declared maximum of **0.062 mm**. This is geometric displacement, not just an increased gloss/normal map.

## Independent tests on saved Blender 5.2.2 LTS scene

Saved Blender reopened with `--disable-autoexec`, five evaluated SDF states (whole, plane, sphere bite, moved/rotated plane, moved/enlarged bite). **All five: zero nonmanifold edges and positive signed volumes.** Atlas bindings and `fruit_rest` present, no missing sampler; `V13_FIBER_HEIGHT_STRENGTH` zero-vs-one tests changed 50,659 planar and 44,414 bite vertices by more than 0.01 mm, max 0.062 mm. No original scenes overwritten.

| State | Evaluated body vertices | Signed volume in scene units | Nonmanifold edges |
| --- | ---: | ---: | ---: |
| Whole | 157,250 | 21,506.834 | 0 |
| Plane | 194,354 | 6,782.623 | 0 |
| Bite | 350,314 | 18,831.170 | 0 |
| Moved plane | 154,762 | 4,267.881 | 0 |
| Moved bite | 361,858 | 16,707.555 | 0 |

**Additional stronger achene-contact check:** previous v10/v12 tests used an ideal unit-radius sphere proxy. New `validate_v13_actual_cutter.py` independently tests all remaining seed *vertices* with nearest-face signed proximity to the **real 6,050-vertex scalloped cutter surface**, not the unit sphere. The planar cutter and two transformed states are checked too. Result **zero retained seed vertices inside the actual cutters** over 16,554, 11,748, 40,228 and 37,558 tested seed vertices respectively. This is still a per-vertex test, not a proof against every possible edge/face intersection.

## Genuine Cycles A/B: visual result is a failure

Compared unchanged v12 baseline vs v13 at same camera, frame, lights, CPU Cycles **860×860, 36 samples**: plane, original scalloped bite and plane macro. Frames 20 (plane/macro), 40 (bite).

- **Plane:** too many pronounced near-parallel light fibers; reads as an artificial regular stripe pattern, rather than irregular plant tissue.
- **Bite:** very obvious swirling/radial ribbons inside an otherwise smooth, scooped bowl. The detached fibrous wet torn edge from the owner's 18–19 s reference is absent.
- **Macro:** strict stripe periodicity is even clearer. This is a **visual regression** relative to subdued v12, even though physical relief is genuinely present.

**Reject v13 as a photorealistic target.** Neither high pass counts nor strong strands mean Frucht visual fidelity. Biology still UNVALIDATED/ARTIST; no measured histological strands or membranes. There is no objective aligned camera/pixel score against Frucht, so comparison is subjective, not claimed as pixel-matched.

## Exact source and outputs

- Original source: [build_v13_spatial_fibrils.py](build_v13_spatial_fibrils.py), [validate_v13.py](validate_v13.py), [validate_v13_actual_cutter.py](validate_v13_actual_cutter.py), [render_v13.py](render_v13.py).
- Actual QA receipts: [v13-build.json](v13-build.json), [v13-validation.json](v13-validation.json), [v13-actual-cutter-contact.json](v13-actual-cutter-contact.json), [render plane](v13-render-plane.json), [render bite](v13-render-bite.json), [render macro](v13-render-macro.json).
- **On user's Mac only**, currently ignored research workspace `build/sdf-vertical-slice/`: `strawberry-sdf-vertical-slice-v13-spatial-fibrils.blend` (SHA-256 `c081922c8264a1913b82a1f567595a30bd6258925abd42792973e819c4c158c0`); `tissue-v13-192-spatial-fibrils.png` (SHA `f9c19ebfacbab58ebd19161f88c8c2596105157b9fa783e1d2734b37b6cceab7`); `sdf-v13-matched-{plane,bite,macro}.png` (SHA values in JSON receipts).
- **NOT uploaded** to Drive in this iteration. Do not mistake local presence for Drive readback/verification. No commercial source frames, third-party copyrighted media or model binaries committed publicly.

Reproduce from checkout of this branch using a trusted copy of the owner-private v12 Blender scene in `build/sdf-vertical-slice/`:
```bash
export STRAWBERRY_SDF_OUT="$PWD/build/sdf-vertical-slice"
B=/Applications/Blender.app/Contents/MacOS/Blender
"$B" -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/build_v13_spatial_fibrils.py
"$B" -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/validate_v13.py
"$B" -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/validate_v13_actual_cutter.py
for shot in plane bite macro; do
  "$B" -b "$STRAWBERRY_SDF_OUT/strawberry-sdf-vertical-slice-v13-spatial-fibrils.blend" --disable-autoexec --python experiments/sdf-exterior-2026-11-22/render_v13.py -- "$shot"
done
```

All scripts and binary outputs refuse to overwrite the original source (builder output guard); standard screenshot/render comparison images are private artifacts until owner chooses distribution.

## Next hypothesis (not implemented)

A fundamentally different **non-periodic, sparse, branching, correlated 3D fibril topology**, anchored to actual current seed/vascular context, coupled to **local physical torn-tissue edge and bundle separation** in the SDF bite (not just uniform cap normal displacement). Build an isolated A/B and compare same whole/plane/bite close-ups before modifying any material/engine architecture. **Do not continue tuning v13 stripe frequency, white contrast or coat/gloss**. Keep v8 and v12 historical sources and this failed v13 control immutable.

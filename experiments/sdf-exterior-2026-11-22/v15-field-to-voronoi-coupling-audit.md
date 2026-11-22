# v15 — Is the Frucht-described 3D vascular → cut-cell coupling visually decisive? (22 Nov 2026)

**Engineering test PASS · visual quality FAIL (negative control).** Research-only Blender 5.2.2 LTS A/B. Do **not** merge, promote to main, call an anatomical reconstruction, or interpret an apparent shape change as a higher-quality strawberry.

## Source-grounded hypothesis

The project's verified [Frucht method audit](../../docs/frucht-architecture-audit.md) reports the commercial strawberry author's *public account*: precomputed 256³ NumPy 3D vascular field sampled in source/rest-space, Geometry Nodes 3D Voronoi cut-cell displacement made flatter over fibers, three soft Voronoi wetness shader layers, and SDF cutting. **The closed paid strawberry node graph was not available.** We do not copy the author's GPL Kiwi graph or infer its top-level Boolean architecture equals the strawberry.

**Important preflight discovery:** The intended principle **already exists in our original v8 source** [build_v8.py](build_v8.py): its `V8 | original rest-space vascular field (192^3)` samples the same packed atlas used by the flesh material, and `Map Range.001` attenuates Voronoi cap displacement through `No cell relief on same pale vascular fibers`. Therefore **v15 does not create a new engine or new vascular geometry**. The question is whether that coupling visibly changes the slice, and why the existing effect did not make convincing fiber-aligned cells.

## Controlled experiment

Both saved variants start from **unchanged v12** `strawberry-sdf-vertical-slice-v12-continuous-wet.blend`, SHA-256 `300a2bfeaa86831220657b74fe8b00d4d7ec0b42f4ffefca863d6410cbb405b7`. Same 192³ packed source R/G/B atlas (3072 × 2304), same native SDF/cutters, real 264 seed sources, seed guards, material nodes/colors, cameras and light. Identical GN Voronoi frequency and 3.2× *ARTIST* cut-cell displacement in both versions.

- **v15A / uncoupled:** `Map Range.001` output `To Min=1.0`, `To Max=1.0` in planar and bite GN. Removes **only** the field-derived attenuation. The 3D field stays in the shader and the evaluated geometry attributes.
- **v15B / coupled:** `Map Range.001` output `To Min=1.0`, `To Max=0.06`; same source R field transitions from no suppression in cortex to 94% peak flattening of cut-cell pillows over high-intensity fibers. All other factors unchanged.

This is a controlled **spatial-field → physical cut-mesh displacement** test, not an extra fiber-object, skin tweak, new wet shader or model family. No one-to-one biological interpretation of the 3D Voronoi sizes/fields is justified.

## Actual Blender independent results

Saved scenes reopened with `--disable-autoexec`. **10 evaluated states** across v15A/v15B: whole, plane, bite, moved+rotated plane, moved+scaled bite. In all ten states positive signed volume and zero nonmanifold edges; saved mesh attributes `fruit_rest`, `v8_vascular_intensity`, `v8_cell_height_mm` read successfully on cuts.

At the original plane and spherical bite, same mesh topology A/B (194,354 / 350,314 vertices). The max absolute physical cell height after 3.2× gain is around 0.06 mm. Independent evaluated vertex-coordinate differences prove the field-controlled displacement is actually geometric rather than shader-only.

| Metric | Plane | Bite |
|---|---:|---:|
| Total evaluated vertices | 194,354 | 350,314 |
| Vertices with high 3D vascular intensity R > 0.3 | 1,582 (0.81%) | 1,994 (0.57%) |
| Vertices with R > 0.3 **and** A cell relief > 0.015 mm (paired QA) | 1,192 | 604 |
| Mean B/A cell relief in this high-R subset | **0.1713** | **0.1588** |
| Mean B/A cell relief in matched low-R subset (R < 0.02) | **1.000** | **1.000** |
| Max actual A-vs-B mesh position difference | **0.05460 mm** | **0.05395 mm** |
| Vertices moving >0.01 mm when enabling coupling | 2,266 | 1,160 |

**Interpretation:** the intended gating works correctly and strongly *where the field is high*. However strong fiber field occupies a very small fraction of exposed evaluated vertices (these percentages are over full evaluated body, not measured cap-only coverage), and **the field is weak/blurred elsewhere**. This explains how valid engineering can coexist with weak visual effect, without claiming to have reconstructed the author's closed implementation.

## True Cycles A/B: visually unaccepted

Six new genuine **860×860, 36 samples, CPU Cycles** images: planar frame 20, spherical bite frame 40, macro frame 20, for both variants. Matching original v12 images have the same camera/light/render settings. Qualitative reading from original Blender images:

- **v12 baseline:** still too smooth and blurry but has some continuous pale lines.
- **A (uncoupled stronger cells):** broadly distributed rough cell pillows look like **orange-peel/caviar micrograin**, not juicy strawberry parenchyma.
- **B (coupled):** slightly smoother at bright white fibers, as intended, but the field coverage is too sparse: **visually almost identical to A** at 860px scale. Both still have an unnaturally scooped, smooth bite cavity and do not approach Frucht's cut-fragment quality.

Direct raw Cycles pixel comparison (same native image dimensions, RGB per-pixel max difference threshold; **not a perceptual-quality metric**):

| Shot | A vs B: % pixels changed >0.01 | Original v12 vs A: % changed >0.01 |
|---|---:|---:|
| Plane | **0.652%** | 10.755% |
| Bite | **0.600%** | 6.947% |
| Macro | **2.613%** | 44.865% |

Thus 3.2× cell amplification causes much larger changes than toggling actual vascular coupling. Amp alone is a **visual regression**, not a solution.

**Scientific status:** all vessel widths/locations, Voronoi scales, tissue maps and sheen settings remain marked `ARTIST`; no new histology, inferred cell membranes or measured vasculature. No claim of exact Frucht fidelity; private reference video was not published/embedded.

## Code, evidence and storage

- Rebuild: [build_v15_field_cells_ab.py](build_v15_field_cells_ab.py).
- Saved-scene numerical validator: [validate_v15_field_cells_ab.py](validate_v15_field_cells_ab.py), [raw validation](v15-validation.json).
- Genuine Cycles renderer: [render_v15.py](render_v15.py); six per-shot render SHA records included on this branch.
- Pixel comparison + genuine Cycles contact sheet: [v15_compare_images.py](v15_compare_images.py), [v15-image-ab.json](v15-image-ab.json). Contact-sheet order left-to-right **v12 / v15A / v15B**; top-to-bottom **plane / bite / macro**.
- Build metadata: [v15-build.json](v15-build.json); [ZIP member hashes](v15-package-manifest.json).
- Local owner Mac, ignored `build/sdf-vertical-slice/`: two independent editable Blender scenes, six original Cycles PNG, three original v12 matched Cycles PNG, 3×3 2580px contact sheet, source scripts and JSON validators. **Never uploaded to Drive.**

Verified local source scene SHA-256:
- v15A: `3f796b53f6a30b560443b02904cc705e186a8d4b596685a62b5178ece0b66f08`
- v15B: `8b2189572d17ee603f5a6d5720ff6768b9d9b79bd7e9439c0969095b92577e12`
- 3×3 Cycles sheet: `f78ec9137c3ab3cd3335a3e86ee575a2682539428dbbb941760aaf0bcf8e4369`
- All 25 ZIP members passed full SHA-256 readback; archive `strawberry-v15-field-cell-coupling-AB.zip`, **62,512,551 bytes**, SHA-256 `e83e0af13a50a824a51664b1ab292b55cabcd9b0b5ad74597865b42ba5a09708`. **Local Mac only**, not a public or Drive download.

Reproduce from trusted private v12 scene placed at `build/sdf-vertical-slice/`:

```bash
export STRAWBERRY_SDF_OUT="$PWD/build/sdf-vertical-slice"
B=/Applications/Blender.app/Contents/MacOS/Blender
"$B" -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/build_v15_field_cells_ab.py
"$B" -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/validate_v15_field_cells_ab.py
for variant in v15a v15b; do
  scene="$STRAWBERRY_SDF_OUT/strawberry-sdf-vertical-slice-$([ "$variant" = v15a ] && echo v15a-uncoupled-cells || echo v15b-restfield-coupled-cells).blend"
  for shot in plane bite macro; do
    "$B" -b "$scene" --disable-autoexec --python experiments/sdf-exterior-2026-11-22/render_v15.py -- "$variant" "$shot"
  done
done
"$B" -b --disable-autoexec --python experiments/sdf-exterior-2026-11-22/v15_compare_images.py
```

## Decision / next limited hypothesis

Preserve **v12** as visually stronger source and v15A/B as a rigorously bounded negative A/B. **Do not merge this into main.** No more isolated changes to Voronoi strength, shader coat, or adding detached fiber solids. The next useful research should analyze the **3D field's spatial strength/width/continuity and resolution, especially how much truly exposed cut area samples high-R fibers**; start with a diagnostic field-coverage visualization and exact rest-space sampling on planar and bite. Only then select one replacement field algorithm that preserves continuous soft pale strands at multiple cutter poses, while leaving SDF cutter and source anatomy alone.

Our test confirms a mechanism in *our* code, not that we have inspected or recreated Frucht's proprietary graph.

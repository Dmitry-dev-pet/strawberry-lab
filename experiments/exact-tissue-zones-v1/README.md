# Exact tissue zones v1

This experiment replaces PR32’s uniform cap-height field with three independent geometric contributions. It uses the same native Boolean, knife, canonical fruit, exterior, diagnostics and packed material. The four native layers are MATCHED, WHOLE, FLESH ONLY and FIBERS ONLY.

Open `strawberry-tissue-zones.blend` with scripts disabled for Fast. To opt into the editable geometric cap, open the Scripting workspace, select `TISSUE_ZONES__RUN.py` in the Text Editor and run it. In the 3D View, use **N → Strawberry Cut → Exact** in MATCHED or FLESH ONLY. Move or rotate the same knife Empty. The panel offers three strength sliders, in millimetres. Saving retains their values and restores native Fast. Run the Text again to enable Exact after reopening.

| Control | Default strength | Effect |
| --- | ---: | --- |
| Cortex relief | 0.135 mm | Fine, vertically elongated variation over the red flesh |
| Pith relief | 0.052 mm | Lower-amplitude, broader undulation in the pale and amber axial tissue |
| Vascular relief | 0.045 mm | Modulated relief near the original authored three-dimensional paths |

These strengths scale separate, nonnegative components. Zero omits the selected component. The all-zero cap remains triangulated and flat. They are **ARTIST** look-development settings for this fruit, including the spatial scales and zone boundaries. The relief represents tissue textures on the cut surface. This experiment makes no histological calibration, segmented-cell, or benchmark-fidelity claims.

## Atlas inventory and field

The original material normalizes PR29 rest coordinates against the lower bound ≈ `(-1.30, -1.30, -1.23)` and span ≈ `(2.60, 2.60, 2.28)`, clamps each axis, and scales by 149. The packed Non-Color PNG is 2250 × 1500. Blender reads rows from the bottom. Slice *k* begins at tile column `k % 15` and row `k // 15`. X/Y sample within pixel centers in each tile and Z blends the two adjacent slices. [The probe](probe_atlas.py) independently evaluates the actual material node graph up to its ungraded RGB blend and checks against the CPU decoder. At 171 points, including tile transitions and corners, the maximum green difference was 5.96 × 10⁻⁸. The [inventory](atlas-inventory.json) records all-channel percentiles, green histograms and sampled RGB.

The voxel distributions informed the classifier. Green medians were 0.369 in the geometric core reference, 0.231 in its transition reference, 0.031 in the more peripheral cortex reference, and 0.278 in the amber axial reference. The cortical reference nevertheless reached 0.424. For example, the center at rest `(0,0,.2)` reads green 0.214, while `(.1,0,.2)` reads 0.314. This reflects the authored amber stripe and pale traces in the RGB source.

The field uses the V0 generator’s wandering axis and axial growth radius. For rest `(x,y,z)`, the axis is `(.017 sin(6z), .014 cos(4z))`, and the radius is `.090 + .142 clamp((z+1.14)/2.16)`. Let `q` be distance from the axis divided by this radius, and let `S` be the clamped cubic smoothstep. The broad axial weight is `A = 1−S((q−.72)/1.18)`, the inner amber protection is `K = 1−S((q−.46)/.46)`, and the atlas response is `G = S((green−.095)/.225)`. The pith weight is `A·(G+(1−G)K)`, with cortex weight `1−pith`. The axial weight suppresses peripheral bright atlas traces from creating false pith islands. At this scene’s scale one rest unit is 22.2222 mm.

[The field module](tissue_field.py) gives the exact millimetre scales and noise offsets. Improved Perlin is sampled in three dimensions with a shorter cortex scale and a longer pith scale. The vascular envelope reaches 1 mm beyond the original radius-interpolated polyline segments. Its envelope follows those paths and is modulated by the quieter cortex noise octaves. Noise anisotropy follows the fruit rest axis rather than a local vessel tangent; this is a restrained surface cue, not vessel-wall reconstruction. The original shader supplies all the color. The field is sampled at the vertex’s undeformed position. The original 0.27 mm CDT, 0.75 mm seam fade, height-to-edge bound, outward normal displacement, material rest attribute, and render-layer switch are all reused. The initial noise basis was replaced after the submicron continuity probe detected steps disproportionate to the sample spacing.

## Reproduce with Blender 5.2.2 LTS

Run from the repo root. Outside the existing workspace, create `.venv` with `python3 -m venv .venv`, install `requirements.txt`, and set `PY=.venv/bin/python` instead of the sibling environment path below. Blender supplies its own Python and NumPy. Put the four authenticated source files under `build/inputs` and choose an unused `OUT`. The receipts record the PR29, PR30, PR31 and PR32 inputs; the builder rejects any other PR32 hash.

```sh
B=/Applications/Blender.app/Contents/MacOS/Blender
PY=../strawberry-lab/.venv/bin/python
E=experiments/exact-tissue-zones-v1
I=build/inputs
O=build/tissue-zones-repro
blend() {
  "$B" -b --factory-startup -t 4 --disable-autoexec --python-exit-code 1 "$@"
}

mkdir -p "$O"
blend "$I/pr32-exact.blend" --python "$E/probe_atlas.py" -- \
  --out "$O/atlas-inventory.json"
blend --python "$E/build_tissue_zones.py" -- \
  --source "$I/pr32-exact.blend" --out "$O" > "$O/build.log" 2>&1
Z="$O/strawberry-tissue-zones.blend"

PYTHONPATH=src "$PY" -m unittest discover -s tests -v > "$O/existing-tests.log" 2>&1
"$PY" -m unittest discover -s "$E" -p 'test_*.py' -v > "$O/atlas-tests.log" 2>&1
blend --python "$E/validate_tissue_zones.py" -- \
  --pr29 "$I/pr29-original.blend" --pr30 "$I/pr30-corrected.blend" \
  --pr31 "$I/pr31-layer-modes.blend" --pr32 "$I/pr32-exact.blend" \
  --scene "$Z" --out "$O/validation.json" > "$O/validation.log" 2>&1

mkdir -p "$O/renders"
for pose_look in saved-beauty saved-clay oblique-clay; do
  for version in pr32 zones; do
    scene="$Z"
    if [ "$version" = pr32 ]; then scene="$I/pr32-exact.blend"; fi
    frame="$O/renders/$version-$pose_look"
    blend --python "$E/render_tissue_zones.py" -- \
      --scene "$scene" --quality exact --pose "${pose_look%-*}" \
      --look "${pose_look#*-}" --out "$frame.png" > "$frame.log" 2>&1
  done
done
"$PY" "$E/compare_renders.py" --renders "$O/renders" --out "$O"
blend --python "$E/validate_cross_layer.py" -- \
  --scene "$Z" --out "$O/cross-layer" > "$O/cross-layer.log" 2>&1
```

A fresh process renders each A/B frame with Cycles CPU, four threads, 650 × 650 pixels, 16 fixed samples and seed 1729. Each pair is matched by knife, camera and light receipts. Clay is a uniform material with no bump and excludes the diagnostic overlays. The contact sheet marks the fixed clay regions and includes enlarged crops. High-pass luminance RMS uses a 2.5 px Gaussian blur and is a relative image metric for these crops and render settings.

Exact is a CPU look-development mode. It rebuilds after the deferred callback for the shared knife or slider change. Native Fast is the interactive preview.

## Verification results

- [Geometry and runtime QA](validation.json) passed on five cuts. Each evaluated receptacle had one connected component, positive signed volume and zero nonmanifold edges. Skin faces, seams, pit values and skin corner normals matched Fast, with zero measured normal error. The raw hull, shared knife, 28 carrier and 539 branch splines, 539 markers, 264 exterior achenes and packed atlas were preserved. MATCHED and FLESH ONLY produced identical evaluated solids across all 274 solid objects. WHOLE parked the knife and FIBERS ONLY hid the solids. The runtime passed repeated activation, deferred translation and rotation, save and reopen, and recovery from an injected reconstruction error.
- Zeroing each slider removed its own response. The cortex and pith components averaged 0.0529 mm and 0.0226 mm in their high-membership zones. At 0.23–0.30 mm edge spacing, their component slope RMS measured 0.0600 mm/mm and 0.00511 mm/mm, respectively. Vascular relief averaged 0.0225 mm within 0.35 mm of the path surface and reached zero beyond 1 mm. All three zeros yielded zero measured displacement.
- Nine rest points returned identical masks and fields across all five knife poses. After a float32 round trip through the actual knife transformations, the largest dimensionless difference was 1.11 × 10⁻⁶. A second check used 1,050 directional pairs, including tile boundaries. Reducing probe distance from 0.002 mm to 0.0002 mm reduced the maximum response differences by approximately 10×.
- [Render QA](render-qa.json) verifies the six frames. In the saved clay crops, high-pass luminance RMS was 25.5% of PR32 in the cortex and 7.2% in the pith. In oblique clay it was 28.1% and 6.9%, respectively. The actual Cycles frames show a smoother axial region through both angles. [Cross-layer render QA](cross-layer-qa.json) produced identical decoded pixels between a cut edited from WHOLE and a freshly prepared control for both cut layers.
- On Apple M4 with four Blender threads, the five Exact knife poses took 1.27–1.45 s to refresh, compared with 1.03–1.21 s for PR32 Exact in the same validation run. Cap refinement in the new runtime took 0.26–0.37 s. The full validator, which retains baseline snapshots for five poses, peaked at 0.96 GiB RSS. The measured Cycles runs took 13–19 s per frame under differing process loads. The 107 existing tests, four atlas sampling tests and four render-receipt regression tests passed.

The [build receipt](build-report.json) authenticates the scene and its embedded runtime. The [artifact manifest](artifacts.json) gives SHA-256 and byte sizes for the editable scene, six renders, contact sheet, QA outputs and logs under `build/tissue-zones-v1`.

## Independent review, correction and private artifacts

[Independent Astra review](independent-review.md) reproduced the new oblique clay image pixel-for-pixel, traced every measured ROI pixel to its intended tissue, checked 2,295 real cap vertices against the field, and compared 256 RGB swatches through actual Cycles to the CPU atlas decoder (maximum channel error below 0.000007). Equal-width crops retained the smoother-pith result. Its full geometry/runtime and cross-layer checks passed.

The review found one provenance gap in the render comparison: a genuine PR32 beauty PNG plus its receipt could be mislabeled as the new frame. The parent fixed the comparison to bind each image to the pinned PR32 hash or current build receipt, expected look, requested/evaluated pose, layer and seed. The actual substitution now fails with `AssertionError: ('zones', 'scene_sha256')`. Four checked-in regression tests also cover a saved pose mislabeled as oblique, wrong evaluated pose and wrong look. The six delivered images and the scene were already genuine; no geometry or embedded runtime changed during this correction. The reviewed comparison report is regenerated under `build/tissue-zones-v1/reviewed/`.

[Owner-private scene](https://drive.google.com/file/d/1YoeDB5WyQW3OymGeQfPhqFk4lviZpUf2/view) · [old/new Cycles contact sheet](https://drive.google.com/file/d/1t4jyWYkA3okWhkWxY1sIa3IC3uFvOyJa/view) · [private reproducibility folder](https://drive.google.com/drive/folders/1tXaF8TiA6wrKdPSnyKiQvlFhqY8mFE4R). The [public artifact manifest](../../assets/manifest-exact-tissue-zones-v1.json) lists canonical Drive files and full-download SHA-256 checks. The downloaded scene passed the full validator again; see [downloaded-scene QA](downloaded-scene-qa.json). The earlier unbound comparison report is preserved as superseded evidence. The binary scene, images and bundle remain private. All old experiments and prior .blend/PNG files remain unchanged.

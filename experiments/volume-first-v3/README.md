# Strawberry Lab — Volume First v3 (carrier profile + achene-anchored Bézier)

**Diagnostic research only.** This is an independently authored test of vascular network morphology. It does not reproduce Frucht's paid scene, does not claim measured histology, and has **not** re-generated the flesh geometry, cut tissue, or shader atlas. See the source-grounded Frucht Free 0.4.3 architecture audit, merged into `main` at `research/frucht-free-043/ARCHITECTURE_AUDIT.md`.

## Contents

- `input-v2-network.npz` — unchanged **539 achene marker positions and 539 subcutaneous branch termini**, based on the project's own historical M1a seeds, reprojected to Volume First's silhouette in v2.
- `input-v2-scene.blend` — unchanged prior scene, including studio camera and materials.
- `generate_v3_network.py` — our own 11-control-point height-dependent PCHIP profile, bent carrier axis and two Bézier handles per independent achene branch; no third-party code or source nodes.
- Five `v3-profile{N}-sag{S}.npz` archives: 14/28/40 central carriers; at 28, sag 0.25/1.0/1.8. All **539** mapped seed markers and terminus coordinates remain exactly equal to v2.
- `build_v3_blender.py` and `v3-carriers-bezier-variants.blend`: **one editable Blender scene** with all five variants, plus original V2 network for A/B. Switch variants with the render script; other scene entities remain unchanged. No viewport-runtime updates when source polylines are edited; regenerate scene.
- `validate_v3_blender.py`, `qa_v3_data.py`, `reproduction-qa.json` — saved-scene and source invariance checks.
- `outputs/only-{variant}.png` — actual **Blender 5.2.4 Cycles** diagnostic renders from fixed camera; `ghost-28-sag1.0.png` adds a semi-transparent fruit.
- `outputs/real-ab-sag.jpg`, `real-ab-strands.jpg` — side-by-side same-camera Blender comparisons.
- **Private-only:** `private-frucht-video-ref15.jpg` (owner-supplied video still) and `outputs/private-frucht-v2-v3-comparison.jpg`; do not publish these in GitHub.

## Reproduce

Requirements: Python 3 with NumPy and SciPy; Blender 5.2.4+.

```sh
python generate_v3_network.py --strands 28 --sag 1.0 --out v3-profile28-sag1.0.npz
python qa_v3_data.py
blender -b input-v2-scene.blend -t 4 --python build_v3_blender.py -- v3-carriers-bezier-variants.blend
blender -b v3-carriers-bezier-variants.blend -t 4 --python validate_v3_blender.py
blender -b v3-carriers-bezier-variants.blend -t 4 --python render_v3_blender.py -- --view only --variant 28-sag1.0 --resolution 680 --samples 11 --out outputs/only-28-sag1.0.png
python make_real_comparisons.py
```

For controlled parameter sweep, generate all five `v3-profile*.npz` files with the exact options in `qa-v3-data.json`, *then* execute Blender build. The scene opens with `28-sag1.0` visible. The 3 visualization contexts inherit cameras from V2: `01 |` fiber only, `02 |` translucent fruit, `03 |` original Volume First v1 cut (not rebuilt). For automated render switching, select `--view only|ghost|cut` and `--variant v2|14-sag1.0|28-sag0.25|28-sag1.0|28-sag1.8|40-sag1.0`.

## Evidence and scope

Blender saved-scene test PASS on all five configurations: **0 displacement of 539 target coordinates and source achene positions**, V2 curves retained. V2 median branch length/chord = 1.0197; V3 sag 0.25 = 1.0332, sag 1.0 = 1.1095, sag 1.8 = 1.2233. This demonstrates controllable curvature, not fidelity to Frucht. Compared with the actual video ~00:15, our long hanging arcs remain morphologically different. Camera and zoom are not equivalent. A high-sample `cut` overlay did not finish in the execution budget; no successful output is claimed for that mode.

**No vendor `.blend`, original source code or full node dumps are committed to GitHub.** Experimental sources and independent documentation can be versioned on a PR stacked on #23. Rendered images, binary assets and private reference remain in the owner's restricted Google Drive.

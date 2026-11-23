# Strawberry Lab — same native cell field for cut geometry + cap shading

**23 November 2026 · Blender 5.2.4 LTS · Engineering PASS (tested states) · Visual acceptance FAIL.**

Stacked research for [PR #49](https://github.com/Dmitry-dev-pet/strawberry-lab/pull/49) (on unmerged PR #48). Source saved scene: owner-private PR49 portable [v20 bridge](https://drive.google.com/file/d/1huv9bwO4wcydPZEvnMbdBCIbfJCURvCa/view), exact SHA-256 `0b79e33b0725f807524061b1afe79671f4fcf1c6b5c429bd8203cec8d6a21bd2`. The current source carries 264 achenes, an original 150³ flesh/material atlas, 192³ owned R/H vascular fields, and SDF plane and sphere cuts. Nothing from Frucht's commercial/GPL code, meshes, shaders or videos is shipped here.

## One controlled hypothesis

The native v20 SDF geometry already samples **one original 3D Voronoi `DISTANCE_TO_EDGE` cell signal at rest-space scale 32** to displace exposed-cut vertices, attenuated by the existing wide vascular H field. But its material reads unrelated microroughness textures and the legacy 150³ color atlas. Instead of inventing more 3D noise or drawing pale cell boundaries, capture a smooth *interior lobe* from that SAME source Voronoi and reuse it in both geometric and optical responses.

`build_cell_optical.py` adds one named GN float attribute `sdf_cell_lobe_response = smoothstep(0.019,0.064,old_voronoi_distance) × old_cell_suppression × cut_only_mask`. It does **not** create a new random field or change source grids. The shared `sdf_cell_surface_gain` control (native driver, 0–1) simultaneously:

- adds at most **0.055 mm** of local convex cell-lobe displacement on active exposed SDF cap vertices, in addition to existing v20 displacement; whole fruit remains unchanged;
- adds at most 10% warm/red-brown color blend on exposed cell interiors (not a white edge outline) via the **same evaluated GN attribute** in the existing cut-face shader;
- adds at most 0.085 roughness on the same cell interiors, preserving all preexisting shader micro-normal fields, SSS=0.08, 150³ atlas, 192³ R/H atlas, lights and cameras.

All numeric coefficients are **ARTIST** (not source-matched strawberry histology or physical fluid properties). A=0 is the pixel-identical v20 bridge; B=1 is the co-registered geometry-and-material intervention. The original saved v20 `.blend` is not overwritten.

## Independent native Blender verification

`qa_cell_optical.py` does not import the builder. After opening A/B saved `.blend` with **script autoexecution disabled**, it validates seven pose/voxel combinations: 0.32 mm WHOLE, plane, oblique plane, default sphere, side-edge sphere; 0.20 mm plane and side-edge sphere. **7/7 A/B matched states pass**: same body vertex count/topology, preserved source rest-space and R/H/cell-suppression point-attribute hashes, zero nonmanifold body edges, positive signed volume; all whole-body coordinates equal; in cut poses B adds measured geometric displacement up to **0.0550013 mm**, changing thousands of real evaluated vertices (e.g. 30,792 plane-fine and 40,494 side-bite-fine at >0.001 mm). A's evaluated coordinates match earlier independent v20 verified SHA-256 for every archived exact pose.

The additional `qa_live.py` checks saved-scene gain 1→0→1 restores identical evaluated geometry, and changing both plane and sphere cutter updates real geometry. All tests work without embedded script execution. **Not verified:** arbitrary cutters, physical cell membranes, SDF self-intersection beyond current checks, exact seed-edge intersection, or measured cellular anatomy.

A clean **portable re-build** of A/B from the same pinned private source using the released CLI-capable builder also passed independent 7/7 pose QA, with identical geometry results. Blender binary file hashes vary with saved paths; original rendered scenes and rebuilt scenes have different binary hashes and the latter are QA-only, not substituted for those tied to renders.

## Matched original Cycles A/B and visual assessment

Six original CPU Cycles PNGs (3 × 2) from individually reopened original A/B scenes; 640×640, 16 samples, seed 1729, matched cameras, cutter poses, lights and color management; denoise ON. `compare_renders.py` verifies SHA receipts and **A is pixel-for-pixel identical to the prior v20 halo render** in all 3 shots.

| Shot | Changed pixels >2/255 | Changed >10/255 | Actual appearance |
|---|---:|---:|---|
| Plane | **16.11%** | 6.81% | Small pulp dimples visible, but too homogeneous |
| Open-side bite | **10.16%** | 3.27% | Slight cellular detail but original smooth cavity and pale core remain |
| Plane macro | **16.17%** | 6.78% | Very uniform stamped-leather/pitted texture |

The pixel change percentages only prove the intervention is real and **are not perceptual scores or proof of Frucht fidelity**. Compared qualitatively to the owner's private author video at ~10.5 and 18.5 seconds (unaligned camera/light), B is still not an adequate approximation to irregular torn wet internal tissue. **Visual target FAIL.** Unlike prior pure-SSS experiments, this paired intervention is visibly stronger but still inadequate.

**Render caveat:** A rendered with 4 CPU threads while B required clean retries with 2 threads (first high-res B attempts stalled). B ultimately rendered all 3 shots and saved SHA receipts, but the elapsed render times **are not fair A/B performance comparisons** and don't prove a specific material performance regression. Keep this as a limitation for subsequent work.

## Reproduction

With Blender 5.2.4+ and the private pinned source saved as `inputs/v20-bridge-portable.blend`, from the repository root:

```bash
BLENDER=/path/to/blender
SRC=inputs/v20-bridge-portable.blend
ROOT=experiments/sdf-cell-coherence-2026-11-23
$BLENDER -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$ROOT/build_cell_optical.py" -- --source "$SRC" --outdir build/cell-ab/scenes
$BLENDER -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$ROOT/qa_cell_optical.py" -- --scene-dir build/cell-ab/scenes --out build/cell-ab/qa.json
$BLENDER -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$ROOT/qa_live.py" -- build/cell-ab/scenes/cell-coherent-B.blend build/cell-ab/live.json
$BLENDER -b --factory-startup --disable-autoexec -t 2 --python-exit-code 1 --python "$ROOT/render_cell.py" -- --scene build/cell-ab/scenes/cell-coherent-B.blend --shot plane --out build/cell-ab/plane-B.png --resolution 640 --samples 16
```

The build refuses wrong input SHA and overwriting existing scene output; the validator refuses overwriting its JSON. A and B source scenes and genuine Cycles images are preserved in the private archive. To run `compare_renders.py`, provide `--renders <directory-of-paired-Cycles-PNG-and-JSON>` and `--source-renders <directory-of-pr49-v20-halo-PNG>`; these prior baseline images are available in the previous restricted PR49 archive. All authored source is public-project-original. No editor reference stills or paid assets are included in the public repo/ZIP.

**Disposition:** preserve as narrow working co-registered-cell mechanism with **visual FAIL**. No automatic merge to `main` or declaration of Frucht parity. Next hypothesis must address actual irregular torn tissue macro-geometry/heterogeneous cell-domain orientation, not endlessly increasing uniform cell-amplitude or SSS.

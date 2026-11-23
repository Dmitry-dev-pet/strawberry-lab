# Vascular Relief — coupled PR50 cell surface and owned vascular field

23 November 2026. Original independent ARTIST research. Input is the PR50 cell-surface scene; reuse of owned PR49 field and sampler only, not a commercial/GPL reference scene. Main is unchanged. This experiment changes geometry only, not materials, SDF, seeds, calyx or original rest atlas.

## Mechanism
- The source PR49 volume is 192^3 in original rest coordinates, contains 557 artist graph segments, and has distinct narrow core R and broad halo H. All 264 named achene anchor positions were compared exactly between the old PR49 scene and the PR50 source.
- Sample R/H trilinearly on the existing conformingly refined surface. Suppress the old dome by a smootherstep H mapping [0.04,0.48] -> [1,0.12]; add 0.12 R + 0.045 H mm times the existing seam fade and both gains. Values ARTIST, not botanical measurements. Same field for all cuts. No independent shader change, no juice layer.
- `vascular_relief_gain=0` retains exact prior PR50 displacement; `1` activates the coupled relief. `cell_surface_gain=1` and `cell_surface_detail=1` for test cuts. Whole mode bypasses refinement. Same global subdivision limitation as PR50.

## Reproduction
Blender 5.2.4 LTS (runtime hash cd5dc428cce1). Run scripts with absolute paths, background mode, autoexec disabled, 4 threads, python-exit-code 1. Input SHA256 pins in builder. Input PR50 `cell-surface-ab.blend` and PR49 `strawberry-v20-seed101-core-halo-bridge.zip` (original archive contains our sampler/field and scene). Baseline QA files `qa-032.json`, `qa-020.json` from PR50, not regenerated.

```
B=/path/to/blender
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python build_vascular_relief.py -- /path/cell-surface-ab.blend /path/strawberry-v20-seed101-core-halo-bridge.zip /path/vascular-ab.blend
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python qa_vascular_relief.py -- /path/vascular-ab.blend /path/strawberry-v20-seed101-core-halo-bridge.zip /path/PR50/qa-032.json /path/qa-032-plane.json .32 plane
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python render_vascular_relief.py -- /path/vascular-ab.blend plane 1 /path/plane-B.png .32
```
Substitute whole/oblique/bite for QA and macro/bite for rendering. Saved scene defaults to whole, vascular gain zero. No source-file overwrite.

## Observed QA
Four A/B pairs at 0.32 mm (whole, longitudinal plane, tilted plane, sphere bite), eight evaluated states PASS: same triangle topology A/B, zero nonmanifold edges and degenerate triangles, positive signed volume, exact A coordinate SHA vs PR50 baseline, exact whole A/B. Cut skin-only and seam position differences zero. Across cut states maximum A/B displacement 0.125285 mm, max ridge 0.125790 mm. Strong-halo cell multiplier 0.12, weak-halo multiplier 1.0. Independent 256 cap samples per cut (768 total): max absolute R/H trilinear error 3.123e-5, threshold .001; max height equation error 2.981e-8 mm. No exhaustive self-intersection/seed/calyx or arbitrary-pose QA. 0.20 mm fine-plane A/B attempted; timed out after 65 seconds, no numerical report, not PASS. Coarse tests do not establish performance of fine mesh.

## Render evidence and verdict
Three original Blender Cycles B frames (plane/macro/bite), matched to PR50 archived cell-surface B frames used here as A; all source PNG hashes, camera matrices, samples, resolution, seed and voxel settings verified. CPU 480x480, 8 samples, seed 1729. A is not newly rendered, and reported pixel changes include any rendering nondeterminism; comparisons are diagnostic, not reference fidelity metrics. Plane and macro show smoother elongated central region, but still broad pale core, fairly uniform outer grain, artificial bite and no realistic liquid. Geometry-only research success at tested resolution, visual parity NOT reached. Do not merge based on numeric checks; next investigate region/vascular optical linkage and cap-local refinement; juice geometry as separate study.

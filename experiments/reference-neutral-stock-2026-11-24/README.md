# Neutral exterior stock — reference-first contract, 24 November 2026

Research continuation of Draft PR50 following `experiments/reference-dependency-map-2026-11-24/README.md`. **Technical prototype only.** No visual parity claim, no change to integrated research control, no main merge. Reuse the independent existing FruitContext, ExteriorShape, PitField and achene ovoid emitter. No Frucht source, node trees, assets or numerical presets copied. The commercial Strawberry graph remains unavailable. Inspired by verified shared anchors and neutral-state deformation, not a literal reconstruction.

## Scope and contract

`neutral_contract.py` defines immutable NeutralStock (the shared anchors are a tuple of the existing immutable AcheneAnchor records), ShapeState, deterministic anchor/stock digests, an analytic forward/inverse radial map and Jacobian-transformed normals. The real Camarosa FruitContext is built through the existing catalog and registry, using the existing 48 mm / 32.5 mm nominal dimensions; all new shape, achene-count and pit settings remain ARTIST for this experiment. This is not a biological count or specimen reconstruction. Stock depends on the neutral source settings, anchor records and mesh sampling version; shape-state edits do not rebuild that stock. Anchor IDs combine context ID, population digest and ordinal, so different populations cannot silently alias. The future vascular dependency key includes the anchor digest (no vascular field built here).

`build_neutral.py` emits the real pitted skin, the existing five ovoid prototypes as closed seeded mesh components, the anchor points and measured triangle-seat points. The source uses the existing 352 × 448 meridian/azimuth grid and compact PitField. Each seed is seated against the actual pitted triangle surface along its anchor normal, and its overlap with the skin triangles is checked. One original 28-node native GN group and a shared controller apply the same continuous position map to all four meshes. Neutral coordinates and anchor indices remain as named attributes. All vertices of seeds deform with the map; no separate rigid instancing/orientation policy is implemented. The two count alternatives are separate independently generated neutral stocks, not a count slider inside one blend.

## Exact inputs

Pinned owned GitHub source at accepted main `61b403eb1fbdc2cff72afdaf95504f4fe7e46b17`; archive `strawberry-generator-v1-fast.zip` retrieved from owner Drive, SHA256 `ab64ad4ceeec51b571aa34f4004c508eacf28d230f2950808f96fc971797235c`. Extracted dependency Git blobs match current accepted main:

| Path | Git blob SHA |
|---|---|
| src/exterior_shape.py | 90bb7874680c55f2940d3ff899e6ab555b9b55e7 |
| src/fruit_platform.py | 6de4853bda8e7cba912af84e9176ccf5f1152d9b |
| src/fruit_engine.py | 3e4bcde8b43a588d40b30bca94469d7b3d93b703 |
| src/fruit_engine_anatomy.py | c2563d57d4fe7062af57cd6f262b3f02e5ee6c9d |
| src/fruit_morphometry.py | 0d9aeee5acee0511c8a3d9aff2966061416f36a5 |
| src/build_strawberry_exterior.py | d38ab90b84bd99015b80b9063dd100ee5a64033b |
| data/morphometry/measurements-v1.json | 0e79d8cd290e4e1cc7d0061c4f523b9adc7954ad |

The archived integrated PR50 control (`790dc4adbd9025b56e7833c2cedb8ada83c0e9b738ac294f96889fbb52e0e215`) is unchanged; it is not used to generate these meshes.

## Results and limitations

Nine pure Python unit tests pass. Two saved Blender 5.2.4 LTS (cd5dc428cce1) scenes with 264 and 326 achenes, both seed 101, independently reopen with scripts disabled. Six evaluated states (identity, changed shape a=.16/b=-.10/h=1.12, restored identity, for both counts) pass. All four objects preserve source vertex buffers, polygon indices, rest coordinates and available anchor indices. Forward/inverse compared with independent NumPy evaluation on every vertex: worst coordinate error <0.000003 mm. Restored position hashes equal identity. Skin maximum displacement 5.7601 mm; original pitted skin has 157,250 vertices. All skin and seed meshes have zero nonmanifold/inconsistent edges and degenerate triangles; positive total signed volume. Actual triangle BVH overlap for all seeds in all six states, seat-to-skin distance <=0.000302 mm. This overlap checks contact, not ideal seed exposure, exact absence of penetration, seed-seed overlap or every possible shape setting. No exhaustive self-intersection proof, all-pose evaluation, scientific calibration, calyx/hairs, flesh, vascular, cutter, seam, cell, juice or production materials. Initial failed Blender invocations due to path and absent world, corrected; second failure log preserved. Render logs contain EGL warnings but all three output PNGs were written successfully and inspected. No claims that a high vertex count or a smooth diagnostic model proves realistic geometry.

Three actual 600x600 Workbench diagnostic images at identical camera and settings: 264 neutral, 264 deformed, 326 neutral. Not Cycles and not a photographic quality comparison. The full anchor and seat receipts are stored with the private scenes. Report `summary.json` is compact aggregate evidence only. Keep the prior integration immutable until separate skin/flesh cutter design is tested.

## Reproduce

Python with NumPy and Blender 5.2.4. Use the pinned repo dependencies on PYTHONPATH (Blender builder also resolves `repo/src` when stored under the experiment directory). In a standalone archive put the pinned source under `deps/src` and pass the catalog path explicitly. Use fresh output paths; binary .blend metadata may differ on rebuild. The source-path resolver was extended to recognize the repo layout after the initial builds; no geometry algorithm was changed. Save default neutral, select `SL Shape Controller | edit Custom Properties` and adjust `shape_a`, `shape_b`, `shape_h` within the tested map bounds. UI limits and Python validation do not assert support for arbitrary values set through external scripting.

```
R=/absolute/path/to/repo
L=$R/experiments/reference-neutral-stock-2026-11-24
D=/absolute/path/to/new/output
B=/absolute/path/to/blender
C=$R/data/morphometry/measurements-v1.json
PYTHONPATH=$R/src python "$L/test_contract.py" "$C"
for n in 264 326; do
  "$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/build_neutral.py" -- "$C" "$n" "$D/stock$n.blend"
  "$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/qa_neutral.py" -- "$D/stock$n.blend" "$D/stock$n.json" "$D/qa$n.json"
done
"$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/render_neutral.py" -- "$D/stock264.blend" neutral "$D/264-neutral.png"
"$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/render_neutral.py" -- "$D/stock264.blend" deformed "$D/264-deformed.png"
"$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/render_neutral.py" -- "$D/stock326.blend" neutral "$D/326-neutral.png"
```

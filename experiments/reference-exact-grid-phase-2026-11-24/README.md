# Exact zero-isovalue grid-phase diagnosis — 24 November 2026

Continuation of draft PR50 at `ce8c7a240477c2bb4a2525db4aa786722e44cf0a`. **Six sampled states PASS the existing common-boundary and seed-contact gates; not a universal Exact proof or visual acceptance.** No vessels/cells/juice, new material, cavity, or main merge. Independent numerical treatment, not an identified Frucht algorithm; no author code, assets, presets or graphs transferred.

## Inputs and read-only diagnosis

Actual Blender 5.2.4 LTS `cd5dc428cce1`. Reassembled the owner-provided runtime from 17 parts, checking each size and SHA256 and the complete archive `2fd14c50987426897ba60237ee996edf2b4151f4b1a72a460ca20be58c1d2d86`. Verified earlier saved input `exact-zero.blend` SHA256 `36f9ff4a5de1f1d222548d3c827a87df209624d55949643d9ff61449a1460cd6`, Fast baseline `4cee7f472d5ebe8a9ee48b39f760ee87a5d16f3c1e2db0ee5aaffe4fcdcd0ff3`. Four owned Python dependencies recovered from private prior evidence ZIPs and matched to Git blobs at the preceding experiment: build_exact.py `5206847d8bd6e72c9c0eab079da7d405bd1ba40d`, qa_exact.py `e62e9780d5e894a0fe2b8fb68b7f2a07fc97ef06`, build_split.py `1fd07748a0bc668b81715d037e3ee5db8b6cad20`, qa_split.py `dbe96d08499190d1b196091054fc4ab5a3030b3b`.

`probe.py` reopens the pinned zero-isovalue scene, sets the prior bite pose at .20 mm, temporarily routes actual evaluated raw difference, uncut body, and standalone cutter zero surface, and reports connected components and actual Blender loop triangle areas. No changes saved to the input. Final and raw difference have identical defects, hence they predate face labels and inverse coordinate modifiers. Uncut body: 153840 vertices, one component, zero triangles <1e-9 mm². Cutter alone: 67688 vertices, one component, six triangles <1e-9 mm². Two of these near [6,-1,30] mm coincide spatially with the two degenerate triangles in the main body component of the bite. The eight-vertex/12-triangle secondary component is a separate issue near [14.19958,-5.78821,35.00190] mm. Its bounding dimensions are about .00537 × .03070 × .01402 mm, signed volume 2.31009e-6 mm³, far below one .20-mm voxel volume; it occurs near the cutter/outer intersection, not at the degenerate face. This is evidence of a sub-voxel isolated component sensitive to rasterization; not proof that no physical near-tangent sliver exists in exact continuous geometry. Full probe receipt records coordinates and component membership.

## Bounded phase experiment

`build_phase.py` changes only Exact's native grid evaluation group. Apply a single predetermined translation of (.5,.5,.5) times voxel size to BOTH source mesh and cutter before grid conversion. Undo translation on cut and uncut reference isosurfaces. Sample the two signed operand fields in the translated frame; all downstream proximity, original surface attribute transfer, inverse-rest and shading coordinates remain in physical frame. Both GridToMesh isovalues stay exactly zero. No change to physical cutter transform or source vertex data; no component deletion, merging, decimation, epsilon isovalue, or seam tuning. This changes raster sampling, not continuous CSG. Saved `exact-phase.blend` SHA256 `2e31a68dba83e689b55b5599a7f2a13a34a9f3fb08dd09b4eff055c31c108224`; 42 nodes in Exact extraction group; saved whole/Fast. This half-cell phase is our independent design choice, not an author setting or a proof that it is best for all poses.

`deps/qa_phase.py` is the owned prior validator with exactly one change: the reference-distance comparison temporarily routes the new physical-frame uncut reference instead of the untranslated grid isosurface. All existing topology/seed/material/pit/rest/Fast checks and tolerances unchanged. Six independent reopened-scene checks, old Fast vs candidate, 4 requested CPU threads, scripts disabled. Observed results:

| Pose / voxel mm | Exact body vertices | Shared skin/cap edges | Median pit depth loss | Seed contacts | Gate |
|---|---:|---:|---:|---:|---|
| Whole .20 | original stock bypass | n/a | n/a | unchanged Fast | PASS |
| Plane .20 | 105340 | 802 | .1666% | 130/130 | PASS |
| Tilted/deformed .20 | 123638 | 1010 | .6210% | 117/117 | PASS |
| Bite .20 | 161756 | 580 | .7687% | 227/227 | PASS |
| Plane .32 | 41128 | 496 | 4.5972% | 130/130 | PASS |
| Bite .32 | 63108 | 360 | 6.0955% | 227/227 | PASS |

All five cut results: one closed body component, one shared material-edge loop, zero bad valence, zero boundary/wire/over-two-face/inconsistent edges and zero triangles below 1e-9 mm². All 831 retained seed contacts across the five cut states; 474/474 at .20. Every Fast roundtrip and tested named-attribute/geometry hash identical to original Fast. Raw stock and anchor digest unchanged. Worst inverse-rest coordinate error 2.129e-6 mm. All 20480 sampled edge distances match actual physical reference triangles to reported precision. Zero incorrect clear-region face labels in sampled probes. Bite .20 minimum analytic sphere margin -.009931 mm; bite .32 -.010771 mm (faceted sphere/discretization). Not exact continuous sphere intersection. The material boundary is still an approximate classification. For bite .20, main body signed volume changes from 18870.369862 to 18870.274211 mm³ (about .00051%); both the near-zero area triangles and tiny component no longer appear, without deleting output geometry. Previous original negative result preserved. The result cannot establish phase robustness over arbitrary cutter positions, shapes, compound cuts or every voxel size; not rigorous self-intersection or ideal seed exposure evidence. No new render or interactive performance benchmark. Whole does not execute Exact. Rechecked previous integrated control `790dc4adbd9025b56e7833c2cedb8ada83c0e9b738ac294f96889fbb52e0e215`, stock264 `d430ac081f5383148e4f6a6a81f0dfc89fdfc5e8fb7538dd76cf97598398026a`, original zero and Fast baseline SHA256 unchanged. No automatic promotion or main changes. Next: reuse the common rest coordinate and stable anchor contract for independently rebuilt ring vascular field and cut-local cell relief. Do not silently reuse the old atlas generated for a different anchor distribution. Maintain the six-state regression set and explicit failure status for new poses.

## Reproduce

In this experiment directory, put the four pinned owned helpers under `deps/` (included in private evidence archive; repo copies in the previous exact-body and split-surface experiments). Use the original .blend files named above and a fresh output path. No Frucht reference files needed. Check gate booleans, not just exit status.

```sh
B=/path/to/blender
L=/path/to/experiment
A=/path/to/exact-zero.blend
F=/path/to/reference-flesh.blend
D=/path/to/fresh/output
"$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/probe.py" -- "$A" "$D/probe.json"
"$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/build_phase.py" -- "$A" "$D/exact-phase.blend"
for spec in 'whole .20' 'plane .20' 'tilted .20' 'bite .20' 'plane .32' 'bite .32'; do
 set -- $spec
 "$B" -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/deps/qa_phase.py" -- "$F" "$D/exact-phase.blend" "$L/deps/qa_split.py" "$1" "$2" "$D/qa-$1-$2.json"
done
```

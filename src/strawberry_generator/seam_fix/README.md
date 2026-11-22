# Explicit physical blade placement for Generator v1

This branch restores the **original CDT Exact method for tested Generator recipes101/202**, using a visible, physical **+0.001 mm rest-Y blade translation**. It does not repair Blender's Boolean solver or the original exact Y=0 cut. This is a cutter-placement workaround, not a claim of universal seam safety.

[Private scenes, original PNGs and ZIP](https://drive.google.com/drive/folders/1wcZlmCYQZ2hZ6qLhCetdhh8W-lgSoMs2) · [Seed101](https://drive.google.com/file/d/1eWHxWuTkhzZ6bh0ye5DJ0YTcJ2aBWOGc/view) · [Seed202](https://drive.google.com/file/d/1-JWSm728UYm-3zr0z81pOhY1mXhdeTpR/view) · [Six-frame Cycles comparison](https://drive.google.com/file/d/1gQDWkIjjHfdsZiA9gC9_bP5wJJ9YXmhq/view)

## Cause and bounded attempts

The original uncropped meshes have no zero edges, zero render triangles or exactly coincident coordinate groups. Minimum native edges are0.00064482 and0.00064254 model units. In seed101, source vertex8481 lies at physical Y=-1.15472449e-8 model units: its unpitted Y was exactly0; an extremely small pit-field tail moved it just off the nominal cut. The MANIFOLD cap then contains two distinct seam edges whose evaluated endpoint coordinates coincide, producing four zero-area render triangles. Incident face IDs, coordinates, pit mask and nearest anchor are recorded in `causal-report.json`. This supports a near-plane finite-precision intersection/rounding mechanism; it is not evidence of a raw zero edge or an unresolved source T-junction.

Only two targeted alternatives were tested:

1. Native EXACT Boolean solver: rejected. Center cuts yielded187/202 zero polygon faces and open output, for seed101/202 respectively.
2. Keep MANIFOLD; translate the actual common cutter +0.001 mm via `delta_location.y`: accepted for the tested cases. This changes physical geometry of the cut. The requested location/euler remains available, while receipts record the actual evaluated matrix. An oblique plane's normal displacement is the projection of this fixed-axis translation, not necessarily0.001 mm.

No body/seed/curve geometry, atlas or material was edited. No seam weld, epsilon change, centroid fallback, alternate cap overlay or skin change is used. Exact's original `cap_patch` and `make_mesh` code remains unchanged. Native Fast with scripts disabled includes the same physical delta.

## Saved scene and generator behavior

Open either scene in Fast with scripts disabled. Run embedded `TISSUE_ZONES__RUN.py`, then **N → Strawberry Cut → Exact**. The panel labels the physical blade offset. Four native modes, live profile Apply, tissue strengths and the new ARTIST28+264 strand source remain available. The original28+539 diagnostics and539 markers remain distinct from264 achenes.

The existing [single JSON CLI](../README.md#generate-a-fruit) now applies `policy.py`, validates three Fast/Exact poses, then saves Fast. Fresh CLI outputs101/202 reproduce the original PR40 anchor/body digests and vertex counts. It rejects a failed pose; it does not issue a success receipt after catching a geometry failure. Both scene copies in Drive are authenticated PR40 outputs with this policy applied, and were independently reopened after full download.

## Tested geometry and runtime gates

For each population: requested center(0,0,0), translated(-0.26,0,0), oblique(0.08,29,32), all with the declared physical delta. At all six Fast and six Exact cases:

- Zero-length edges, zero-area polygons and zero-area render triangles: **0**. These are separate float64 coordinate metrics, not inferred from topology.
- One connected closed body, positive signed volume; original skin faces, seam edges, pit values and normals unchanged between corresponding Fast/Exact meshes.
- Exact creates real geometric relief; sampled CPU rest/inverse and atlas shader coordinates agree within1e-6 model units. New cap attributes retain physical source coordinates so inverseF is applied once.
- Each population retains264 actual seed/body triangle intersections, exact ARTIST terminal attachments and immutable old diagnostic source buffers/atlas.
- Live A→B→A restores coordinates exactly in this run. Two profile states pass two poses each in Fast/Exact; embedded double-run, callback translation/rotation, error fallback and save/reopen Fast pass.
- Cross-layer render regression changes profile and knife while WHOLE is selected, then renders MATCHED/FLESH ONLY. Its candidate must equal a freshly prepared control pixel-for-pixel.

124 existing Python tests and3 new Blender physical-metric regression cases pass. The latter distinguish coincident vertices, collinear triangles and very small nonzero triangles; no tolerance is relaxed to obtain zeros.

## Visual result and limits

Six native750×750 Cycles frames,12 samples with denoise, same camera/light/seed. Each seed has matched Fast/Exact uniform-clay images with material bump disabled and one Exact beauty image. Exact clay shows localized geometric relief without the rejected fallback's radial fan artifacts. This is a limited inspection at750px/12samples, not proof against all render artifacts. Waxy skin, coarse pit rims and simple crown remain inherited artistic limitations.

The knife is still freely movable. Arbitrary seeds, profiles and blade planes are **not** guaranteed free of Boolean degeneracy; cancelling the explicit delta can reproduce the original defect. The original runtime safely returns Fast after Exact rebuild errors, but Fast itself is not universally guaranteed clean. A solver/source-tessellation solution for exact prescribed planes remains open. All depths and relief are artistic, not measured histology. Main, PR40 files and live GUI Blender were untouched.

## Reproduce evidence

Run commands from repository root with Blender5.2.2. Private ZIP supplies the authenticated PR40 files; `qa.py` expects their original sibling-worktree path, so adjust the source path when reproducing elsewhere.

```sh
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python src/strawberry_generator/seam_fix/probe.py
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python src/strawberry_generator/seam_fix/probe_bias.py
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python src/strawberry_generator/seam_fix/qa.py -- build/source-seam-v1/seed101.blend build/source-seam-v1/new-101-qa.json
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python src/strawberry_generator/seam_fix/test_metrics.py
python src/strawberry_generator/seam_fix/render_all.py
python src/strawberry_generator/seam_fix/plate.py
```

Evidence JSON pins source/output/PNG hashes and actual matrices. Binary artifacts remain owner-private; only code/docs/quantitative receipts are public.

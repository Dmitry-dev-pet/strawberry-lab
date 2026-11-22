# Rejected Exact fallback experiment — PR40 stays Fast-only

**Not a successful integration. Do not use the candidate scenes as a Generator v1 replacement. No success PR is opened.** This experimental branch records two bounded attempts and the measured reason for rejection. Production generator code, previous assets, main and GUI Blender are unchanged.

[Private negative QA and clay PNGs](https://drive.google.com/drive/folders/1OAe06LrTucOYU0cp8J0Cqh-eYBiokolM).

## Results

| Seed / physical pose | Inherited zero-length seam edges | Inherited zero-area render triangles | Newly degenerate render triangles beyond Fast | Physical-clean result |
| --- | ---: | ---: | ---: | --- |
|101 center|2|4|0|FAIL|
|101 oblique (.08,29,32)|0|0|0|pass at this pose only|
|202 center|0|0|0|pass at this pose only|
|202 oblique (.08,29,32)|0|0|0|pass at this pose only|

Zero-area numbers use float64 cross products on saved vertex coordinates, not BMesh manifoldness. `inherited_zero_area_faces` in the receipt means Fast's native render triangles. Fast has zero degenerate native **polygon** faces at seed101 center, but its tessellation has4 zero-area triangles. The candidate has2 zero-area polygon faces and the SAME4 zero-area render-triangle coordinate multisets. Hence `newly_created_degenerate_faces=0` is not a claim that its physical geometry is clean.

The one actual750px/12sample center clay Fast/Exact pair is visually unacceptable: Exact shows strong radial fan/ridge artifacts. Curves are hidden and the gray material has no bump. The artifacts arise from the centroid-refined original fan layout; they are not evidence of plausible tissue. This independent visual failure rejects the second attempt even though BMesh closure, connectedness and positive volume pass.

## Two attempts, then stop

1. Retain the old CDT path and its collision check. On exactly `The triangulator merged distinct seam vertices`, rebuild BMesh from the untouched native Boolean, triangulate cap faces, then insert only interior centroid vertices. Keep every original seam vertex and edge. This stopped on `Fallback produced a degenerate triangle` for seed101 center.
2. Retain inherited boundary-only degeneracies without refining them. Strictly reject a degenerate NEW Steiner-child triangle. This passes legacy topology/coordinate checks, but retains the collapsed native boundary and produces the unacceptable clay fan artifacts. It is rejected, not promoted.

No seam vertex was welded, split or moved. CDT epsilon and original integrity checks were not relaxed. The first and second candidates are retained only as private diagnostics. Original seed populations, pits, networks, atlas and the physical knife were not changed to evade the failure.

`topology_qa.py` contains the reused skin/seam/inverse/controls/callback/save/error-fallback checks; those passed for the second candidate. They do NOT certify physical mesh cleanliness. The authoritative final outcome is `audit_degeneracy.py` / `evidence.json` plus visual FAIL. Existing124 base tests were not rerun after rejection; this branch does not claim release validation or a new passing seam regression.

## Reproduce the negative evidence

With the owned PR40 input scenes at the sibling path authenticated in `build.py`, use Blender5.2.2 headlessly:

```sh
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python src/strawberry_generator/exact/build.py
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python src/strawberry_generator/exact/audit_degeneracy.py
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python src/strawberry_generator/exact/render.py -- build/generator-exact-v2/seed101.blend fast clay cut build/generator-exact-v2/seed101-fast-clay-isolated.png
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python src/strawberry_generator/exact/render.py -- build/generator-exact-v2/seed101.blend exact clay cut build/generator-exact-v2/seed101-exact-clay-isolated.png
```

The experimental builder refuses existing outputs. Its candidate embedded runtime is intentionally test-enabled; private filenames mark it REJECTED. The public PR40 generator and its explicit Fast-only guard remain unchanged. No third algorithm or geometry iteration was attempted.

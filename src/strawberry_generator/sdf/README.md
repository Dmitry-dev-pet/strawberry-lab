# Technical SDF vertical slice — lookdev pending

One editable seed101 fruit from PR40, one native Geometry Nodes engine: **Mesh to SDF Grid → SDF Grid Boolean difference → Grid to Mesh**. Whole, moving/rotating halfspace and spherical bite work after reopening with scripts disabled. No Mesh Boolean, Exact CDT, physical blade bias or commercial/GPL Frucht code is used.

[Owner-private artifacts](https://drive.google.com/drive/folders/1xePLbBZM2Hd6h33yGHgBYcWT9Ar2kHq3) · [Editable scene](https://drive.google.com/file/d/1m61GaulIcYGaGiS5P1Xh5jfPdMiorwWn/view)

Follows the owner's [accepted main ADR](https://github.com/Dmitry-dev-pet/strawberry-lab/blob/main/docs/architecture-decision-2026-11-22-sdf-visual-first.md), Issue8 decision7083933344 and our own M1c/M1d principles. Stacked on PR40, not on PR41; main and previous artifacts remain untouched.

[Six native Cycles frames](https://drive.google.com/file/d/1d16Je-yuC7BXDCMjRJOxStQfYNzj8xw1/view) · [Private ZIP](https://drive.google.com/file/d/1BGpdfZJvASrTAzt4l9Kf9r5m-Ns4rzxW/view)

## Use / reproduce

Select **Receptacle | canonical PR29 hull → Object Custom Properties**:

- `sdf_mode`:0 whole,1 plane,2 sphere.
- `sdf_voxel_mm`: actual millimetres; default0.20. GN divides by22.22222276 mm per Blender unit.
- Move/rotate **SDF | editable plane halfspace** in Object Mode. Its local Y=0 face is the physical cutting plane; no offset. Keep its finite box large enough to cover the fruit.
- Move/uniform-scale **SDF | editable sphere bite** in Object Mode. Do not edit cutter mesh shapes or nonuniform-scale the sphere: solid center masks assume these defined cutter primitives.

Native drivers and nodes perform updates; no embedded Python/add-on is required. One `SDF | live` View Layer replaces legacy four-layer/Exact UI in this bounded slice. The nonlinear source profile is fixed. Legacy Apply Profile/Exact scripts were removed deliberately; this does not restore those features.

With Blender5.2.2, repository root and the authenticated PR40 input supplied in the private ZIP:

```sh
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python src/strawberry_generator/sdf/build.py -- --input inputs/pr40-seed101.blend --out build/my-sdf/strawberry-sdf.blend
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python src/strawberry_generator/sdf/test_contract.py -- build/my-sdf/strawberry-sdf.blend
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python src/strawberry_generator/sdf/qa.py -- build/my-sdf/strawberry-sdf.blend build/my-sdf/reopened-sdf-qa.json --source inputs/pr40-seed101.blend
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python src/strawberry_generator/sdf/render.py -- build/my-sdf/strawberry-sdf.blend plane build/my-sdf/plane.png
```

Build refuses a different input SHA or existing output. The reopened-scene QA requires an explicit `--source` pointing to the hash-pinned PR40 `.blend`; it never reads a sibling worktree and refuses a mismatched source SHA or an existing receipt path. Source and render receipts pin hashes; Blender binary serialization itself is not promised deterministic.

## Fields, organs and policy

The single physical PR40 hull is the GN input; no second fruit shell is overlaid. Its independently generated264 seed IDs, physical pits and original geometry are preserved as source. Original28+539 diagnostic curves/539 markers and the distinct ARTIST28+264 seed-linked graph remain stored unchanged and hidden; neither is a new measured anatomical model.

After Grid→Mesh, GN computes true `sdf_rest_position = inverseF(physical_position)`. Both skin and cap consume that same attribute. The existing packed Non-Color150³ RGB atlas is **inherited/template-derived artistic data**, not newly synthesized cells. The previous shader inverse is bypassed to avoid applying inverseF twice. Three cut-vertex rest/atlas probes per cut type per voxel pass1e-6 model-unit inverse tolerance. Vertex-interpolated rest coordinates approximate inverseF inside polygons; no GPU radiometric equality claim is made.

The separate cut material is assigned by active-cutter proximity within1.7voxels; three restrained 3D Voronoi layers drive shader bump/roughness with coat/SSS. This is **shader microtexture, not geometric cell walls or Exact microrelief**. Source `achene_pit` shading mask is nearest-surface transferred after remeshing.

Seeds, eight sepals and stem use **whole-solid CENTER culling** against the same plane/sphere transforms. Boundary-crossing seeds/crown parts are not physically intersected and can protrude across a cut. Native visible achene counts: whole264, plane133, oblique118, bite233. This limitation is intentional, not solid clipping.

## Measured result

Engineering gates pass for whole, center plane, oblique plane and sphere at both voxel sizes, plus moved sphere. All8 states: one connected closed body, positive volume,0 nonmanifold edges,0 zero-length edges,0 zero-area render triangles. The downloaded scene was reopened with scripts disabled and repeated these gates. All264 actual seed meshes intersect the fine whole SDF body (52–84 triangle pairs each).

| Whole body |0.32mm voxel|0.20mm voxel|
|---|---:|---:|
| Vertices |91,046|233,258|
| Median pit depth along transformed anchor normal |0.146mm|0.167mm|
| Source median before SDF |0.177mm|0.177mm|
| Positive pit depths |264/264|264/264|

The fine remesh loses about5.4% of the median pit depth; coarse loses17.2%. This is a ray-based anchor statistic, not a complete geometric-error bound. Fine whole/plane/oblique/bite evaluation took approximately0.8–2.0s, including depsgraph update and mesh copy, on this Mac. Sequential QA process peak RSS reached1.12GiB including input data/atlas; it is not isolated SDF memory or VRAM. This is not realtime.

124 prior tests +4 saved-SDF graph/unit/field-binding regressions pass. Six genuine900×900 Cycles PNGs use16 samples and denoise: whole, plane, sphere, oblique, macro and coarse plane. Main states share camera/light/seed; macro changes camera only. Fine/coarse plane uses the same pose/camera. One lookdev correction increased sphere tessellation and softened coat after the first sphere frame showed broad faceted highlights.

## Visual acceptance: FAIL versus target; lookdev pending

The private comparison uses authenticated owner video frames04s/10s, with different camera/lighting and compression, so it is qualitative. Our whole skin is waxy/pink and crown simplified; the template cut has a broad smooth pith column, blurred tissue detail and little convincing wet microstructure compared with the reference. A thin pale bite/cut rim remains. The denser sphere removes the first frame's conspicuous angular highlight patches, but this is **not Frucht-level fidelity** and does not close Issue8.

This is a working technical SDF slice, not a completed general fruit generator or accepted photoreal result. Arbitrary cutter poses, profile regeneration, radius-aware seed clipping, dynamic diagnostic-network cuts and detailed geometric cut microstructure remain outside this delivery. No further geometry/lookdev iterations are part of this milestone. Reference images remain owner-private; public GitHub contains only our code, compact numbers and SHA.

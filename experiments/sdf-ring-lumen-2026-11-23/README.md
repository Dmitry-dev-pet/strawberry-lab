# Independent ring topology and medullary lumen — two controlled experiments

23 November 2026. Research continuation of Draft PR50, using the audit in `experiments/sdf-vascular-topology-audit-2026-11-23/README.md`. A is the shadow-corrected scene SHA256 `361696819fd44733d560e3f59b101cd11f59862e7ebd7b7f83ce94fd07909963`; the failed pigment, tint and SSS candidates are not the input. B (ring) and C (cavity) are independently derived from A, not stacked. Original ARTIST models: no author code, assets, numerical presets or node templates copied. No botanical calibration, visual acceptance or main merge.

## B: ring-oriented vascular scaffold

28 bent longitudinal carriers fitted to a kernel-smoothed radial envelope of the 264 existing rest-space anchors, with variable width, azimuthal modulation and two tapered ends. The nominal ring radius peaks at z=28.96 mm (6.46 mm) in graph coordinates, from 0.36 mm at z=2.8 to 1.34 mm at z=46.5. Each seed ID has a continuous tapered branch joined exactly to a carrier sample, endpoint recessed 0.95 mm toward the fruit center. No central trunk or secondary twigs. 292 segments, 19,976 sampled points; nearest outward normal against the existing rest-hull surface places all samples inside (minimum signed margin 0.562 mm). This is a sampled nearest-normal check, not proof of containment of the entire Gaussian support or all continuous curves. Deterministic graph generation was repeated with identical points and widths. Reuse the original PR50 sampler, same grid bounds, 192³ R and H, max-combined variable-width Gaussian dabs. H>=R; 35,999 dabs for each, none completely outside the grid. Third channel is a separate finite normalized signed radial position relative to the nominal elliptical ring, stored but **not used** in relief or material in this A/B. Initial B-channel float32 sine at t=1 yielded nonfinite values; rejected and fixed using float64 and clamped nonnegative sine; prior invalid build log preserved. New field and scene hashes are in `ring-B.json`. Original 150³ pigment atlas, geometry node links, source meshes, material/shadow settings unchanged by construction. Only the existing owned vascular atlas pixels and provenance property replaced.

Independent saved-scene QA (`ring-qa-*.json`): 3 pairs (whole, plane, bite), 0.32 mm, all PASS: exact A coords/topology and juice receipt match, B topology identical to A, zero nonmanifold edges/degenerate triangles, positive volume. Whole identical; cap shifts up to 0.1253 mm plane, 0.1123 mm bite; skin-only and seam displacement zero. 512 cap samples for each cut checked against NumPy trilinear samples, max error <5.6e-5. Rest positions exact. Existing juice verifier confirms source cap-interior membership, equations and all liquid boundary vertices tucked below tissue. No new fine-voxel, arbitrary-pose, exhaustive self-intersection or seed/calyx tests. R/H support coverage and widths change, so this isolates the new vascular field as a whole, not an experiment isolating only the centreline.

## C: independently authored cavity

Starting from A, a separate 3,010-vertex closed irregular tapered cavity mesh (nominal 15 mm longitudinal length; 2.2 / 1.5 mm semi-axes) is converted to an SDF at the original voxel size, subtracted from the flesh grid **before** the user cutter and the whole/cut branch selection. The hidden cutter mesh has original volume 104.45 mm³; all its vertices have nearest-normal hull margin >=11.89 mm. Separate pinkish moist-wall ARTIST material assigned by distance to the lumen vs user cutter. Existing cap-only cell and juice paths exclude the cavity wall. This does not implement tissue bridges, an editable cavity on/off gain, or a measured biological lumen. It is an isolated geometry-plus-wall-material intervention, not the ring candidate combined with cavity.

Independent saved-scene QA (`lumen-qa-*.json`): whole, plane, bite at 0.32 mm. Whole exact exterior coordinate set (91,046 original vertices), exterior signed volume unchanged, new internal boundary signed volume -102.671 mm³ and 2,028 wall faces. Plane opens cavity; the evaluated body has one positively oriented connected component, 3,708 wall faces. Bite misses cavity; two boundary components, one negative internal cavity, 8,112 wall faces after refinement. All three: zero nonmanifold/inconsistent winding edges, zero degenerate triangles, one positive-volume component; juice boundary/clearance checks PASS, no juice on whole. Wall excluded from cap interior. Initial combined plane A/B command timed out; new B-only run used the earlier independent A receipt from ring QA, as did bite. Whole A/B evaluated directly. No fine-voxel, arbitrary cutter, general self-intersection or fresh seed QA.

## Visual evidence and next decision

Two new actual Cycles CPU renders (plane B and C; 480x480, 8 samples, seed 1729, 0.32 mm) compared against archived SHA-verified A, same camera/gains and render settings; A was not rerendered. `render-comparison.json` records exact receipts. Ring changed 16.23% of pixels above 2/255, cavity 1.63%; these are difference measurements, not perceptual quality scores. B gives more grain/less flatness in the pale central region, but the wide pale atlas-driven pith remains. C introduces a real cavity but it looks like a smooth pink pocket. No demonstrated Frucht parity. Retain both as independent research. Do not merge on geometric PASS. Ring-relative pigment mapping using existing independent B field and cavity wall/bridge study can be tested next, separately. Bite and whole have geometry QA only, no new renders. Do not claim combined scene tested.

## Reproduction and evidence layout

Blender 5.2.4 LTS build cd5dc428cce1, CPU 4 threads, scripts disabled. Use the pinned shadow-corrected scene (`optical-lab/juice-shadow-transparent.blend`). Put the previous original helper files in `ROOT/vascular-lab/qa_vascular_relief.py`, `ROOT/juice-lab/qa_juice_surface.py`, and `ROOT/optical-lab/render_optical.py` (their exact source is in earlier PR50 experiment folders). Put the three previous optical QA receipts and archived plane-B.png/json in `ROOT/optical-lab/`. The `ROOT/ring-lab` and `ROOT/lumen-lab` output directories must exist. Run from this experiment directory, using fresh output paths and absolute paths for Blender arguments:

```
B=/absolute/path/to/blender
R=/absolute/path/to/ROOT
S=$R/optical-lab/juice-shadow-transparent.blend
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python build_ring.py -- "$S" "$R/ring-lab/ring-B.blend" "$R/ring-lab/ring-field.npz"
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python build_lumen.py -- "$S" "$R/lumen-lab/lumen-B.blend"
for pose in whole plane bite; do
  $B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python qa_ring.py -- "$S" "$R/ring-lab/ring-B.blend" "$R/ring-lab/ring-field.npz" "$pose" "$R/optical-lab" "$R" "$R/ring-lab/qa-$pose.json"
  $B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python qa_lumen.py -- "$S" "$R/lumen-lab/lumen-B.blend" "$pose" "$R" "$R/lumen-lab/qa-$pose.json"
done
for pair in ring lumen; do
  $B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$R/optical-lab/render_optical.py" -- "$R/$pair-lab/$pair-B.blend" "$R/juice-lab/qa_juice_surface.py" plane B "$R/$pair-lab/plane-B.png"
done
python compare.py "$R/optical-lab" "$R/ring-lab" "$R/lumen-lab" "$R/comparison"
```
The renderer's B flag identifies shadow visibility false for both candidates, not a shared scene. File hashes of saved scenes may depend on save path, so inspect QA and field hashes instead of assuming byte-identical Blender rebuilds. Private binary scenes, numerical grid and comparison PNG are archived on owner Drive. Public GitHub contains only original source, compact evidence and prose.

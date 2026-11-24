# Integrated Strawberry Lab research scene — 24 Nov 2026

Owner-authorized bounded integration of previously checked PR50 research. **Technical PASS at three sampled poses, visual target FAIL. No main merge or claim of Frucht parity.** All fruit model dimensions and optical parameters in this branch are ARTIST unless separately evidenced. No Frucht source, nodes, assets, or numerical presets copied.

## Integrated components and exact inputs
- Start with the previous independent ring-pigment scene SHA256 `2d540447b36063408808995079295d2c6f3045835e4362216fbc48c6ca78b23d`. It contains the native SDF cutter, conforming cell relief, the 292-segment/264-anchor ring vascular field (192³), stored ring-relative coordinate, separate juice patches and the positive shadow-visibility correction.
- Run the exact earlier **owned** `build_lumen.py` and `build_lumen_protrusions.py` install functions against this scene, checking their Git blob SHAs `c083b79ee28665d3372117b398c3e6d9f598e461` and `7d6e24adabfaabf5d6e7fb47292e095e014d77b5`. No new geometry/optical tuning; cavity with 18 generated attachments subtracts from tissue BEFORE user cutter. Verify exactly one effective cavity input to the tissue difference to avoid the previously observed multi-input union bug.
- Integrated saved scene SHA256 `790dc4adbd9025b56e7833c2cedb8ada83c0e9b738ac294f96889fbb52e0e215`. Defaults: whole, 0.32 mm, cell/detail/vascular/juice gains enabled; ring-relative diagnostic pigment gain OFF because it failed visual acceptance. Material's `SL Ring Pigment | A/B gain` value node can switch to 1. This is not an approved product default.

## Independent evaluated QA
Reopened saved scene with scripts disabled in Blender 5.2.4 LTS (cd5dc428cce1, runtime archive 17 part SHAs and full SHA validated). Three separate 0.32 mm states pass: whole, longitudinal plane, side sphere bite. All body boundary edges manifold and consistently oriented; zero degenerate render triangles; one positive-volume boundary component. Whole and bite have an additional negative-oriented enclosed cavity boundary; plane opens the cavity. Whole coordinates and triangle indices exactly equal the previously checked protrusion scene (93,370 vertices); internal boundary volume -98.365858 mm³. On cut poses 256 sampled cap vertices each independently match NumPy trilinear R/H/B fields, worst error 4.574e-5. Existing independent juice checks confirm cap-interior membership, normal/position clearance equations, buried boundary vertices, no over-two-face edges or degenerate triangles; whole has no juice. Separate wall material excluded from cap interior. See qa-*.json. This is not an exhaustive test of arbitrary cutter transforms, self-intersection, protrusion survival at fine resolution, or seed/calyx intersection. The integrated scene inherits PR47-era center-based seed culling from PR50; does not integrate the unmerged PR48 seed guard. The earlier 17/18 protrusion probe result remains historical (the entire whole mesh matches); no new independent per-protrusion probe test. No fresh 0.20 mm or performance acceptance.

## Visual evidence
Five new original CPU Cycles frames (whole, plane, bite, macro, and alternate ring-pigment-on plane), 480², 8 samples, seed 1729, fixed lighting, 0.32 mm. Per-image JSON receipts pin source SHA, settings and PNG hashes. Plane A/B uses identical camera and settings except pigment gain. Gain 1 changes 27.4518% pixels >2/255 and 23.9544% >10/255; this is change detection, not quality. Gain 1 produces a more sharply bounded pale band and salmon color, not accepted, left off by default.

Direct private comparison with the actual owner's reference MP4 (SHA256 `cbe17cfd0ffa0e7697462892a28bd339e0b9666418276287499c49ca6bae684e`, 37.98 s, 1080×1350, 30 fps), decoded at 4.0, 10.5, 18.5 s. Different cameras, lights, fruit shape and bite counts; qualitative only, no pixel similarity or numerical fidelity claim. Original reference has more natural elongated irregular exterior, deep wet seed pits, stronger surface reflections with fine variation, redder flesh, clearer pale tapered vascular traces, and irregular torn multi-bite pulp. Integrated model: smooth waxy pink skin, broad pale core, small smooth cavity with rounded attached projections, overly uniform relief, smooth circular bite rim and weaker wet effect. **Visual acceptance not met.** Preserve this integrated scene as the reference for subsequent visual improvements, not another branch of disconnected parameter sweeps. Prioritize exterior profile/pits, realistic region-specific cap color and nonperiodic bite shape with a real-cutter seed guard; evaluate actual matched shape and lighting. No new modification to main.

## Reproduction
Use paths to exact pinned previous artifacts; no third-party implementation. All CLI runs with `--disable-autoexec` and CPU only. Prior helper is `experiments/sdf-juice-surface-2026-11-23/qa_juice_surface.py` from the archived original source (passed existing checks).

```sh
B=/path/to/blender
L=/path/to/this/experiment
R=/path/to/repo
S=/path/to/ring-pigment.blend
H=$R/experiments/sdf-juice-surface-2026-11-23/qa_juice_surface.py
F=/path/to/ring-field.npz
P=$R/experiments/sdf-lumen-protrusions-ring-pigment-2026-11-24/lumen-qa-whole.json
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/build_integrated.py" -- "$S" "$R/experiments/sdf-ring-lumen-2026-11-23/build_lumen.py" "$R/experiments/sdf-lumen-protrusions-ring-pigment-2026-11-24/build_lumen_protrusions.py" "$L/integrated.blend"
for pose in whole plane bite; do
  $B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/qa_integrated.py" -- "$L/integrated.blend" "$pose" .32 "$H" "$F" "$P" "$L/qa-$pose.json"
done
for shot in whole plane bite macro; do
  $B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/render_integrated.py" -- "$L/integrated.blend" "$H" "$shot" 0 "$L/$shot-A.png"
done
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python "$L/render_integrated.py" -- "$L/integrated.blend" "$H" plane 1 "$L/plane-B.png"
```
Use fresh output paths. Saved Blender binary serialization can depend on path. Original reference pixels are not part of this evidence archive or public GitHub; private comparison is separate. Owner-private Drive stores the scene and archive; GitHub stores only original source and compact evidence. 

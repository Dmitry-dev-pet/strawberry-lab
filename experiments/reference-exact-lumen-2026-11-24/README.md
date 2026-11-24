# Exact: internal cavity and attached tissue — 24 November 2026

Draft PR50 continuation from `25f26bc460b573369407a57e54e2faace118e62c`. Independent ARTIST geometry, not a reconstruction of the unavailable commercial Frucht tree. Previous exact tissue scene is immutable: SHA256 `95b40e781ee948f9496ba5277ac08be0bb305435de1b498031b51c669be1b5c2`. Native Blender 5.2.4 LTS `cd5dc428cce1` with scripts disabled when reopening.

## Construction

Reuses the geometric principle of our own earlier ring-lumen experiment, with a deterministic irregular closed lumen in millimetres (15 mm long, neutral centre z=30 mm, nominal radii 2.2/1.5 mm). Eighteen closed tapered tissue source solids cross the cavity boundary. Their roots and ends were selected with triangle-ray and signed-nearest-surface probes. Original source meshes have 3010 and 3456 vertices, respectively; all source edges manifold, positive signed volumes, minimum sampled distance inside outer hull 9.8406 mm. These dimensions and seed 73191 are independent artistic choices, not biological measurements or Frucht parameters. Both sources use the existing common forward shape map. Cavity and protrusions receive the same positive half-voxel translation as body and cutter, with zero isovalue. The effective cavity is cavity minus protrusion solids. It is removed from the body *before* the user cutter. There are no separately joined tissue islands in the displayed result. Outer uncut reference, existing vascular volume and sampler remain intact. Three signed operands determine outer skin, user cap and cavity wall classification; cavity walls and shared boundaries are excluded from cell displacement. Existing tissue_gain is left at zero by default. Fast and whole display routing remain unchanged: the cavity is evaluated on the Exact cut path only. No cavity display/processing in Fast, no adaptive refinement, no juice or production shading in this experiment.

## Measured results

Six saved-scene states compared with pinned baseline, scripts disabled. Five cut states all pass: same set of actual skin triangles by coordinates (not just vertex counts), same raw stock, same seed mesh, same Fast before/after. Gain zero and gain one have zero open, inconsistent, wire/over-two-face edges and degenerate triangles. One positive connected body in every cut. On both bites the interior is a separate negative-oriented *boundary of the enclosed void*, not a detached positive solid. The plane opens the cavity. All 831 retained seed solids contacted skin by triangle BVH; 13,089 wall vertex observations (and 3,744 cap-boundary observations, including skin/wall interfaces) remain fixed at gain one. Cavity wall labels agree with the sampled three signed operands and material indices. Vascular and rest-coordinate attributes unchanged between relief gains. Whole test verifies the original display bypass, not whole-body interior geometry. No exhaustive pose, self-intersection, biological or performance proof.

| Pose | Voxel mm | Wall vertices | Seed contacts | Gate |
| --- | --- | ---: | --- | --- |
| whole (display bypass) | .20 | — | unchanged | PASS |
| plane | .20 | 2991 | 130/130 | PASS |
| tilted + deformed | .20 | 562 | 117/117 | PASS |
| bite | .20 | 6042 | 227/227 | PASS |
| plane | .32 | 1180 | 130/130 | PASS |
| bite | .32 | 2314 | 227/227 | PASS |

Closed bite cavity boundary signed volume: -99.4146 mm³ at .20, -98.3477 mm³ at .32. Independent source-ring centre probe: all 18 sites have at least one interior sample retained as tissue at both resolutions, 96/96 sampled interior locations at .20 and 86/96 at .32. Endpoint probes: all 18 original end-cap centres lie outside the sampled reconstructed material (shortening/rounding from discretization; approximately 0.0035–0.0632 mm at .20, 0.0159–0.1808 mm at .32 by nearest wall signed-normal probe). No claim of complete tip retention. These are sampled local occupancy measurements, not a continuous shape or attachment proof. Initial unit-scale exact-equality assertion, ambiguous node-label lookup and validator import path were corrected; first two failed builder logs retained. Results are independent of visual acceptance.

## Reproduce

Use original `exact-tissue.blend` (pinned SHA above). For QA and render place the unchanged `build_split.py`, `qa_split.py` from the prior tissue evidence under `deps/` beside scripts (included in private evidence archive). Use Blender 5.2.4 and fresh output paths.

```sh
blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python build_lumen.py -- exact-tissue.blend exact-lumen.blend
for spec in 'whole .20' 'plane .20' 'tilted .20' 'bite .20' 'plane .32' 'bite .32'; do
  set -- $spec
  blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python qa_lumen.py -- exact-tissue.blend exact-lumen.blend "$1" "$2" "qa-$1-$2.json"
done
blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python probe_protrusions.py -- exact-lumen.blend protrusion-probe.json
for gain in 0 1; do
  blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python render_lumen.py -- exact-lumen.blend plane "$gain" "plane-$gain.png"
done
```

This is an Exact-only technical milestone; continue with cap-local adaptive subdivision after reviewing the diagnostic geometry. Do not merge into main based on these checks alone.

## Diagnostic render

`comparison.png` juxtaposes the pinned earlier plane gain-zero diagnostic image and two newly rendered 700×700 Blender Workbench images, same plane/camera/voxel settings, gain zero and gain one. This is actual geometry, not ImageGen. The cavity and wall-attached rounded projections are visible; existing cell relief still looks textile-like. The small elongated void is an ARTIST model, not a measured strawberry interior. Visual acceptance pending. EGL warnings did not prevent completed image files. `plane-0.json` and `plane-1.json` record the new image hashes and camera settings.

# Optical audit — PR50 juice shadow-only control

23 November 2026. Independent comparison with the owner-provided Frucht Free Kiwi 0.4.3 archive. Geometry and materials intentionally unchanged. This is a positive local optical correction for tested poses, not visual parity with Frucht and not physically validated juice.

## Evidence from accessible reference
Archive SHA-256 `aaa218470ab068ed1cb806308d9a4da1d43fd5d9e3de30f6486ac7d204787877` verified from local bytes. The complete commercial strawberry material is not available. `daten/zellen_saft.json` contains the `saft_material` and `saft_wasser` shader templates from a strawberry scene, and a partial `fleisch_werte` socket inventory; `reissbrett.py` includes later optical adjustment routines. No author code, node tree, template, presets or assets are included here.

| Channel | Accessible reference evidence | Actual PR50 scene (reopened in Blender) |
|---|---|---|
| Liquid shadow rays | `saft_wasser`: Light Path shadow-ray output selects transparent rather than dielectric shader | Juice material directly outputs transmissive Principled; object shadow visibility enabled |
| Liquid color | `saft_wasser`: liquid height drives tint strength; `reissbrett.py` also adjusts water settings | Constant warm tint |
| Liquid roughness | Template value lower than our fixed roughness; additional author tuning is present | 0.13, fixed |
| Flesh optics | `fleisch_werte` and `reissbrett.py`: cell pigment/size/brightness controls, differentiated vascular and radial regions, spatial scattering scale and separate rim color controls | 82-node cap shader; base color through inherited 150-cubed atlas, constant SSS weight 0.08 and scale 0.012; roughness and bump driven by three rest-space Voronoi edge fields, no direct current dome/vascular attributes in that material |

These are verified fragment-level observations, not a complete commercial material audit. The original author's graph and values are not transplanted. Directly inspect the source archive privately to reproduce the reference observations. `audit_own_materials.py` inspects only our own scene.

## Hypothesis and implementation
The open intersecting juice interface may cast artificial dark shadows. Test that mechanism independently: set only the separate juice object's Cycles shadow visibility to false. This uses Blender's object ray-visibility mechanism rather than importing or rebuilding the author's graph. This is a deliberate optical approximation; it does not establish physically correct refraction/caustics. The existing Principled material, all node groups, fruit, juice geometry, camera, illumination and cutter remain as before. No additional parameter sweep.

Source input `juice-ab.blend` SHA-256 `2fcc5a8e65273d3ac0f633f887e4f5522da9642c375f5d4499e891bc2889d394`. Output `juice-shadow-transparent.blend` SHA-256 `361696819fd44733d560e3f59b101cd11f59862e7ebd7b7f83ce94fd07909963`.

## Reproduce (Blender 5.2.4 LTS, CPU)
Use the pinned PR50 juice scene, the preceding `experiments/sdf-juice-surface-2026-11-23/qa_juice_surface.py` and its saved `qa-plane.json`, `qa-bite.json`, `qa-whole.json` in one directory. In each command use absolute paths and a nonexistent output path. Autoexec disabled.

```
B=/path/to/blender
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python build_optical.py -- /path/juice-ab.blend /path/juice-shadow-transparent.blend
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python qa_optical.py -- /path/juice-ab.blend /path/juice-shadow-transparent.blend /path/qa_juice_surface.py plane /path/new-qa-plane.json
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python render_optical.py -- /path/juice-shadow-transparent.blend /path/qa_juice_surface.py plane B /path/new-plane-B.png
```
Repeat QA for bite and whole, rendering for macro and bite. Variant A is the original scene with the original visibility, and can also be rendered using `render_optical.py ... plane A ...`. Existing A frames in this report are the preceding archive's verified original Juice Surface B frames, not newly rendered; checksums, camera matrices, voxel, gains, samples, seed and resolution agree with the new images. CPU 480×480, 8 samples, seed 1729, four threads. `render-comparison.json` records pixel changes, not a perceptual fidelity score. The saved scene remains default whole/off, as input.

## Independent QA and visual outcome
- 3/3 reopened-scene pose checks at 0.32 mm (whole, plane, bite). Body coordinate and triangle-index SHA exactly match prior saved QA. Liquid coordinate SHA, independently compared triangle-index SHA, topology counts and measured contact/clearance diagnostics match. Whole has zero liquid faces. The 12 material/group trees have identical audited node names/types, socket values, selected properties and link endpoints; every object's audited ray visibility matches except juice shadow visibility. This is not an exhaustive all-property/mesh self-intersection audit or a fine voxel test.
- Three new original Cycles frames: >2/255 RGB change plane 11.12%, macro 11.26%, bite 9.48%. >10/255: 6.29%, 6.36%, 4.92%. The dark mottled areas on plane and macro noticeably diminish. Bite changes less but looks smoother/brighter. Thus the suspected shadow mechanism contributes to the artifact; there may be other causes. The oversized pale core, uniform tissue and smooth bowl-shaped bite remain. No full author parity or owner acceptance.
- Preserve this as a candidate optical correction in Draft PR50; no main merge. Next compare height-dependent liquid tint versus fixed tint independently, then spatially differentiated flesh optics (the old constant SSS-only tests failed). Keep geometry frozen and retain a matched control. Do not treat author-specific values as measured fruit properties.

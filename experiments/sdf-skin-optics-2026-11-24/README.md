# Skin optics — bounded spatial gloss experiment (2026-11-24)

**Research candidate; no visual acceptance or merge.** Control A is the integrated PR50 scene, SHA-256 `790dc4adbd9025b56e7833c2cedb8ada83c0e9b738ac294f96889fbb52e0e215`. Candidate B `skin-B.blend` SHA-256 `00e47d77536886a7770d6aa01bec06c6ff3336073b41c86485e637ec728a11d7`. All values ARTIST; no Frucht source or assets copied.

## Mechanism
16 original shader nodes change only the existing skin Principled Roughness and Coat Weight links. Reuse `achene_pit` (smootherstep 0.08–0.70), existing shoulder fade (normalized by 0.60), and existing ripening noise (coat variation 0.055–0.225). The maximum of pit and shoulder masks reduces coat contribution by up to 93% and adds up to 0.14 to original roughness. `SL Skin Optics | A/B gain` allows 0 = original input equations, 1 = candidate. No new geometry, bump, color, scattering, seed placement, cutter, or internal-field changes. B is saved separately with gain 1; integrated A is unchanged.

## Verification
Blender 5.2.4 LTS build cd5dc428cce1, CPU, autoexec disabled. Three independent saved-scene A/B comparisons at 0.32 mm (whole/plane/bite) PASS: exact evaluated local vertex coordinates, triangle indices, material indices, object matrices, and specified named spatial attributes for 275 objects (body, liquid, 264 achenes, 8 sepals, pedicel). 18 material and Geometry Nodes trees compared: other trees unchanged by audited inputs/outputs/properties/links, original skin nodes identical, only intended links changed. Two packed images match. This is regression equality, not new exhaustive manifold, seed clipping or fine-resolution QA.

Four final native Cycles images, 640x640, 16 samples, seed 1729: whole A/B and close-up A/B (orthographic scale 1.05). Whole image delta >2/255: 6.6521%; close-up: 15.5466%; >10/255: 0.5107% and 0.2935%. Initial two attempts at macro framing retained original orthographic scale, so excluded from final comparison and archive. Camera transform and orthographic scale are matched within final pairs. Visual effect is modest: localized reflections change but exterior remains smooth/waxy with shallow-looking pits. **Visual target not met.** Preserve as negative/limited control, not accepted product default. Next isolate pit-depth preservation and seed-seat geometry; avoid further gloss-only parameter sweeps.

## Reproduce
Use pinned integrated scene and new output paths, Blender CLI `-b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python`.

```sh
B=/path/to/blender
S=/path/to/integrated.blend
D=/path/to/new/output
$B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python build_skin.py -- "$S" "$D/skin-B.blend"
for pose in whole plane bite; do
  $B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python qa_skin.py -- "$S" "$D/skin-B.blend" "$pose" "$D/qa-$pose.json"
done
for shot in whole macro; do
  $B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python render_skin.py -- "$S" "$shot" "$D/$shot-A.png"
  $B -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python render_skin.py -- "$D/skin-B.blend" "$shot" "$D/$shot-B.png"
done
```
Original whole receipts precede the final addition of camera-type/scale metadata to the renderer; the image settings did not change. Final macro files are named `detail-A/B` in archive. Private binary/PNG evidence stays on owner's Drive. GitHub stores original source and compact evidence only.

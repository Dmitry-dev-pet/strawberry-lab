# Exact: coordinated skin and achene materials — 24 November 2026

Continuation of draft PR50 at `9ec07e3c55e28e6d9f766a975e58d142e20b4c82`. Source exact-pigment.blend SHA256 `267bdaa85d806f383e24875be46f8a056a2841574819776d734509784ffe0915`; candidate exact-exterior.blend SHA256 `d8f86ac4a3fbe69d34ae43a6410583c16c6ddc7d8805886bc28d65d7ed27974a`. Blender 5.2.4 LTS cd5dc428cce1. Independent ARTIST implementation, no commercial author code, graphs, assets, images or parameter sets copied. Main unchanged.

## Source-grounded design

Reopened owner-provided Free Kiwi archive SHA256 `aaa218470ab068ed1cb806308d9a4da1d43fd5d9e3de30f6486ac7d204787877`, inspected `ordnen_texte.py:85–87,102,137–143,158,161–163,171–177` and `farbe.py:8–10`. Descriptions support large ripe-colour patches, speckles, lighter stalk, organic relief and waxy wet gloss, local pit gloss masking, translucent golden achene shell, dark grain, light cap and individual gradients. Complete commercial shader unavailable. Our implementation does not reproduce its exact transfer functions. Verified own neutral stock receipt and source `build_neutral.py` / `src/build_strawberry_exterior.py` at the recorded pins: seed longitudinal axis is the original local y, seat offset is 0.19 times thickness, geometry is independently authored. Stock receipt SHA256 `23beb6082f419148578ed556cc8dee0b83799b83f499df6453b161d9bb79bde6`.

## Candidate

22 new skin shader nodes reuse **the exact same** existing skin foundation and global grade groups as the revised cut rim; actual neutral pit field drives darkening, roughness and coat masking. Neutral-space pores and elongated folds drive only shader bump; no geometric displacement. Skin SSS and wax parameters are ARTIST. 20 new achene nodes use normalized coordinates independently recovered from each existing seed's actual seat and anchor axes. New point attributes `sl_achene_local`, `sl_achene_variation`, `sl_achene_gradient` are immutable through the existing deformation/cut path. Deterministic per-seed variation, gradient direction and tilt; independent golden/olive/brown palette, fine grain and light cap, modest SSS and transmission. All 264 original solids preserved. `exterior_material_mode` 0 (default) uses original diagnostic shader; 1 selects coloured exterior on both whole/Fast and Exact. Existing grade drives skin plus revised cap/wall; achenes deliberately independent. No change to geometry, material indices, existing cap, wall or juice shaders. No calyx or hairs in this scene.

## QA

Reopened actual saved scenes with scripts disabled. Whole (modes 0 and 1), longitudinal plane, bite, tilted/deformed (mode 1), all .32 mm, full prior tissue/juice settings. 4/4 poses, 5 mode observations pass actual coordinate/triangle/material-index and existing named attribute snapshots of body, seeds, Fast display meshes and juice. Other material inventories unchanged; original exterior nodes preserved with original output route retained behind switch; shared groups verified. All 46,992 raw achene vertices independently recovered from actual verified anchor/seat basis; max normalized local coordinate error <3e-8. Each retained seed preserves all new shading attributes exactly; 738 retained-seed observations with colour enabled (264/130/227/117). These are comparisons, not fresh contact counts or exhaustive geometry/optical proof. Two initial builder errors (import path and missing helper label) were fixed, logs retained. No fine voxel or exhaustive-pose retest.

## Visual verdict

Five original Cycles PNGs at 700x700, 24 samples, seed1729. Matched whole mode 0 and 1; mode 1 whole, longitudinal cut, bite, achene macro. Same temporary light rig as previous pigment experiment, 700 resolution rather than 560. Actual image hashes/camera/light settings recorded. New whole colour is recognizable; shoulder too pale, highlights broad, red too orange, macro smooth with very weak pore/grain detail; regular seed layout and stylized interior remain. No visual acceptance or Frucht parity. Next add independent calyx/pedicel and improve coordinated saturation, local skin relief/gloss and vessel pattern; retain baseline. No merge.

## Reproduce

Use pinned source and exact owned helpers/stock receipt under `deps/`; archive includes them. Fresh output paths, run sequentially to bound memory.

```sh
blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python build_exterior.py -- exact-pigment.blend deps/stock264.json exact-exterior.blend
for pose in whole plane bite tilted; do
  blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python qa_exterior.py -- exact-pigment.blend exact-exterior.blend "$pose" "qa-$pose.json"
done
for pose in whole plane bite achene; do
  blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python render_exterior.py -- exact-exterior.blend "$pose" 1 1 "$pose-1.png"
done
blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python render_exterior.py -- exact-exterior.blend whole 1 0 whole-0.png
```

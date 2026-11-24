# Exact crown and regional palette continuation — 24 November 2026

**Draft PR50; not accepted for main.** Pinned base `f5cfa38f4aae26635ef25d3856cd8f7641aea7da`. Restored Blender 5.2.4 LTS cd5dc428cce1 locally in ChatGPT from the already existing verified 17-part owner Drive bundle, per current main AGENTS.md. No Mac or paid execution. Source scene exact-exterior.blend SHA256 `d8f86ac4a3fbe69d34ae43a6410583c16c6ddc7d8805886bc28d65d7ed27974a`. All new dimensions/colors ARTIST; no commercial Frucht code, assets or parameter presets.

## Crown
Reused our owned emit_calyx from src/build_strawberry_exterior.py (blob d38ab90b84bd99015b80b9063dd100ee5a64033b) and ExteriorShape (blob 90bb7874680c55f2940d3ff899e6ab555b9b55e7), with pinned stock264 receipt. Eight thick curved sepals and one curved closed stalk use existing common shape GN map and MANIFOLD mesh Boolean with the actual shared cutter. No change to body, original 264 seed stock, cavity, vascular atlas, cut tissue or juice. Actual saved-scene comparisons for four .32 mm poses: baseline geometry/selected attributes and preexisting materials unchanged; all remaining organ meshes passed closed/positive volume and analytic cutter-margin checks. Attachment via triangle BVH contact graph PASS whole, center plane, sphere bite; **FAIL tilted/deformed**: Sepal 5 small detached fragment (~0.03245 mm³). This is not proof of arbitrary pose support or exhaustive self-intersection absence. Do not silently remove physically cut pieces without a defined policy. Hair system not implemented.

## Pigment follow-up
Reuse existing shared warm skin foundation v2, regional tissue v2, grade and foliage ramps. Redder ripe palette, lower stem-shoulder weight (.65 to .36), redder cortex and cut edge, small foliage color correction. Twelve existing socket/ramp values changed; no new shader/geometry nodes, no change to existing rest-space fields, vessel intensity, SSS, roughness, juice, light rig or camera in matched A/B. Separate saved scene preserves original palette. Independent reopened whole and plane evaluated mesh/selected attribute/material-index hashes equal, including crown and juice (2/2 comparisons). Four actual matched 480-square, 8-sample CPU Cycles frames, seed 1729. Pixel change >2/255: 24.93% whole, 19.59% plane (difference, not quality score). The new candidate is visibly redder with less orange shoulder but still waxy and pale at center; regular pale vessel spokes and weak wetness remain. **Visual target not accepted.** Next isolate light rig and optical/structural issues, not indiscriminate hue/brightness sweeps. No new biological calibration or exact reference RGB claim.

## Private durable evidence
[Owner Drive folder](https://drive.google.com/drive/folders/1vcPviq9W_6BhiPfrTbgrTTT25vbnd-CB).
- [Crown scene](https://drive.google.com/file/d/12TsCeS8iV7KhDFd6t-3hVGYpHF4czis9/view), SHA256 `6e7d052440772337dbc9f74b4603d8199f86517d39e7da5463c0bc26945b6984`.
- [Revised palette scene](https://drive.google.com/file/d/19tGyEFr1lcH5y7Gko5FuUbcps49UrcHV/view), SHA256 `d276270ab0794c61715d4f9614ccd2e6a912e13d85e9ae956a2d31eabd37530b`.
- [Matched four-image comparison](https://drive.google.com/file/d/1dHXC6KauVnITf68yfRVGJRYF7055OeJ0/view), SHA256 `29df4560be8309f63ed5cbc8392e7db2899d3ba0b92b809590212d911744546a`.
- [Evidence/source ZIP](https://drive.google.com/file/d/1zRPhOW3jEahQLwP3XzOr-HqptPqJuP0I/view), SHA256 `98cc2c861a7630b46174358c9d65f1affa4c1be9c4ad430de25c66b95d6d7fb7`.
4/4 top-level Drive files downloaded and SHA-matched; ZIP CRC and 49/49 internal manifest entries verified. Contains only owned sources, original renders, numeric QA and logs, no author footage. Initial QA import errors retained and corrected.

## Reproduce
Unpack evidence ZIP in fresh local directory, restore pinned source from previous report, use Blender 5.2.4 with autoexec disabled and fresh outputs. Archive includes source/deps/stock264.json, owned old/src modules, original prior QA/build helpers and render_crown.py. Source scene binary serialization on rebuild may differ; color builder deliberately pins the archived crown scene.
```sh
blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python build_crown.py -- exact-exterior.blend source/deps/stock264.json exact-crown.blend old/src source/deps
for pose in whole plane bite tilted; do
 blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python qa_crown.py -- exact-exterior.blend exact-crown.blend "$pose" "qa-crown-$pose.json"
done
# Use the pinned archived exact-crown.blend for the next command.
blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python build_color.py -- exact-crown.blend exact-crown-color.blend
for pose in whole plane; do
 blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python qa_color.py -- exact-crown.blend exact-crown-color.blend "$pose" "qa-color-$pose.json"
 blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python source/render_crown.py -- exact-crown.blend "$pose" 1 1 "crown-$pose.png"
 blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python source/render_crown.py -- exact-crown-color.blend "$pose" 1 1 "color-$pose.png"
done
```

Current state: geometry experiment with documented negative attachment case; pigment experiment with two verified invariant geometry states. No automatic merge to main.

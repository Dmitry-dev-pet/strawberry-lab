# Exact: regional warm pigment v2 — 24 November 2026

Independent ARTIST continuation of draft PR50 at `1bc4fca72d66f551e0d4578a238f1b4c56d3c5d9`. Pinned source exact-flesh.blend SHA256 `7443e948ca2dc90e23a891f1262ff0afd68bb501f49c4a3d8f323fcff4f2a173`. Candidate exact-pigment.blend SHA256 `267bdaa85d806f383e24875be46f8a056a2841574819776d734509784ffe0915`. Blender 5.2.4 LTS cd5dc428cce1. No author code, graph, asset, image or numeric preset copied into the model or evidence. Main unchanged.

## Reference and design decisions

Reopened owner-supplied Free Kiwi archive SHA256 `aaa218470ab068ed1cb806308d9a4da1d43fd5d9e3de30f6486ac7d204787877` and read `reissbrett.py:5–21,74–111,132–179`, `ordnen_texte.py:84–100,146–152,186–200`, `farbe.py:5–11,54–76,91–105`. The accessible shared code and author descriptions support a warm regional palette, softer vessel halo and less white at the tip, pale pith, red cortex, stalk yellow wedge, skin pigment entering the flesh near the rim, cellular brightness, selective saturation and separate broad rim/narrow edge/highlight corrections. Cavity wall is described as flesh colours, darker and wet, rather than a universally lighter wall. The author also exposes whole-fruit hue/saturation/value and hue on the scattering-radius path. The complete commercial Strawberry shader and its evaluated outputs are not available. Names and descriptions do not specify the entire ordering or transfer functions. The reference is design evidence, not biological calibration.

## Candidate

Three new native shader groups: shared warm skin foundation (11 nodes, rest coordinates, regional ripe patches, speckles, lighter stalk); regional tissue (50 nodes, shared R/H/B atlas and actual dome, axial taper and spatial variation of whitening, warm cortex and pith, cell grain, tapered shoulder, shared skin pigment and two edge corrections); colour grade (8 nodes with global properties). Palette is independently selected and explicitly converted from sRGB to scene-linear. Only cap Base Color route and cavity wall Surface route change; existing cap SSS values and links are unchanged. Wall uses the same regional colour group with a darker moist shader and no cut-edge grading. `pigment_revision=0` default retains prior colour and wall; `1` selects revision with coloured Exact mode. New colour grade controls `fruit_hue_degrees`, `fruit_saturation`, `fruit_brightness` default neutral. These apply only to revised flesh and wall at this stage; global exterior grade and coordinated scattering-radius hue have not been implemented. Shared skin foundation is sampled by the cut pigment, not yet by the actual exterior material. No changes to geometry, vascular atlas, cells, juice or other materials. All numeric parameters ARTIST, not author presets.

## QA and visual verdict

Actual saved scenes reopened with scripts disabled; three poses at .32 mm. Whole checks revision 0 and 1, colour grade driver values and Exact=0 bypass. Plane and bite check revision 1 against prior scene actual body, seed, Fast-display and juice mesh/attribute/material-index snapshots. Original material node data and all original links except the one designated route in each of cap and wall preserved; other materials match. Shared group links verified. Independent axial multiplier evaluated at 19,879 pure cap positions on plane (range .18–1); bite samples do not reach tip. Four observed revision checks total, 3/3 sampled poses pass. Initial full plane validator timed out; isolated reduced tests used. No .20/tilted retest, no exhaustive intersection or direct shader-socket sampling. Initial builder import and HSV output-name errors archived and fixed.

Three fresh actual Cycles PNGs, 560²/24 samples/seed1729; prior plane/macro/bite from exact-flesh mode 2 used as A, matching listed camera, lights, settings and hashes. A not rerendered. Full-image pixels max channel change >2/255: plane 36.67%, macro 99.63%, bite 13.55%. Differences are not realism scores. B is visibly warmer with reduced white at the tip, lighter warm shoulder, less uniform vessel colour and coherent shaded wall. Still overly soft and orange; regular vessel geometry and pale core remain. White diagnostic shell and seeds still contrast with colour. No visual acceptance or Frucht parity. Retain as optional revision; next apply shared skin foundation to exterior and add achene material, then compare full fruit and revise under matched lighting. No main merge.

## Reproduction

Use pinned input and owned dependencies from evidence. Fresh output paths, run sequentially to bound RAM.

```sh
blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python build_pigment.py -- exact-flesh.blend exact-pigment.blend
for pose in whole plane bite; do
  blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python qa_pigment.py -- exact-flesh.blend exact-pigment.blend "$pose" "qa-$pose.json"
done
for pose in plane macro bite; do
  blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python render_pigment.py -- exact-pigment.blend "$pose" 1 1 "$pose-1.png"
done
python compare.py /path/to/exact-flesh-lab
```

Archive contains fresh images, archived matched A images/receipts, source scripts, dependency scripts and logs. No reference archive content included.

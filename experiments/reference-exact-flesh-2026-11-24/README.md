# Exact: tissue pigment and spatial scattering — 24 November 2026

Continuation of draft PR #50 at `292b0145b154b21763e6a379d24f782431a06d07`. Original ARTIST experiment, not a reconstruction of the unavailable commercial Frucht Strawberry shader. Source `exact-optics.blend` SHA-256 `d147164be18c2feecd170568b46df698ad3882c48f7f9645fc758d07fd81a0a0`; candidate `exact-flesh.blend` SHA-256 `7443e948ca2dc90e23a891f1262ff0afd68bb501f49c4a3d8f323fcff4f2a173`. Blender 5.2.4 LTS build cd5dc428cce1. Main unchanged.

## Reference boundary

Reopened owner-provided Free Kiwi archive, SHA-256 `aaa218470ab068ed1cb806308d9a4da1d43fd5d9e3de30f6486ac7d204787877`. Shared `reissbrett.py:5–21,74–111,148–179` and the `fleisch_werte` inventory in `daten/zellen_saft.json` establish separate pigment regions, a soft vascular halo, cellular brightness variation, an axis-dependent scattering-scale map and cut-edge color adjustments. The accessible inventory indicates a Principled SSS tissue shader, rather than a fully transmissive cell volume. It does not establish the complete commercial Strawberry graph. Our implementation uses original nodes and independently selected palette/coefficients; no author asset, code, parameter set or graph is included. The biology specification and the SDF visual-first ADR remain binding; coefficients are not measurements of fruit tissue.

## Controlled experiment

Only the existing cap material receives 36 new shader nodes. A driver-controlled `flesh_material_mode` on the common shape controller selects 0 (original diagnostic clay, default), 1 (regional pigment, zero SSS), 2 (same pigment plus spatial SSS). When Exact is off, the original shader is selected regardless of the material-mode setting; no change to the Fast geometry or its intended appearance. Whole display bypass unchanged. Use the existing neutral vascular ring-relative/core/halo fields, existing cell-dome attribute, original rest position and cut edge distance. Independent smooth ring-to-cortex color gradient with slight spatial modulation; restrained core/halo tint; fine rest-space grain and dome brightness; thin outer red tint. New Principled shader uses a smoothly varying SSS scale 0.13–0.65 in the mm-coordinate scene, weight 0.58 in mode 2, zero in mode 1; relative RGB radius `(1,.43,.24)`. These are artist parameters, not measured optical penetration. Skin, achenes, cavity wall, juice geometry/shader and upstream geometry nodes remain unchanged. This is a cap-material experiment, not full exterior or tissue acceptance.

## Measured evidence

Four actual reopened-scene poses at .32 mm, refinement 2, tissue gain 1, juice gain 1, juice optics mode 2. Whole passes four material-mode observations 0→1→2→0 with initial validator. Plane, bite and tilted/deformed pass actual mesh/material-index/named-attribute snapshots at modes 0 and 2 against the pinned source, including body, achenes, display objects and juice; ten observed comparisons total. Other existing material node/socket/link inventories and original cap nodes match; only the original cap output route is replaced by a selector. Driver values verified, including Exact=0 bypass. The initial import failed for a missing local owned helper and was fixed; the first full repeated liquid validation of plane timed out. For cut retries use exact mesh and named attribute hashes rather than repeat the preceding full liquid topology/occupancy validator; do not claim additional all-mode full geometry validation. Initial QA scripts/logs are archived. Numerical independent radial SSS formula is finite at sampled mesh points; it is not a direct per-pixel shader socket measurement. No new .20 mm tests, arbitrary-pose or exhaustive geometry proof.

Five actual original Cycles images (560², 24 samples, seed 1729): matched plane A/B/C; C macro and C bite. Lighting is deliberately held fixed across the new plane set, at 70% of the earlier diagnostic light powers; not pixel-comparable to earlier lighting. All render receipts verified against actual PNG and scene hashes. A→B >2/255 change 35.425% of full-image pixels; B→C 27.432%, >10/255 1.009%. These are differences, not a realism metric. Separate bite rerun completed after the combined render command timed out. The new red cut is visibly coherent with the modeled vessels, but the pale regular branches and axial region still appear stylized; the macro looks soft and the uncolored shell contrasts sharply with flesh. **Visual parity not achieved; leave material mode 0 as default, retain B/C as research alternatives.** Do not claim biological calibration or merge. Next: coordinated exterior skin and achene material experiment, then visual comparison of full colored fruit and cut; separately assess vessel pattern realism without tuning SSS blindly.

## Reproduce

Use pinned source and fresh output paths. `build_juice.py`, `qa_juice.py`, `deps/build_split.py`, `deps/qa_split.py` are unchanged owned dependencies included in private evidence. Use source tree scripts, or extract the private archive for the exact run layout. Run sequentially to bound memory.

```sh
blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python build_flesh.py -- exact-optics.blend exact-flesh.blend
blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python qa_flesh_initial.py -- exact-optics.blend exact-flesh.blend whole qa-whole-initial.json
for pose in plane bite tilted; do
  blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python qa_flesh.py -- exact-optics.blend exact-flesh.blend "$pose" "qa-$pose.json"
done
for mode in 0 1 2; do
  blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python render_flesh.py -- exact-flesh.blend plane 1 "$mode" "plane-$mode.png"
done
for pose in macro bite; do
  blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python render_flesh.py -- exact-flesh.blend "$pose" 1 2 "$pose-2.png"
done
```

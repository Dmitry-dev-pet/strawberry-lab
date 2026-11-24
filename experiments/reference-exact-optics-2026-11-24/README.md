# Exact juice optics — 24 November 2026

Continuation of PR #50, on the independently built Exact juice geometry. Source exact-juice.blend SHA256 `250732d06c5c2cfbc24f531612cda2672755ba8cad50afddd0a2a894553954fb`; output exact-optics.blend SHA256 `d147164be18c2feecd170568b46df698ad3882c48f7f9645fc758d07fd81a0a0`. Blender 5.2.4 LTS (cd5dc428cce1). Main unchanged. No commercial Frucht asset, code, parameters or node tree imported.

## Source-grounded scope

The earlier project audits of `saft.py`, `reissbrett.py`, and the accessible `daten/zellen_saft.json` confirm separate juice geometry, height-dependent exponential tint and a transparent shadow path. The complete commercial strawberry material is unavailable. Our normal-gap proxy is not necessarily the author's height variable or a physical optical path. See `../sdf-optical-fields-2026-11-23/README.md` and `../sdf-optical-shadow-2026-11-23/README.md` for the earlier source-level evidence.

## Independent optical comparison

Only the existing juice shader receives fourteen new nodes. The original shader and transparent shadow-ray switch are preserved. `juice_optics_mode` is a native driver-controlled custom property on the shared shape controller: 0 = original thin reflective/straight-through interface, 1 = independent full-transmission refractive Principled dielectric (IOR 1.333, roughness .12), 2 = same dielectric with gap-dependent tint. For each linear RGB channel use `T = T0 ** (clamp(gap_mm,0,.20)/.10)`, with artist T0=(.96,.82,.75). Mode 1 forces unit tint. Negative gap yields white. The existing `juice_gain` defaults to off and optics mode defaults to 0. Geometry remains untouched. Open intersecting liquid interfaces are not a closed fluid volume; this is neither calibrated absorption nor a measured ray length, and no physical wetting/caustic proof is claimed.

## Actual QA

Original and candidate scenes reopened with autoexec disabled. Plane and bite at .32 mm, tissue gain 1 and refinement 2; four driver states 0->1->2->0 on each. All eight actual geometry comparisons pass: unchanged body, seeds, Fast-display objects, juice coordinates/triangles/material indices and selected named attributes. The evaluated shader driver matches each setting. Existing transparent shadow route verified. Prior juice geometry receipts remain 6/6; fresh optical comparisons are two poses only, not a repeat of all six. Independently calculated linear RGB attenuation at juice vertices remains finite and matches intended endpoint behavior; this is not direct per-pixel shader-socket sampling. See `qa-plane.json`, `qa-bite.json`.

## Actual renders and verdict

Five original CPU Cycles PNGs, 480x480, 12 samples, seed 1729. Three plane images (A/B/C), two macro images (A/C), matched camera, lighting, gains and geometry within each set. Under the temporary diagnostic light rig on the existing pale diagnostic flesh, refractive change >2/255 in any RGB channel covers 1.706% of plane pixels; additional tint B->C covers 0.154%; A->C covers 1.549% plane and 2.942% macro. No B->C plane pixel changes by >10/255. These are difference metrics, not a quality score. The images show small highlight changes, not convincing strawberry pulp. The pale/high-key diagnostic material and lighting limit conclusions; no production color/SSS, no visual acceptance. Preserve these as research modes rather than adopting mode 2 by default. Next isolate actual flesh pigment and spatial scattering on this fixed geometry. No blind tint-strength sweep.

## Reproduce

Use the pinned source and fresh output names. `build_juice.py` and `qa_juice.py` are unchanged owned dependencies from the geometry milestone; place `build_split.py` and `qa_split.py` under deps/ as in evidence archive. Run sequentially to bound RAM.

```
blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python build_optics.py -- exact-juice.blend exact-optics.blend
for pose in plane bite; do
  blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python qa_optics.py -- exact-juice.blend exact-optics.blend "$pose" "qa-$pose.json"
done
for mode in 0 1 2; do
  blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python render_optics.py -- exact-optics.blend plane 1 "$mode" "plane-$mode.png"
done
for mode in 0 2; do
  blender -b --factory-startup --disable-autoexec -t 4 --python-exit-code 1 --python render_optics.py -- exact-optics.blend macro 1 "$mode" "macro-$mode.png"
done
```
